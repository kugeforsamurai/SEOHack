"""Supabase バックエンドのチーム共有ストレージ。
旧 file-based 設計を Supabase KV (`artifacts` テーブル) に置き換えたもの。
全ユーザーが同じデータ空間を共有する team-shared モード（sid 分離は廃止）。

旧 file path（"2026-05-13/runs/r1/axes.json" 等）を Supabase の path カラムにそのままキーとして格納する。
互換性のため `*_path(d)` 関数は Path 型を返すが、これは「キー文字列の表現」であって、
実際の filesystem は触らない。"""
from __future__ import annotations
import json
from datetime import date, datetime
from io import StringIO
from pathlib import PurePosixPath
from typing import Any

import pandas as pd

from core import supabase_backend as sb

# Path 型互換のため PurePosixPath を「キー」として使う（filesystem に触らない）
Path = PurePosixPath  # type: ignore[misc, assignment]

DEFAULT_CASE_COLUMNS = [
    "誰が", "何を", "どう測ったか", "結果_数字",
    "出典URL", "示唆", "国_地域", "情報源言語",
]

EMPTY_STAGES = {
    "diverge": False, "converge": False, "outline": False,
    "review": False, "write": False, "publish": False,
}


# ============================================================
# Path builders (実体は Supabase キーの文字列表現)
# ============================================================
def _key(p: PurePosixPath) -> str:
    return str(p)


def _date_root(d: date) -> Path:
    return Path(d.isoformat())


def date_dir(d: date) -> Path:
    """注: 名前は互換性のため。実体は active run のキープレフィックス。"""
    rid = active_run_id(d)
    return _date_root(d) / "runs" / rid


def state_path_for(d: date, run_id: str) -> Path:
    return _date_root(d) / "runs" / run_id / "state.json"


def state_path(d: date) -> Path:
    return date_dir(d) / "state.json"


def runs_meta_path(d: date) -> Path:
    return _date_root(d) / "runs.json"


# ---------- artifact paths（各ステージ用） ----------
def themes_path(d: date) -> Path:
    return date_dir(d) / "themes.json"


def cases_path(d: date) -> Path:
    return date_dir(d) / "cases.csv"


def axes_path(d: date) -> Path:
    return date_dir(d) / "axes.json"


def angle_path(d: date) -> Path:
    return date_dir(d) / "angle.md"


def outline_path(d: date) -> Path:
    return date_dir(d) / "outline.md"


def sections_path(d: date) -> Path:
    return date_dir(d) / "blog_sections.json"


def blog_path(d: date) -> Path:
    return date_dir(d) / "blog.md"


def posts_path(d: date) -> Path:
    return date_dir(d) / "posts.json"


def review_path(d: date) -> Path:
    return date_dir(d) / "review.json"


def images_dir(d: date) -> Path:
    return date_dir(d) / "images"


def image_path(d: date, image_id: str, ext: str = "png") -> Path:
    safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in image_id)
    return images_dir(d) / f"{safe_id}.{ext}"


def results_path(d: date) -> Path:
    return date_dir(d) / "post_results.json"


# ============================================================
# Themes Global（全ユーザー共通の探索履歴）
# ============================================================
def load_themes_global() -> list[dict]:
    raw = sb.get_global("themes_global")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def save_themes_global(history: list[dict]) -> None:
    sb.put_global("themes_global", json.dumps(history, ensure_ascii=False, indent=2))


# ============================================================
# Run management
# ============================================================
def _ensure_runs_structure(d: date) -> None:
    key = _key(runs_meta_path(d))
    if sb.exists(key):
        return
    # 何もない → r1 を作る
    meta = {
        "active": "r1",
        "runs": [{
            "id": "r1", "topic": "",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "stages": dict(EMPTY_STAGES),
        }],
    }
    sb.put_json(key, meta)
    # r1 の初期 state も置く
    sb.put_json(_key(state_path_for(d, "r1")), {"topic": "", "stages": dict(EMPTY_STAGES)})


def load_runs_meta(d: date) -> dict:
    _ensure_runs_structure(d)
    raw = sb.get_json(_key(runs_meta_path(d)), default={"active": "r1", "runs": []})
    # 各 run の stages/topic を state.json から最新化
    for run in raw.get("runs", []):
        rid = run["id"]
        state = sb.get_json(_key(state_path_for(d, rid)), default=None)
        if state:
            run["topic"] = state.get("topic", run.get("topic", ""))
            run["stages"] = {**EMPTY_STAGES, **state.get("stages", {})}
    return raw


def save_runs_meta(d: date, meta: dict) -> None:
    sb.put_json(_key(runs_meta_path(d)), meta)


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
    sb.put_json(_key(state_path_for(d, new_id)), {"topic": topic, "stages": dict(EMPTY_STAGES)})
    return new_id


def set_active_run(d: date, run_id: str) -> None:
    meta = load_runs_meta(d)
    if run_id not in [r["id"] for r in meta["runs"]]:
        raise ValueError(f"Run {run_id} が存在しません")
    meta["active"] = run_id
    save_runs_meta(d, meta)


def delete_run(d: date, run_id: str) -> None:
    """Run を削除（配下キー全削除）。最後の1つは削除不可。"""
    meta = load_runs_meta(d)
    if len(meta["runs"]) <= 1:
        raise ValueError("最後の Run は削除できません")
    meta["runs"] = [r for r in meta["runs"] if r["id"] != run_id]
    if meta["active"] == run_id:
        meta["active"] = meta["runs"][-1]["id"]
    save_runs_meta(d, meta)
    # 配下キーを全削除
    prefix = f"{d.isoformat()}/runs/{run_id}/"
    sb.delete_prefix(prefix)


def rename_run_topic(d: date, run_id: str, topic: str) -> None:
    sp_key = _key(state_path_for(d, run_id))
    s = sb.get_json(sp_key, default={"stages": dict(EMPTY_STAGES)})
    s["topic"] = topic
    sb.put_json(sp_key, s)


def update_run_name(d: date, run_id: str, name: str) -> None:
    meta = load_runs_meta(d)
    for r in meta["runs"]:
        if r["id"] == run_id:
            r["name"] = name
            break
    save_runs_meta(d, meta)


def list_all_runs() -> list[dict]:
    """全日付の全制作を最新順で一覧化（全ユーザー共通）。
    各要素: {date, id, name, topic, stages, created_at}"""
    # 全 runs.json を列挙
    all_paths = sb.list_paths("")
    runs_meta_keys = [p for p in all_paths if p.endswith("/runs.json")]
    result: list[dict] = []
    for key in runs_meta_keys:
        date_str = key.split("/")[0]
        meta = sb.get_json(key, default=None)
        if not meta:
            continue
        for r in meta.get("runs", []):
            rid = r["id"]
            stages = dict(EMPTY_STAGES)
            stages.update(r.get("stages", {}))
            topic = r.get("topic", "")
            state = sb.get_json(f"{date_str}/runs/{rid}/state.json", default=None)
            if state:
                topic = state.get("topic", topic)
                stages = {**EMPTY_STAGES, **state.get("stages", {})}
            result.append({
                "date": date_str,
                "id": rid,
                "name": r.get("name", ""),
                "topic": topic,
                "stages": stages,
                "created_at": r.get("created_at") or date_str,
            })
    result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return result


# ============================================================
# State (active run)
# ============================================================
def load_state(d: date) -> dict[str, Any]:
    s = sb.get_json(_key(state_path(d)), default=None)
    if s is None:
        return {"topic": "", "stages": dict(EMPTY_STAGES)}
    s.setdefault("stages", {})
    s["stages"] = {k: bool(s["stages"].get(k, False)) for k in EMPTY_STAGES}
    return s


def save_state(d: date, state: dict[str, Any]) -> None:
    sb.put_json(_key(state_path(d)), state)


def mark_stage(d: date, stage: str, done: bool = True) -> None:
    s = load_state(d)
    s.setdefault("stages", {})[stage] = done
    save_state(d, s)


# ============================================================
# Stage artifacts: themes / cases / axes / angle / outline / sections / blog / posts / review
# ============================================================
def load_themes(d: date) -> dict:
    return sb.get_json(_key(themes_path(d)), default={"target": "", "themes": [], "selected_idx": -1})


def save_themes(d: date, data: dict) -> None:
    sb.put_json(_key(themes_path(d)), data)


def load_cases(d: date) -> pd.DataFrame:
    csv = sb.get_text(_key(cases_path(d)))
    if not csv:
        return pd.DataFrame(columns=DEFAULT_CASE_COLUMNS)
    try:
        return pd.read_csv(StringIO(csv))
    except Exception:
        return pd.DataFrame(columns=DEFAULT_CASE_COLUMNS)


def save_cases(d: date, df: pd.DataFrame) -> None:
    sb.put_text(_key(cases_path(d)), df.to_csv(index=False))


def load_axes(d: date) -> list[dict[str, str]]:
    return sb.get_json(_key(axes_path(d)), default=[])


def save_axes(d: date, axes: list[dict[str, str]]) -> None:
    """軸を保存。`assignments` を初めて見たときに `original_assignments` を保持。"""
    existing = load_axes(d)
    for i, ax in enumerate(axes):
        if "assignments" not in ax:
            continue
        prev_original = existing[i].get("original_assignments") if i < len(existing) else None
        if prev_original is not None:
            ax["original_assignments"] = prev_original
        else:
            ax["original_assignments"] = dict(ax["assignments"])
    sb.put_json(_key(axes_path(d)), axes)


def load_angle(d: date) -> str:
    return sb.get_text(_key(angle_path(d))) or ""


def save_angle(d: date, text: str) -> None:
    sb.put_text(_key(angle_path(d)), text)


def load_outline(d: date) -> str:
    return sb.get_text(_key(outline_path(d))) or ""


def save_outline(d: date, text: str) -> None:
    sb.put_text(_key(outline_path(d)), text)


def load_sections_file(d: date) -> dict:
    return sb.get_json(_key(sections_path(d)), default={"title": "", "lead": "", "sections": []})


def save_sections_file(d: date, data: dict) -> None:
    sb.put_json(_key(sections_path(d)), data)


def load_blog(d: date) -> str:
    return sb.get_text(_key(blog_path(d))) or ""


def save_blog(d: date, text: str) -> None:
    sb.put_text(_key(blog_path(d)), text)


def load_posts(d: date) -> list[dict[str, Any]]:
    return sb.get_json(_key(posts_path(d)), default=[])


def save_posts(d: date, posts: list[dict[str, Any]]) -> None:
    sb.put_json(_key(posts_path(d)), posts)


def load_review(d: date) -> dict:
    return sb.get_json(_key(review_path(d)), default={"key_sections": [], "images": []})


def save_review(d: date, data: dict) -> None:
    sb.put_json(_key(review_path(d)), data)


def load_results(d: date) -> dict[str, Any]:
    return sb.get_json(_key(results_path(d)), default={})


def save_results(d: date, results: dict[str, Any]) -> None:
    sb.put_json(_key(results_path(d)), results)


# ============================================================
# Image I/O (binary)
# ============================================================
def image_exists(d: date, image_id: str, ext: str = "png") -> bool:
    return sb.exists(_key(image_path(d, image_id, ext)))


def load_image_bytes(d: date, image_id: str, ext: str = "png") -> bytes | None:
    return sb.get_bytes(_key(image_path(d, image_id, ext)))


def save_image_bytes(d: date, image_id: str, data: bytes, ext: str = "png") -> None:
    sb.put_bytes(_key(image_path(d, image_id, ext)), data)


# ============================================================
# Snapshot original (AI原案保存)
# ============================================================
def snapshot_original(target: Path | str) -> None:
    """AI生成完了後に呼ぶ。target を `.original.<ext>` キーへコピー保存。
    再生成時は上書きされ、user_save時は触らない。"""
    src = str(target)
    if not sb.exists(src):
        return
    # 拡張子を分離
    if "." in src.rsplit("/", 1)[-1]:
        head, _, ext = src.rpartition(".")
        dst = f"{head}.original.{ext}"
    else:
        dst = f"{src}.original"
    sb.copy_path(src, dst)


def load_original(target: Path | str) -> str | None:
    src = str(target)
    if "." in src.rsplit("/", 1)[-1]:
        head, _, ext = src.rpartition(".")
        dst = f"{head}.original.{ext}"
    else:
        dst = f"{src}.original"
    return sb.get_text(dst)


# ============================================================
# 互換性スタブ: 旧 _user_root / themes_global_path（参照されたら globals に逃がす）
# ============================================================
def _user_root() -> Path:
    """互換性のため残置。Supabase化により実体は意味を持たないが、
    ZIPバックアップ等の旧コードが参照するため空の Path を返す。"""
    return Path("")


def themes_global_path() -> Path:
    """互換性のため残置。Supabase版では globals テーブルが正。"""
    return Path("themes_global.json")


# ============================================================
# Backup / Export
# ============================================================
def export_zip_bytes() -> bytes:
    """全アーティファクトを ZIP にまとめてバイトで返す。サイドバーのバックアップ機能用。
    artifacts テーブル全パスを取り出し、テキストはそのまま / バイナリは base64 デコードして格納。
    globals テーブルの内容も `_globals/<key>` として含める。"""
    import io
    import zipfile
    import base64
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # artifacts 全件
        for p in sb.list_paths(""):
            text = sb.get_text(p)
            if text is not None:
                zf.writestr(p, text.encode("utf-8"))
            else:
                # バイナリ
                data = sb.get_bytes(p)
                if data is not None:
                    zf.writestr(p, data)
        # globals
        for key in ["themes_global"]:
            val = sb.get_global(key)
            if val is not None:
                zf.writestr(f"_globals/{key}.json", val.encode("utf-8"))
    return buf.getvalue()


def import_zip_bytes(zip_bytes: bytes) -> int:
    """ZIPバックアップから復元。既存データは上書き（同じキーは置き換え）。
    戻り値: 復元したファイル数。"""
    import io
    import zipfile
    count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            data = zf.read(info.filename)
            name = info.filename
            if name.startswith("_globals/"):
                key = name[len("_globals/"):].rsplit(".json", 1)[0]
                try:
                    sb.put_global(key, data.decode("utf-8"))
                    count += 1
                except Exception:
                    pass
            else:
                # テキスト判定: utf-8 デコードできるか
                try:
                    text = data.decode("utf-8")
                    sb.put_text(name, text)
                except UnicodeDecodeError:
                    sb.put_bytes(name, data)
                count += 1
    return count
