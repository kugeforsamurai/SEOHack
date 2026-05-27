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


def _samples_block(label: str, samples: str) -> str:
    """ユーザー記述の文体サンプルをプロンプトに織り込む。空なら何も挿入しない。
    重要: サンプルからは「文章の形（語尾・改行・段落構成）」だけを学び、
    「内容のアプローチ（哲学的・内省的など）」は学ばない。"""
    samples = (samples or "").strip()
    if not samples:
        return ""
    return f"""\

## 参考文体サンプル（{label} / **文体のみ** をサンプルに寄せる）
以下はこのアカウントの筆者が過去に書いた文章。

### サンプルから学ぶこと（文体のみ）
- **語尾**（「〜と思います」「〜と感じています」「〜ではないでしょうか」など）
- **接続詞・つなぎの言葉**（「一方、」「つまり、」「実際に」「先述の」など）
- **改行密度・段落の長さ**
- **体言止めや断定の頻度**
- **呼びかけのトーン**（穏やか／断定的／問いかけ風など）

### サンプルから**学ばないこと**（厳禁）
- ❌ **哲学的・抽象的・内省的な内容アプローチ**：サンプルがそういう内容でも、SEO記事は「読者の実務課題への直接的な回答」が第一目的。哲学的思索や時代論には流れない
- ❌ **自伝的・エッセイ的な構成**：「私が体験した→社会的に解釈→自分の生き方」のような構造は SEO 記事には不要
- ❌ **結論を曖昧に締める**（「〜ではないでしょうか」「〜だと感じています」だけで本文を終えない。読者の問いに対する明確な答えを必ず提示する）
- ❌ **テーマ・事例・引用のコピー**：サンプルに出てくる地名・人名・引用（ピカソ、ドバイ等）を流用しない

SEO記事は **実用情報の提供**。文体の「形」だけサンプルから借りて、中身は読者の問題解決として組み立てる。

---
{samples}
---
"""


def blog_block() -> str:
    cfg = load()
    p = cfg.get("blog", {})
    s = cfg.get("shared", {})
    default_tone = (
        "**SEO記事として書く**。読者の検索意図への明確な回答を最優先。"
        "**否定的・批判的表現は極力避け、建設的に書く**（『〜は誤り』『〜してはならない』を避ける）。"
        "**ただし強すぎる断定・命令調も避ける**：『〜は明確です』『〜は決定的です』『〜こそが正解』"
        "『絶対に〜』『〜しかありません』のような表現は禁止（読者を受動的にする）。"
        "代わりに『〜が選ばれています』『〜という結果が出ています』『〜が有力な選択肢です』など、"
        "事実+穏やかな解釈で書く。哲学的・内省的な思索や過度なエッセイ調には流れず、"
        "事例 → 示唆 → 実装ステップ の実用的な流れを基本とする。"
        "**語尾を変化させる**：同じ語尾を3文以上連続させず、『です/ます/でしょう/ではないでしょうか/と考えられます』等をローテーション。体言止めや倒置を適度に混ぜる。"
        "**AIっぽいMarkdown装飾を避ける**：`**太字**` の濫用、`| 列 | 列 |` のテーブル記法、`-` 箇条書きの多用は避ける。"
        "比較データは『A は CPA 77%減、B は CPL 73%減』のように散文で書く。地の文を主軸にした自然な人間の文章にする。"
    )
    tone_constraints = (p.get("tone_constraints") or "").strip() or default_tone
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
- **トーン制約（最重要）**: {tone_constraints}
{_samples_block('ブログ', p.get('style_samples', ''))}"""


def posts_block() -> str:
    cfg = load()
    p = cfg.get("posts", {})
    s = cfg.get("shared", {})
    default_tone = (
        "**否定的・批判的表現は極力避け、建設的に書く**（『〜は誤り』『〜は無意味』を避ける）。"
        "**ただし命令調・断言調も避ける**：『〜は明確だ』『〜は決定的だ』『〜こそが正解』『絶対に〜』"
        "は禁止。代わりに『〜が選ばれる』『〜という結果が出ている』『〜が成果に繋がりやすい』など、"
        "事実+穏やかな解釈で書く。哲学的・内省的な思索ではなく、読者の実務に直接効くデータ・事例・How-toを主軸にする。"
        "語尾は変化させ、同じ語尾の連続を避ける。"
    )
    tone_constraints = (p.get("tone_constraints") or "").strip() or default_tone
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
- **トーン制約（最重要）**: {tone_constraints}
{_samples_block('X投稿', p.get('style_samples', ''))}"""


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
