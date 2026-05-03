"""STUDIO への投稿データ変換。
Markdown から STUDIO 用 HTML へ変換（H2→H3 / H3→H4）。
"""
from __future__ import annotations
import re
from pathlib import Path


def _inline(text: str) -> str:
    """インライン書式: 太字・リンク・画像プレースホルダ。"""
    # 太字 **text** → <strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 斜体 *text* → <em>（**を先に処理した後、残った*）
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    # リンク [text](url) → <a>
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # インライン画像 ![alt](src) → コメント（STUDIO では別途貼付するため）
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"<!-- 画像挿入位置: \1 -->", text)
    return text


def md_to_studio_html(md: str) -> str:
    """簡易 Markdown → HTML 変換。
    STUDIO 仕様に合わせて：
    - H1 (`# `) はタイトル扱いなので本文からは除外
    - H2 (`## `) → H3（STUDIO の大見出し）
    - H3 (`### `) → H4（STUDIO の小見出し）
    - H4以上 (`#### `) → H4 のまま
    - 箇条書き、太字、リンク 対応
    - 画像 ![alt](src) は HTML コメント化（STUDIO で別途 Cmd+V 貼付）
    - 区切り線 --- → <hr>
    """
    lines = md.split("\n")
    out: list[str] = []
    in_list = False

    for raw in lines:
        line = raw.rstrip()

        # H1 はスキップ（タイトルは別フィールド）
        if line.startswith("# ") and not line.startswith("## "):
            continue

        # 見出し
        if line.startswith("## "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{_inline(line[3:].strip())}</h3>")
            continue
        if line.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{_inline(line[4:].strip())}</h4>")
            continue
        if line.startswith("#### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h4>{_inline(line[5:].strip())}</h4>")
            continue

        # 区切り線
        if line.strip() in ("---", "***"):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr>")
            continue

        # 箇条書き
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(line[2:].strip())}</li>")
            continue

        # 空行
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue

        # 段落
        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{_inline(line.strip())}</p>")

    if in_list:
        out.append("</ul>")

    return "\n".join(out)


def extract_title(md: str) -> str:
    """Markdown の最初の H1 をタイトルとして抽出。"""
    m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else ""


def strip_h1(md: str) -> str:
    """先頭の H1 行を本文から除去。"""
    return re.sub(r"^#\s+.+\n+", "", md, count=1)


def build_studio_payload(blog_md: str) -> dict:
    """STUDIO 用 payload。クリップボードに JSON 形式で渡す。
    {title, body_html}
    """
    title = extract_title(blog_md)
    body_md = strip_h1(blog_md)
    body_html = md_to_studio_html(body_md)
    return {"title": title, "body_html": body_html}


def make_bookmarklet() -> str:
    """STUDIO 編集画面で実行するブックマークレットコード。
    クリップボードから JSON を読み、タイトルと本文を自動入力。"""
    # 改行とインデントを削った 1 行 JS（ブックマークレット形式）
    js = (
        "javascript:(async()=>{"
        "try{"
        "const t=await navigator.clipboard.readText();"
        "const d=JSON.parse(t);"
        "if(!d.title||!d.body_html){alert('クリップボードのデータ形式が不正です');return;}"
        # タイトル入力欄を探す
        "const allInputs=[...document.querySelectorAll('input,textarea')];"
        "const titleEl=allInputs.find(e=>/タイトル|title|題名|name/i.test("
        "(e.placeholder||'')+(e.getAttribute('aria-label')||'')+(e.name||'')"
        "));"
        "if(titleEl){"
        "const proto=titleEl.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
        "const setter=Object.getOwnPropertyDescriptor(proto,'value').set;"
        "setter.call(titleEl,d.title);"
        "titleEl.dispatchEvent(new Event('input',{bubbles:true}));"
        "titleEl.dispatchEvent(new Event('change',{bubbles:true}));"
        "}else{console.warn('タイトル入力欄が見つかりません');}"
        # 本文 ProseMirror に挿入
        "const body=document.querySelector('.ProseMirror[contenteditable=\"true\"]');"
        "if(body){"
        "body.focus();"
        "const dt=new DataTransfer();"
        "dt.setData('text/html',d.body_html);"
        "dt.setData('text/plain',d.body_html.replace(/<[^>]+>/g,''));"
        "body.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:dt}));"
        "}else{alert('本文エディタが見つかりませんでした。STUDIO の編集画面で実行してください。');return;}"
        "alert('入力完了。画像と書式を確認の上、STUDIO の公開ボタンを押してください。');"
        "}catch(e){alert('エラー: '+e.message);}})();"
    )
    return js
