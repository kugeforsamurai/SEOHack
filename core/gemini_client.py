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


def _post(payload: dict) -> dict:
    url = f"{API_BASE}/models/{_model()}:generateContent"
    headers = {"x-goog-api-key": _api_key(), "Content-Type": "application/json"}
    with httpx.Client(timeout=TIMEOUT) as client:
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


def generate_text(prompt: str) -> str:
    """Markdown/通常テキスト生成。"""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = _post(payload)
    return _extract_text(resp)


def generate_json(prompt: str) -> Any:
    """JSON出力モード。"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    resp = _post(payload)
    text = _extract_text(resp)
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error: {e}\n--- raw ---\n{text[:500]}")
