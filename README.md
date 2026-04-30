# メディアなんとか — HookHack 6段階コンテンツパイプライン

ターゲット入力 → 事例リサーチ → 軸選択 → 章立て → 画像&レビュー → セクション執筆 → X投稿の全工程を AI 支援で回す Streamlit アプリ。

## 機能

- ⓪ **テーマ探索**（独立）: ChatGPT で記事テーマ候補を発散
- ① 発散: Gemini で世界中の事例を JSON で収集 → スプレッドシート編集
- ② 収束: 事例から「お題に答える切り口の軸」候補を提案
- ③ 企画: 章立てを H1/リード/H2 単位で構造化編集
- ④ 画像&レビュー: 重点セクションコメント + 機能図（チェックリスト・比較表は Pillow、その他は OpenAI gpt-image-1）
- ⑤ 執筆: セクション単位で本文生成、画像を自動挿入して blog.md を結合
- ⑥ 発信: X API v2（OAuth 1.0a）で5本独立投稿、ブログは STUDIO 手動コピー

## ローカル起動

```bash
# Python 3.12 (uv 推奨)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

# .env を作成（オプション、ない場合は UI から入力）
cp .env.example .env  # 編集して各 API キーを設定

streamlit run app.py
```

ブラウザで http://localhost:8501

## Streamlit Community Cloud にデプロイ

1. このリポジトリを GitHub に push
2. https://share.streamlit.io にログイン（GitHub 連携）
3. 「New app」→ リポジトリ・ブランチ・`app.py` を指定
4. デプロイ完了後、URL が発行される（例: `https://your-app.streamlit.app`）
5. アプリを開いて **サイドバーの「API設定」** に各キーを入力（保存はセッションのみ）

### Secrets を Streamlit Cloud 側で設定する場合（任意）

開発者自身が常用する場合のみ。`.streamlit/secrets.toml` をクラウド側に設定するとデフォルト値として使えるが、UI 入力が優先されます。

## API キー

すべてのキーは **ブラウザセッション内のみ** に保持され、サーバーには記録されません。タブを閉じると消えます。

| キー | 取得元 | 用途 |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/app/apikey | ①〜⑤の文章生成、画像案生成 |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | ⓪テーマ提案 / ④画像生成 (gpt-image-1) |
| `X_API_KEY` `X_API_SECRET` `X_ACCESS_TOKEN` `X_ACCESS_TOKEN_SECRET` | https://developer.x.com/ | ⑥X 投稿（Read+Write 権限が必要） |

## データの保存

- **マルチユーザー対応**: ブラウザセッションごとに `output/sessions/{uuid}/` 配下で隔離
- **永続化**: Streamlit Cloud は再起動でディスクが消える可能性あり。サイドバーの **「📦 データのバックアップ / 復元」** で ZIP ダウンロード推奨
- **ローカル**: 同じ Streamlit セッション中はディスクに保存、ブラウザ閉じると orphan ファイル化（ローカルディレクトリには残る）

## カスタマイズ

`config/persona.json` で AI の人格・読者像・NGワード等を編集可能。サイドバーの「Persona設定」expander から JSON 直接編集も可。

## アーキテクチャ

```
app.py                    # Streamlit エントリ
core/
  api_keys.py             # APIキーを session_state 優先で取得
  storage.py              # session 隔離されたファイルI/O
  gemini_client.py        # Gemini REST API（httpx 直接）
  openai_client.py        # OpenAI Chat / Image API
  x_client.py             # X API v2 (tweepy)
  prompts.py              # HookHack戦略埋め込みプロンプト + persona 注入
  persona.py              # 人格設定の load/save + 絵文字サニタイズ
  outline_parser.py       # outline.md ⇔ 構造化辞書 変換
  diagram_renderer.py     # Pillow で checklist/comparison_table 描画
config/
  persona.json            # 人格設定
.streamlit/
  config.toml             # Streamlit テーマ・サーバー設定
output/sessions/{uuid}/   # ユーザーセッションごとのデータ
```
