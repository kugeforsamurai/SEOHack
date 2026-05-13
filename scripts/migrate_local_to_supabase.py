"""4月のローカルデータ（output/sessions/e9188b0046f0/）を Supabase へ移行する1回限りスクリプト。

旧パス（ローカル）:
    output/sessions/{sid}/2026-04-25/runs.json
    output/sessions/{sid}/2026-04-25/runs/r1/state.json
    output/sessions/{sid}/themes_global.json
    ...

新パス（Supabase artifacts.path）:
    2026-04-25/runs.json
    2026-04-25/runs/r1/state.json
    ...
新グローバル（Supabase globals.key）:
    themes_global

使い方:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python3 scripts/migrate_local_to_supabase.py [--dry-run]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import supabase_backend as sb  # noqa: E402


SOURCE_SESSION = ROOT / "output" / "sessions" / "e9188b0046f0"


def is_probably_text(path: Path) -> bool:
    """拡張子で text/binary を判定。"""
    return path.suffix.lower() in {".json", ".md", ".csv", ".txt"}


def migrate(dry_run: bool = False) -> None:
    if not SOURCE_SESSION.exists():
        print(f"❌ ソースが見つかりません: {SOURCE_SESSION}")
        sys.exit(1)

    print(f"📂 ソース: {SOURCE_SESSION}")
    print(f"🔧 dry_run = {dry_run}")
    print()

    text_count = 0
    binary_count = 0
    global_count = 0
    skipped = 0

    for src in sorted(SOURCE_SESSION.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(SOURCE_SESSION)
        rel_str = str(rel)

        # themes_global.json は globals テーブルへ
        if rel_str == "themes_global.json":
            try:
                content = src.read_text(encoding="utf-8")
                print(f"  [globals] themes_global ← {src.name}")
                if not dry_run:
                    sb.put_global("themes_global", content)
                global_count += 1
            except Exception as e:
                print(f"  ⚠️  skip {rel_str}: {e}")
                skipped += 1
            continue

        # 通常のアーティファクト
        dst_path = rel_str  # sid prefix を取り除いたもの
        try:
            if is_probably_text(src):
                content = src.read_text(encoding="utf-8")
                print(f"  [text]    {dst_path}")
                if not dry_run:
                    sb.put_text(dst_path, content)
                text_count += 1
            else:
                data = src.read_bytes()
                print(f"  [bin]     {dst_path}  ({len(data):,} bytes)")
                if not dry_run:
                    sb.put_bytes(dst_path, data)
                binary_count += 1
        except UnicodeDecodeError:
            # 拡張子で誤判定された場合のフォールバック
            data = src.read_bytes()
            print(f"  [bin*]    {dst_path}  ({len(data):,} bytes)")
            if not dry_run:
                sb.put_bytes(dst_path, data)
            binary_count += 1
        except Exception as e:
            print(f"  ⚠️  skip {dst_path}: {e}")
            skipped += 1

    print()
    print("=" * 50)
    print(f"text artifacts:    {text_count}")
    print(f"binary artifacts:  {binary_count}")
    print(f"globals:           {global_count}")
    print(f"skipped:           {skipped}")
    if dry_run:
        print("🔍 dry-run なので Supabase には書き込んでいません。")
    else:
        print("✅ Supabase へ移行完了。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="書き込まず内容だけ表示")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
