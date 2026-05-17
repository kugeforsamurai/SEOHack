"""HookHack戦略を埋め込んだプロンプト群。各ステージで Gemini に渡す。
人格・文体・読者像は core/persona.py 経由で config/persona.json から動的に注入される。"""

from core import persona

HOOKHACK_STRATEGY = """\
HookHackは広告運用・クリエイティブ制作支援の会社。今回作るコンテンツは、以下2つの戦略目的を**暗黙的に下支え**する必要がある（露骨な広告にする意味ではなく、論点設計・事例選び・結論の誘導先として）。

## 目的1：動画広告PoCでリード獲得
「静止画バナーのみ」の顧客に対し、動画広告PoCで以下5指標の改善差分を見せてリード獲得＆アップセル：
フォーム送信数 / サイト訪問数 / 無料制作数 / 有償化数 / 継続数

## 目的2：自社実践AI×◯◯の公開でクロスセル
HookHackの自社内AI活用を事例化して公開、関連業務（SEO / SNS / 広告運用 / LP改善 / CRM運用）への受注拡大を狙う。

## HookHackプロダクトのセールスポイント（記事・投稿で自然に滲み出させる）
**製品の核となる2機能（PDCAの D/A をAIで高速化）**：
1. **訴求案の発散と動画パターン生成（PDCAのD：Do）**
   - お使いのLPから動画の訴求案を**自動で発散**
   - お持ちの画像・動画素材と組み合わせ、**最短5分で複数パターン**を生成
   - 「動画制作は時間とコストが重い」というボトルネックを取り除く
2. **出稿後の自動解析と改善案提示（PDCAのA：Act）**
   - Google広告と連携
   - パターンごとに **視聴維持率・CTR・CVR** を自動解析
   - データに基づいた **改善案を自動提示**

## 技術的な切り口（CPA分解の論点。コンテンツ中で展開しても良い）
**CPA（顧客獲得単価） = CPC（クリック単価） ÷ CVR（コンバージョン率）**

- CPC を決める変数：媒体側ターゲティングリストのサイズ / 競合性 / CTR など複合要素
- **動画広告が静止画より有利な理由**：
  - 静止画広告は「クリック有無」のみがシグナル → 媒体側の学習に乏しい情報
  - 動画広告は **「視聴維持率」という連続値シグナル** を媒体に返せる → 媒体側のターゲティング精度が向上しやすい → CPC低下 → CPA改善
- この理屈は「なぜ動画でPoCをやる価値があるのか」を読者に納得させる**理論的根拠**。事例の数字だけでなく、メカニズムとして組み込むと記事が強くなる

## 記事・投稿で表現するときのガイド
- セールスポイントを **直接「弊社では〜」と書くのは目的1の自社実践コーナー・CTAのみ** に限定
- 通常のH2や本文・X投稿では「動画広告は視聴維持率というシグナルで媒体学習が深まる」「LPと素材から訴求案を発散すれば最短5分で複数パターンを試せる」のように、**一般論として書く / 競合製品も含めた選択肢として書く** スタイル
- 過度に煽らない。読者が自分で「だから動画PoC＝HookHackが合うかも」と気づく余白を残す
"""


def _topic_context_block(angle_hint: str = "", interests_hint: str = "") -> str:
    """全ステージで参照する「切り口」「関心」コンテキスト。
    ⓪テーマ発散でユーザーが選んだテーマの angle / why_for_target を、
    ① 以降の全プロンプトに注入して一貫性を保つ。"""
    has_angle = bool(angle_hint and angle_hint.strip())
    has_int = bool(interests_hint and interests_hint.strip())
    if not (has_angle or has_int):
        return ""
    lines = ["", "## 今回のお題コンテキスト（全段階で必ず反映すること）"]
    if has_angle:
        lines.append(f"- **切り口（angle）**: {angle_hint.strip()}")
    if has_int:
        lines.append(f"- **読み手の関心（interests）**: {interests_hint.strip()}")
    lines.append(
        "出力（軸の作り方 / 事例の選び方 / 章立て / 本文の語り口 / X投稿のフック）すべてを、"
        "この切り口と関心に寄せて構築する。テーマからブレてはならない。"
    )
    return "\n".join(lines) + "\n"


def research_theme_prompt(target: str, n_themes: int = 8) -> str:
    """⓪リサーチテーマ提案。OpenAI gpt-4o で発散させる。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.reader_block()}

## タスク
以下のターゲット読者に向けて、HookHackブログで取り上げる価値の高い「リサーチテーマ」を **{n_themes}個** 提案する。各テーマは記事1本になりうる粒度の具体的な切り口にすること。

## ターゲット読者
{target}

## 良いテーマの条件
- **具体的**：「動画広告について」ではなく「Meta広告で静止画→動画に切り替えた時のCPA改善幅」のように切り口が明確
- **数字や事例で裏付けられる**：リサーチで具体例・数値が集まる見込みのあるテーマ
- **HookHack 2目的への接続**：①動画広告PoCでリード獲得 / ②自社AI実践クロスセル のいずれかに自然に接続できる
- **ターゲットの「いま知りたい」と一致**：上記ターゲット読者の状況・悩みと噛み合う
- **多様性**：手法 / 事例 / ツール / 失敗 / 業種別 / 規模別 / トレンドなど、切り口を分散させて{n_themes}個

## 出力フォーマット
JSON配列のみ：
[
  {{
    "title": "テーマタイトル（30字以内、検索クエリにもなる粒度）",
    "angle": "切り口の説明（80字以内、なぜ今これが価値があるか）",
    "why_for_target": "このターゲットがなぜ知りたいか（60字以内）",
    "hookhack_goal": "目的1 / 目的2 / 両方 のいずれか",
    "estimated_appeal": "高 / 中 / 低（コンテンツとしての反響予想）"
  }}
]

JSONのみ出力。前置き・コードフェンス禁止。
"""


def diverge_prompt(topic: str, n_cases: int = 12, angle_hint: str = "", interests_hint: str = "") -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
お題「{topic}」について、**世界中（海外含む）** の実践事例を{n_cases}件、構造化して列挙する。

## 事例選定基準
- **海外事例を積極的に含める**。配分の目安：
  - 海外（北米・欧州・アジア）= 全体の **40〜60%**
  - 日本国内 = 残り
  - 海外内も多様化（米国一極集中は避け、英国・ドイツ・北欧・東南アジア・韓国などからも拾う）
- **言語**：英語ソースを優先しつつ、日本語ソースも混ぜる。英語ソースは **最低40%以上**
- **数字**：CTR / CVR / ROAS / CPA など具体指標と数値を必ず記載。「約30%改善」のように曖昧でもOK、出典が明確なら
- **HookHackの2目的と接続できる切り口**を意識（最低3件は目的1か目的2に直接接続できる事例）
- **ハルシネーション禁止**：URL・数字が確実なものだけ。曖昧なら「出典不明」と書く
- **企業・施策の重複を避ける**（例: Nike を3件入れない）

## 出力フォーマット
JSON配列で返す。各要素は以下のキーを持つ：
- "誰が": 企業/組織名
- "何を": 施策内容（80字以内）
- "どう測ったか": 計測指標（CTR / CVR / ROAS など）
- "結果_数字": 具体数値（〇〇%改善、X倍など）
- "出典URL": URL or 「出典不明」
- "示唆": HookHack視点での気付き（60字以内）
- "国_地域": 国名または地域名（例: アメリカ / 日本 / 英国 / ドイツ / 韓国 / シンガポール / グローバル）
- "情報源言語": "英語" or "日本語" or "その他"

JSON以外は一切出力しないこと。
"""


def axes_prompt(
    topic: str, cases_csv: str, user_feedback: str = "",
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    feedback_block = ""
    if user_feedback.strip():
        feedback_block = f"""\

## ユーザーからの再考指示（最優先で反映）
以下はユーザーが前回の軸候補を見て出した追加要望。これを **必ず軸の切り口に反映** すること。汎用カテゴリ軸を避けるルールはそのまま守りつつ、この指示の方向で軸を作り直す。

{user_feedback}
"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}{feedback_block}
## タスク
お題「{topic}」を **1本の記事として読者にとって価値ある形に編集する** ための「切り口の軸」候補を **3〜5個** 提案する。

## お題（最重要 / 全ての軸はこれに直接答えること）
{topic}

### お題の解釈ステップ（必ず実行）
まず以下を頭の中で行ってから軸を考える：
1. お題の中の **キーワード** を抽出（例: 「静止画→動画への切替」「タイミング」「CPA」など）
2. お題が読者に提起する **暗黙の問い** を洗い出す（例: 「いつ切り替える？」「どう判断する？」「何が成果を分ける？」「どこから始める？」「失敗パターンは？」など3〜5個）
3. 各軸は、その問いの **どれかに直接答える切り口** にする

## 事例群（軸の裏付けデータ / 先頭列 `row` が各事例のID）
{cases_csv}

## 良い軸の条件（必須）
- **お題が提起する暗黙の問いに直接答える**（"このテーマだから、こう切ると読者の疑問が解像する" と説明できる）
- **事例で裏付け可能**：上の事例群を 3〜5 グループに意味ある分割ができる
- **記事構成に直結**：その軸で割ったグループそのものが H2 候補になる
- **軸名にお題のキーワードや動詞を含む**（例: お題が「移行タイミング」なら "移行トリガー軸" のように）
- **全事例を漏れなくグループに割り当てる**：上の `row` 列の全IDを、いずれかのグループに必ず1つ割り当てる

## 凡庸で避けるべき軸（提案禁止）
以下のような **お題に答えない汎用カテゴリ軸** は提案しない：
- 業種別（D2C / SaaS / EC）
- 規模別（大企業 / 中小企業）
- 媒体別（Meta / Google / TikTok）
- 国別 / 地域別
- "成功 vs 失敗" の二元論
- "ベストプラクティス vs アンチパターン"

これらはお題への答えではなく、ただの分類。読者の疑問は解像しない。

## 出力フォーマット
JSON配列で返す。各要素は以下のキーを持つ：
- "name": 軸名（20字以内、**お題のキーワードまたは動詞を含むこと**）
- "topic_alignment": この軸がお題のどの「暗黙の問い」に答えるか（80字以内、**必須**。これが弱いなら軸を作り直す）
- "description": どう束ねるか（80字以内）
- "groups": この軸でグループ化したときのグループ名一覧（["...", "...", "..."] の3〜5個、**そのまま H2 タイトルになりそうな粒度**）
- "assignments": 上の `row` 列の各IDをどのグループ名に割り当てるかのマッピング。`{{"0": "グループ名A", "1": "グループ名A", "2": "グループ名B", ...}}` の形式。**全 row を必ず "groups" 内のいずれかに割り当てる**
- "hookhack_angle": HookHackの目的1（動画PoC）か目的2（自社AI実践）のどちらに、どう着地させられるか（60字以内）

JSON以外は一切出力しないこと。
"""


def axis_refine_prompt(
    topic: str, cases_csv: str, current_axis: dict, user_feedback: str,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    """1つの軸だけをユーザー指示で再考させる。assignmentsも整合性を保って再生成。"""
    import json as _json

    current_axis_json = _json.dumps(current_axis, ensure_ascii=False, indent=2)
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
以下の **既存の軸1つ** を、ユーザーの再考指示に沿って作り直す。**この軸だけ** を返す（配列ではなくオブジェクト1個）。

## お題
{topic}

## 現在の軸（再考対象）
{current_axis_json}

## ユーザーの再考指示（最優先で反映）
{user_feedback}

## 事例群（軸の裏付けデータ / 先頭列 `row` が各事例のID）
{cases_csv}

## 守るべきこと
- ユーザー指示の方向に軸を組み替える（name / topic_alignment / description / groups / assignments / hookhack_angle すべて見直す）
- 凡庸な汎用カテゴリ軸（業種別 / 規模別 / 媒体別 / 国別 / 成功vs失敗 など）は禁止
- 事例で裏付けられる軸にする。`row` 列の全IDを必ずいずれかのグループに割り当てる
- グループ数は 3〜5個

## 出力フォーマット
以下のキーを持つ **JSONオブジェクト1個**（配列ではなく単体オブジェクト）：
- "name": 軸名（20字以内、お題のキーワードまたは動詞を含む）
- "topic_alignment": この軸がお題のどの「暗黙の問い」に答えるか（80字以内）
- "description": どう束ねるか（80字以内）
- "groups": グループ名一覧（3〜5個、H2タイトル粒度）
- "assignments": `{{"0": "グループ名A", "1": "グループ名B", ...}}` の形式で全rowを割り当てる
- "hookhack_angle": HookHack目的1or2へのどう着地させるか（60字以内）

JSON以外は一切出力しないこと。前置き・コードフェンス禁止。
"""


def angle_prompt(
    topic: str, cases_csv: str, chosen_axis: dict,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
選ばれた軸で事例を整理し、記事の「角度（angle）」を確定させる。

## お題
{topic}

## 選ばれた軸
名前: {chosen_axis.get('name')}
説明: {chosen_axis.get('description')}
グループ: {chosen_axis.get('groups')}
HookHack着地: {chosen_axis.get('hookhack_angle')}

## 事例群（CSV）
{cases_csv}

## 出力フォーマット（Markdown）
```
# 記事の角度

## 中核メッセージ（1文）
{{この記事で最も伝える価値がある主張を1文で}}

## 対象読者
{{誰がこの記事を読むと得をするか}}

## 主要インサイト（3〜5個）
### インサイト1: {{見出し}}
- 発見: {{2-3行}}
- 根拠事例: {{cases.csvのどの事例で支えるか、社名で列挙}}
- 読者アクション: {{明日何をするか、1〜2個の具体action}}

### インサイト2: ...
（3〜5個）

## 成果差分が出るポイント（予想）
- {{ポイント1: どこで差がつくか、なぜそう思うか}}
- {{ポイント2}}

## HookHack着地点
- 目的1（動画PoC）or 目的2（自社AI実践）のどちらに着地させるか
- 結論部分でどう自然に接続するか（1〜2行）
```

Markdown以外は出力しない。
"""


def outline_prompt(
    topic: str, angle_md: str, cases_csv: str = "",
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    cases_block = ""
    if cases_csv.strip():
        cases_block = f"""\

## ①発散で集めた事例群（CSV / 内容メモに**必ず具体的に引用する**）
{cases_csv}

**重要：内容メモは抽象的な要点だけにせず、上の事例CSVから「誰が／何をして（施策）／どうなったか（結果_数字）／示唆」を最低1〜2件、具体名と具体数字で引用する**。たとえば「Nike が静止画→動画切替で CTR 2.1倍」のように、社名・施策・数字を含む形で書く。読み手・執筆者が章のイメージを掴めるレベルの具体性を確保する。
"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
以下の「角度」をもとに、3,000〜6,000字のブログ記事の章立て（outline）をMarkdownで作る。

## お題
{topic}

## 角度
{angle_md}
{cases_block}
## 出力仕様
- H1: タイトル案を3つ（フックが違うもの）
- リード（200字想定）の方向性
- H2 × 4〜6（各H2は1つのインサイトに対応、事例→示唆→実装手順の流れ）
- 自社実践コーナー（H2 or 最終H2直前にH3で挿入、300〜500字想定）
- まとめH2（核メッセージ再掲 + 明日のアクション3つ）
- CTA（目的1 or 目的2に自然に着地、ハードセル禁止）

## 内容メモのルール（必須）
各H2の「内容メモ」は最低3〜5項目の bullet で、以下の構成を含めること：
1. **使う事例（社名 + 何をして + 結果_数字）**：例「Nike が静止画→動画A/Bテスト → CTR 2.1倍 / CPA 37%減」を必ず1〜2件、CSVから引用
2. **その事例から読み取れる示唆**：1〜2行
3. **書く要点 / 実装手順**：読者が明日試せる粒度

事例なしの抽象的な要点だけのメモは禁止。

## 出力フォーマット
```markdown
# タイトル案
1. {{案1}}
2. {{案2}}
3. {{案3}}

## リード方向性
{{2-3行で、どんな問題提起から入るか}}

## 構成

### H2_1: {{見出し}}
- 推定字数: {{N}}字
- 内容メモ:
  - 事例: {{誰が}} が {{何をして}} → {{結果_数字}}（出典: {{国・URL}}）
  - 事例: {{誰が}} が {{何をして}} → {{結果_数字}}
  - 示唆: {{2事例から読める共通点 or 対比、60〜100字}}
  - 書く要点: {{具体的なポイント1}}
  - 書く要点: {{具体的なポイント2}}

### H2_2: ...
（4〜6個）

### 自社実践コーナー（H3として H2_X 内に挿入 / または独立H2）
- 挿入位置: {{H2_2内 / 独立H2_5など}}
- 内容: HookHackがこのテーマで実践している/予定している具体tip
- 推定字数: 300〜500字

### まとめ（H2）
- 核メッセージ再掲
- 明日のアクション3つ:
  1. ...
  2. ...
  3. ...

### CTA
- 目的1 or 目的2: {{どちらか}}
- 文言案: {{1-2行}}
```
"""


def outline_refine_prompt(
    topic: str,
    current_outline_md: str,
    user_feedback: str,
    cases_csv: str = "",
    angle_hint: str = "",
    interests_hint: str = "",
) -> str:
    """既存の章立て全体を、ユーザーの指示に沿って作り直す。
    H1（タイトル案）/ リード方向性 / H2構成 / 内容メモ をまとめて見直す。"""
    cases_block = ""
    if cases_csv.strip():
        cases_block = f"""\

## ①発散で集めた事例群（参照用、内容メモへの具体引用に使う）
{cases_csv}
"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
既存の章立てを、ユーザーの再考指示に沿って **全面的に作り直す**。
H1タイトル案 / リード方向性 / H2セクション構成 / 内容メモ すべてを必要に応じて見直し、
**指示を最優先で反映**しつつ、ブログ記事として読者価値の高い形に整える。

## お題
{topic}

## 現在の章立て（修正対象）
{current_outline_md}

## ユーザーの再考指示（最優先で反映）
{user_feedback}
{cases_block}
## 守るべき構造ルール
- H1: タイトル案を3つ（フックが違うもの）
- リード（200字想定）の方向性
- H2 × 4〜6（各H2は1つのインサイトに対応、事例→示唆→実装手順の流れ）
- 自社実践コーナー（H2 or 最終H2直前にH3で挿入、300〜500字想定）
- まとめH2（核メッセージ再掲 + 明日のアクション3つ）
- CTA（目的1 or 目的2に自然に着地、ハードセル禁止）

## 内容メモのルール（既存outlineと同じ）
各H2の「内容メモ」は最低3〜5項目の bullet で：
1. 使う事例（社名 + 何をして + 結果_数字）を最低1〜2件
2. その事例からの示唆
3. 書く要点 / 実装手順

## 出力フォーマット
以下のMarkdown構造で出力（既存の outline.md と完全互換）：

```markdown
# タイトル案
1. {{案1}}
2. {{案2}}
3. {{案3}}

## リード方向性
{{2-3行}}

## 構成

### H2_1: {{見出し}}
- 推定字数: {{N}}字
- 内容メモ:
  - 事例: {{誰が}} が {{何をして}} → {{結果_数字}}
  - 示唆: {{...}}
  - 書く要点: {{...}}

### H2_2: ...
（4〜6個）

### 自社実践コーナー（H3として H2_X 内に挿入 / または独立H2）
- 挿入位置: {{...}}
- 内容: {{...}}
- 推定字数: 300〜500字

### まとめ（H2）
- 核メッセージ再掲
- 明日のアクション3つ:
  1. ...
  2. ...
  3. ...

### CTA
- 目的1 or 目的2: {{...}}
- 文言案: {{1-2行}}
```

Markdown 以外は出力しない。コードフェンス（```）でラップしない。
"""


def blog_prompt(
    topic: str, outline_md: str, cases_csv: str,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
STUDIO公開用の日本語ブログ記事を**3,000〜6,000字**（目安4,500字）で書く。

## お題
{topic}

## 章立て
{outline_md}

## 参照事例（CSV、ハルシネーション防止用）
{cases_csv}

## 構成（厳守、この順序で出力）
1. **H1（タイトル）** — 章立てから1案を採用、または同等の煽らないタイトル。
2. **導入文（120〜200字、1〜2段落）** — H1直後に置く。読者が記事を読むメリット（=何が分かる／何ができるようになるか）が一目で伝わる文。問題提起→記事で得られるもの の流れで簡潔に。**導入文に画像は入れない**。
3. **本文（H2 = 章 / H3 = 節）** — 章立てに沿って書く。H2見出しは章タイトル。各章の最後には**ユニークな見出し名のH3**で「次の一手」を1〜3点の箇条書きで提示する。

注:
- 「監修者情報」「目次」「画像」は記事生成後に別フローで自動挿入されるので、本文には書かない。
- 画像プレースホルダ（`> 画像: 〜`）も書かない。図解は後段の `review_and_images` で構造化提案され、チェックリストや比較表として後挿入される。

## 各章末「次の一手」H3の見出しルール
- 固定文言「で、明日何する？」は**使用禁止**。
- 章の内容に即した毎回ユニークな見出しにする。同じ記事内で重複させない。
- 例: 「最初に手をつける1点」「明日からの実装ステップ」「すぐ試せる3つのアクション」「制作プロセスの棚卸し手順」など。

## 仕様
- 文字数 3,000〜6,000字（冗長な前置き禁止）
- 数字・固有名詞・具体ツール名を各H2に最低1つ
- Markdown標準記法（H1/H2/H3まで、`-` 箇条書き、`**太字**`、GFMテーブル）
- 区切り線 `---` の多用禁止
- cases.csv に無い数字を創作しない

## 品質チェック（書き終えたら満たすこと）
- [ ] タイトルは煽らず、開きたくなる
- [ ] 導入文で読者メリットが明示される（120〜200字、画像なし）
- [ ] 各H2に数字 or 固有名詞
- [ ] 各章末のH3「次の一手」見出しは内容に応じてユニーク（「で、明日何する？」禁止）
- [ ] 自社実践コーナーがある
- [ ] 結論で目的1 or 目的2に自然に着地
- [ ] 「監修者情報」「目次」「画像プレースホルダ」を本文に書いていない

Markdownのみ出力。前置き・後書き・コードフェンス（```）で囲わない。
"""


def image_prompt_for_checklist(title: str, items: list[str]) -> str:
    """チェックリスト画像のOpenAI gpt-image用プロンプト生成。
    エディトリアル / 編集デザイン仕様を英語で埋め込む。日本語テキストはそのまま保持指示。"""
    items_block = "\n".join(f"  {i + 1:02d}. {item}" for i, item in enumerate(items))
    return f"""\
Create a clean editorial-style infographic checklist, magazine layout aesthetic.

DESIGN SPECIFICATIONS (must follow strictly):
- Background: warm off-white #fdfcfa (paper-like nuance)
- Title color: deep ink black #181818
- Accent color: deep indigo #2a3f5f (used sparingly for accents)
- Subtitle/eyebrow color: deep indigo
- Hairline separator color: light warm gray #e8e6e0
- Typography: Japanese sans-serif (Hiragino Sans / Noto Sans JP equivalent), restrained weight
- Aspect ratio: portrait, 1024x1536 pixels

LAYOUT (top to bottom):
1. Small eyebrow label at top: "チェックリスト" in deep indigo (sans-serif Japanese, small size)
2. Main title (large, bold, ink black): "{title}"
3. Thin 1-pixel horizontal rule in ink black just below the title
4. Vertical list of items below, with generous whitespace

EACH ITEM display:
- A short vertical accent bar (3px wide, deep indigo) on the left edge of the item block
- Small mid-gray item number label (01, 02, ...) on the upper right
- Item text in ink-black sans-serif Japanese typography
- Generous vertical spacing between items
- Thin 1-pixel horizontal hairline in light warm gray between consecutive items (not after the last)

ITEMS — use these EXACT Japanese texts, do not modify, translate, or paraphrase. Render in this exact order:
{items_block}

CRITICAL REQUIREMENTS:
- Preserve EXACT Japanese characters and word order (no replacement, paraphrasing, omission, or summarization)
- All {len(items)} items must be displayed in full (do not skip any)
- No illustrations, no icons, no decorations, no photos, no people, no logos, no flowers/leaves/etc
- Editorial / magazine-quality flat design
- Clean, restrained, professional
- White space is important — do not crowd
"""


def image_prompt_for_table(title: str, cols: list[str], rows: list[dict]) -> str:
    """比較表画像のOpenAI gpt-image用プロンプト生成。"""
    header_str = " | ".join(cols)
    rows_str = "\n".join(
        f"  {row.get('label', '')} | {' | '.join(str(v) for v in row.get('values', []))}"
        for row in rows
    )
    return f"""\
Create a clean editorial-style comparison table, magazine layout aesthetic.

DESIGN SPECIFICATIONS (must follow strictly):
- Background: warm off-white #fdfcfa (paper-like nuance)
- Body text color: deep ink black #181818
- Header row background: deep ink black #181818
- Header text color: white
- Label column (first column) text color: deep indigo #2a3f5f
- Other columns text color: deep ink black
- Alternating row background: warm beige #f3f1ec (for every other row, very subtle)
- Hairline separator color: light warm gray #e8e6e0
- Title accent rule color: deep indigo #2a3f5f
- Typography: Japanese sans-serif (Hiragino Sans / Noto Sans JP), restrained weight
- Aspect ratio: landscape, 1536x1024 pixels

LAYOUT (top to bottom):
1. Small eyebrow label at top-left: "比較表" in deep indigo (sans-serif Japanese, small)
2. Main title (large, bold, ink black): "{title}"
3. Thin 1-pixel horizontal rule in deep indigo below title
4. Comparison table below

TABLE STRUCTURE:
- {len(cols)} columns total
- Header row: dark ink-black background with white sans-serif Japanese text
- Below header: thick 2-pixel ink-black bottom border
- {len(rows)} data rows
- Alternating row backgrounds (row 1: white, row 2: warm beige, row 3: white, ...)
- First column (label) text in deep indigo, bold
- Other columns text in ink black
- Generous cell padding
- Between data rows: thin 1-pixel hairline in light warm gray
- Bottom of table: thin 1-pixel ink-black rule
- No outer border around the whole table

DATA — use these EXACT Japanese texts, do not modify, translate, or paraphrase. Render in this exact order:
Header: {header_str}
Data rows:
{rows_str}

CRITICAL REQUIREMENTS:
- Preserve EXACT Japanese characters and word order in every cell
- All {len(rows)} data rows must be visible (do not skip any)
- All {len(cols)} columns must be present
- Cell alignment: text left-aligned, vertically centered
- No illustrations, no icons, no decorations, no photos, no people, no logos
- Editorial / magazine-quality flat design
- Clean, restrained, professional
"""


def review_and_images_prompt(
    topic: str, outline_md: str, angle_md: str,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}

## タスク
ブログ記事執筆の前段で、以下2つを構造化出力する：

### 1. 重要セクションのレビュー
outline の中で「ここが記事の核。読者に最も価値がある」と思うセクションを **1〜2個** 指摘し、なぜそう思うか・執筆時に強調すべき点をコメント。

### 2. 挿入画像の提案
記事の理解を助ける機能的な図を提案する。**checklist と comparison_table は Python で描画される（日本語OK、項目数自由、テキスト崩れなし）**。process_flow と data_chart のみ OpenAI 生成。

## 必ず提案してほしいもの
- **「まとめ」セクション(summary)向けに `checklist` を1枚必須**。記事中で出てきた重要なアクション・確認すべき項目を **7〜12個** 拾い、明日からのアクションリストとして読者が持ち帰れる形に
- 記事内で **2つ以上の対立概念** が登場する場合（例: 静止画 vs 動画、AI制作 vs 人手制作）、それらを比較する `comparison_table` を1枚。**5〜10行** の対比指標を含めて多面的に違いを示す

## 任意で追加可能（最大1枚）
- `process_flow`: 手順・段階を示す図（OpenAI、英語プロンプトで指示）
- `data_chart`: 具体数値の比較・推移グラフ（OpenAI、英語プロンプトで指示）

## 絶対ルール
- イラスト・装飾画像・ヒーロー画像・写真・人物・抽象アートは提案しない
- 各H2に機械的に画像はつけない。価値ある図だけ
- placement の section_id は outline 内の `### H2_N:` を h2_1, h2_2 ... と呼び、`### 自社実践` は self_practice、`### まとめ` は summary、`### CTA` は cta

## お題
{topic}

## 角度（angle）
{angle_md}

## 章立て (outline)
{outline_md}

## 出力フォーマット
以下の JSON オブジェクトのみ：
{{
  "key_sections": [
    {{
      "section_id": "h2_1 など outline のID",
      "section_title": "対応セクションのタイトル（短縮可）",
      "why_important": "なぜこのセクションが核なのか（80字以内）",
      "writing_advice": "執筆時の注意点・強調すべき要素（120字以内）"
    }}
  ],
  "images": [
    /* checklist の例（必須1枚） */
    {{
      "id": "summary_checklist",
      "diagram_type": "checklist",
      "placement": "after:summary",
      "purpose": "記事のまとめとして、明日からの実装アクションを網羅（80字以内、日本語）",
      "size": "1024x1536",
      "checklist": {{
        "title": "明日からの実装チェックリスト（日本語、30字以内）",
        "items": [
          "1項目目（日本語、40〜80字、具体的なアクション、固有名詞・数字を含めると強い）",
          "2項目目",
          "..."
        ]
      }}
    }},
    /* comparison_table の例（対立概念があれば必須） */
    {{
      "id": "static_vs_video",
      "diagram_type": "comparison_table",
      "placement": "after:h2_2",
      "purpose": "静止画と動画の差を多面的に対比（80字以内、日本語）",
      "size": "1536x1024",
      "table": {{
        "title": "静止画広告 vs 動画広告 比較（日本語、30字以内）",
        "cols": ["指標", "静止画広告", "動画広告"],
        "rows": [
          {{"label": "CPA", "values": ["平均100（基準）", "約63（37%改善）"]}},
          {{"label": "ROAS", "values": ["1.8倍", "2.4倍"]}},
          {{"label": "..", "values": ["..", ".."]}}
        ]
      }}
    }},
    /* process_flow or data_chart の例（任意、OpenAI 生成） */
    {{
      "id": "creative_pdca_flow",
      "diagram_type": "process_flow",
      "placement": "after:h2_3",
      "purpose": "クリエイティブPDCAの5ステップを視覚化（80字以内、日本語）",
      "size": "1536x1024",
      "prompt_en": "クリエイティブ運用の5ステップを横並びのフラットなプロセスフロー図にする。背景は白、ステップ間は矢印で接続。各ステップのラベル（日本語）: 「計画」「制作」「テスト」「分析」「改善」。和文サンセリフ書体、ミニマルなフラットデザイン。イラスト・装飾・人物・写真は禁止。**画像内の全ての文字は日本語で描画する**。"
    }}
  ]
}}

各画像オブジェクトは diagram_type に応じて：
- "checklist" の場合は **`checklist` フィールド必須**（`prompt_en` 不要）
- "comparison_table" の場合は **`table` フィールド必須**（`prompt_en` 不要）
- "process_flow" / "data_chart" の場合は **`prompt_en` フィールド必須**（**日本語で記述**、画像内のラベル・テキストは必ず日本語にする）

JSONのみ。前置き・コードフェンス禁止。
"""


def image_prompt_wrap_for_freeform(user_prompt: str) -> str:
    """process_flow / data_chart 用：ユーザー記述プロンプト（日本語OK）を、
    デザイン仕様 + 日本語テキスト保持の指示で包む。OpenAI gpt-image に投げる最終形。"""
    return f"""\
{user_prompt}

DESIGN SPECIFICATIONS (must follow strictly):
- Background: warm off-white #fdfcfa (paper-like)
- Body text color: deep ink black #181818
- Accent color: deep indigo #2a3f5f (used sparingly)
- Typography: Japanese sans-serif (Hiragino Sans / Noto Sans JP equivalent), restrained weight
- Editorial / magazine-quality flat design
- Clean, restrained, professional, generous whitespace

ABSOLUTE PROHIBITIONS:
- No illustrations, no icons, no decorations, no photos, no people, no logos, no flowers/leaves/etc
- No 3D rendering, no gradients, no shadows beyond minimal

CRITICAL LANGUAGE REQUIREMENT:
- All visible text labels, headings, captions, and annotations in the image **MUST be rendered in Japanese (日本語) characters**
- If the prompt above contains English terms, render them as their Japanese equivalents while preserving meaning
- **Do NOT include any English text in the final image** (numbers and units like "%", "x" are acceptable as universal symbols)
- Preserve EXACT Japanese characters as written above (no paraphrasing, no translation, no omission)
"""


def lead_prompt(
    topic: str, title: str, lead_direction: str, outline_md: str,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    """ブログ記事のリード文（120〜200字）をGeminiで生成。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
以下の記事タイトル・方向性・章立てに基づき、**リード文（120〜200字、1〜2段落）**を書く。

## お題
{topic}

## 記事タイトル
{title}

## リードの方向性（③企画で書いたメモ。これを噛み砕いて本文化する）
{lead_direction}

## 章立て全体（リードと本文の重複を避けるため参照）
{outline_md}

## 仕様
- **120〜200字**（前後20%まで許容）。冗長な前置き禁止
- 構成：問題提起 → この記事で得られるもの（何が分かる／何ができるようになるか）の流れ
- 1〜2段落、読みやすい改行
- 数字 or 固有名詞を最低1つ入れて具体性を出す
- 煽らない（「衝撃！」「絶対！」「必読！」等は禁止）
- 結論を最初に言い切らない（記事を読む動機を残す）
- 読者が **記事冒頭3行で「これは自分のための記事だ」と気づく** ことを最優先

## 出力フォーマット
リード文の本文Markdownのみ出力。
- H1見出し（# タイトル）は書かない
- 「リード:」「## リード」のような見出し・ラベルも書かない
- 純粋にリード本文の段落のみ
- コードフェンス（```）禁止
"""


def section_prompt(
    topic: str,
    outline_md: str,
    section_title: str,
    section_memo: str,
    target_chars: int,
    cases_csv: str,
    written_sections: list[tuple[str, str]],
    is_self_practice: bool = False,
    is_summary: bool = False,
    is_cta: bool = False,
    angle_hint: str = "",
    interests_hint: str = "",
) -> str:
    written_block = ""
    if written_sections:
        written_block = "\n\n## 既に書いた他セクションの抜粋（重複回避用、内容は引用しない）\n"
        for title, content in written_sections:
            written_block += f"\n### {title}\n{content[:300]}{'...' if len(content) > 300 else ''}\n"

    role_hint = ""
    if is_self_practice:
        role_hint = "\n- このセクションは『HookHack 自社実践コーナー』。押し付けがましくなく、読者の学びになる形で 300〜500 字"
    elif is_summary:
        role_hint = "\n- このセクションは『まとめ』。記事の核メッセージ再掲 + 明日のアクション3つを箇条書きで"
    elif is_cta:
        role_hint = "\n- このセクションは『CTA』。HookHack 目的1（動画PoC）or 目的2（自社AI実践）に自然に着地。ハードセル禁止、1〜2 段落"

    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint)}
## タスク
ブログ記事の **このセクション1つだけ** 書く。

## このセクションのタイトル
{section_title}

## 目標字数
{target_chars}字前後（前後20%まで許容）

## このセクションのメモ（章立てから）
{section_memo}
{role_hint}

## 全体の章立て（参考）
{outline_md}

## お題
{topic}

## 参照事例（CSV、ハルシネーション防止用）
{cases_csv}
{written_block}

## 仕様
- このセクションのMarkdownのみ出力。**`## {section_title}` の見出しから始める**
- 数字・固有名詞・具体ツール名を最低1つ
- 「で、明日何する？」に答える具体性
- cases.csv に無い数字を創作しない
- 既に書いた他セクションと内容が重複しないよう注意
- 箇条書き・GFMテーブルを適宜使う
- 区切り線 `---` 禁止

Markdown本文のみ。前置き・後書き・コードフェンス（```）禁止。
"""


def posts_prompt(
    topic: str, blog_md: str, n_posts: int = 5,
    angle_hint: str = "", interests_hint: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.posts_block()}
{_topic_context_block(angle_hint, interests_hint)}

## タスク
本日のブログ記事をもとに、X（Twitter）投稿を**{n_posts}本**生成する。**5本それぞれ独立した投稿**（スレッドではない）。

## お題
{topic}

## 本日のブログ
{blog_md}

## 5本のバリエーション
1. **データ一発**：本文中の最強数字1つ + 文脈ひとこと
2. **How-to / チェックリスト**：3〜5ステップ or 3つのチェック項目
3. **逆張り / Hot take**：通説への反論 or 誤解の指摘
4. **事例紹介**：本文中で最も強い事例を1つ、独立で語る
5. **自社実践 or 動画PoC誘導**：HookHack自社AI実践tip、または「静止画のみ運用なら」系の軽い誘導。`[BLOG_URL]` プレースホルダを末尾に入れる

## 文体ルール（必須）
- **1投稿 140字以内**（全角換算）
- 改行で1画面に収まる密度
- 冒頭1行目で手を止めさせる（数字 / 疑問 / 断定）
- 絵文字禁止
- ハッシュタグは最大1つ、業界タグのみ（`#広告運用` `#マーケ` 等）
- 「〜しましょう」より「〜する」体言止め
- 過剰な煽り・ビックリマーク禁止

## 出力フォーマット
JSON配列で返す。各要素：
- "kind": "data" / "howto" / "hot_take" / "case" / "self_practice"
- "title": 1行要約（30字以内、内部管理用）
- "text": 投稿本文（140字以内、改行は \\n で表現）
- "scheduled_hint": "08:00" / "12:00" / "15:00" / "18:00" / "21:00" のいずれか

JSON以外は一切出力しないこと。
"""
