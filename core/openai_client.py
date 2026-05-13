"""OpenAI API ラッパ。
- 画像生成: gpt-image-1 (env: OPENAI_IMAGE_MODEL)
- テキスト生成: gpt-4o 等 (env: OPENAI_TEXT_MODEL) — Stage⓪のテーマ提案で使用"""
from __future__ import annotations
import base64
import json as _json
import os
import re
from pathlib import Path
from typing import Any

import httpx

from core import api_keys

API_URL = "https://api.openai.com/v1/images/generations"
CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
TIMEOUT = httpx.Timeout(180.0, connect=10.0)


def _api_key() -> str:
    key = api_keys.get_key("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY が未設定です。サイドバーの『API設定』で入力してください。")
    return key


def _model() -> str:
    return os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")


def _text_model() -> str:
    return os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o")


def keys_configured() -> bool:
    return api_keys.has("OPENAI_API_KEY")


def generate_text(prompt: str) -> str:
    """gpt-4o でテキスト生成。"""
    payload = {
        "model": _text_model(),
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(CHAT_API_URL, headers=headers, json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:600]}")
    data = r.json()
    return (data["choices"][0]["message"]["content"] or "").strip()


def generate_json(prompt: str) -> Any:
    """gpt-4o で JSON 出力（コードフェンス剥がし対応）。"""
    text = generate_text(prompt)
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return _json.loads(text)
    except _json.JSONDecodeError as e:
        raise RuntimeError(f"OpenAI JSON parse error: {e}\n--- raw ---\n{text[:500]}")


def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "medium",
    _model_override: str | None = None,
) -> bytes:
    """画像を生成して PNG バイト列で返す。保存は呼び出し側で行う（Supabase等）。
    gpt-image-2 が verify 未完了で 403 になった場合、自動で gpt-image-1 にフォールバック。"""
    chosen_model = _model_override or _model()
    payload = {
        "model": chosen_model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        r = client.post(API_URL, headers=headers, json=payload)

    # 自動フォールバック: gpt-image-2 verify 未完了 → gpt-image-1 で再試行
    if (
        r.status_code == 403
        and chosen_model.startswith("gpt-image-2")
        and ("verified" in r.text or "verify" in r.text.lower())
        and _model_override is None  # 無限ループ防止
    ):
        return generate_image(
            prompt=prompt, size=size, quality=quality,
            _model_override="gpt-image-1",
        )

    if r.status_code >= 400:
        raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:600]}")
    data = r.json()
    b64 = data["data"][0]["b64_json"]
    return base64.b64decode(b64)
