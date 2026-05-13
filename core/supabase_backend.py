"""Supabase REST API (PostgREST) を直接叩く軽量KVバックエンド。
artifacts テーブル: path PK / content TEXT / is_text BOOL
globals テーブル: key PK / content TEXT
画像などのバイナリは base64 で content に格納する（is_text=False）。"""
from __future__ import annotations
import base64
import json
import os
from functools import lru_cache
from typing import Optional

import httpx


def _read_secret(name: str) -> Optional[str]:
    """Streamlit secrets 優先、無ければ環境変数。両方無ければ None。"""
    try:
        import streamlit as st  # type: ignore
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name)


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    url = _read_secret("SUPABASE_URL")
    key = _read_secret("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY が未設定です。"
            "Streamlit Cloud の Settings → Secrets で設定してください。"
        )
    return httpx.Client(
        base_url=f"{url.rstrip('/')}/rest/v1",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


# ---------- artifacts (path → content) ----------

def get_text(path: str) -> Optional[str]:
    """テキストアーティファクトを読む。なければ None。"""
    r = _client().get(
        "/artifacts",
        params={"path": f"eq.{path}", "select": "content,is_text"},
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return None
    row = rows[0]
    if not row.get("is_text", True):
        return None  # バイナリは get_bytes を使え
    return row.get("content")


def put_text(path: str, content: str) -> None:
    """テキストアーティファクトを書き込む（upsert）。"""
    r = _client().post(
        "/artifacts",
        params={"on_conflict": "path"},
        headers={"Prefer": "resolution=merge-duplicates"},
        json={"path": path, "content": content, "is_text": True, "content_bytes": None},
    )
    r.raise_for_status()


def get_bytes(path: str) -> Optional[bytes]:
    """バイナリアーティファクトを読む。なければ None。"""
    r = _client().get(
        "/artifacts",
        params={"path": f"eq.{path}", "select": "content,is_text"},
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return None
    row = rows[0]
    content = row.get("content")
    if content is None:
        return None
    if row.get("is_text", True):
        # テキストとして保存されている → そのまま bytes に
        return content.encode("utf-8")
    return base64.b64decode(content)


def put_bytes(path: str, data: bytes) -> None:
    """バイナリアーティファクト（base64 で content に格納）。"""
    encoded = base64.b64encode(data).decode("ascii")
    r = _client().post(
        "/artifacts",
        params={"on_conflict": "path"},
        headers={"Prefer": "resolution=merge-duplicates"},
        json={"path": path, "content": encoded, "is_text": False, "content_bytes": None},
    )
    r.raise_for_status()


def exists(path: str) -> bool:
    r = _client().get(
        "/artifacts",
        params={"path": f"eq.{path}", "select": "path"},
    )
    r.raise_for_status()
    return bool(r.json())


def list_paths(prefix: str) -> list[str]:
    """指定prefixで始まる全 path を返す。"""
    r = _client().get(
        "/artifacts",
        params={"path": f"like.{prefix}*", "select": "path"},
    )
    r.raise_for_status()
    return [row["path"] for row in r.json()]


def delete_path(path: str) -> None:
    r = _client().delete(
        "/artifacts",
        params={"path": f"eq.{path}"},
    )
    r.raise_for_status()


def delete_prefix(prefix: str) -> None:
    """prefix から始まる全 path を削除（run削除などに使用）。"""
    r = _client().delete(
        "/artifacts",
        params={"path": f"like.{prefix}*"},
    )
    r.raise_for_status()


def copy_path(src: str, dst: str) -> None:
    """src のレコードを dst へコピー（snapshot_original で使用）。"""
    r = _client().get(
        "/artifacts",
        params={"path": f"eq.{src}", "select": "content,content_bytes,is_text"},
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return
    row = rows[0]
    payload = {
        "path": dst,
        "content": row.get("content"),
        "is_text": row.get("is_text", True),
        "content_bytes": row.get("content_bytes"),
    }
    r2 = _client().post(
        "/artifacts",
        params={"on_conflict": "path"},
        headers={"Prefer": "resolution=merge-duplicates"},
        json=payload,
    )
    r2.raise_for_status()


# ---------- globals (key → content TEXT) ----------

def get_global(key: str) -> Optional[str]:
    r = _client().get(
        "/globals",
        params={"key": f"eq.{key}", "select": "content"},
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return None
    return rows[0].get("content")


def put_global(key: str, content: str) -> None:
    r = _client().post(
        "/globals",
        params={"on_conflict": "key"},
        headers={"Prefer": "resolution=merge-duplicates"},
        json={"key": key, "content": content},
    )
    r.raise_for_status()


# ---------- 便利関数 ----------

def get_json(path: str, default=None):
    raw = get_text(path)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return default


def put_json(path: str, data) -> None:
    put_text(path, json.dumps(data, ensure_ascii=False, indent=2))
