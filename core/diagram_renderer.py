"""Pillow ベースのチェックリスト・比較表 PNG レンダラ。
gpt-image-1 が苦手な構造化テキスト（多項目チェックリスト・列×行表）を、
Python で正確に描画する。日本語フォントは macOS の Hiragino Sans GB を使用。"""
from __future__ import annotations
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

JP_FONT_CANDIDATES = [
    # Linux (Streamlit Cloud) — fonts-noto-cjk パッケージ
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    # macOS（ローカル開発）
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]

SIZES = {
    "1024x1024": (1024, 1024),
    "1024x1536": (1024, 1536),
    "1536x1024": (1536, 1024),
}

# Color palette — editorial / luxe stylish minimal
# 主役: 漆黒に近いインク、アクセントは深いインディゴを最小限に
COLOR_BG = "#fdfcfa"            # わずかに温かみのあるオフホワイト（紙のニュアンス）
COLOR_TEXT = "#181818"          # 純黒に近いインクブラック
COLOR_SUBTEXT = "#7a7a7a"       # ミッドグレー
COLOR_HAIRLINE = "#e8e6e0"      # 細い罫線（紙色になじむウォームグレー）
COLOR_RULE = "#181818"          # 強い区切り線
COLOR_ACCENT = "#2a3f5f"        # アクセント主：深いインディゴ（落ち着いた色味）
COLOR_ACCENT_SOFT = "#f3f1ec"   # アクセント淡：ウォームベージュ（行交互の極薄帯）
COLOR_HEADER_BG = "#181818"     # 比較表ヘッダの濃色背景


def _font_path() -> str:
    custom = os.environ.get("JP_FONT_PATH")
    if custom and Path(custom).exists():
        return custom
    for p in JP_FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError("日本語フォントが見つかりません。.envにJP_FONT_PATHを設定してください")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(), size)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """文字単位で折り返し（日本語向け、英語の単語分割は妥協）。"""
    if not text:
        return [""]
    lines: list[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        test = cur + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def _resolve_size(size: str) -> tuple[int, int]:
    return SIZES.get(size, (1024, 1536))


# ============================================================
# Checklist
# ============================================================
def render_checklist(
    title: str,
    items: list[str],
    output_path: Path,
    size: str = "1024x1536",
) -> Path:
    """ラグジュアリーミニマル / 編集デザイン。
    - eyebrow（小キャプション）"チェックリスト"
    - 大きめのタイトル（左寄せ）
    - 細い1pxのインクブラック下線
    - 番号は超薄いミッドグレーで脇に小さく
    - チェックボックスはなし、左に細いアクセントバー
    - 多めの余白、ヘアライン仕切り"""
    w, h = _resolve_size(size)
    img = Image.new("RGB", (w, h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    margin = 112  # 余白広め（紙の余白感）
    title_size = 64
    eyebrow_size = 20
    num_size = 22
    item_size = 30
    line_spacing = 12
    item_gap = 44
    bar_w = 3        # 左の細い縦アクセントバー
    bar_indent = 32  # バーの右の余白
    text_indent = bar_w + bar_indent

    title_font = _font(title_size)
    eyebrow_font = _font(eyebrow_size)
    num_font = _font(num_size)
    item_font = _font(item_size)

    # 自動フォント縮小（収まるまで）
    title_block_h = eyebrow_size + 16 + title_size + 32
    items_h_budget = (h - margin * 2) - title_block_h
    text_max_w = w - margin * 2 - text_indent

    def measure_items_height(item_font_):
        total = 0
        for item in items:
            wrapped = _wrap_text(draw, item, item_font_, text_max_w)
            block_h = len(wrapped) * item_size + max(0, len(wrapped) - 1) * line_spacing
            total += block_h + item_gap
        return total

    while item_size >= 18 and measure_items_height(item_font) > items_h_budget:
        item_size -= 2
        line_spacing = max(6, line_spacing - 1)
        item_gap = max(28, item_gap - 2)
        item_font = _font(item_size)

    # Eyebrow（日本語小キャプション、アクセント色）
    eyebrow = "C H E C K L I S T"  # ロゴ風レター（疑似トラッキング）
    # 日本語要望なので "チェックリスト" にする
    eyebrow = "チェックリスト"
    draw.text((margin, margin), eyebrow, fill=COLOR_ACCENT, font=eyebrow_font)

    # Title
    title_y = margin + eyebrow_size + 16
    draw.text((margin, title_y), title, fill=COLOR_TEXT, font=title_font)

    # 細い1pxのインクブラック下線
    rule_y = title_y + title_size + 22
    draw.line((margin, rule_y, w - margin, rule_y), fill=COLOR_RULE, width=1)

    # Items
    cur_y = rule_y + 44
    for idx, item in enumerate(items):
        wrapped = _wrap_text(draw, item, item_font, text_max_w)
        block_h = len(wrapped) * item_size + max(0, len(wrapped) - 1) * line_spacing

        # 左の細い縦アクセントバー（item_block の高さに合わせる）
        draw.rectangle(
            (margin, cur_y + 4, margin + bar_w, cur_y + block_h + 4),
            fill=COLOR_ACCENT,
        )

        # 番号（極小、ミッドグレー、本文の右上に小さく）
        num_text = f"{idx + 1:02d}"
        num_x = w - margin - 60
        num_y = cur_y - 2
        draw.text((num_x, num_y), num_text, fill=COLOR_SUBTEXT, font=num_font)

        # 本文
        for i, line in enumerate(wrapped):
            text_y = cur_y + i * (item_size + line_spacing)
            draw.text((margin + text_indent, text_y), line, fill=COLOR_TEXT, font=item_font)

        cur_y += block_h + item_gap // 2

        # 項目間のヘアライン
        if idx < len(items) - 1:
            sep_y = cur_y
            draw.line((margin + text_indent, sep_y, w - margin, sep_y), fill=COLOR_HAIRLINE, width=1)
            cur_y += item_gap // 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


# ============================================================
# Comparison Table
# ============================================================
def render_comparison_table(
    title: str,
    cols: list[str],
    rows: list[dict],
    output_path: Path,
    size: str = "1536x1024",
) -> Path:
    """ミニマル / 編集デザインの比較表。
    - タイトル左寄せ + 細い黒のhairline 下線
    - ヘッダ行: 白地、太字（同フォントだがサイズで強調）、下に黒2px
    - データ行: 白地のみ、行間に1pxヘアライン
    - 外枠なし"""
    w, h = _resolve_size(size)
    img = Image.new("RGB", (w, h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    margin = 112
    title_size = 56
    eyebrow_size = 20
    header_font_size = 26
    cell_font_size = 24
    cell_padding = 32

    n_cols = len(cols)
    if n_cols == 0:
        raise ValueError("cols が空です")

    title_font = _font(title_size)
    eyebrow_font = _font(eyebrow_size)

    # Eyebrow（日本語小キャプション、アクセント色）
    eyebrow = "比較表"
    draw.text((margin, margin), eyebrow, fill=COLOR_ACCENT, font=eyebrow_font)

    # Title
    title_y = margin + eyebrow_size + 16
    draw.text((margin, title_y), title, fill=COLOR_TEXT, font=title_font)

    # 細い1pxのインク下線
    rule_y = title_y + title_size + 22
    draw.line((margin, rule_y, w - margin, rule_y), fill=COLOR_RULE, width=1)

    table_top = rule_y + 40

    # 列幅計算（label列 30%, 他は均等）
    table_left = margin
    table_right = w - margin
    table_w = table_right - table_left
    if n_cols == 1:
        col_widths = [table_w]
    else:
        label_w = int(table_w * 0.30)
        rest = (table_w - label_w) // (n_cols - 1)
        col_widths = [label_w] + [rest] * (n_cols - 1)
        col_widths[-1] += table_w - sum(col_widths)

    # 自動縮小
    header_h = 76
    row_h = 64

    cell_font = _font(cell_font_size)
    header_font = _font(header_font_size)

    available_h = h - table_top - margin
    needed_h = header_h + row_h * len(rows)
    while needed_h > available_h and row_h > 40:
        row_h -= 4
        if cell_font_size > 20:
            cell_font_size -= 1
            cell_font = _font(cell_font_size)
        if header_font_size > 22:
            header_font_size -= 1
            header_font = _font(header_font_size)
        needed_h = header_h + row_h * len(rows)

    # Header row（濃ネイビー背景 + 白文字）
    draw.rectangle(
        (table_left, table_top, table_right, table_top + header_h),
        fill=COLOR_HEADER_BG,
    )
    cur_x = table_left
    for i, col in enumerate(cols):
        avail = col_widths[i] - cell_padding * 2
        wrapped = _wrap_text(draw, col, header_font, avail)
        n_lines = len(wrapped)
        block_h = n_lines * header_font_size + max(0, n_lines - 1) * 4
        text_y = table_top + (header_h - block_h) // 2
        for j, line in enumerate(wrapped):
            draw.text(
                (cur_x + cell_padding, text_y + j * (header_font_size + 4)),
                line, fill="#ffffff", font=header_font,
            )
        cur_x += col_widths[i]

    header_bottom_y = table_top + header_h

    # Data rows
    for r_idx, row in enumerate(rows):
        ry = header_bottom_y + r_idx * row_h

        # 行の背景（交互に薄ブルー）
        if r_idx % 2 == 1:
            draw.rectangle(
                (table_left, ry, table_right, ry + row_h),
                fill=COLOR_ACCENT_SOFT,
            )

        cells: list[str] = [str(row.get("label", ""))]
        cells.extend(str(v) for v in row.get("values", []))
        cells = (cells + [""] * n_cols)[:n_cols]

        cur_x = table_left
        for i, cell in enumerate(cells):
            avail = col_widths[i] - cell_padding * 2
            wrapped = _wrap_text(draw, cell, cell_font, avail)
            if len(wrapped) > 2:
                wrapped = wrapped[:2]
                wrapped[-1] = wrapped[-1][:-2] + "..."
            n_lines = len(wrapped)
            block_h = n_lines * cell_font_size + max(0, n_lines - 1) * 4
            text_y = ry + (row_h - block_h) // 2
            # ラベル列はアクセント色、他列はテキスト色（編集トーン）
            color = COLOR_ACCENT if i == 0 else COLOR_TEXT
            for j, line in enumerate(wrapped):
                draw.text(
                    (cur_x + cell_padding, text_y + j * (cell_font_size + 4)),
                    line, fill=color, font=cell_font,
                )
            cur_x += col_widths[i]

        # Row separator（最後以外）
        if r_idx < len(rows) - 1:
            draw.line(
                (table_left, ry + row_h, table_right, ry + row_h),
                fill=COLOR_HAIRLINE, width=1,
            )

    # 表の最下部にインク色の細い締め
    final_y = header_bottom_y + row_h * len(rows)
    draw.line((table_left, final_y, table_right, final_y), fill=COLOR_RULE, width=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
