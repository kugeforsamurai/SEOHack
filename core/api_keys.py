"""APIキーを session_state 優先で取得するヘルパー。
- クラウド環境: ユーザーがUIで入力 → st.session_state に保持（サーバー保存なし、セッションのみ）
- ローカル環境: .env からも読み取り可能（フォールバック）
"""
from __future__ import annotations
import os


def get_key(name: str) -> str:
    """API キーを返す。優先順位:
    1. st.session_state[f"key_{name}"]（ユーザーが UI で入力した一時的な上書き）
    2. st.secrets[name]（Streamlit Cloud Secrets、認証されたユーザーが共有利用）
    3. os.environ[name]（ローカル開発の .env 用）
    4. 空文字（未設定）"""
    # 1. UI入力（一時オーバーライド）
    try:
        import streamlit as st
        v = st.session_state.get(f"key_{name}", "") or ""
        if v.strip():
            return v.strip()
    except Exception:
        pass

    # 2. Streamlit Secrets（クラウド共有）
    try:
        import streamlit as st
        if name in st.secrets:
            v = (st.secrets[name] or "").strip()
            if v:
                return v
    except Exception:
        pass

    # 3. .env（ローカル開発）
    return (os.environ.get(name, "") or "").strip()


def has(name: str) -> bool:
    return bool(get_key(name))


def get_app_password() -> str:
    """アプリ全体のパスワード。Secrets / env から取得。空ならパスワード認証無効。"""
    try:
        import streamlit as st
        if "APP_PASSWORD" in st.secrets:
            return (st.secrets["APP_PASSWORD"] or "").strip()
    except Exception:
        pass
    return (os.environ.get("APP_PASSWORD", "") or "").strip()
