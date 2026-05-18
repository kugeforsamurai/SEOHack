"""STUDIO への投稿データ変換。
Markdown から STUDIO 用 HTML へ変換（H2→H3 / H3→H4）。
記事の構造: タイトル → 導入文 → 監修者情報 → 目次 → 本文。
"""
from __future__ import annotations
import html
import re
from pathlib import Path

PROFILE_URL = "https://samurai-style.tokyo/hashimoto"
SUPERVISOR_NAME = "サムライスタイル株式会社　代表取締役　橋本圭司"
SUPERVISOR_BIO = (
    "事業会社・Web系ベンダー双方での経験とBtoC・BtoBで多様な業界30社以上の"
    "インハウス支援を経験。マクロでの業界理解に基づく戦略立案からミクロでの"
    "施策立案・実行まで伴走し、特に獲得領域におけるリスティング・動画広告運用"
    "からLP改善、CRMへの接続までを得意とする。"
)

QUOTE_IMG_RE = re.compile(r"^>\s*画像[:：]\s*(.+)$")


def _inline(text: str) -> str:
    """インライン書式: 太字・画像・リンク。"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_studio_html(md: str, images: dict[str, str] | None = None) -> str:
    """簡易 Markdown → HTML 変換。
    - H1 (`# `) はタイトル扱いなので本文からは除外
    - H2 (`## `) → H3（STUDIO の大見出し）
    - H3 (`### `) → H4（STUDIO の小見出し）
    - H4以上 (`#### `) → H4 のまま
    - 箇条書き、太字、リンク、画像（`![alt](src)`）対応
    - 引用形式の画像プレースホルダ `> 画像: alt` を、images dict にマッチしたら <img> に、なければプレースホルダ <p data-image-placeholder> として残す
    - 区切り線 `---` → <hr>
    """
    images = images or {}
    lines = md.split("\n")
    out: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("# ") and not line.startswith("## "):
            continue

        # 引用形式の画像プレースホルダ
        m = QUOTE_IMG_RE.match(line.strip())
        if m:
            close_list()
            alt = m.group(1).strip()
            src = images.get(alt)
            if src:
                out.append(f'<p><img src="{src}" alt="{html.escape(alt)}"></p>')
            else:
                out.append(
                    f'<p data-image-placeholder="{html.escape(alt, quote=True)}">'
                    f'[画像プレースホルダ: {html.escape(alt)}]</p>'
                )
            continue

        if line.startswith("## "):
            close_list()
            out.append(f"<h3>{_inline(line[3:].strip())}</h3>")
            continue
        if line.startswith("### "):
            close_list()
            out.append(f"<h4>{_inline(line[4:].strip())}</h4>")
            continue
        if line.startswith("#### "):
            close_list()
            out.append(f"<h4>{_inline(line[5:].strip())}</h4>")
            continue

        if line.strip() in ("---", "***"):
            close_list()
            out.append("<hr>")
            continue

        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(line[2:].strip())}</li>")
            continue

        if not line.strip():
            close_list()
            continue

        close_list()
        out.append(f"<p>{_inline(line.strip())}</p>")

    close_list()
    return "\n".join(out)


def extract_title(md: str) -> str:
    m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else ""


def strip_h1(md: str) -> str:
    return re.sub(r"^#\s+.+\n+", "", md, count=1)


def split_intro_and_body(body_md: str) -> tuple[str, str]:
    """H1 を除いた本文を、最初の H2 (`## `) の前と後ろに分ける。"""
    lines = body_md.split("\n")
    intro_lines: list[str] = []
    body_lines: list[str] = []
    seen_h2 = False
    for ln in lines:
        if not seen_h2 and ln.startswith("## "):
            seen_h2 = True
        (body_lines if seen_h2 else intro_lines).append(ln)
    return "\n".join(intro_lines).strip(), "\n".join(body_lines)


def extract_chapter_titles(body_md: str) -> list[str]:
    """`## ` 行を抽出（章タイトル）。"""
    return [ln[3:].strip() for ln in body_md.split("\n") if ln.startswith("## ")]


def extract_image_placeholders(blog_md: str) -> list[str]:
    """`> 画像: 〜` の alt（画像内容説明）を順に抽出。重複は許容（順序は出現順）。"""
    out: list[str] = []
    for ln in blog_md.split("\n"):
        m = QUOTE_IMG_RE.match(ln.strip())
        if m:
            out.append(m.group(1).strip())
    return out


def supervisor_html() -> str:
    """監修者情報ブロック。
    順序: ラベル → 名前 → 経歴 → プロフィールリンク
    """
    return (
        '<p><strong>監修者情報：</strong></p>\n'
        '<p>' + html.escape(SUPERVISOR_NAME) + '</p>\n'
        '<p>' + html.escape(SUPERVISOR_BIO) + '</p>\n'
        '<p><a href="' + PROFILE_URL + '">詳細なプロフィールはこちら</a></p>'
    )


def build_studio_payload(blog_md: str, images: dict[str, str] | None = None) -> dict:
    """STUDIO 用 payload。
    返り値: {title, body_html, chapter_titles, image_placeholders}
    body_html の構成: 導入文 → 監修者ブロック → 本文
    （目次は STUDIO の table_of_contents ノードを別途 createTableOfContents で挿入する）
    （画像は review_and_images のフローで生成・配置するので body_html には含めない）
    """
    title = extract_title(blog_md)
    rest = strip_h1(blog_md)
    intro_md, main_md = split_intro_and_body(rest)
    chapter_titles = extract_chapter_titles(main_md)
    image_placeholders = extract_image_placeholders(blog_md)

    intro_html = md_to_studio_html(intro_md, images=images)
    sup_html = supervisor_html()
    main_html = md_to_studio_html(main_md, images=images)

    body_html = "\n".join(part for part in (intro_html, sup_html, main_html) if part)
    return {
        "title": title,
        "body_html": body_html,
        "chapter_titles": chapter_titles,
        "image_placeholders": image_placeholders,
    }


def build_full_payload(blog_md: str, image_data: list[dict] | None = None) -> dict:
    """全部入りpayload。image_data: [{id, placement, png_bytes}, ...]

    返り値: {title, body_html, images:[{id, placement, filename, data:"data:image/png;base64,..."}, ...]}

    1クリックでSTUDIOに反映するためのフルペイロード。
    クリップボード経由でブックマークレットに渡し、本文+全画像をSTUDIO側でアップロード+配置する。"""
    import base64
    base = build_studio_payload(blog_md)
    images: list[dict] = []
    for d in image_data or []:
        if "png_bytes" not in d or "id" not in d:
            continue
        b64 = base64.b64encode(d["png_bytes"]).decode("ascii")
        images.append({
            "id": d["id"],
            "placement": d.get("placement", ""),
            "filename": f"{d['id']}.png",
            "data": f"data:image/png;base64,{b64}",
        })
    return {
        "title": base["title"],
        "body_html": base["body_html"],
        "images": images,
    }


def make_bookmarklet_full() -> str:
    """全部入りブックマークレット。
    クリップボードから build_full_payload の JSON を読み、STUDIO 編集画面に：
    - タイトルをセット
    - 本文を完全置換
    - 画像を STUDIO の uploadFunc でアップロード（data URL → File 変換）
    - TOC を最初の H3 の前に挿入
    - 画像を placement 位置に配置
    まで自動実行する。"""
    js = (
        "javascript:(async()=>{try{"
        "const d=JSON.parse(await navigator.clipboard.readText());"
        "const{title,body_html,images=[]}=d;"
        "const tEl=document.querySelector('div.title-div.focusable.title.main-title');"
        "if(!tEl){alert('STUDIO\\u306e\\u7de8\\u96c6\\u753b\\u9762\\u3067\\u5b9f\\u884c\\u3057\\u3066\\u304f\\u3060\\u3055\\u3044');return;}"
        "tEl.focus();tEl.textContent=title;"
        "tEl.dispatchEvent(new InputEvent('input',{bubbles:true}));"
        "tEl.dispatchEvent(new Event('change',{bubbles:true}));tEl.blur();"
        "const ed=document.querySelector('.ProseMirror.in-cms');"
        "if(!ed||!ed.editor){alert('\\u672c\\u6587\\u30a8\\u30c7\\u30a3\\u30bf\\u304c\\u898b\\u3064\\u304b\\u308a\\u307e\\u305b\\u3093');return;}"
        "const e=ed.editor;"
        "e.chain().focus().clearContent(true).setContent(body_html,true).run();"
        "await new Promise(r=>setTimeout(r,300));"
        "const urls={};"
        "const fe=e.extensionManager.extensions.find(x=>x.name==='figure');"
        "const up=fe&&fe.options&&fe.options.uploadFunc;"
        "if(up&&images.length){"
        "for(const img of images){"
        "try{const r=await fetch(img.data);const b=await r.blob();"
        "const f=new File([b],img.filename||(img.id+'.png'),{type:'image/png'});"
        "urls[img.id]=await up(f);"
        "}catch(err){console.warn('upload fail',img.id,err);}}}"
        "let fh=-1;e.state.doc.descendants((n,p)=>{if(fh!==-1)return false;"
        "if(n.type.name==='heading3'){fh=p;return false;}return true;});"
        "if(fh!==-1)e.commands.insertContentAt(fh,{type:'table_of_contents'});"
        "await new Promise(r=>setTimeout(r,200));"
        "const ch=[];e.state.doc.descendants((n,p)=>{if(n.type.name==='heading3')ch.push({pos:p});return true;});"
        "const de=e.state.doc.content.size;"
        "function p2p(t){if(!t||t==='after:summary')return de;"
        "const m=t.match(/^after:h2_(\\d+)$/);"
        "if(m){const n=parseInt(m[1]);return ch[n]?ch[n].pos:de;}return de;}"
        "const ins=images.filter(i=>urls[i.id]).map(i=>({pos:p2p(i.placement),url:urls[i.id],id:i.id}))"
        ".sort((a,b)=>b.pos-a.pos);"
        "for(const i of ins){"
        "e.chain().focus().insertContentAt(i.pos,`<p><img src=\"${i.url}\" alt=\"${i.id}\"></p>`).run();"
        "await new Promise(r=>setTimeout(r,100));}"
        "alert('\\u2705 STUDIO\\u53cd\\u6620\\u5b8c\\u4e86: \\u753b\\u50cf'+ins.length+'/'+images.length+'\\u679a');"
        "}catch(e){alert('\\u30a8\\u30e9\\u30fc: '+e.message);}})();"
    )
    return js


def make_bookmarklet() -> str:
    """STUDIO 編集画面で実行するブックマークレットコード（旧フロー、後方互換用）。
    クリップボードから build_studio_payload の JSON を読み、タイトルと本文を自動入力。
    画像/目次は処理しない。新規入稿は core.studio_runner + chrome-devtools-mcp を推奨。
    """
    js = (
        "javascript:(async()=>{"
        "try{"
        "const t=await navigator.clipboard.readText();"
        "const d=JSON.parse(t);"
        "if(!d.title||!d.body_html){alert('クリップボードのデータ形式が不正です');return;}"
        "const allInputs=[...document.querySelectorAll('input,textarea,div.title-div')];"
        "const titleEl=allInputs.find(e=>/タイトル|title|題名|name|main-title/i.test("
        "(e.placeholder||'')+(e.getAttribute('aria-label')||'')+(e.name||'')+(e.className||'')"
        "));"
        "if(titleEl){"
        "if(titleEl.tagName==='DIV'){titleEl.focus();titleEl.textContent=d.title;"
        "titleEl.dispatchEvent(new Event('input',{bubbles:true}));"
        "titleEl.dispatchEvent(new Event('change',{bubbles:true}));"
        "}else{"
        "const proto=titleEl.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
        "const setter=Object.getOwnPropertyDescriptor(proto,'value').set;"
        "setter.call(titleEl,d.title);"
        "titleEl.dispatchEvent(new Event('input',{bubbles:true}));"
        "titleEl.dispatchEvent(new Event('change',{bubbles:true}));"
        "}}else{console.warn('タイトル入力欄が見つかりません');}"
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
