"""ファイル入出力。
構造: output/{YYYY-MM-DD}/runs/{run_id}/ 配下で各Runを独立管理。
Run はお題ごとの試行単位。複数Runを保持し、サイドバーで切替可能。"""
from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "output"

DEFAULT_CASE_COLUMNS = [
    "誰が",
    "何を",
    "どう測ったか",
    "結果_数字",
    "出典URL",
    "示唆",
    "国_地域",
    "情報源言語",
]

EMPTY_STAGES = {
    "diverge": False, "converge": False, "outline": False,
    "review": False, "write": False, "publish": False,
}

# ⓪テーマ探索は制作とは独立した参照ツール。履歴をユーザーごとに保存。


def _user_root() -> Path:
    """セッションごと（ユーザーごと）に隔離されたルートパス。
    優先順位:
      1. st.session_state['_app_session_id']
      2. URLクエリパラメータ ?sid=...（リロードでも保持される）
      3. output/sessions/ 配下に既存ディレクトリがあれば最新を採用（リロード後の自動復旧）
      4. 新規UUIDを発行 + URLにsidを書き込み（次回以降復旧できるように）
    Streamlitコンテキスト外（CLIテスト等）では OUTPUT_ROOT そのまま。"""
    try:
        import streamlit as st

        sid = st.session_state.get("_app_session_id", "")

        # 2. URLクエリパラメータから復元
        if not sid:
            try:
                qp_sid = st.query_params.get("sid", "")
                if qp_sid:
                    sid = str(qp_sid)
                    st.session_state["_app_session_id"] = sid
            except Exception:
                pass

        # 3. 既存ディレクトリから自動復旧（最新更新分を選択）
        if not sid:
            sessions_root = OUTPUT_ROOT / "sessions"
            if sessions_root.exists():
                existing = [d for d in sessions_root.iterdir() if d.is_dir()]
                if existing:
                    most_recent = max(existing, key=lambda p: p.stat().st_mtime)
                    sid = most_recent.name
                    st.session_state["_app_session_id"] = sid
                    try:
                        st.query_params["sid"] = sid
                    except Exception:
                        pass

        # 4. 新規発行 + URLに保存
        if not sid:
            import uuid
            sid = uuid.uuid4().hex[:12]
            st.session_state["_app_session_id"] = sid
            try:
                st.query_params["sid"] = sid
            except Exception:
                pass

        p = OUTPUT_ROOT / "sessions" / sid
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        return OUTPUT_ROOT


def themes_global_path() -> Path:
    return _user_root() / "themes_global.json"


def load_themes_global() -> list[dict]:
    """テーマ探索の全履歴（このユーザーセッションのみ）。最新順。"""
    p = themes_global_path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_themes_global(history: list[dict]) -> None:
    p = themes_global_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# Run management
# ============================================================
def _date_root(d: date) -> Path:
    p = _user_root() / d.isoformat()
    p.mkdir(parents=True, exist_ok=True)
    return p


def runs_meta_path(d: date) -> Path:
    return _date_root(d) / "runs.json"


def _ensure_runs_structure(d: date) -> None:
    """旧構造（output/{date}/state.json 等が直置き）を runs/r1/ へ移行。"""
    root = _date_root(d)
    if (root / "runs.json").exists():
        return
    flat_state = root / "state.json"
    has_old_files = flat_state.exists() or (root / "cases.csv").exists()
    if not has_old_files:
        # 何もない: 空の runs.json + r1 ディレクトリを作る
        r1 = root / "runs" / "r1"
        r1.mkdir(parents=True, exist_ok=True)
        meta = {
            "active": "r1",
            "runs": [{
                "id": "r1", "topic": "",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "stages": dict(EMPTY_STAGES),
            }],
        }
        (root / "runs.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    # 旧フラット構造を移行
    topic = ""
    stages = dict(EMPTY_STAGES)
    if flat_state.exists():
        try:
            s = json.loads(flat_state.read_text(encoding="utf-8"))
            topic = s.get("topic", "")
            stages = {**EMPTY_STAGES, **s.get("stages", {})}
        except Exception:
            pass

    r1 = root / "runs" / "r1"
    r1.mkdir(parents=True, exist_ok=True)
    for child in list(root.iterdir()):
        if child.name in ("runs", "runs.json"):
            continue
        target = r1 / child.name
        try:
            child.rename(target)
        except Exception:
            pass

    meta = {
        "active": "r1",
        "runs": [{
            "id": "r1", "topic": topic,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "stages": stages,
        }],
    }
    (root / "runs.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def load_runs_meta(d: date) -> dict:
    _ensure_runs_structure(d)
    raw = json.loads(runs_meta_path(d).read_text(encoding="utf-8"))
    # 各 run の stages/topic を state.json から最新に同期
    for run in raw.get("runs", []):
        rid = run["id"]
        sp = _date_root(d) / "runs" / rid / "state.json"
        if sp.exists():
            try:
                s = json.loads(sp.read_text(encoding="utf-8"))
                run["topic"] = s.get("topic", run.get("topic", ""))
                run["stages"] = {**EMPTY_STAGES, **s.get("stages", {})}
            except Exception:
                pass
    return raw


def save_runs_meta(d: date, meta: dict) -> None:
    runs_meta_path(d).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def active_run_id(d: date) -> str:
    return load_runs_meta(d)["active"]


def list_runs(d: date) -> list[dict]:
    return load_runs_meta(d)["runs"]


def create_run(d: date, topic: str = "") -> str:
    meta = load_runs_meta(d)
    existing = {r["id"] for r in meta["runs"]}
    n = len(existing) + 1
    new_id = f"r{n}"
    while new_id in existing:
        n += 1
        new_id = f"r{n}"
    new_run = {
        "id": new_id, "topic": topic,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "stages": dict(EMPTY_STAGES),
    }
    meta["runs"].append(new_run)
    meta["active"] = new_id
    save_runs_meta(d, meta)
    (_date_root(d) / "runs" / new_id).mkdir(parents=True, exist_ok=True)
    # 初期 state.json も書いておく
    state_path_for(d, new_id).write_text(
        json.dumps({"topic": topic, "stages": dict(EMPTY_STAGES)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return new_id


def set_active_run(d: date, run_id: str) -> None:
    meta = load_runs_meta(d)
    if run_id not in [r["id"] for r in meta["runs"]]:
        raise ValueError(f"Run {run_id} が存在しません")
    meta["active"] = run_id
    save_runs_meta(d, meta)


def delete_run(d: date, run_id: str) -> None:
    """Run を削除（フォルダごと）。最後の1つは削除不可。"""
    import shutil
    meta = load_runs_meta(d)
    if len(meta["runs"]) <= 1:
        raise ValueError("最後の Run は削除できません")
    meta["runs"] = [r for r in meta["runs"] if r["id"] != run_id]
    if meta["active"] == run_id:
        meta["active"] = meta["runs"][-1]["id"]
    save_runs_meta(d, meta)
    target = _date_root(d) / "runs" / run_id
    if target.exists():
        shutil.rmtree(target)


def rename_run_topic(d: date, run_id: str, topic: str) -> None:
    """Run のトピックだけ更新（state.json経由）。"""
    sp = state_path_for(d, run_id)
    s = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"stages": dict(EMPTY_STAGES)}
    s["topic"] = topic
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def update_run_name(d: date, run_id: str, name: str) -> None:
    """Run に表示用の名前を付与（runs.json経由）。"""
    meta = load_runs_meta(d)
    for r in meta["runs"]:
        if r["id"] == run_id:
            r["name"] = name
            break
    save_runs_meta(d, meta)


def list_all_runs() -> list[dict]:
    """全日付の全制作を最新順で一覧化（このユーザーセッションのみ）。
    各要素: {date, id, name, topic, stages, created_at}"""
    result: list[dict] = []
    root = _user_root()
    if not root.exists():
        return result
    for date_dir in sorted(root.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        rp = date_dir / "runs.json"
        if not rp.exists():
            continue
        try:
            meta = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in meta.get("runs", []):
            rid = r["id"]
            sp = date_dir / "runs" / rid / "state.json"
            stages = dict(EMPTY_STAGES)
            stages.update(r.get("stages", {}))
            topic = r.get("topic", "")
            if sp.exists():
                try:
                    s = json.loads(sp.read_text(encoding="utf-8"))
                    topic = s.get("topic", topic)
                    stages = {**EMPTY_STAGES, **s.get("stages", {})}
                except Exception:
                    pass
            result.append({
                "date": date_dir.name,
                "id": rid,
                "name": r.get("name", ""),
                "topic": topic,
                "stages": stages,
                "created_at": r.get("created_at") or date_dir.name,
            })
    result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return result


def state_path_for(d: date, run_id: str) -> Path:
    return _date_root(d) / "runs" / run_id / "state.json"


# ============================================================
# Active run の dir / state（既存APIは active run を指すように維持）
# ============================================================
def date_dir(d: date) -> Path:
    """注: 名前は互換性のため date_dir のまま。実体は active run のディレクトリ。"""
    rid = active_run_id(d)
    p = _date_root(d) / "runs" / rid
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_path(d: date) -> Path:
    return date_dir(d) / "state.json"


def load_state(d: date) -> dict[str, Any]:
    p = state_path(d)
    if not p.exists():
        return {"topic": "", "stages": dict(EMPTY_STAGES)}
    s = json.loads(p.read_text(encoding="utf-8"))
    s.setdefault("stages", {})
    # 既知ステージのみ残す（旧'explore'などは無視）
    s["stages"] = {k: bool(s["stages"].get(k, False)) for k in EMPTY_STAGES}
    return s


def save_state(d: date, state: dict[str, Any]) -> None:
    state_path(d).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_stage(d: date, stage: str, done: bool = True) -> None:
    s = load_state(d)
    s.setdefault("stages", {})[stage] = done
    save_state(d, s)


# --- Stage 0 (NEW): themes.json — テーマ提案候補 + ターゲット ---
def themes_path(d: date) -> Path:
    return date_dir(d) / "themes.json"


def load_themes(d: date) -> dict:
    """構造: {target, themes: [{title, angle, ...}], selected_idx}"""
    p = themes_path(d)
    if not p.exists():
        return {"target": "", "themes": [], "selected_idx": -1}
    return json.loads(p.read_text(encoding="utf-8"))


def save_themes(d: date, data: dict) -> None:
    themes_path(d).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Stage 1: cases.csv ---
def cases_path(d: date) -> Path:
    return date_dir(d) / "cases.csv"


def load_cases(d: date) -> pd.DataFrame:
    p = cases_path(d)
    if not p.exists():
        return pd.DataFrame(columns=DEFAULT_CASE_COLUMNS)
    return pd.read_csv(p)


def save_cases(d: date, df: pd.DataFrame) -> None:
    df.to_csv(cases_path(d), index=False)


# --- Stage 2: axes.json + angle.md ---
def axes_path(d: date) -> Path:
    return date_dir(d) / "axes.json"


def load_axes(d: date) -> list[dict[str, str]]:
    p = axes_path(d)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save_axes(d: date, axes: list[dict[str, str]]) -> None:
    axes_path(d).write_text(json.dumps(axes, ensure_ascii=False, indent=2), encoding="utf-8")


def angle_path(d: date) -> Path:
    return date_dir(d) / "angle.md"


def load_angle(d: date) -> str:
    p = angle_path(d)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def save_angle(d: date, text: str) -> None:
    angle_path(d).write_text(text, encoding="utf-8")


# --- Stage 3: outline.md ---
def outline_path(d: date) -> Path:
    return date_dir(d) / "outline.md"


def load_outline(d: date) -> str:
    p = outline_path(d)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def save_outline(d: date, text: str) -> None:
    outline_path(d).write_text(text, encoding="utf-8")


# --- Stage 4: sections / blog.md / posts.json ---
def sections_path(d: date) -> Path:
    return date_dir(d) / "blog_sections.json"


def load_sections_file(d: date) -> dict:
    """構造: {title, lead, sections: [{id, title, memo, target_chars, content}]}"""
    p = sections_path(d)
    if not p.exists():
        return {"title": "", "lead": "", "sections": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_sections_file(d: date, data: dict) -> None:
    sections_path(d).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def blog_path(d: date) -> Path:
    return date_dir(d) / "blog.md"


def load_blog(d: date) -> str:
    p = blog_path(d)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def save_blog(d: date, text: str) -> None:
    blog_path(d).write_text(text, encoding="utf-8")


def posts_path(d: date) -> Path:
    return date_dir(d) / "posts.json"


def load_posts(d: date) -> list[dict[str, Any]]:
    p = posts_path(d)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def save_posts(d: date, posts: list[dict[str, Any]]) -> None:
    posts_path(d).write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Stage 4 (image+review): review.json + images/ ---
def review_path(d: date) -> Path:
    return date_dir(d) / "review.json"


def load_review(d: date) -> dict:
    """構造: {key_sections: [...], images: [...]}"""
    p = review_path(d)
    if not p.exists():
        return {"key_sections": [], "images": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_review(d: date, data: dict) -> None:
    review_path(d).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def images_dir(d: date) -> Path:
    p = date_dir(d) / "images"
    p.mkdir(parents=True, exist_ok=True)
    return p


def image_path(d: date, image_id: str, ext: str = "png") -> Path:
    safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in image_id)
    return images_dir(d) / f"{safe_id}.{ext}"


# --- Stage 6: post_results.json ---
def results_path(d: date) -> Path:
    return date_dir(d) / "post_results.json"


def load_results(d: date) -> dict[str, Any]:
    p = results_path(d)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_results(d: date, results: dict[str, Any]) -> None:
    results_path(d).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
