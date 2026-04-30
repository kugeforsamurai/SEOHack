"""Gemini REST API直叩き。SDKを介さず httpx で直接呼ぶ（Streamlit再実行でクライアントが閉じる問題を回避）。"""
from __future__ import annotations
import json
import os
import re
from typing import Any

import httpx

from core import api_keys

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def _api_key() -> str:
    key = api_keys.get_key("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY が未設定です。サイドバーの『API設定』で入力してください。")
    return key


def keys_configured() -> bool:
    return api_keys.has("GEMINI_API_KEY")


def _model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")


def _deep_research_on() -> bool:
    """サイドバーのディープリサーチモードが ON か。
    ON なら Google Search grounding + 拡張 thinking budget を使う。"""
    try:
        import streamlit as st
        return bool(st.session_state.get("deep_research_mode", False))
    except Exception:
        return False


def _post(payload: dict) -> dict:
    url = f"{API_BASE}/models/{_model()}:generateContent"
    headers = {"x-goog-api-key": _api_key(), "Content-Type": "application/json"}
    # ディープリサーチモード時は所要時間が長くなるのでタイムアウト延長
    timeout = httpx.Timeout(300.0, connect=10.0) if _deep_research_on() else TIMEOUT
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=headers, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"Gemini API {r.status_code}: {r.text[:500]}")
    return r.json()


def _extract_text(resp: dict) -> str:
    try:
        candidates = resp.get("candidates", [])
        if not candidates:
            block = resp.get("promptFeedback", {}).get("blockReason")
            if block:
                raise RuntimeError(f"Geminiが入力をブロック: {block}")
            raise RuntimeError(f"候補なし: {json.dumps(resp)[:300]}")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"レスポンス解析失敗: {e}\n{json.dumps(resp)[:500]}")


def _gen_config_with_thinking() -> dict:
    """ディープリサーチON時は thinking budget を増量。"""
    cfg: dict = {}
    if _deep_research_on():
        # -1 = モデルが自動で最大限使う
        cfg["thinkingConfig"] = {"thinkingBudget": -1}
    return cfg


def _maybe_search_tools() -> list:
    """ディープリサーチON時は google_search ツールを有効化。"""
    if _deep_research_on():
        return [{"google_search": {}}]
    return []


def generate_text(prompt: str) -> str:
    """Markdown/通常テキスト生成。
    ディープリサーチONで Google検索グラウンディング + 拡張thinking。"""
    payload: dict = {"contents": [{"parts": [{"text": prompt}]}]}
    tools = _maybe_search_tools()
    if tools:
        payload["tools"] = tools
    cfg = _gen_config_with_thinking()
    if cfg:
        payload["generationConfig"] = cfg
    resp = _post(payload)
    return _extract_text(resp)


def generate_json(prompt: str) -> Any:
    """JSON出力。
    通常モード: responseMimeType=application/json で strict.
    ディープリサーチON: tools と JSON strict は併用不可なので、tools 有効化 + プロンプト末尾の指示でJSONを引き出して parse する。"""
    payload: dict = {"contents": [{"parts": [{"text": prompt}]}]}

    if _deep_research_on():
        payload["tools"] = [{"google_search": {}}]
        cfg = _gen_config_with_thinking()
        if cfg:
            payload["generationConfig"] = cfg
    else:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    resp = _post(payload)
    text = _extract_text(resp)
    # コードフェンス剥がし + JSON部分の抽出（grounded時はテキストに前置きが混じる可能性）
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    # JSON以外の前後テキストを除去（最初の { または [ から最後の } または ] まで）
    if _deep_research_on():
        m = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
        if m:
            text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error: {e}\n--- raw ---\n{text[:800]}")
