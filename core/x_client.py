"""X (Twitter) API v2 ラッパ。OAuth 1.0a User Context で投稿。"""
from __future__ import annotations
from dataclasses import dataclass

import tweepy

from core import api_keys


@dataclass
class PostResult:
    ok: bool
    tweet_id: str | None
    url: str | None
    error: str | None


def _required_keys() -> list[str]:
    return ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]


def keys_configured() -> bool:
    return all(api_keys.has(k) for k in _required_keys())


def missing_keys() -> list[str]:
    return [k for k in _required_keys() if not api_keys.has(k)]


def _client() -> tweepy.Client:
    if not keys_configured():
        raise RuntimeError(f"X API キー未設定: {missing_keys()}")
    return tweepy.Client(
        consumer_key=api_keys.get_key("X_API_KEY"),
        consumer_secret=api_keys.get_key("X_API_SECRET"),
        access_token=api_keys.get_key("X_ACCESS_TOKEN"),
        access_token_secret=api_keys.get_key("X_ACCESS_TOKEN_SECRET"),
    )


def verify_credentials() -> tuple[bool, str]:
    """認証確認。screen_nameを返す。"""
    try:
        auth = tweepy.OAuth1UserHandler(
            api_keys.get_key("X_API_KEY"),
            api_keys.get_key("X_API_SECRET"),
            api_keys.get_key("X_ACCESS_TOKEN"),
            api_keys.get_key("X_ACCESS_TOKEN_SECRET"),
        )
        api = tweepy.API(auth)
        me = api.verify_credentials()
        return True, me.screen_name
    except Exception as e:
        return False, str(e)


def post_tweet(text: str) -> PostResult:
    """単発ツイート投稿。"""
    try:
        client = _client()
        resp = client.create_tweet(text=text)
        tweet_id = str(resp.data["id"])
        # URLはユーザー名を含むのが理想だがAPIで取得すると追加リクエストになるためi/web/status形式を使う
        return PostResult(ok=True, tweet_id=tweet_id, url=f"https://x.com/i/web/status/{tweet_id}", error=None)
    except Exception as e:
        return PostResult(ok=False, tweet_id=None, url=None, error=str(e))
