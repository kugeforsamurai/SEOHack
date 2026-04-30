"""APIキーを session_state 優先で取得するヘルパー。
- クラウド環境: ユーザーがUIで入力 → st.session_state に保持（サーバー保存なし、セッションのみ）
- ローカル環境: .env からも読み取り可能（フォールバック）
"""
from __future__ import annotations
import os


def get_key(name: str) -> str:
    """API キーを返す。優先順位:
    1. st.session_state[f"key_{name}"]（ユーザーが UI で入力）
    2. os.environ[name]（ローカル開発の .env 用）
    3. 空文字（未設定）"""
    try:
        import streamlit as st
        v = st.session_state.get(f"key_{name}", "") or ""
        if v.strip():
            return v.strip()
    except Exception:
        pass
    return (os.environ.get(name, "") or "").strip()


def has(name: str) -> bool:
    return bool(get_key(name))
