"""メディアなんとか — 5段階コンテンツパイプライン (Streamlit)
Stage 1 発散 → 2 収束 → 3 企画 → 4 執筆 → 5 発信(X API)
ナビゲーションはサイドバーのラジオで明示切替（タブはプログラム遷移できないため）
"""
from __future__ import annotations
import os
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from core import storage, prompts, gemini_client, x_client, openai_client, outline_parser, diagram_renderer, persona, api_keys

load_dotenv()

st.set_page_config(page_title="メディアなんとか", page_icon=None, layout="wide")


# ============================================================
# パスワード認証ゲート
# APP_PASSWORD が Secrets / env に設定されていれば、起動時に認証を要求。
# 未設定ならゲート無効（ローカル開発用）。
# ============================================================
def _check_password() -> bool:
    expected = api_keys.get_app_password()
    if not expected:
        return True  # APP_PASSWORD 未設定なら認証スキップ
    if st.session_state.get("_authenticated"):
        return True

    # 未認証 → ログイン画面
    st.title("メディアなんとか")
    st.caption("HookHack コンテンツ生成パイプライン")
    st.divider()
    st.subheader("🔒 パスワードを入力してください")

    pwd = st.text_input(
        "パスワード",
        type="password",
        key="_login_pwd",
        label_visibility="collapsed",
        placeholder="パスワード",
    )
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("ログイン", type="primary", width="stretch"):
            if pwd == expected:
                st.session_state["_authenticated"] = True
                if "_login_pwd" in st.session_state:
                    del st.session_state["_login_pwd"]
                st.rerun()
            else:
                st.error("パスワードが違います")
                # 簡易ブルートフォース対策
                import time
                time.sleep(1)
    return False


if not _check_password():
    st.stop()

STAGES = [
    ("diverge", "①発散"),
    ("converge", "②収束"),
    ("outline", "③企画"),
    ("review", "④画像&レビュー"),
    ("write", "⑤執筆"),
    ("publish", "⑥発信"),
]
N_STAGES = len(STAGES)


def goto(stage_key: str) -> None:
    """完了ボタン押下後に次ステージへ自動遷移。
    radio widget が作成される前に session_state を書き換えられないため、
    pending を立てて次runの先頭で current_stage に反映する。"""
    st.session_state["_pending_stage"] = stage_key
    st.rerun()


def _clear_run_widget_state() -> None:
    """Run 切替時に全ステージのエディタ widget の session_state を消す。
    text_area / data_editor / selectbox は key を持つと値が永続するので、
    Run が変わったら新Runの値を value= から読み直させるためにクリアが必須。"""
    targets = (
        "explore_target", "explore_n",
        "cases_editor", "axis_choice",
        "angle_editor", "outline_editor",
        "out_title_", "out_lead", "out_sec_",
        "blog_title", "blog_lead", "blog_editor",
        "sec_text_", "post_text_",
        "img_prompt_", "img_size_", "img_qual_",
        "cl_title_", "cl_items_",
        "tb_title_", "tb_cols_", "tb_rows_",
    )
    for k in list(st.session_state.keys()):
        if any(k == t or k.startswith(t) for t in targets):
            del st.session_state[k]


# ---------- Sidebar ----------
with st.sidebar:
    st.title("メディアなんとか")

    # ---- ログアウト（パスワード認証が有効な時のみ表示）----
    if api_keys.get_app_password():
        if st.button("🚪 ログアウト", help="認証セッションを終了する"):
            st.session_state["_authenticated"] = False
            st.rerun()
        st.divider()

    # ---- モード切替（⓪テーマ探索 と 制作 は完全分離） ----
    mode = st.radio(
        "モード",
        options=["production", "themes"],
        format_func=lambda k: {
            "production": "📝 制作（①〜⑥）",
            "themes": "💡 ⓪テーマ探索（独立）",
        }[k],
        key="app_mode",
        horizontal=False,
    )
    if mode == "themes":
        st.caption("テーマ探索は制作とは完全に独立。生成したテーマは制作に組み込まれません。気になるテーマは手動で『制作のお題』へコピーしてください。")
    else:
        st.caption("HookHack 6段階パイプライン（①〜⑥）")
    st.divider()


# ============================================================
# 制作モードのサイドバー（テーマ探索モード時はスキップ）
# ============================================================
if mode == "production":
  with st.sidebar:

    # ---- 全制作リスト（日付横断） ----
    all_runs = storage.list_all_runs()

    # 現在のactive制作を session_state で管理（日付+run_id）
    if "_current_work_date" not in st.session_state:
        if all_runs:
            st.session_state["_current_work_date"] = all_runs[0]["date"]
        else:
            st.session_state["_current_work_date"] = date.today().isoformat()

    work_date_str = st.session_state["_current_work_date"]
    work_date = date.fromisoformat(work_date_str)

    # その日の runs.json を読み active を確定（initialize で空ならr1作成）
    runs_meta = storage.load_runs_meta(work_date)
    active_id = runs_meta["active"]

    # 全制作リストが空なら今初期化したr1を含めて再取得
    if not all_runs:
        all_runs = storage.list_all_runs()

    # session 切替検出（日付+activeRun の組合せ）
    _session_id = f"{work_date_str}/{active_id}"
    if "_session_id" in st.session_state and st.session_state["_session_id"] != _session_id:
        _clear_run_widget_state()
    st.session_state["_session_id"] = _session_id

    # ---- 制作リスト（全日付横断、最新順） ----
    def _all_label(r: dict) -> str:
        name = (r.get("name") or "").strip()
        topic = (r.get("topic") or "").replace("\n", " ").strip()
        n_done = sum(1 for v in (r.get("stages") or {}).values() if v)
        if name:
            display = name[:30]
        elif topic:
            display = f"({topic[:24]}{'…' if len(topic) > 24 else ''})"
        else:
            display = "（無題・未着手）"
        return f"{display}　[{r['date']}]　〔{n_done}/{N_STAGES}〕"

    cur_pos = next(
        (i for i, r in enumerate(all_runs) if r["date"] == work_date_str and r["id"] == active_id),
        0,
    )

    st.markdown("**制作を選ぶ**")
    selected_pos = st.selectbox(
        "制作を選ぶ",
        list(range(len(all_runs))),
        format_func=lambda i: _all_label(all_runs[i]),
        index=cur_pos if all_runs else 0,
        key="all_runs_selectbox",
        label_visibility="collapsed",
    )
    if all_runs:
        sel = all_runs[selected_pos]
        if sel["date"] != work_date_str or sel["id"] != active_id:
            st.session_state["_current_work_date"] = sel["date"]
            storage.set_active_run(date.fromisoformat(sel["date"]), sel["id"])
            st.rerun()

    # ---- 名前（保存はサイドバー末尾でまとめて、ボタン操作と競合しないように） ----
    current_run_meta = next((r for r in runs_meta["runs"] if r["id"] == active_id), {})
    current_name = current_run_meta.get("name", "")
    new_name = st.text_input(
        "この制作の名前（一覧に表示）",
        value=current_name,
        placeholder="例：動画広告比較記事 v1",
        key=f"run_name_input_{_session_id}",
    )
    main_rename_pending: tuple | None = None
    if new_name != current_name:
        main_rename_pending = (work_date, active_id, new_name)

    st.caption(f"日付: {work_date_str}　/　ID: #{active_id.lstrip('r')}")

    # ---- 操作ボタン ----
    col_new, col_clean, col_del = st.columns([2, 1, 1])
    with col_new:
        if st.button("➕ 新規制作", width="stretch", help="今日の日付で新しい空の制作を作成"):
            today = date.today()
            storage.create_run(today, topic="")
            st.session_state["_current_work_date"] = today.isoformat()
            st.session_state["current_stage"] = "diverge"
            st.rerun()
    with col_clean:
        # 全日付横断で「空・未着手」の制作を集める（active 以外）
        empties_global: list[tuple[str, str]] = []
        for r in all_runs:
            if (r["date"] == work_date_str and r["id"] == active_id):
                continue
            if not (r.get("name") or "").strip() and not (r.get("topic") or "").strip() \
                    and not any((r.get("stages") or {}).values()):
                empties_global.append((r["date"], r["id"]))
        if st.button("🧹", width="stretch",
                     help=f"全日付の空・未着手制作を一括削除（{len(empties_global)}件）",
                     disabled=len(empties_global) == 0):
            for ds, rid in empties_global:
                try:
                    storage.delete_run(date.fromisoformat(ds), rid)
                except Exception:
                    pass
            st.success(f"空制作 {len(empties_global)} 件を削除")
            st.rerun()
    with col_del:
        if st.button("🗑️", width="stretch", help="現在の制作を削除（最後の1つは削除不可）"):
            try:
                storage.delete_run(work_date, active_id)
                st.success("削除しました")
                # 次に表示する制作を選ぶ（最新の1つ）
                remaining = storage.list_all_runs()
                if remaining:
                    st.session_state["_current_work_date"] = remaining[0]["date"]
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # ---- 制作一覧（管理：開く / 名前変更 / 削除） ----
    with st.expander(f"制作一覧 / 管理（全{len(all_runs)}件）"):
        st.caption("名前を直接編集できます。▶で切替、🗑️で削除（2段階確認）。")

        # 1パス目: 全rowのwidgetを描画 + アクションを収集
        # 2パス目: 名前変更を全部保存してからボタンアクションを処理
        # こうしないと、別行の名前textinput blur と▶クリックが同時発火した時に
        # 名前保存のst.rerun()でボタンクリックが失われる
        pending_renames: list[tuple[str, str, str]] = []
        button_action: tuple[str, str, str] | None = None  # (kind, date, id)

        for r in all_runs:
            r_date = r["date"]
            r_id = r["id"]
            name_key = f"_listname_{r_date}_{r_id}"
            del_key = f"_del_pending_{r_date}_{r_id}"
            current_name = r.get("name", "") or ""
            topic_disp = (r.get("topic") or "").replace("\n", " ").strip()
            n_done = sum(1 for v in (r.get("stages") or {}).values() if v)
            is_active = (r_date == work_date_str and r_id == active_id)

            with st.container(border=True):
                meta_l, meta_r = st.columns([3, 1])
                with meta_l:
                    head_text = "● 現在開いています" if is_active else f"[{r_date}]　#{r_id.lstrip('r')}"
                    st.caption(head_text)
                with meta_r:
                    st.caption(f"〔{n_done}/{N_STAGES}〕")

                cols = st.columns([5, 1, 1])
                with cols[0]:
                    new_name = st.text_input(
                        "名前",
                        value=current_name,
                        key=name_key,
                        label_visibility="collapsed",
                        placeholder="（名前を入力）",
                    )
                with cols[1]:
                    if st.button(
                        "▶ 開く",
                        key=f"_open_{r_date}_{r_id}",
                        disabled=is_active,
                        width="stretch",
                        type="primary" if not is_active else "secondary",
                        help="この制作に切替",
                    ):
                        button_action = ("open", r_date, r_id)
                with cols[2]:
                    if st.session_state.get(del_key):
                        if st.button("確定", key=f"_yes_{r_date}_{r_id}", type="primary", width="stretch"):
                            button_action = ("delete_confirm", r_date, r_id)
                        if st.button("✕", key=f"_no_{r_date}_{r_id}", width="stretch"):
                            button_action = ("delete_cancel", r_date, r_id)
                    else:
                        if st.button("🗑️", key=f"_del_{r_date}_{r_id}", help="削除（2段階確認）", width="stretch"):
                            button_action = ("delete_init", r_date, r_id)

                if topic_disp:
                    truncated = topic_disp[:70] + ("…" if len(topic_disp) > 70 else "")
                    st.caption(f"お題: {truncated}")

            if new_name != current_name:
                pending_renames.append((r_date, r_id, new_name))

        # 全行描画後にまとめて処理（管理一覧の expander 内）
        # main_rename_pending（メイン名前欄）も同時処理して、blur+クリック衝突を解消
        if main_rename_pending or pending_renames or button_action:
            if main_rename_pending:
                wd, ai, nm = main_rename_pending
                try:
                    storage.update_run_name(wd, ai, nm)
                except Exception as e:
                    st.error(f"メイン名前保存エラー: {e}")
            for rd, rid, nm in pending_renames:
                try:
                    storage.update_run_name(date.fromisoformat(rd), rid, nm)
                except Exception as e:
                    st.error(f"一覧名前保存エラー: {e}")
            if button_action:
                kind, ad, aid = button_action
                if kind == "open":
                    try:
                        storage.set_active_run(date.fromisoformat(ad), aid)
                        st.session_state["_current_work_date"] = ad
                        st.session_state["current_stage"] = "diverge"
                        _clear_run_widget_state()
                    except Exception as e:
                        st.error(f"開く失敗: {e}")
                elif kind == "delete_init":
                    st.session_state[f"_del_pending_{ad}_{aid}"] = True
                elif kind == "delete_confirm":
                    try:
                        storage.delete_run(date.fromisoformat(ad), aid)
                        if (ad, aid) == (work_date_str, active_id):
                            remaining = storage.list_all_runs()
                            if remaining:
                                st.session_state["_current_work_date"] = remaining[0]["date"]
                        if f"_del_pending_{ad}_{aid}" in st.session_state:
                            del st.session_state[f"_del_pending_{ad}_{aid}"]
                    except ValueError as e:
                        st.error(str(e))
                elif kind == "delete_cancel":
                    if f"_del_pending_{ad}_{aid}" in st.session_state:
                        del st.session_state[f"_del_pending_{ad}_{aid}"]
            st.rerun()

    st.divider()
    state = storage.load_state(work_date)
    stages_done = state.get("stages", {})

    topic = st.text_area(
        "お題（誰に何を）",
        value=state.get("topic", ""),
        placeholder="例: D2C向けに動画クリエイティブのAI制作で何が成果差を生むか",
        height=80,
    )
    if topic != state.get("topic", ""):
        state["topic"] = topic
        storage.save_state(work_date, state)

    st.divider()
    st.subheader("ステージ（クリックで切替）")

    def _radio_label(key: str, label: str) -> str:
        mark = "✅" if stages_done.get(key) else "⬜"
        return f"{mark} {label}"

    stage_keys = [k for k, _ in STAGES]
    if "current_stage" not in st.session_state:
        st.session_state["current_stage"] = "diverge"
    # pending遷移要求があればここで反映（radio生成前なのでOK）
    if "_pending_stage" in st.session_state:
        st.session_state["current_stage"] = st.session_state.pop("_pending_stage")

    current_stage = st.radio(
        "ステージ",
        options=stage_keys,
        format_func=lambda k: _radio_label(k, dict(STAGES)[k]),
        key="current_stage",
        label_visibility="collapsed",
    )

    st.divider()
    with st.expander("📦 データのバックアップ / 復元"):
        st.caption(
            "データは Supabase（クラウドDB）に保存されているため、Streamlit Cloud の再起動でも消えません。"
            "ローカルにも一応バックアップしたい場合は ZIP ダウンロードを使ってください。"
        )

        from datetime import datetime as _dt
        if st.button("📥 全データを ZIP でダウンロード", width="stretch", key="_dl_zip_btn"):
            try:
                zip_bytes = storage.export_zip_bytes()
                st.download_button(
                    "↓ ダウンロード（クリック）",
                    data=zip_bytes,
                    file_name=f"media_data_{_dt.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    width="stretch",
                    key="_dl_zip_actual",
                )
            except Exception as e:
                st.error(f"バックアップ失敗: {e}")

        st.divider()
        st.caption("以前ダウンロードした ZIP を復元（**同じキーのデータは上書きされます**）")
        uploaded = st.file_uploader("ZIP を選択", type=["zip"], key="_upload_zip", label_visibility="collapsed")
        if uploaded is not None:
            if st.button("⚠️ 復元する（同名データは上書き）", width="stretch"):
                try:
                    n = storage.import_zip_bytes(uploaded.read())
                    st.success(f"{n} 件を復元しました。ページを再読み込みしてください。")
                    st.rerun()
                except Exception as e:
                    st.error(f"復元エラー: {e}")

    with st.expander("Persona設定（人格・文体）"):
        cfg = persona.load()
        st.caption("config/persona.json — 全プロンプトに自動注入")
        st.markdown(f"**記事**: {cfg.get('blog', {}).get('voice', '?')} / 一人称「{cfg.get('blog', {}).get('first_person', '?')}」")
        st.markdown(f"**X投稿**: {cfg.get('posts', {}).get('voice', '?')} / 一人称「{cfg.get('posts', {}).get('first_person', '?')}」")
        st.markdown(f"**読者**: {cfg.get('blog', {}).get('reader_persona', '')[:60]}…")
        st.markdown(f"**NGワード**: {', '.join(cfg.get('blog', {}).get('ng_phrases', []))}")
        with st.expander("JSON編集"):
            import json as _json
            edited_json = st.text_area(
                "persona.json",
                value=_json.dumps(cfg, ensure_ascii=False, indent=2),
                height=320,
                key="persona_json_editor",
                label_visibility="collapsed",
            )
            if st.button("保存"):
                try:
                    parsed = _json.loads(edited_json)
                    persona.save(parsed)
                    st.success("保存しました（次の生成から反映）")
                except _json.JSONDecodeError as e:
                    st.error(f"JSONエラー: {e}")

    # ---- ディープリサーチモード（Geminiの拡張機能） ----
    st.checkbox(
        "🔍 ディープリサーチモード（Gemini）",
        value=False,
        key="deep_research_mode",
        help=(
            "ON にすると Gemini が Google検索でリアルタイム情報を取得しながら生成し、"
            "thinking budget も最大化します（応答時間が30〜120秒に延びます）。"
            "①発散・②収束で精度UPに有効。"
        ),
    )

    with st.expander("API設定（このセッションのみ保持・サーバー保存なし）"):
        st.caption("各キーはあなたのブラウザセッションにのみ保持され、サーバーには記録されません。タブを閉じると消えます。")

        # 入力フィールド一覧（環境変数名 / 表示名 / リンク / type）
        key_specs = [
            ("GEMINI_API_KEY", "Gemini API Key", "https://aistudio.google.com/app/apikey"),
            ("OPENAI_API_KEY", "OpenAI API Key", "https://platform.openai.com/api-keys"),
            ("X_API_KEY", "X (Twitter) API Key（Consumer Key）", "https://developer.x.com/"),
            ("X_API_SECRET", "X API Secret（Consumer Secret）", ""),
            ("X_ACCESS_TOKEN", "X Access Token（Read+Write）", ""),
            ("X_ACCESS_TOKEN_SECRET", "X Access Token Secret", ""),
        ]

        for env_name, label, url in key_specs:
            sk_name = f"key_{env_name}"
            existing_val = st.session_state.get(sk_name, "") or os.environ.get(env_name, "")
            new_val = st.text_input(
                label,
                value=existing_val,
                type="password",
                key=f"_input_{env_name}",
                help=f"取得元: {url}" if url else None,
                placeholder="未設定" if not existing_val else None,
            )
            if new_val != existing_val:
                st.session_state[sk_name] = new_val

        st.divider()
        st.markdown("**現在の状態**")
        st.write(f"Gemini: {'✅' if gemini_client.keys_configured() else '❌'}　モデル: `{os.environ.get('GEMINI_MODEL', 'gemini-2.5-pro')}`")
        st.write(f"OpenAI: {'✅' if openai_client.keys_configured() else '❌'}　画像: `{os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-1')}` / テキスト: `{os.environ.get('OPENAI_TEXT_MODEL', 'gpt-4o')}`")
        st.write(f"X API: {'✅' if x_client.keys_configured() else '❌'}")
        if not x_client.keys_configured():
            st.caption(f"不足: {x_client.missing_keys()}")


def stage_done_banner(stage_key: str, next_label: str | None) -> None:
    if stages_done.get(stage_key):
        if next_label:
            st.success(f"✅ このステージは完了済 → 左サイドバーで **{next_label}** を選んでください（このまま再生成・再編集してもOK）")
        else:
            st.success("✅ このステージは完了済")


# ============================================================
# ⓪テーマ探索モード（制作とは独立、参照ツール）
# ============================================================
if mode == "themes":
    st.header("⓪テーマ探索（独立）")
    st.caption(
        f"ChatGPT ({os.environ.get('OPENAI_TEXT_MODEL', 'gpt-5.5')}) でテーマ案を発散。"
        f"ここで生成されたテーマは制作には組み込まれません。気に入ったテーマがあれば、"
        f"右上のモードを「制作」に切り替えてからお題欄に手動で貼ってください。"
    )

    history = storage.load_themes_global()

    # ---- 新規生成 ----
    with st.container(border=True):
        st.markdown("**新しいテーマ探索**")
        target = st.text_area(
            "ターゲット読者（誰に向けた記事の候補を知りたい？）",
            value="",
            placeholder="例：動画広告を始めたい中小企業の経営層。広告費は月50万〜200万、内製化はまだ。Meta広告は出しているが動画クリエイティブは未着手。",
            height=100,
            key="explore_target_v2",
        )
        col_n, col_btn = st.columns([1, 2])
        with col_n:
            n_themes = st.number_input("提案数", 4, 15, 8, key="explore_n_v2")
        with col_btn:
            if st.button(
                f"ChatGPT ({os.environ.get('OPENAI_TEXT_MODEL', 'gpt-5.5')}) でテーマ案を発散",
                type="primary",
                disabled=not target or not openai_client.keys_configured(),
                width="stretch",
            ):
                with st.spinner("ChatGPTがテーマを発散しています..."):
                    try:
                        themes = openai_client.generate_json(
                            prompts.research_theme_prompt(target, n_themes)
                        )
                        if not isinstance(themes, list):
                            st.error(f"想定外の出力（list でない）: {str(themes)[:200]}")
                        else:
                            from datetime import datetime
                            new_entry = {
                                "id": f"t-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                                "created_at": datetime.now().isoformat(timespec="seconds"),
                                "target": target,
                                "themes": themes,
                            }
                            history = [new_entry] + history
                            storage.save_themes_global(history)
                            st.session_state["_explore_view_id"] = new_entry["id"]
                            st.success(f"テーマ {len(themes)} 件生成 → 履歴に追加")
                            st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")

        if not openai_client.keys_configured():
            st.warning("OpenAIキーが未設定。`.env` に OPENAI_API_KEY を追加してください。")

    # ---- 履歴 + 表示 ----
    if history:
        st.divider()
        st.subheader(f"探索履歴（{len(history)}件）")
        ids = [e["id"] for e in history]
        labels = {
            e["id"]: f"{e.get('created_at', '')} — {(e.get('target', '') or '')[:36]}…"
            for e in history
        }

        if "_explore_view_id" not in st.session_state or st.session_state["_explore_view_id"] not in ids:
            st.session_state["_explore_view_id"] = ids[0]

        col_pick, col_del = st.columns([4, 1])
        with col_pick:
            sel_id = st.selectbox(
                "表示する探索結果",
                ids,
                format_func=lambda i: labels[i],
                index=ids.index(st.session_state["_explore_view_id"]),
                key="explore_history_pick",
            )
            st.session_state["_explore_view_id"] = sel_id
        with col_del:
            if st.button("🗑️ この履歴を削除", width="stretch"):
                history = [e for e in history if e["id"] != sel_id]
                storage.save_themes_global(history)
                if history:
                    st.session_state["_explore_view_id"] = history[0]["id"]
                st.rerun()

        entry = next((e for e in history if e["id"] == sel_id), None)
        if entry:
            st.caption(f"ターゲット: {entry.get('target', '')[:200]}")
            st.divider()
            for i, t in enumerate(entry.get("themes", [])):
                with st.container(border=True):
                    st.markdown(f"**{t.get('title', '?')}**")
                    st.caption(f"切り口: {t.get('angle', '')}")
                    st.caption(f"このターゲットの関心: {t.get('why_for_target', '')}")
                    st.caption(
                        f"HookHack目的: {t.get('hookhack_goal', '')}　/　反響予想: {t.get('estimated_appeal', '')}"
                    )
                    # 制作のお題欄に手動コピーするための見やすい box
                    with st.expander("📋 タイトル文言（制作のお題欄にコピー用）"):
                        st.code(t.get("title", ""), language="text")
    else:
        st.info("まだ探索履歴がありません。上のフォームでターゲットを入力して『発散』を押してください。")


# ============================================================
# Stage 1: 発散
# ============================================================
elif current_stage == "diverge":
    st.header("①発散 — 具体事例の列挙")
    st.caption("Geminiで世界の事例を集める → スプレッドシートで自由に編集（行追加・列追加可）")
    stage_done_banner("diverge", "②収束")

    if not topic:
        st.warning("左サイドバーで『お題』を入力してください")
    else:
        col_a, col_b = st.columns([1, 3])
        with col_a:
            n_cases = st.number_input("生成件数", 4, 20, 12)
            if st.button("Geminiで事例を生成", type="primary", width="stretch"):
                with st.spinner("Geminiが事例を集めています..."):
                    try:
                        cases = gemini_client.generate_json(prompts.diverge_prompt(topic, n_cases))
                        if not isinstance(cases, list):
                            st.error(f"想定外の出力: {cases}")
                        else:
                            df = pd.DataFrame(cases)
                            for col in storage.DEFAULT_CASE_COLUMNS:
                                if col not in df.columns:
                                    df[col] = ""
                            storage.save_cases(work_date, df)
                            storage.snapshot_original(storage.cases_path(work_date))
                            st.success(f"{len(df)} 件生成しました")
                            st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")
        with col_b:
            st.caption(f"保存先: `{storage.cases_path(work_date)}`")

        df = storage.load_cases(work_date)
        if df.empty:
            st.info("まだ事例がありません。左の『Geminiで事例を生成』を押すか、下の表に直接入力できます。")
            df = pd.DataFrame(columns=storage.DEFAULT_CASE_COLUMNS)

        edited = st.data_editor(
            df,
            num_rows="dynamic",
            width="stretch",
            height=500,
            key="cases_editor",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("シートを保存", width="stretch"):
                storage.save_cases(work_date, edited)
                st.success("保存しました")
        with c2:
            if st.button("①発散を完了 → ②収束へ", type="primary", width="stretch"):
                storage.save_cases(work_date, edited)
                storage.mark_stage(work_date, "diverge", True)
                goto("converge")


# ============================================================
# Stage 2: 収束
# ============================================================
elif current_stage == "converge":
    st.header("②収束 — 軸を選んで角度を決める")
    st.caption("事例群をどう束ねるか、軸候補をGeminiが提案 → ユーザーが選択 → 角度（angle）を確定")
    stage_done_banner("converge", "③企画")

    df = storage.load_cases(work_date)
    if df.empty:
        st.warning("①発散の事例シートがまだ空です")
    else:
        st.write(f"事例 {len(df)} 件を対象に収束します")

        if st.button("軸候補を提案", type="primary"):
            with st.spinner("Geminiが軸を考えています..."):
                try:
                    axes = gemini_client.generate_json(
                        prompts.axes_prompt(topic, df.to_csv(index=True, index_label="row"))
                    )
                    storage.save_axes(work_date, axes)
                    storage.snapshot_original(storage.axes_path(work_date))
                    st.success(f"軸 {len(axes)} 個提案")
                    st.rerun()
                except Exception as e:
                    st.error(f"エラー: {e}")

        axes = storage.load_axes(work_date)

        if axes:
            with st.expander("🔁 全軸を再考（Geminiに追加指示を出す）", expanded=False):
                st.caption(
                    "前回の軸候補がイマイチなら、ここに「もっと若手社員視点で」「採用観点に寄せて」など"
                    "の指示を入れて作り直させる。読み手の需要に当てに行くための切り口調整用。"
                )
                feedback_all = st.text_area(
                    "Geminiへの再考指示",
                    placeholder="例: もっと若手社員の悩みに寄せて。業種別じゃなくて、判断タイミング軸で。",
                    height=100,
                    key="axes_refeed_feedback",
                    label_visibility="collapsed",
                )
                if st.button("この指示で全軸を作り直す", key="axes_refeed_btn"):
                    if not feedback_all.strip():
                        st.warning("再考指示を入力してください")
                    else:
                        with st.spinner("Geminiが軸を作り直しています..."):
                            try:
                                new_axes = gemini_client.generate_json(
                                    prompts.axes_prompt(
                                        topic,
                                        df.to_csv(index=True, index_label="row"),
                                        user_feedback=feedback_all,
                                    )
                                )
                                storage.save_axes(work_date, new_axes)
                                storage.snapshot_original(storage.axes_path(work_date))
                                st.success(f"軸 {len(new_axes)} 個を再生成しました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")

            st.subheader(f"軸候補 × {len(axes)}")
            st.caption("各軸が **お題にどう沿っているか**（topic_alignment）を確認して、1つ選んでください。")

            # カード一覧 + 選択用ラジオを下に配置
            for i, ax in enumerate(axes):
                with st.container(border=True):
                    st.markdown(f"**#{i + 1}　{ax.get('name', '?')}**")
                    align = ax.get("topic_alignment", "（topic_alignmentが空）")
                    st.markdown(f"🎯 **お題への沿い方**: {align}")
                    st.caption(f"束ね方: {ax.get('description', '')}")
                    groups = ax.get("groups", [])
                    if groups:
                        st.caption("グループ（H2候補）: " + " / ".join(f"`{g}`" for g in groups))
                    st.caption(f"HookHack着地: {ax.get('hookhack_angle', '')}")

            chosen_idx = st.radio(
                "どの軸で記事を企画する？",
                options=list(range(len(axes))),
                format_func=lambda i: f"#{i + 1}　{axes[i].get('name', '?')}",
                key="axis_choice",
            )
            chosen = axes[chosen_idx]
            with st.expander("選択中の軸の詳細（生JSON）"):
                st.json(chosen)

            # ---- この軸だけをGeminiに再考させる ----
            with st.expander("🔁 この軸だけを再考（Geminiに指示）", expanded=False):
                st.caption(
                    "選択中の軸（テーマ自体）だけを作り直す。「もっと採用観点に寄せて」"
                    "「失敗パターンの分類軸に変えて」など、読み手の需要に当てるための切り口指示。"
                )
                feedback_one = st.text_area(
                    "この軸への再考指示",
                    placeholder="例: 採用観点ではなく、ROI判断のフレームで切り直して。",
                    height=100,
                    key=f"axis_refine_feedback_{chosen_idx}",
                    label_visibility="collapsed",
                )
                if st.button(
                    "この軸を作り直す", key=f"axis_refine_btn_{chosen_idx}"
                ):
                    if not feedback_one.strip():
                        st.warning("再考指示を入力してください")
                    else:
                        with st.spinner("Geminiがこの軸を作り直しています..."):
                            try:
                                new_axis = gemini_client.generate_json(
                                    prompts.axis_refine_prompt(
                                        topic,
                                        df.to_csv(index=True, index_label="row"),
                                        chosen,
                                        feedback_one,
                                    )
                                )
                                # 配列で返ってきたら先頭を採用（ガード）
                                if isinstance(new_axis, list) and new_axis:
                                    new_axis = new_axis[0]
                                axes[chosen_idx] = new_axis
                                storage.save_axes(work_date, axes)
                                storage.snapshot_original(storage.axes_path(work_date))
                                st.success("軸を再生成しました")
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")

            # ---- 軸の「束ね方（description）」編集 ----
            st.divider()
            st.markdown("**この軸の「束ね方（description）」を編集**")
            st.caption("事例を見て、軸の切り口（束ね方の説明）を自分で調整できます。後段のangle生成にも反映されます。")
            original_desc = chosen.get("original_description", chosen.get("description", ""))
            edited_desc = st.text_area(
                "束ね方（description）",
                value=chosen.get("description", ""),
                height=100,
                key=f"axis_desc_editor_{chosen_idx}",
                label_visibility="collapsed",
            )
            col_desc_save, col_desc_reset = st.columns(2)
            with col_desc_save:
                if st.button("束ね方を保存", width="stretch", key=f"save_desc_{chosen_idx}"):
                    if "original_description" not in axes[chosen_idx]:
                        axes[chosen_idx]["original_description"] = chosen.get("description", "")
                    axes[chosen_idx]["description"] = edited_desc
                    storage.save_axes(work_date, axes)
                    st.success("束ね方を保存しました")
                    st.rerun()
            with col_desc_reset:
                if st.button("Gemini提案にリセット", width="stretch", key=f"reset_desc_{chosen_idx}"):
                    axes[chosen_idx]["description"] = original_desc
                    storage.save_axes(work_date, axes)
                    st.success("リセットしました")
                    st.rerun()

            # ---- 事例×グループ振り分け編集 ----
            if "assignments" in chosen and chosen.get("groups"):
                st.divider()
                st.markdown("**事例 × グループの振り分け**（Gemini提案を編集できます）")
                st.caption("「現在のグループ」列のセルをクリックで変更。元のGemini提案は読み取り専用で隣に表示。")

                groups = chosen.get("groups", [])
                assignments = {str(k): v for k, v in chosen.get("assignments", {}).items()}
                original = {str(k): v for k, v in chosen.get("original_assignments", assignments).items()}

                cases_view = df.reset_index().rename(columns={"index": "row"})
                cases_view["row"] = cases_view["row"].astype(str)
                cases_view["元のGemini提案"] = cases_view["row"].map(original).fillna("（未割当）")
                cases_view["現在のグループ"] = cases_view["row"].map(assignments).fillna(groups[0] if groups else "")

                # 不明なグループ値（編集中に groups から消えた等）は groups[0] に寄せる
                cases_view["現在のグループ"] = cases_view["現在のグループ"].where(
                    cases_view["現在のグループ"].isin(groups), groups[0] if groups else ""
                )

                show_cols = ["row"]
                for c in ["誰が", "何を", "結果_数字"]:
                    if c in cases_view.columns:
                        show_cols.append(c)
                show_cols += ["元のGemini提案", "現在のグループ"]

                column_config = {
                    "row": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "元のGemini提案": st.column_config.TextColumn("元のGemini提案", disabled=True),
                    "現在のグループ": st.column_config.SelectboxColumn(
                        "現在のグループ", options=groups, required=True
                    ),
                }
                for c in ["誰が", "何を", "結果_数字"]:
                    if c in show_cols:
                        column_config[c] = st.column_config.TextColumn(c, disabled=True)

                edited = st.data_editor(
                    cases_view[show_cols],
                    column_config=column_config,
                    hide_index=True,
                    width="stretch",
                    key=f"assignments_editor_{chosen_idx}",
                )

                col_save, col_reset = st.columns(2)
                with col_save:
                    if st.button("振り分けを保存", width="stretch", key=f"save_assign_{chosen_idx}"):
                        new_assignments = dict(zip(edited["row"], edited["現在のグループ"]))
                        axes[chosen_idx]["assignments"] = new_assignments
                        storage.save_axes(work_date, axes)
                        st.success("保存しました")
                        st.rerun()
                with col_reset:
                    if st.button("Gemini提案にリセット", width="stretch", key=f"reset_assign_{chosen_idx}"):
                        axes[chosen_idx]["assignments"] = dict(original)
                        storage.save_axes(work_date, axes)
                        st.success("リセットしました")
                        st.rerun()

            if st.button("この軸で角度（angle）を確定 → ③企画へ", type="primary"):
                with st.spinner("Geminiが角度を組み立てています..."):
                    try:
                        angle_md = gemini_client.generate_text(
                            prompts.angle_prompt(topic, df.to_csv(index=False), chosen)
                        )
                        angle_md = persona.sanitize_emoji(angle_md)
                        storage.save_angle(work_date, angle_md)
                        storage.snapshot_original(storage.angle_path(work_date))
                        st.session_state["angle_editor"] = angle_md
                        storage.mark_stage(work_date, "converge", True)
                        goto("outline")
                    except Exception as e:
                        st.error(f"エラー: {e}")

        angle = storage.load_angle(work_date)
        if angle:
            st.divider()
            st.subheader("確定した角度（編集可）")
            edited_angle = st.text_area(
                "angle.md",
                value=angle,
                height=400,
                key="angle_editor",
                label_visibility="collapsed",
            )
            if st.button("角度を保存"):
                storage.save_angle(work_date, edited_angle)
                st.success("保存しました")


# ============================================================
# Stage 3: 企画
# ============================================================
elif current_stage == "outline":
    st.header("③企画 — 章立て")
    st.caption("H1（タイトル候補）/ リード文 / H2セクション ごとに分けて編集できます")
    stage_done_banner("outline", "④画像&レビュー")

    angle = storage.load_angle(work_date)
    if not angle:
        st.warning("②収束で角度が確定していません")
    else:
        with st.expander("角度（参考）"):
            st.markdown(angle)

        # ---- ①事例リファレンス（編集中に常時参照できる） ----
        cases_df = storage.load_cases(work_date)
        if not cases_df.empty:
            with st.expander(f"📚 ①発散の事例リファレンス × {len(cases_df)}（コピペ用）", expanded=False):
                st.caption("各H2の「内容メモ」に貼るために、ここから事例を探してコピーしてください。")
                ref_cols = [c for c in ["誰が", "何を", "結果_数字", "示唆", "国_地域"] if c in cases_df.columns]
                if ref_cols:
                    st.dataframe(cases_df[ref_cols], hide_index=False, width="stretch")
                else:
                    st.dataframe(cases_df, hide_index=False, width="stretch")

        outline_md = storage.load_outline(work_date)

        # ---- 生成ボタン ----
        col_gen, col_info = st.columns([1, 2])
        with col_gen:
            btn_label = "🔁 章立てを再生成" if outline_md else "章立てを生成"
            if st.button(btn_label, type="primary" if not outline_md else "secondary", width="stretch"):
                with st.spinner("Geminiが章立てを組んでいます..."):
                    try:
                        cases_csv_for_outline = (
                            cases_df.to_csv(index=False) if not cases_df.empty else ""
                        )
                        outline_md = gemini_client.generate_text(
                            prompts.outline_prompt(topic, angle, cases_csv_for_outline)
                        )
                        outline_md = persona.sanitize_emoji(outline_md)
                        storage.save_outline(work_date, outline_md)
                        storage.snapshot_original(storage.outline_path(work_date))
                        # 構造化エディタの session_state をクリアして file から再ロード
                        for k in list(st.session_state.keys()):
                            if k.startswith("out_"):
                                del st.session_state[k]
                        st.success("章立て生成完了")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")
        with col_info:
            st.caption(f"保存先: `{storage.outline_path(work_date)}`")

        if outline_md:
            structured = outline_parser.parse_full(outline_md)

            # ---- H1 タイトル候補 ----
            st.divider()
            st.subheader("H1　タイトル候補")
            st.caption("3案ほど。最終的に⑤執筆で1つに決めます。")
            titles = list(structured.get("title_candidates", []))
            while len(titles) < 3:
                titles.append("")
            edited_titles: list[str] = []
            for i, t in enumerate(titles[:5]):
                v = st.text_input(
                    f"案 {i+1}",
                    value=t,
                    key=f"out_title_{i}",
                    label_visibility="visible",
                )
                edited_titles.append(v)

            # ---- リード方向性 ----
            st.divider()
            st.subheader("リード文の方向性")
            st.caption("200字前後。問題提起 → この記事で得られるもの。")
            edited_lead = st.text_area(
                "リード（編集可）",
                value=structured.get("lead_direction", ""),
                height=140,
                key="out_lead",
                label_visibility="collapsed",
            )

            # ---- H2 セクション ----
            st.divider()
            sections = structured.get("sections", [])
            st.subheader(f"H2 セクション × {len(sections)}")
            st.caption("各セクションごとに「タイトル / 推定字数 / 内容メモ」を編集できます。⑤執筆ではここのメモを元に本文が書かれます。")

            # 並び替え対象（通常H2のみ。self_practice / summary / cta は固定位置）
            FIXED_IDS = {"self_practice", "summary", "cta"}

            def _move_section(from_idx: int, to_idx: int) -> None:
                """sections を並び替えて保存し、out_sec_* state をクリアして rerun。"""
                current_struct = {
                    "title_candidates": [t for t in edited_titles if t.strip()],
                    "lead_direction": edited_lead,
                    "sections": [
                        {
                            "id": s.get("id", ""),
                            "title": st.session_state.get(f"out_sec_title_{i}", s.get("title", "")),
                            "target_chars": int(st.session_state.get(f"out_sec_target_{i}", s.get("target_chars", 500))),
                            "memo": st.session_state.get(f"out_sec_memo_{i}", s.get("memo", "")),
                        }
                        for i, s in enumerate(sections)
                    ],
                }
                secs = current_struct["sections"]
                if 0 <= to_idx < len(secs):
                    secs[from_idx], secs[to_idx] = secs[to_idx], secs[from_idx]
                new_md = outline_parser.serialize_full(current_struct)
                storage.save_outline(work_date, new_md)
                for k in list(st.session_state.keys()):
                    if k.startswith("out_sec_"):
                        del st.session_state[k]
                st.rerun()

            edited_sections: list[dict] = []
            for idx, sec in enumerate(sections):
                # ID から種別を判定してアイコン的なラベル
                sid = sec.get("id", "")
                if sid == "self_practice":
                    role = "📌 自社実践"
                elif sid == "summary":
                    role = "🎯 まとめ"
                elif sid == "cta":
                    role = "📣 CTA"
                else:
                    role = f"H2_{idx + 1}"

                is_movable = sid not in FIXED_IDS

                with st.container(border=True):
                    head_l, head_r, head_up, head_down, head_d = st.columns([4, 1, 0.5, 0.5, 1])
                    with head_l:
                        sec_title = st.text_input(
                            f"{role} タイトル",
                            value=sec.get("title", ""),
                            key=f"out_sec_title_{idx}",
                            label_visibility="visible",
                        )
                    with head_r:
                        target = st.number_input(
                            "推定字数",
                            min_value=100, max_value=3000, step=50,
                            value=int(sec.get("target_chars") or 500),
                            key=f"out_sec_target_{idx}",
                        )
                    with head_up:
                        st.write("")  # 縦位置調整
                        up_clicked = st.button(
                            "⬆️",
                            key=f"out_sec_up_{idx}",
                            help="このセクションを1つ上へ",
                            disabled=not is_movable or idx == 0,
                            width="stretch",
                        )
                    with head_down:
                        st.write("")
                        down_clicked = st.button(
                            "⬇️",
                            key=f"out_sec_down_{idx}",
                            help="このセクションを1つ下へ",
                            disabled=not is_movable or idx >= len(sections) - 1,
                            width="stretch",
                        )
                    with head_d:
                        st.write("")
                        delete_clicked = st.button(
                            "🗑️ 削除",
                            key=f"out_sec_del_{idx}",
                            help="このセクションを削除",
                            width="stretch",
                        )

                    sec_memo = st.text_area(
                        "内容メモ（書く要点・使う事例・実装ステップなど。1行=1ポイント）",
                        value=sec.get("memo", ""),
                        height=280,
                        key=f"out_sec_memo_{idx}",
                    )

                    if up_clicked:
                        _move_section(idx, idx - 1)
                    if down_clicked:
                        _move_section(idx, idx + 1)

                    if delete_clicked:
                        # 現在の編集状態を保ったまま、idx だけ抜く
                        new_struct = {
                            "title_candidates": [t for t in edited_titles if t.strip()],
                            "lead_direction": edited_lead,
                            "sections": [
                                {
                                    "id": s.get("id", ""),
                                    "title": st.session_state.get(f"out_sec_title_{i}", s.get("title", "")),
                                    "target_chars": int(st.session_state.get(f"out_sec_target_{i}", s.get("target_chars", 500))),
                                    "memo": st.session_state.get(f"out_sec_memo_{i}", s.get("memo", "")),
                                }
                                for i, s in enumerate(sections) if i != idx
                            ],
                        }
                        new_md = outline_parser.serialize_full(new_struct)
                        storage.save_outline(work_date, new_md)
                        # 構造変更 → 全 out_sec_* を再読込のため削除
                        for k in list(st.session_state.keys()):
                            if k.startswith("out_sec_"):
                                del st.session_state[k]
                        st.rerun()

                    edited_sections.append({
                        "id": sec.get("id", f"sec_{idx}"),
                        "title": sec_title,
                        "target_chars": int(target),
                        "memo": sec_memo,
                    })

            # ---- セクション追加 ----
            if st.button("➕ H2セクションを追加"):
                new_struct = {
                    "title_candidates": [t for t in edited_titles if t.strip()],
                    "lead_direction": edited_lead,
                    "sections": edited_sections + [{
                        "id": f"sec_{len(edited_sections) + 1}",
                        "title": "",
                        "target_chars": 500,
                        "memo": "",
                    }],
                }
                new_md = outline_parser.serialize_full(new_struct)
                storage.save_outline(work_date, new_md)
                for k in list(st.session_state.keys()):
                    if k.startswith("out_sec_"):
                        del st.session_state[k]
                st.rerun()

            # ---- 保存 / 完了 ----
            st.divider()
            new_struct = {
                "title_candidates": [t for t in edited_titles if t.strip()],
                "lead_direction": edited_lead,
                "sections": edited_sections,
            }
            cs, cn = st.columns(2)
            with cs:
                if st.button("章立てを保存", width="stretch"):
                    new_md = outline_parser.serialize_full(new_struct)
                    storage.save_outline(work_date, new_md)
                    st.success("保存しました")
            with cn:
                if st.button("③企画を完了 → ④画像&レビューへ", type="primary", width="stretch"):
                    new_md = outline_parser.serialize_full(new_struct)
                    storage.save_outline(work_date, new_md)
                    storage.mark_stage(work_date, "outline", True)
                    goto("review")

            # ---- Markdown プレビュー ----
            with st.expander("Markdown プレビュー（自動生成）"):
                preview_md = outline_parser.serialize_full(new_struct)
                st.markdown(preview_md)
                st.code(preview_md, language="markdown")


# ============================================================
# Stage 4 (NEW): 画像&レビュー — 重点セクション + OpenAI画像生成
# ============================================================
elif current_stage == "review":
    st.header("④画像&レビュー — 重点セクション + 機能的な図の生成")
    st.caption("画像はチェックリスト・比較表・プロセスフロー・データチャートに限定。イラスト・装飾画像は生成しません。")
    stage_done_banner("review", "⑤執筆")

    angle = storage.load_angle(work_date)
    outline = storage.load_outline(work_date)
    if not outline:
        st.warning("③企画で章立てがまだ作られていません")
    else:
        with st.expander("章立て (参考)"):
            st.markdown(outline)

        col_gen, col_info = st.columns([1, 2])
        with col_gen:
            if st.button("Geminiで重点セクション+画像案を提案", type="primary", width="stretch"):
                with st.spinner("Geminiが提案中..."):
                    try:
                        review = gemini_client.generate_json(
                            prompts.review_and_images_prompt(topic, outline, angle)
                        )
                        storage.save_review(work_date, review)
                        storage.snapshot_original(storage.review_path(work_date))
                        st.success(f"提案完了: 重点{len(review.get('key_sections', []))}件 / 画像{len(review.get('images', []))}件")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")
        with col_info:
            st.caption(f"レビューファイル: `{storage.review_path(work_date)}`")
            st.caption(f"画像保存先: `{storage.images_dir(work_date)}`")

        review = storage.load_review(work_date)

        # 重点セクション
        key_sections = review.get("key_sections", [])
        st.divider()
        st.subheader(f"重点セクション（執筆時の核） × {len(key_sections)}")
        st.caption("どこを「記事の核」として強調するかを編集できます。⑤執筆では ⭐ マーク付きで表示され、執筆時の注意が反映されます。")

        edited_key_sections: list[dict] = []
        delete_ks_idx = None
        for i, ks in enumerate(key_sections):
            with st.container(border=True):
                head_l, head_d = st.columns([5, 1])
                with head_l:
                    ks_id = st.text_input(
                        "セクションID（h2_1 / self_practice / summary / cta など）",
                        value=ks.get("section_id", ""),
                        key=f"ks_id_{i}",
                    )
                with head_d:
                    st.write("")
                    if st.button(
                        "🗑️ 削除", key=f"ks_del_{i}",
                        help="この重点セクションを削除", width="stretch",
                    ):
                        delete_ks_idx = i

                ks_title = st.text_input(
                    "セクションタイトル",
                    value=ks.get("section_title", ""),
                    key=f"ks_title_{i}",
                )
                ks_why = st.text_area(
                    "なぜ重要（80字程度）",
                    value=ks.get("why_important", ""),
                    height=80,
                    key=f"ks_why_{i}",
                )
                ks_advice = st.text_area(
                    "執筆時の注意・強調すべき要素（120字程度）",
                    value=ks.get("writing_advice", ""),
                    height=120,
                    key=f"ks_advice_{i}",
                )
                edited_key_sections.append({
                    "section_id": ks_id,
                    "section_title": ks_title,
                    "why_important": ks_why,
                    "writing_advice": ks_advice,
                })

        col_ks_add, col_ks_save = st.columns(2)
        with col_ks_add:
            if st.button("➕ 重点セクションを追加", width="stretch"):
                review["key_sections"] = edited_key_sections + [{
                    "section_id": "",
                    "section_title": "",
                    "why_important": "",
                    "writing_advice": "",
                }]
                storage.save_review(work_date, review)
                for k in list(st.session_state.keys()):
                    if k.startswith("ks_"):
                        del st.session_state[k]
                st.rerun()
        with col_ks_save:
            if st.button("💾 重点セクションを保存", type="primary", width="stretch"):
                review["key_sections"] = edited_key_sections
                storage.save_review(work_date, review)
                st.success("重点セクションを保存しました")

        if delete_ks_idx is not None:
            review["key_sections"] = [
                ks for j, ks in enumerate(edited_key_sections) if j != delete_ks_idx
            ]
            storage.save_review(work_date, review)
            for k in list(st.session_state.keys()):
                if k.startswith("ks_"):
                    del st.session_state[k]
            st.rerun()

        # 画像案
        images = review.get("images", [])
        if images:
            st.divider()
            st.subheader(f"画像案 × {len(images)}")

            updated = []
            size_options = ["1024x1024", "1024x1536", "1536x1024"]

            for i, img in enumerate(images):
                img_id = img.get("id", f"img_{i}")
                img_path = storage.image_path(work_date, img_id)
                exists = storage.image_exists(work_date, img_id)
                diagram_type = img.get("diagram_type") or img.get("style") or "?"

                with st.container(border=True):
                    st.markdown(f"**`{img_id}`** — 配置: `{img.get('placement', '?')}` / 種別: `{diagram_type}`")
                    st.caption(f"目的: {img.get('purpose', '')}")

                    cur_size = img.get("size", "1024x1536")
                    if cur_size not in size_options:
                        cur_size = "1024x1536"

                    # ---- diagram_type 別の編集UI ----
                    if diagram_type == "checklist":
                        st.caption(f"🎨 OpenAI {os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-2')} で生成（編集デザイン仕様を内部プロンプトに埋込み）")
                        cl = img.get("checklist", {"title": "", "items": []})
                        cl_title = st.text_input(
                            "チェックリスト タイトル",
                            value=cl.get("title", ""),
                            key=f"cl_title_{i}",
                        )
                        items_str = "\n".join(cl.get("items", []))
                        cl_items_text = st.text_area(
                            "項目（1行=1項目、必要に応じて行を追加・編集）",
                            value=items_str,
                            height=260,
                            key=f"cl_items_{i}",
                        )
                        cl_items = [ln.strip() for ln in cl_items_text.split("\n") if ln.strip()]
                        size = st.selectbox(
                            "サイズ", size_options, index=size_options.index(cur_size),
                            key=f"img_size_{i}",
                        )
                        quality = st.selectbox(
                            "品質", ["low", "medium", "high"], index=2,
                            key=f"img_qual_{i}",
                        )
                        st.caption(f"項目数: {len(cl_items)}")

                        col_btn, col_dl = st.columns([1, 1])
                        with col_btn:
                            btn_label = "🔁 再生成" if exists else "🎨 OpenAIで生成"
                            if st.button(
                                btn_label, key=f"img_gen_{i}",
                                type="primary" if not exists else "secondary",
                                disabled=not openai_client.keys_configured() or not cl_items,
                                width="stretch",
                            ):
                                with st.spinner("OpenAI で画像生成中...（30〜60秒）"):
                                    try:
                                        prompt_en = prompts.image_prompt_for_checklist(cl_title, cl_items)
                                        img_bytes = openai_client.generate_image(
                                            prompt=prompt_en,
                                            size=size, quality=quality,
                                        )
                                        storage.save_image_bytes(work_date, img_id, img_bytes)
                                        st.success("生成完了")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"エラー: {e}")
                        with col_dl:
                            if exists:
                                _img_data = storage.load_image_bytes(work_date, img_id) or b""
                                st.download_button(
                                    "ダウンロード", _img_data, file_name=img_path.name,
                                    mime="image/png", key=f"img_dl_{i}", width="stretch",
                                )

                        updated.append({
                            **img, "size": size,
                            "checklist": {"title": cl_title, "items": cl_items},
                        })

                    elif diagram_type == "comparison_table":
                        st.caption(f"🎨 OpenAI {os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-2')} で生成（編集デザイン仕様を内部プロンプトに埋込み）")
                        tb = img.get("table", {"title": "", "cols": [], "rows": []})
                        tb_title = st.text_input(
                            "比較表 タイトル",
                            value=tb.get("title", ""),
                            key=f"tb_title_{i}",
                        )
                        cols_str = ", ".join(tb.get("cols", []))
                        cols_text = st.text_input(
                            "列名（カンマ区切り、最初が左端のラベル列）",
                            value=cols_str,
                            key=f"tb_cols_{i}",
                            help="例: 指標, 静止画広告, 動画広告",
                        )
                        cols = [c.strip() for c in cols_text.split(",") if c.strip()]

                        if cols:
                            data = []
                            for r in tb.get("rows", []):
                                row_dict = {cols[0]: str(r.get("label", ""))}
                                values = r.get("values", [])
                                for j, c in enumerate(cols[1:]):
                                    row_dict[c] = str(values[j]) if j < len(values) else ""
                                data.append(row_dict)
                            df_rows = pd.DataFrame(data, columns=cols)
                            edited_rows_df = st.data_editor(
                                df_rows, num_rows="dynamic", width="stretch",
                                key=f"tb_rows_{i}", height=300,
                            )
                            new_rows = []
                            for _, row in edited_rows_df.iterrows():
                                label = str(row.get(cols[0], ""))
                                values = [str(row.get(c, "")) for c in cols[1:]]
                                if label or any(values):
                                    new_rows.append({"label": label, "values": values})
                        else:
                            st.warning("列名を設定してください")
                            new_rows = []

                        size = st.selectbox(
                            "サイズ", size_options,
                            index=size_options.index(cur_size if cur_size in size_options else "1536x1024"),
                            key=f"img_size_{i}",
                        )
                        quality = st.selectbox(
                            "品質", ["low", "medium", "high"], index=2,
                            key=f"img_qual_{i}",
                        )

                        col_btn, col_dl = st.columns([1, 1])
                        with col_btn:
                            btn_label = "🔁 再生成" if exists else "🎨 OpenAIで生成"
                            if st.button(
                                btn_label, key=f"img_gen_{i}",
                                type="primary" if not exists else "secondary",
                                disabled=not openai_client.keys_configured() or not cols or not new_rows,
                                width="stretch",
                            ):
                                with st.spinner("OpenAI で画像生成中...（30〜60秒）"):
                                    try:
                                        prompt_en = prompts.image_prompt_for_table(tb_title, cols, new_rows)
                                        img_bytes = openai_client.generate_image(
                                            prompt=prompt_en,
                                            size=size, quality=quality,
                                        )
                                        storage.save_image_bytes(work_date, img_id, img_bytes)
                                        st.success("生成完了")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"エラー: {e}")
                        with col_dl:
                            if exists:
                                _img_data = storage.load_image_bytes(work_date, img_id) or b""
                                st.download_button(
                                    "ダウンロード", _img_data, file_name=img_path.name,
                                    mime="image/png", key=f"img_dl_{i}", width="stretch",
                                )

                        updated.append({
                            **img, "size": size,
                            "table": {"title": tb_title, "cols": cols, "rows": new_rows},
                        })

                    else:
                        # process_flow / data_chart など → OpenAI 経由
                        st.caption("🎨 OpenAI gpt-image-1 で生成（プロンプトは日本語OK、画像内の文字も自動で日本語化）")
                        col_p, col_c = st.columns([2, 1])
                        with col_p:
                            prompt_user = st.text_area(
                                "プロンプト（日本語OK、編集可）",
                                value=img.get("prompt_en", ""),
                                height=140,
                                key=f"img_prompt_{i}",
                                help="図の構成・ラベル名・矢印関係などを日本語で記述。デザイン仕様と日本語化指示はシステム側で自動で付加されます。",
                            )
                        with col_c:
                            size = st.selectbox(
                                "サイズ", size_options,
                                index=size_options.index(cur_size if cur_size in size_options else "1536x1024"),
                                key=f"img_size_{i}",
                            )
                            quality = st.selectbox(
                                "品質", ["low", "medium", "high"], index=2,
                                key=f"img_qual_{i}",
                            )

                        col_btn, col_dl = st.columns([1, 1])
                        with col_btn:
                            btn_label = "🔁 再生成" if exists else "🎨 OpenAIで生成"
                            if st.button(
                                btn_label, key=f"img_gen_{i}",
                                type="primary" if not exists else "secondary",
                                disabled=not openai_client.keys_configured(), width="stretch",
                            ):
                                with st.spinner("OpenAIで画像生成中...（10〜30秒）"):
                                    try:
                                        wrapped_prompt = prompts.image_prompt_wrap_for_freeform(prompt_user)
                                        img_bytes = openai_client.generate_image(
                                            prompt=wrapped_prompt,
                                            size=size, quality=quality,
                                        )
                                        storage.save_image_bytes(work_date, img_id, img_bytes)
                                        st.success("生成完了")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"エラー: {e}")
                        with col_dl:
                            if exists:
                                _img_data = storage.load_image_bytes(work_date, img_id) or b""
                                st.download_button(
                                    "ダウンロード", _img_data, file_name=img_path.name,
                                    mime="image/png", key=f"img_dl_{i}", width="stretch",
                                )

                        updated.append({**img, "size": size, "prompt_en": prompt_user})

                    if exists:
                        _disp_bytes = storage.load_image_bytes(work_date, img_id)
                        if _disp_bytes:
                            st.image(_disp_bytes, width="stretch")

            if st.button("画像案を保存（編集内容を反映）"):
                review["images"] = updated
                storage.save_review(work_date, review)
                st.success("保存しました")

        st.divider()
        if st.button("④画像&レビューを完了 → ⑤執筆へ", type="primary"):
            storage.mark_stage(work_date, "review", True)
            goto("write")


# ============================================================
# Stage 5: 執筆 — セクション単位
# ============================================================
elif current_stage == "write":
    st.header("⑤執筆 — セクション単位でブログを書く")
    stage_done_banner("write", "⑥発信")

    outline = storage.load_outline(work_date)
    if not outline:
        st.warning("③企画で章立てがまだ作られていません")
    else:
        df = storage.load_cases(work_date)
        cases_csv = df.to_csv(index=False)

        with st.expander("章立て（参考）", expanded=False):
            st.markdown(outline)

        # outlineをパースしてセクション一覧を取得
        parsed_sections = outline_parser.parse(outline)
        title_candidates = outline_parser.extract_title_candidates(outline)
        lead_direction = outline_parser.extract_lead_direction(outline)

        # ④で生成したレビュー（重点セクション + 画像）を読み込み
        review = storage.load_review(work_date)
        advice_by_id: dict[str, dict] = {ks.get("section_id"): ks for ks in review.get("key_sections", [])}

        # 既存のセクション内容（content）とマージ
        saved = storage.load_sections_file(work_date)
        existing_content = {s["id"]: s.get("content", "") for s in saved.get("sections", [])}
        merged = [
            {
                "id": s.id,
                "title": s.title,
                "memo": s.memo,
                "target_chars": s.target_chars,
                "content": existing_content.get(s.id, ""),
            }
            for s in parsed_sections
        ]

        # ---- タイトル + リード ----
        st.subheader("タイトル + リード")
        col_t, col_l = st.columns([1, 1])
        with col_t:
            saved_title = saved.get("title", "")
            if not saved_title and title_candidates:
                saved_title = title_candidates[0]
            title = st.text_input("タイトル（H1）", value=saved_title, key="blog_title")
            if title_candidates:
                with st.expander("候補から選ぶ"):
                    for tc in title_candidates:
                        st.markdown(f"- {tc}")
        with col_l:
            lead = st.text_area(
                "リード（200字目安）",
                value=saved.get("lead", ""),
                height=100,
                key="blog_lead",
                placeholder=lead_direction[:120] if lead_direction else "",
            )
            lead_gen_disabled = not title or not lead_direction
            lead_gen_help = (
                "タイトル or ③のリード方向性が空のため生成できません"
                if lead_gen_disabled
                else "③で書いたリード方向性を元に120〜200字のリード文をGeminiで生成"
            )
            if st.button(
                "✨ リード文を生成",
                key="lead_gen_btn",
                disabled=lead_gen_disabled,
                help=lead_gen_help,
                width="stretch",
            ):
                with st.spinner("Geminiがリード文を書いています..."):
                    try:
                        new_lead = gemini_client.generate_text(
                            prompts.lead_prompt(topic, title, lead_direction, outline)
                        )
                        new_lead = persona.sanitize_emoji(new_lead).strip()
                        storage.save_sections_file(work_date, {
                            "title": title, "lead": new_lead, "sections": merged,
                        })
                        storage.snapshot_original(storage.sections_path(work_date))
                        st.session_state["blog_lead"] = new_lead
                        st.success(f"リード生成完了（{len(new_lead)}字）")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")

        st.divider()

        # ---- セクション単位 ----
        st.subheader(f"H2セクション × {len(merged)}")
        if not merged:
            st.warning("章立てから`###`セクションが抽出できませんでした。outlineの形式を確認してください。")

        for i, sec in enumerate(merged):
            advice = advice_by_id.get(sec["id"])
            is_key = advice is not None
            with st.container(border=True):
                col_head, col_btn = st.columns([4, 1])
                with col_head:
                    star = "⭐ " if is_key else ""
                    st.markdown(f"### {star}{sec['title']}")
                    st.caption(f"目標 {sec['target_chars']}字 / id: `{sec['id']}`")
                    if is_key:
                        st.info(
                            f"**重点セクション** — {advice.get('why_important', '')}\n\n"
                            f"**執筆時の注意**: {advice.get('writing_advice', '')}"
                        )
                with col_btn:
                    label = "再生成" if sec["content"] else "生成"
                    btype = "secondary" if sec["content"] else "primary"
                    if st.button(label, key=f"gen_sec_{i}", type=btype, width="stretch"):
                        with st.spinner(f"Gemini が「{sec['title']}」を書いています..."):
                            try:
                                written = [
                                    (s["title"], s["content"])
                                    for s in merged
                                    if s["id"] != sec["id"] and s["content"]
                                ]
                                # 重点セクションなら memo に advice を追記して Gemini に伝える
                                memo = sec["memo"]
                                if is_key:
                                    memo += (
                                        f"\n\n## 重点セクション指定\n"
                                        f"このセクションは記事の核です。\n"
                                        f"- 重要な理由: {advice.get('why_important', '')}\n"
                                        f"- 執筆時の注意: {advice.get('writing_advice', '')}\n"
                                        f"特に丁寧に、具体的に書いてください。"
                                    )
                                content = gemini_client.generate_text(
                                    prompts.section_prompt(
                                        topic=topic,
                                        outline_md=outline,
                                        section_title=sec["title"],
                                        section_memo=memo,
                                        target_chars=sec["target_chars"],
                                        cases_csv=cases_csv,
                                        written_sections=written,
                                        is_self_practice=(sec["id"] == "self_practice"),
                                        is_summary=(sec["id"] == "summary"),
                                        is_cta=(sec["id"] == "cta"),
                                    )
                                )
                                content = persona.sanitize_emoji(content)
                                merged[i]["content"] = content
                                storage.save_sections_file(work_date, {
                                    "title": title, "lead": lead, "sections": merged,
                                })
                                storage.snapshot_original(storage.sections_path(work_date))
                                st.session_state[f"sec_text_{i}"] = content
                                st.rerun()
                            except Exception as e:
                                st.error(f"エラー: {e}")

                with st.expander("メモ（章立てから）", expanded=False):
                    st.text(sec["memo"])

                edited = st.text_area(
                    f"section_{i}",
                    value=sec["content"],
                    height=300,
                    key=f"sec_text_{i}",
                    label_visibility="collapsed",
                )
                merged[i]["content"] = edited

                count = len(edited)
                target = sec["target_chars"]
                ratio = count / target if target else 0
                color = "🟢" if 0.7 <= ratio <= 1.4 else ("🟡" if count > 0 else "⬜")
                st.caption(f"{color} {count} / {target} 字")

        st.divider()
        c_save, c_assemble = st.columns([1, 2])
        with c_save:
            if st.button("セクションを保存", width="stretch"):
                storage.save_sections_file(work_date, {
                    "title": title, "lead": lead, "sections": merged,
                })
                st.success("保存")
        with c_assemble:
            if st.button("全セクションを結合してblog.mdに書き出し", type="primary", width="stretch"):
                # 画像placementを集計
                hero_imgs: list[str] = []
                before_imgs: dict[str, list[str]] = {}
                after_imgs: dict[str, list[str]] = {}
                for img in review.get("images", []):
                    img_id = img.get("id", "")
                    if not storage.image_exists(work_date, img_id):
                        continue
                    img_path = storage.image_path(work_date, img_id)
                    rel = f"images/{img_path.name}"
                    alt = img.get("purpose", img_id)
                    md = f"![{alt}]({rel})"
                    placement = img.get("placement", "")
                    if placement == "hero":
                        hero_imgs.append(md)
                    elif placement.startswith("before:"):
                        before_imgs.setdefault(placement.split(":", 1)[1], []).append(md)
                    elif placement.startswith("after:"):
                        after_imgs.setdefault(placement.split(":", 1)[1], []).append(md)
                    else:
                        # 不明な placement は before: 扱い
                        before_imgs.setdefault(placement, []).append(md)

                parts: list[str] = []
                if title:
                    parts.append(f"# {title}")
                if lead:
                    parts.append(lead)
                parts.extend(hero_imgs)
                for sec in merged:
                    sid = sec["id"]
                    if sid in before_imgs:
                        parts.extend(before_imgs[sid])
                    if sec["content"]:
                        parts.append(sec["content"].strip())
                    if sid in after_imgs:
                        parts.extend(after_imgs[sid])

                blog_md = "\n\n".join(parts)
                storage.save_blog(work_date, blog_md)
                storage.snapshot_original(storage.blog_path(work_date))
                storage.save_sections_file(work_date, {
                    "title": title, "lead": lead, "sections": merged,
                })
                st.session_state["blog_editor"] = blog_md
                inserted = len(hero_imgs) + sum(len(v) for v in before_imgs.values()) + sum(len(v) for v in after_imgs.values())
                st.success(f"blog.md 書き出し完了（{len(blog_md)}字 / 画像 {inserted}枚挿入）")
                st.rerun()

        # ---- 結合後のblog.md ----
        blog_md = storage.load_blog(work_date)
        if blog_md:
            st.divider()
            with st.expander(f"結合後のブログ本文（{len(blog_md)}字、編集可）", expanded=False):
                edited_blog = st.text_area(
                    "blog.md",
                    value=blog_md,
                    height=500,
                    key="blog_editor",
                    label_visibility="collapsed",
                )
                if st.button("結合後のblog.mdを上書き保存"):
                    storage.save_blog(work_date, edited_blog)
                    st.success("保存")

        # ---- X投稿5本 ----
        st.divider()
        st.subheader("X投稿5本")
        if st.button("X投稿5本を生成", type="primary"):
            blog_md = storage.load_blog(work_date)
            if not blog_md:
                st.error("先に『全セクションを結合してblog.mdに書き出し』を実行してください")
            else:
                with st.spinner("Geminiが投稿を書いています..."):
                    try:
                        posts = gemini_client.generate_json(
                            prompts.posts_prompt(topic, blog_md, 5)
                        )
                        # 絵文字・豆腐文字サニタイズ
                        for p in posts:
                            if isinstance(p, dict) and p.get("text"):
                                p["text"] = persona.sanitize_emoji(p["text"])
                        storage.save_posts(work_date, posts)
                        storage.snapshot_original(storage.posts_path(work_date))
                        for i, p in enumerate(posts):
                            st.session_state[f"post_text_{i}"] = p.get("text", "")
                        st.success(f"投稿 {len(posts)} 本生成")
                        st.rerun()
                    except Exception as e:
                        st.error(f"エラー: {e}")

        posts = storage.load_posts(work_date)
        if posts:
            edited_posts = []
            for i, p in enumerate(posts):
                with st.container(border=True):
                    st.caption(f"#{i+1} [{p.get('kind', '?')}] {p.get('title', '')} / 想定: {p.get('scheduled_hint', '')}")
                    text = st.text_area(
                        f"post_{i}",
                        value=p.get("text", ""),
                        height=120,
                        key=f"post_text_{i}",
                        label_visibility="collapsed",
                    )
                    char_count = len(text)
                    color = "🟢" if char_count <= 140 else "🔴"
                    st.caption(f"{color} {char_count}/140字")
                    edited_posts.append({**p, "text": text})

            if st.button("投稿を保存"):
                storage.save_posts(work_date, edited_posts)
                st.success("保存")

        st.divider()
        if st.button("⑤執筆を完了 → ⑥発信へ", type="primary"):
            if storage.load_blog(work_date) and storage.load_posts(work_date):
                storage.mark_stage(work_date, "write", True)
                goto("publish")
            else:
                st.error("『blog.md書き出し』と『X投稿生成』の両方を完了してください")


# ============================================================
# Stage 5: 発信
# ============================================================
elif current_stage == "publish":
    st.header("⑥発信 — X API投稿 + ブログコピー")
    stage_done_banner("publish", None)

    posts = storage.load_posts(work_date)
    blog_md = storage.load_blog(work_date)

    st.subheader("ブログ（STUDIO 連携）")
    if not blog_md:
        st.info("ブログがありません")
    else:
        st.caption(f"{len(blog_md)} 字")

        # ---- STUDIO 連携: 半自動投稿 ----
        from core import studio_export
        import streamlit.components.v1 as components
        import json as _json
        import base64 as _b64

        try:
            payload = studio_export.build_studio_payload(blog_md)
        except Exception as e:
            st.error(f"STUDIO payload 生成エラー: {e}")
            payload = {"title": "", "body_html": ""}

        st.markdown("### 📥 STUDIO へ半自動投稿")
        st.caption(
            "ブックマークレットで STUDIO の編集画面にタイトル+本文を自動入力します。"
            "見出しは H2→H3、H3→H4 に自動変換（STUDIO の大見出し/小見出し階層に合わせる）。"
        )
        st.markdown(f"- タイトル: `{payload['title'][:60]}...`")
        st.markdown(f"- 本文 HTML: {len(payload['body_html'])} 文字")

        # クリップボードコピー: 2つの方法を提供
        payload_str = _json.dumps(payload, ensure_ascii=False)
        js_payload = _json.dumps(payload_str)

        # 方法1: HTMLボタン（埋込み iframe、たまに見えない問題あり）
        st.markdown("#### 方法 1: ボタンクリックでコピー")
        components.html(
            f"""
            <div style="padding:8px 0;">
            <button id="cp-payload" onclick="
                navigator.clipboard.writeText({js_payload}).then(() => {{
                    this.innerText = '✅ コピー完了 — STUDIO 編集画面でブックマークレット実行';
                    this.style.background = '#16a34a';
                    setTimeout(() => {{
                        this.innerText = '📋 STUDIO 投稿データをクリップボードにコピー';
                        this.style.background = '#2563eb';
                    }}, 3500);
                }}).catch(e => {{ this.innerText = '❌ ' + e.message; }});
            " style="
                background: #2563eb; color: white; padding: 14px 24px;
                border: none; border-radius: 8px; cursor: pointer;
                width: 100%; font-size: 15px; font-weight: 700;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">📋 STUDIO 投稿データをクリップボードにコピー</button>
            </div>
            """,
            height=80,
        )

        # 方法2: コードブロック（右上の📋アイコンで確実にコピー可能）
        st.markdown("#### 方法 2: 上のボタンが押せない時 — コードブロック右上の 📋 でコピー")
        st.code(payload_str, language="json")

        # 画像コピー（各画像をクリップボードに貼付け可能な形でコピー）
        # review の images から ID を集める（Supabase化により filesystem 走査廃止）
        review_for_imgs = storage.load_review(work_date)
        image_entries: list[tuple[str, bytes]] = []
        for img_meta in review_for_imgs.get("images", []):
            img_id = img_meta.get("id", "")
            if not img_id:
                continue
            data = storage.load_image_bytes(work_date, img_id)
            if data:
                image_entries.append((img_id, data))
        if image_entries:
            st.markdown(f"**画像（{len(image_entries)}枚）** — STUDIO 本文で挿入位置をクリック → 下のボタン → STUDIO で `Cmd+V`")
            for img_id, img_data in image_entries:
                img_b64 = _b64.b64encode(img_data).decode("ascii")
                img_filename = f"{img_id}.png"
                with st.container(border=True):
                    col_thumb, col_btn = st.columns([1, 2])
                    with col_thumb:
                        st.image(img_data, width=140)
                    with col_btn:
                        st.caption(img_filename)
                        components.html(
                            f"""
                            <button onclick="
                                (async () => {{
                                    try {{
                                        const r = await fetch('data:image/png;base64,{img_b64}');
                                        const blob = await r.blob();
                                        await navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]);
                                        this.innerText = '✅ コピー完了 — STUDIO で Cmd+V';
                                        this.style.background = '#16a34a';
                                        setTimeout(() => {{
                                            this.innerText = '📋 この画像をクリップボードへ';
                                            this.style.background = '#2563eb';
                                        }}, 3000);
                                    }} catch (e) {{
                                        this.innerText = '❌ ' + e.message;
                                    }}
                                }})();
                            " style="
                                background: #2563eb; color: white; padding: 8px 14px;
                                border: none; border-radius: 6px; cursor: pointer;
                                width: 100%; font-size: 13px;
                            ">📋 この画像をクリップボードへ</button>
                            """,
                            height=50,
                        )
        else:
            st.caption("画像なし（④画像&レビューで生成すれば表示されます）")

        # ブックマークレット
        with st.expander("🔖 ブックマークレットの登録方法（初回のみ・5分）"):
            st.markdown("""
            ### 手順
            1. Chrome のブックマークバーを表示（`Cmd + Shift + B`）
            2. ブックマークバーで**右クリック** → **「ページを追加」**
            3. **名前**: `📥 STUDIOに取り込む`
            4. **URL**: 下のコードを**全部コピーして貼付け**（先頭の `javascript:` ごと）
            5. **保存**

            ### 使い方
            1. メディアなんとかで「📋 STUDIO 投稿データをコピー」を押す
            2. STUDIO の編集画面（新規記事 or 既存記事）を開く
            3. ブックマーク `📥 STUDIOに取り込む` をクリック
            4. 自動でタイトル+本文が入る
            5. 画像を入れたい位置でクリック → メディアなんとかで「画像をコピー」 → STUDIO で `Cmd+V`
            6. 確認 → STUDIO の「公開」ボタン
            """)
            st.code(studio_export.make_bookmarklet(), language="javascript")
            st.caption("⚠️ 上のコードは1行 javascript: スキームです。改行されていないものをそのままコピーしてください。")

        st.divider()
        with st.expander("ブログ Markdown プレビュー"):
            st.markdown(blog_md)
            st.code(blog_md, language="markdown")

    st.divider()
    st.subheader("Xに5本独立投稿")

    if not x_client.keys_configured():
        st.error(f"X API キーが未設定です。`.env` に以下を設定: {x_client.missing_keys()}")
        st.caption("https://developer.x.com/ で OAuth 1.0a User Context のキーを取得（Read and Write 権限が必要）")
    else:
        if st.button("X認証チェック"):
            ok, info = x_client.verify_credentials()
            if ok:
                st.success(f"認証OK: @{info}")
            else:
                st.error(f"認証失敗: {info}")

    if not posts:
        st.info("投稿データがありません（④で生成してください）")
    else:
        results = storage.load_results(work_date)

        for i, p in enumerate(posts):
            with st.container(border=True):
                col_l, col_r = st.columns([3, 1])
                with col_l:
                    st.caption(f"#{i+1} [{p.get('kind', '?')}] {p.get('title', '')}")
                    st.text(p.get("text", ""))
                    st.caption(f"{len(p.get('text', ''))}/140字")
                with col_r:
                    rkey = f"post_{i}"
                    prev = results.get(rkey)
                    if prev and prev.get("ok"):
                        st.success("投稿済")
                        st.caption(f"[Xで確認]({prev.get('url')})")
                    elif prev:
                        st.error("失敗")
                        st.caption(prev.get("error", ""))

                    if st.button(f"#{i+1}を投稿", key=f"btn_{i}", disabled=not x_client.keys_configured()):
                        with st.spinner("投稿中..."):
                            r = x_client.post_tweet(p.get("text", ""))
                            results[rkey] = {
                                "ok": r.ok,
                                "tweet_id": r.tweet_id,
                                "url": r.url,
                                "error": r.error,
                            }
                            storage.save_results(work_date, results)
                            st.rerun()

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            unposted = [i for i in range(len(posts)) if not results.get(f"post_{i}", {}).get("ok")]
            if st.button(
                f"未投稿 {len(unposted)} 本を一括投稿",
                type="primary",
                disabled=not x_client.keys_configured() or len(unposted) == 0,
            ):
                progress = st.progress(0.0)
                for j, i in enumerate(unposted):
                    p = posts[i]
                    r = x_client.post_tweet(p.get("text", ""))
                    results[f"post_{i}"] = {
                        "ok": r.ok,
                        "tweet_id": r.tweet_id,
                        "url": r.url,
                        "error": r.error,
                    }
                    storage.save_results(work_date, results)
                    progress.progress((j + 1) / len(unposted))
                st.success("一括投稿完了")
                st.rerun()
        with col_b:
            all_ok = posts and all(results.get(f"post_{i}", {}).get("ok") for i in range(len(posts)))
            if st.button("⑥発信を完了にする", disabled=not all_ok):
                storage.mark_stage(work_date, "publish", True)
                st.success("本日のパイプライン完了")
                st.rerun()
