"""人格設定をJSONから読み、各プロンプトに注入できるブロックを生成する。"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "persona.json"


def load() -> dict:
    if not CONFIG_PATH.exists():
        return {"blog": {}, "posts": {}, "shared": {}}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ng_list(ng: list[str]) -> str:
    return "、".join(f"「{w}」" for w in ng) if ng else "（指定なし）"


def _emoji_line(use_emoji: bool) -> str:
    if use_emoji:
        return "適度に使用OK"
    return (
        "**絵文字・特殊記号・豆腐文字を一切使わない**。"
        "具体的に禁止: 絵文字全般（🎨🚀🔥💡✨など）/ 特殊記号（☐ □ ⬜ ■ ▼ ▲ ★ ☆ ✓ ✗ ✕ → ⇒ ⇨ ⇒ など）/ "
        "Unicodeの装飾文字（特殊な括弧・矢印・チェックマーク等）。"
        "理由: フォント未対応で『×』『□』『豆腐文字』として表示崩れする事故を防ぐため。"
        "強調はMarkdown記法（**太字**）または箇条書き（-）のみで行う。"
    )


def blog_block() -> str:
    cfg = load()
    p = cfg.get("blog", {})
    s = cfg.get("shared", {})
    return f"""\
## 記事の人格設定（必ず守ること）
- **文体**: {p.get('voice', '敬体')}
- **一人称**: 「{p.get('first_person', 'HookHack')}」（『弊社』『当社』『私たち』ではなく必ず『HookHack』と書く）
- **読者像**: {p.get('reader_persona', '')}
- **読者への呼びかけ**: {p.get('address_reader', '')}
- **NGワード（絶対に使わない）**: {_ng_list(p.get('ng_phrases', []))}
- **絵文字・記号**: {_emoji_line(p.get('use_emoji', False))}
- **専門用語の解説**: {p.get('term_explanation', '')}
- **断定の強さ**: {p.get('assertion', '')}
- **CTA**: {p.get('cta_style', '')}
- **競合・他社**: {s.get('competitor_stance', '')}
- **数字・単位の表記**: {s.get('numbers_format', '')}
- **記事末の定型**: {s.get('ending_format', '')}
"""


def posts_block() -> str:
    cfg = load()
    p = cfg.get("posts", {})
    s = cfg.get("shared", {})
    return f"""\
## X投稿の人格設定（必ず守ること）
- **文体**: {p.get('voice', '常体')}
- **一人称**: 「{p.get('first_person', 'HookHack')}」
- **読者像**: {p.get('reader_persona', '')}
- **NGワード（絶対に使わない）**: {_ng_list(p.get('ng_phrases', []))}
- **絵文字・記号**: {_emoji_line(p.get('use_emoji', False))}
- **断定の強さ**: {p.get('assertion', '')}
- **競合・他社**: {s.get('competitor_stance', '')}
- **末尾の定型**: {s.get('ending_format', '')}
"""


def reader_block() -> str:
    """research / synthesizer / outline 用の軽量版（読者像と一人称のみ）。"""
    cfg = load()
    blog = cfg.get("blog", {})
    return f"""\
## 読者像・前提
- 読者: {blog.get('reader_persona', '')}
- 一人称: 「{blog.get('first_person', 'HookHack')}」
"""


def sanitize_emoji(text: str) -> str:
    """絵文字・代表的な特殊記号・豆腐文字（フォント未対応で『×』表示される文字）を除去するポストプロセッサ。
    モデルが指示違反した場合の最終防衛線。"""
    if not text:
        return text
    import re
    # Unicode 絵文字レンジ（多くの絵文字 + 装飾記号）
    emoji_ranges = [
        (0x1F300, 0x1FAFF),  # 各種絵文字（記号・図、絵文字、補足、追加）
        (0x2600, 0x27BF),    # その他の記号 + 装飾用記号
        (0x1F000, 0x1F02F),  # 麻雀牌
        (0x1F0A0, 0x1F0FF),  # トランプ
        (0x1F100, 0x1F1FF),  # 囲み文字
        (0x2300, 0x23FF),    # 各種技術記号
        (0x25A0, 0x25FF),    # 幾何学模様（■□▼▲ など）
        (0xFE00, 0xFE0F),    # バリエーションセレクタ
        (0x200D, 0x200D),    # ZWJ（絵文字結合）
    ]
    out = []
    for ch in text:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in emoji_ranges):
            continue
        out.append(ch)
    cleaned = "".join(out)
    # ZWJ 周辺の余分な空白除去
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    return cleaned
