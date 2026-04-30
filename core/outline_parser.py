"""outline.md から `###` セクション一覧を抽出する。"""
from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class Section:
    id: str  # 安定識別子: h2_1 / self_practice / summary / cta / sec_N
    title: str  # ユーザー表示用タイトル（"H2_1:" 等のプレフィックスは除去済）
    memo: str  # outline メモ全文（生成時に Gemini に渡す）
    target_chars: int  # 推定字数（パースできなければ 500）


def _slug(title: str) -> str:
    # H2_N より特殊セクション判定を先に（"H2_5: まとめ" を summary と認識するため）
    if "自社実践" in title:
        return "self_practice"
    if "まとめ" in title or "結論" in title or "総括" in title:
        return "summary"
    if "CTA" in title.upper() or "誘導" in title:
        return "cta"
    if "リード" in title:
        return "lead"
    m = re.match(r"^(H2[_\-]?\d+)", title, re.IGNORECASE)
    if m:
        return m.group(1).lower().replace("-", "_")
    return ""


def parse(outline_md: str) -> list[Section]:
    """### で始まる各ブロックをセクションとして抽出。
    Geminiの出力フォーマットがブレても拾えるよう緩く解析する。"""
    if not outline_md:
        return []

    parts = re.split(r"(?m)^###\s+", outline_md)
    sections: list[Section] = []
    counter = 0

    for part in parts[1:]:
        lines = part.split("\n", 1)
        header = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""

        # 次の H2 (##) や H1 (#) が来たら本文ここまで
        m = re.search(r"(?m)^(?:##|#)\s+", body)
        if m:
            body = body[: m.start()]

        # タイトルクリーン: "H2_1: タイトル" → "タイトル"
        title_raw = header.rstrip(":：").strip()
        title_clean = re.sub(r"^H2[_\-]?\d+\s*[:：]?\s*", "", title_raw).strip() or title_raw

        slug = _slug(title_raw)
        if not slug:
            counter += 1
            slug = f"sec_{counter}"

        # 推定文字数（"1,200字" のようなカンマ区切りも対応）
        target = 500
        m_chars = re.search(r"推定字数[：:]\s*([0-9][0-9,]*)\s*字?", body)
        if m_chars:
            try:
                target = int(m_chars.group(1).replace(",", ""))
            except ValueError:
                pass

        sections.append(Section(
            id=slug,
            title=title_clean,
            memo=body.strip(),
            target_chars=target,
        ))

    return sections


def extract_title_candidates(outline_md: str) -> list[str]:
    """`# タイトル案` セクション直下の番号付きリストを取得。"""
    m = re.search(r"(?ms)^#\s*タイトル案\s*\n(.+?)(?=^#|\Z)", outline_md)
    if not m:
        return []
    block = m.group(1)
    return [s.strip() for s in re.findall(r"(?m)^\s*\d+\.\s*(.+)$", block)]


def extract_lead_direction(outline_md: str) -> str:
    """`## リード方向性` セクションのテキスト本文を取得。"""
    m = re.search(r"(?ms)^##\s*リード方向性\s*\n(.+?)(?=^##|\Z)", outline_md)
    if not m:
        return ""
    return m.group(1).strip()


def parse_full(outline_md: str) -> dict:
    """outline.md 全体を構造化辞書に変換。
    {
      "title_candidates": [str, ...],
      "lead_direction": str,
      "sections": [{id, title, target_chars, memo}, ...]
    }
    """
    sections = []
    for s in parse(outline_md):
        sections.append({
            "id": s.id,
            "title": s.title,
            "target_chars": s.target_chars,
            "memo": s.memo,
        })
    return {
        "title_candidates": extract_title_candidates(outline_md),
        "lead_direction": extract_lead_direction(outline_md),
        "sections": sections,
    }


def serialize_full(structured: dict) -> str:
    """構造化辞書 → outline.md Markdown 文字列。
    parse_full の逆変換だが、メモは bullet list に整形し直す。"""
    out: list[str] = []

    titles = [t for t in structured.get("title_candidates", []) if (t or "").strip()]
    out.append("# タイトル案")
    for i, t in enumerate(titles, 1):
        out.append(f"{i}. {t.strip()}")
    out.append("")

    lead = (structured.get("lead_direction") or "").strip()
    out.append("## リード方向性")
    out.append(lead if lead else "")
    out.append("")

    out.append("## 構成")
    out.append("")
    for sec in structured.get("sections", []):
        title = (sec.get("title") or "").strip() or "（無題セクション）"
        target = int(sec.get("target_chars") or 500)
        memo = (sec.get("memo") or "").strip()
        out.append(f"### {title}")
        out.append(f"- 推定字数: {target}字")
        out.append("- 内容メモ:")
        # メモ複数行を bullet 化
        if memo:
            for line in memo.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # 既に "- " で始まっていたら剥がす
                line = line.lstrip("-•*").strip()
                if line:
                    out.append(f"  - {line}")
        else:
            out.append("  - （未記入）")
        out.append("")

    return "\n".join(out).rstrip() + "\n"
