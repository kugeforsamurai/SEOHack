"""HookHack戦略を埋め込んだプロンプト群。各ステージで Gemini に渡す。
人格・文体・読者像は core/persona.py 経由で config/persona.json から動的に注入される。"""

from core import persona

HOOKHACK_STRATEGY = """\
記事の書き手は **HookHack**（サムライスタイル株式会社が展開する獲得特化動画広告ブランド）。同社は兄弟プロダクトとして LP制作・改善ブランドの **LPHack** も展開しており、お題に応じて自然に紹介する。今回作るコンテンツは、以下の戦略目的を **暗黙的に下支え** する（露骨な広告にする意味ではなく、論点設計・事例選び・結論の誘導先として）。

## 目的1：動画広告PoCでリード獲得（HookHack）
**静止画バナーのみ運用中の顧客** に対し、動画広告PoCで以下5指標の改善差分を見せてリード獲得＆アップセル：
フォーム送信数 / サイト訪問数 / 無料制作数 / 有償化数 / 継続数
→ 構成の方向性: 動画 vs 静止画の比較、CPA/CVR/視聴維持率の差分メカニズム、移行判断の意思決定材料、まずは小さくPoCを回す道筋

## 目的2：自社実践AI×◯◯の公開でクロスセル
HookHack/LPHack がどう **自社内でAIを活用** しているかを事例化、関連業務（**SEO / SNS / 広告運用 / LP改善 / CRM運用**）の受注に繋げる。
→ 構成の方向性: 自社実践コーナーの厚みを出す、AIワークフローのHow-to、関連業務に活きるTipsまで広げる、結論で関連業務支援に着地

## 両方
上記2つに **同時接続できる射程の広いテーマ**（例: 動画広告制作にAIを取り入れる方法、動画クリエイティブPDCAの自動化、広告×LP連動運用など）。
→ 構成の方向性: 動画広告の論点 + AI活用の論点を両輪で。重点セクションを動画側、自社実践コーナーをAI側に振り分けて両方滲ませる

## プロダクト紹介（記事・投稿で自然に滲み出させる）

### HookHack（動画広告ブランド）
- 獲得特化動画広告を **最短5分・〜3,000円/1本** で制作
- 製品の核（PDCAの D/A をAIで高速化）:
  1. **訴求案発散と動画パターン生成（D）**: LPから動画訴求案を自動発散、画像・動画素材と組み合わせ最短5分で複数パターン
  2. **出稿後の自動解析と改善案提示（A）**: Google広告連携、視聴維持率/CTR/CVRをパターン別解析、改善案自動提示

### LPHack（LP制作・改善ブランド）
- 獲得特化LPを **最短即日・〜2万円/1枚** で制作
- 3つの差別化軸:
  1. **検証スピード**: LPを最短即日で立ち上げ、検証サイクルを最速化
  2. **検証コスト**: 〜2万円で勝ち筋探索の試行回数を最大化
  3. **検証精度**: 広告×LP連動運用で「勝ち訴求」を切り出し、データのノイズを減らす
- 体制: 日本ディレクター（戦略・品質） × AI（コピー・画像・構成） × インドネシアオフショア（仕上げ・実装）
- 実績例: 教育（オンライン教室・資格アプリ）/ 不動産（分譲マンション・戸建てオープンハウス）/ 通販（生活雑貨・ガジェット）

### 連動運用（HookHack × LPHack）— 最大の差別化ポイント
- 動画とLPを **同じ仮説で連動運用**、「広告だけ・LPだけ」では埋もれる勝ち訴求を切り出す
- 代表的な提案: **「まず1セット、無料で試す（動画1本+LP1枚）」**
- お題が広告クリエイティブ全般・PDCA高速化・コンバージョン改善などに該当する場合、連動運用の話を最も推奨する

## 記事・投稿で表現するときのガイド（重要）
- **HookHack / LPHack の話（ブランド名・サービス名・PoC案内・自社実践事例）は基本「CTA章（記事末の次の一歩章）」のみに集約する**
- **通常のH2・まとめH2では HookHack / LPHack を一切名指ししない**。セールスポイント（最短5分で動画パターン生成、最短即日でLP立ち上げ、Google広告連携の自動解析、広告×LP連動運用）も通常H2では具体的に書かない
- **独立した「自社実践コーナー」H2/H3 はデフォルトで作らない**。HookHack / LPHack の話はCTA章で次の一歩として滲ませるだけ
- 「自社実践コーナーを入れて」「自社事例を厚く」等のユーザー指示がある場合のみ、独立コーナーを設置する
- 過度に煽らない。読者が自分で「だから動画PoC＝HookHack / LP改善＝LPHackが合うかも」と気づく余白を残す
- **記事構成**: 通常H2群 → まとめ章（純粋集約） → CTA章（次の一歩、HookHack / LPHack誘導）の3パートに分ける

## お題と HookHack / LPHack 目的の整合性ルール（最重要・厳守）
お題に応じて、CTA章でどのブランドへ誘導するかを **自動で判断** する：

| お題のジャンル | CTA章で出すブランド | 動画 vs 静止画の比較を持ち込むか |
|---|---|---|
| 動画広告 / 広告クリエイティブ / 動画運用 | HookHack（場合により連動も） | OK |
| LP / LPO / CVR改善 / コンバージョン最適化 | LPHack（場合により連動も） | NG（動画話は要らない） |
| 広告×LPの連携 / PDCA高速化 / 検証ループ / 勝ち訴求の見つけ方 | 連動運用（HookHack×LPHack） | OK（連動の文脈で） |
| 自社AI活用 / SEO / SNS / CRM / 業務効率化 | 目的2（自社AI実践） | NG |
| 上記いずれにも該当しない（組織論・採用・IRなど） | **そもそもブランド誘導しない**（中立記事として終わる） | NG |

- **お題と無関係なブランド話を持ち込まない**（読者が違和感を持つ。記事の信頼を損ねる）
- 動画広告メカニズム（視聴維持率がシグナル → 媒体学習が深まる等）は、**お題が動画・広告クリエイティブと直結する時のみ** 持ち込む理論
- LPHack のセールスポイント（最短即日・〜2万円、広告×LP連動）は、**お題がLP・コンバージョン改善と直結する時のみ** 持ち込む
"""


def _disable_hookhack_block(disable_hookhack: bool = False) -> str:
    """記事から HookHack / LPHack 言及を完全に外したい場合のオーバーライドブロック。
    True ならプロンプト末尾に最重要指示として注入される。"""
    if not disable_hookhack:
        return ""
    return """

## ⚠️ この記事では HookHack / LPHack について一切触れない（最優先・上書き指示）
上記の HookHack / LPHack / 連動運用 の戦略・セールスポイント・着地点はすべて無視する。記事には以下を一切含めない：
- 「HookHack」「LPHack」「サムライスタイル」「HookHack社」「弊社では」などの社名・自社言及
- 動画広告PoCサービス、LP制作サービス、AIによる訴求案発散・パターン生成、Google広告連携の自動解析、広告×LP連動運用 など、HookHack/LPHack 製品の機能紹介
- 「自社実践コーナー」「自社事例」「私たちのチームでは」のような自社経験の差し込み
- まとめ章・CTA章の最後で HookHack / LPHack への誘導・問い合わせ・サービス案内に着地させる

記事は **中立的な情報源** として、業界一般のベストプラクティス・データ・他社事例のみで構成する。
まとめ章は「業界の方向性」、CTA章は「読者が次に試せる一般論ベースの手」として書き、特定企業への誘導はしない。
"""


def _topic_context_block(
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    """全ステージで参照する「切り口」「関心」「ユーザー方針」コンテキスト。
    - angle_hint / interests_hint: ⓪テーマ発散でユーザーが選んだテーマの angle / why_for_target
    - user_direction: ②収束で軸を選んだ後にユーザーが書いた自分の方針メモ
    ① 以降の全プロンプトに注入して一貫性を保つ。"""
    has_angle = bool(angle_hint and angle_hint.strip())
    has_int = bool(interests_hint and interests_hint.strip())
    has_dir = bool(user_direction and user_direction.strip())
    if not (has_angle or has_int or has_dir):
        return ""
    lines = ["", "## 今回のお題コンテキスト（全段階で必ず反映すること）"]
    if has_angle:
        lines.append(f"- **切り口（angle）**: {angle_hint.strip()}")
    if has_int:
        lines.append(f"- **読み手の関心（interests）**: {interests_hint.strip()}")
    if has_dir:
        lines.append(f"- **ユーザーの方針メモ（最優先で反映）**: {user_direction.strip()}")
    lines.append(
        "出力（軸の作り方 / 事例の選び方 / 章立て / 本文の語り口 / X投稿のフック）すべてを、"
        "この切り口・関心・ユーザー方針メモに寄せて構築する。テーマからブレてはならない。"
        "**ユーザーの方針メモは最優先**で、軸の解釈・章立て・本文のトーンに反映すること。"
    )
    return "\n".join(lines) + "\n"


def research_theme_prompt(target: str, n_themes: int = 8) -> str:
    """⓪リサーチテーマ提案。OpenAI gpt-4o で発散させる。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.reader_block()}

## タスク
以下のターゲット読者に向けて、HookHack/LPHack ブログで取り上げる価値の高い「リサーチテーマ」を **{n_themes}個** 提案する。各テーマは記事1本になりうる粒度の具体的な切り口にすること。

## ターゲット読者
{target}

## 良いテーマの条件
- **具体的**：「動画広告について」ではなく「Meta広告で静止画→動画に切り替えた時のCPA改善幅」のように切り口が明確
- **数字や事例で裏付けられる**：リサーチで具体例・数値が集まる見込みのあるテーマ
- **HookHack/LPHack の戦略目的への接続**：①動画広告PoCでリード獲得（HookHack）/ ②自社AI実践クロスセル / LP制作改善（LPHack）/ 広告×LP連動運用 のいずれかに自然に接続できる
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


def diverge_prompt(topic: str, n_cases: int = 12, angle_hint: str = "", interests_hint: str = "", user_direction: str = "") -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}
## タスク
お題「{topic}」について、**中小企業を主軸とした** 実践事例を{n_cases}件、構造化して列挙する。

## 事例選定基準
### 規模（最重要）
- **HookHack/LPHack の顧客層は中小企業（年商1〜100億円規模、従業員30〜500人規模、スタートアップ含む）**。事例の企業もこの規模感に揃える。
- **大手・グローバル企業（Nike / Sephora / HubSpot / Adobe / Salesforce / Apple / Google / Amazon等）を引用しない**。これらは読者が「うちとは規模が違う」と感じて記事から離脱する原因になる。
- 上場前のスタートアップ、地方の中堅企業、SaaS黎明期の小さな企業、D2Cブランド、地域密着のEC事業者、業界特化の中小SaaS など、**読者が「うちと近い」と感じる規模感**を優先する。
- **やむを得ず大手を引用する場合**は、その大手が **小さな単一施策・小さな実験フェーズ** で得た学びだけを切り出して紹介し、規模感のミスマッチが目立たないようにする。

### 地域・言語の配分
- **日本国内の中小企業を主軸（全体の 60〜70%）**。残りを海外の中小企業・スタートアップ事例で補う。
- 海外内も多様化（米国一極集中は避け、英国・ドイツ・北欧・東南アジア・韓国などのスタートアップ・SMBから）
- 言語: 日本語ソース優先、英語ソースで補完

### 数字・データ
- CTR / CVR / ROAS / CPA など具体指標と数値を必ず記載。「約30%改善」のように曖昧でもOK、出典が明確なら
- **桁感に注意**: 大手の「年間広告費10億円」のような巨大数字は中小読者にはピンと来ない。「月10万円の広告費で〜」「3ヶ月で〜件」のような **中小企業が共感できるスケール** を優先

### その他
- **HookHack/LPHackの戦略目的と接続できる切り口**を意識（最低3件は接続できる事例）
- **ハルシネーション禁止**：URL・数字が確実なものだけ。曖昧なら「出典不明」と書く
- **企業・施策の重複を避ける**

## 出力フォーマット
JSON配列で返す。各要素は以下のキーを持つ：
- "誰が": 企業/組織名
- "何を": 施策内容（80字以内）
- "どう測ったか": 計測指標（CTR / CVR / ROAS など）
- "結果_数字": 具体数値（〇〇%改善、X倍など）
- "出典URL": URL or 「出典不明」
- "示唆": HookHack/LPHack視点での気付き（60字以内）
- "国_地域": 国名または地域名（例: アメリカ / 日本 / 英国 / ドイツ / 韓国 / シンガポール / グローバル）
- "情報源言語": "英語" or "日本語" or "その他"

JSON以外は一切出力しないこと。
"""


def axes_prompt(
    topic: str, cases_csv: str, user_feedback: str = "",
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
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
{_topic_context_block(angle_hint, interests_hint, user_direction)}{feedback_block}
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
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    """1つの軸だけをユーザー指示で再考させる。assignmentsも整合性を保って再生成。"""
    import json as _json

    current_axis_json = _json.dumps(current_axis, ensure_ascii=False, indent=2)
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}
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
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}
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
- 読者アクション: {{次に取る具体action、1〜2個。「明日からできる」のような決まり文句は避けて多様な表現で}}

### インサイト2: ...
（3〜5個）

## 成果差分が出るポイント（予想）
- {{ポイント1: どこで差がつくか、なぜそう思うか}}
- {{ポイント2}}

## HookHack/LPHack着地点
- HOOKHACK_STRATEGY のお題整合性表に従い、CTA章で何を推すか（HookHack動画 / LPHack LP / 連動運用 / 目的2 / 誘導なし）
- 結論部分でどう自然に接続するか（1〜2行）
```

Markdown以外は出力しない。
"""


def _hookhack_goal_block(hookhack_goal: str) -> str:
    """テーマ選択時に決まった hookhack_goal（目的1 / 目的2 / 両方）を outline 生成時に強調注入する。"""
    g = (hookhack_goal or "").strip()
    if not g:
        return ""
    if "1" in g and "2" in g:
        kind = "両方"
        hint = (
            "**両方**: 動画広告の論点とAI活用の論点を両輪で。"
            "重点セクションを動画側（CPA/CVR/視聴維持率）に、自社実践コーナーをAI側"
            "（SEO/SNS/広告運用/LP改善/CRM運用への応用）に振り分けて両方の戦略目的を滲ませる。"
            "CTA章は、まずは動画PoCを試す（HookHack）or AI活用支援に相談 のどちらにも繋がる出口にする。LPと連動する文脈なら LPHack 連動運用も選択肢に。"
        )
    elif "両方" in g:
        kind = "両方"
        hint = (
            "**両方**: 動画広告の論点とAI活用の論点を両輪で。"
            "重点セクションを動画側（CPA/CVR/視聴維持率）に、自社実践コーナーをAI側"
            "（SEO/SNS/広告運用/LP改善/CRM運用への応用）に振り分けて両方の戦略目的を滲ませる。"
            "CTA章は、まずは動画PoCを試す（HookHack）or AI活用支援に相談 のどちらにも繋がる出口にする。LPと連動する文脈なら LPHack 連動運用も選択肢に。"
        )
    elif "1" in g:
        kind = "目的1（動画広告PoCでリード獲得）"
        hint = (
            "**目的1（動画広告PoCでリード獲得）**: 静止画運用中の読者を動画PoCに動かすことを最終ゴールに。"
            "H2構成は『動画 vs 静止画の差分（メカニズム+数字）』『移行判断の意思決定軸』『PoCの始め方・小さく回す道筋』を中心に。"
            "自社実践コーナーは動画クリエイティブ制作AIの実例を簡潔に。"
            "まとめは『まず1パターンだけ動画を回してCPA差分を観測してみる』のような小さな次の一歩を提示。"
            "\n\n### この目的でのみ展開してよい技術論点（CPA分解 / 動画 vs 静止画メカニズム）"
            "\n- **CPA = CPC ÷ CVR**。CPC は媒体側ターゲティングリストのサイズ・競合性・CTR等の複合要素"
            "\n- 静止画広告は「クリック有無」のみのシグナル → 媒体側の学習に乏しい"
            "\n- 動画広告は **「視聴維持率」という連続値シグナル** を媒体に返せる → ターゲティング精度向上 → CPC低下 → CPA改善"
            "\n- この理屈は「なぜ動画でPoCをやる価値があるのか」の理論的根拠。事例の数字とセットでメカニズムとして組み込むと記事が強くなる"
            "\n- **この技術論点は目的1の記事限定**。他の目的・未指定の記事では持ち込まない"
            "\n\n### お題がLPと交差するケース（広告×LP連動）"
            "\nお題が『広告クリエイティブ全般』『PDCA高速化』『コンバージョン改善』『勝ち訴求の見つけ方』等で動画とLP両方が関係する場合、"
            "CTA章では **HookHack（動画）と LPHack（LP）の連動運用**（『まず1セット、無料で試す（動画1本+LP1枚）』）を推奨するシナリオに切り替えてOK。"
            "純粋な動画広告お題なら HookHack 単独でCTAを組む。"
        )
    elif "2" in g:
        kind = "目的2（自社実践AI×◯◯でクロスセル）"
        hint = (
            "**目的2（自社実践AI×◯◯でクロスセル）**: HookHackがどう自社内でAIを活用しているかを事例化し、"
            "関連業務（SEO / SNS / 広告運用 / LP改善 / CRM運用）への受注拡大に繋げる。"
            "H2構成は『AIを使ったワークフロー』『成果の出るAI活用 vs 出ない使い方』『How-to・実装手順』を中心に。"
            "自社実践コーナーは記事の核として厚めに（500字以上）、具体的なAI活用フロー・ツール名・数字を入れる。"
            "まとめは関連業務支援への問い合わせを自然な選択肢として滲ませる。"
            "\n\n### この目的では動画広告の比較を持ち込まない"
            "\n- 動画 vs 静止画の差分、CPA分解メカニズム、視聴維持率の話を **記事に一切入れない**（お題と無関係なため読者が混乱する）"
            "\n- HookHackの強みは『AI活用のノウハウ』として書く。動画制作AIの話に流れない"
            "\n- CTA章の誘導も『AI活用の相談・支援』に着地させる。『動画PoCを試す』には誘導しない"
        )
    else:
        return ""
    return f"""\

## この記事のHookHack戦略目的（最重要 / SEO構成を決定づける）
**{kind}**

{hint}
"""


def outline_prompt(
    topic: str, angle_md: str, cases_csv: str = "",
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
    hookhack_goal: str = "",
    disable_hookhack: bool = False,
) -> str:
    cases_block = ""
    if cases_csv.strip():
        cases_block = f"""\

## ①発散で集めた事例群（CSV / H2の論点に合うものは引用、合わなければ理論で深掘り）
{cases_csv}

**事例引用の方針（最重要）**：
- **H2の論点と合致する事例があれば**、cases.csv から「誰が／何をして（施策）／どうなったか（結果_数字）／示唆」を1〜2件、具体名と具体数字で引用する。
  例: 「地方の食品EC〇〇社が静止画→動画切替で CTR 2.1倍」のように、社名・施策・数字を含む形で（**大手・グローバル企業ではなく中小企業の事例を優先**）
- **H2の論点に合う事例が無い、または無理がある場合**は **事例を入れない** で、代わりに **その論点のメカニズム・理論・原理を詳しく説明** する。
  例: 「視聴維持率が媒体学習を深める理由を、媒体側のシグナル設計から3段階で解説」のように
- 強引に関係薄い事例を当てはめるのは禁止（事例が無理矢理感を与え、説得力が下がる）
- 理論深掘りの場合も、抽象論で終わらず「だから何が起きる／何ができるか」の具体的示唆まで踏み込む
"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}{_hookhack_goal_block(hookhack_goal)}{_disable_hookhack_block(disable_hookhack)}
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
- 通常H2 × 4〜6（各H2は1つのインサイトに対応、事例→示唆→実装手順の流れ）
- **「自社実践コーナー」H2/H3 はデフォルトでは作らない**（ユーザー方針メモに「自社実践を入れて」のような指示がある時のみ作る）
- **まとめH2（最終から2番目、300〜500字）= 純粋な集約**：核メッセージ再掲 + 記事全体の論点振り返り + 次の打ち手3つ。**事例は引用しない**（具体的な社名・数字は出さない）。**HookHack / LPHack には触れない**（CTA章で触れる）。
  - タイトル例: 「視聴維持率改善のまとめ」「動画PoC論点の総括」「AI×SEO実装の結論」「静止画→動画移行 — ラップアップ」（「まとめ」「総括」「結論」「ラップアップ」のいずれかを含める）
- **CTA H2（最終、200〜400字）= 次の一歩への誘導**：HOOKHACK_STRATEGY のお題整合性表（動画系=HookHack / LP系=LPHack / 連動系=連動運用 / 自社AI=目的2 / 無関係=誘導なし）に従って自動判定。煽らず自然な「次の一歩」として滲ませる。**事例は引用しない**。
  - タイトルは **「CTA」「誘導」「お問い合わせ」などの事務的単語を絶対に使わない**。記事内容を反映した自然な見出しにする。例: 「次の一歩へ」「最初の一歩」「動画PoCで成果差を確かめる」「実装に向けて」「踏み出すための準備」「より深く取り組みたい方へ」「アクションプラン」
  - 「弊社サービスは…」「お問い合わせは…」のような告知文ではなく、読者視点の選択肢として書く

## 内容メモのルール（必須）
各H2の「内容メモ」は最低3〜5項目の bullet で、以下の構成を含めること：
1. **使う事例（社名 + 何をして + 結果_数字）**：例「D2Cコスメの〇〇社が静止画→動画A/Bテスト → CTR 2.1倍 / CPA 37%減」を必ず1〜2件、CSVから引用（**中小企業の事例を優先**）
2. **その事例から読み取れる示唆**：1〜2行
3. **書く要点 / 実装手順**：読者がすぐ試せる粒度

事例なしの抽象的な要点だけのメモは禁止。

## ハルシネーション禁止（最重要 / 違反すると ⚠️ 警告が出る）
- **数字（％・倍・件数など）を書くときは、その出所が cases.csv にある社名・事例に限る**
- **cases.csv に無い社名 + 数字の組み合わせを内容メモに書かない**（例: cases.csv に無い「Acme社が CTR 30% 改善」は禁止）
- 数字を入れたい場合は、cases.csv の `誰が` 列の表記をそのまま使う（半角/全角・略称も合わせる）
- cases.csv に該当事例が無いH2は、**社名を出さず数字も書かず、メカニズム・原理・実装手順の詳述で組み立てる**
- 一般論や業界平均の数字（「一般に動画広告は CTR 1.5倍」など出典不明の概算）も書かない

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

### {{記事内容を反映したまとめタイトル（「まとめ」「総括」「結論」「ラップアップ」のいずれかを含める）}}（H2 / 最終から2番目）
- 推定字数: 300〜500字
- 内容メモ:
  - 核メッセージ再掲（2〜3行）
  - 記事全体の論点振り返り（各H2が何を主張したか短く整理）
  - 次の打ち手3つ（箇条書き、表現を多様に：「最初に手をつけるポイント」「すぐ試せる3案」「導入の3ステップ」など）
  - **このセクションには事例（社名・数字）を出さない**。本文側で既に出している事例の数字を再掲する必要もない。純粋に論点の集約に絞る。
  - **HookHack / LPHack には触れない**（CTA章で触れる）

### {{記事内容を反映したCTAタイトル（「CTA」「誘導」「お問い合わせ」を使わず、内容を表す自然な見出しにする）}}（H2 / 最終）
- 推定字数: 200〜400字
- 内容メモ:
  - 読者が今すぐ取れるアクションを1〜2個（一般論で）
  - **最後の段落で HOOKHACK_STRATEGY のお題整合性表に従って次の一歩を提示**：動画系=HookHack / LP系=LPHack / 連動系=連動運用（『動画1本+LP1枚 無料セット』）/ 自社AI=目的2 / お題と無関係=誘導なし
  - **このセクションにも事例（社名・数字）を出さない**。CTAは集約と誘導に集中する
- タイトル例: 「次の一歩へ」「最初の一歩」「動画PoCで成果差を確かめる」「実装に向けて」「踏み出すための準備」「より深く取り組みたい方へ」
- **「自社実践コーナー」はデフォルトでは作らない**（ユーザー方針メモで明示的に指示があれば追加）
```
"""


def outline_refine_prompt(
    topic: str,
    current_outline_md: str,
    user_feedback: str,
    cases_csv: str = "",
    angle_hint: str = "",
    interests_hint: str = "",
    user_direction: str = "",
    hookhack_goal: str = "",
    disable_hookhack: bool = False,
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
{_topic_context_block(angle_hint, interests_hint, user_direction)}{_hookhack_goal_block(hookhack_goal)}{_disable_hookhack_block(disable_hookhack)}
## タスク（最重要）
既存の章立てを、**ユーザーの再考指示を絶対的な最優先事項として** 作り直す。
- ユーザー指示は **必ず・具体的に反映** すること。指示を無視したり一般論で薄めたりしてはならない
- ユーザー指示と既存の章立てに矛盾がある場合、**指示が勝つ**（既存の構成を壊してでも指示に従う）
- 指示がH2の順序入れ替えなら順序を本当に入れ替える。タイトル候補の方針変更ならタイトル候補を実際に作り直す
- H1タイトル案 / リード方向性 / H2セクション構成 / 内容メモ すべて見直しの対象。**指示で言及されていない部分は前のままでもOK**だが、指示に言及された部分は **必ず変える**

これを満たした上で、ブログ記事として読者価値の高い形に整える。

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
- 通常H2 × 4〜6（各H2は1つのインサイトに対応、事例→示唆→実装手順の流れ）
- **「自社実践コーナー」H2/H3 はデフォルトでは作らない**（ユーザー方針メモに明示的指示がある時のみ）
- **まとめH2（最終から2番目、300〜500字）= 純粋な集約**：核メッセージ再掲 + 記事全体の論点振り返り + 次の打ち手3つ。**事例は引用しない**（社名・数字は出さない）。**HookHack / LPHack には触れない**（CTA章で触れる）
  - タイトル例: 「視聴維持率改善のまとめ」「動画PoC論点の総括」「AI×SEO実装の結論」「静止画→動画移行 — ラップアップ」（「まとめ」「総括」「結論」「ラップアップ」のいずれかを含める）
- **CTA H2（最終セクション、200〜400字）= 次の一歩誘導**：HOOKHACK_STRATEGY のお題整合性表（動画広告系=HookHack / LP系=LPHack / 広告×LP連動=連動運用 / 自社AI=目的2 / 無関係=誘導なし）に従って自動判定。**事例は引用しない**
  - タイトルは **「CTA」「誘導」「お問い合わせ」などの事務語禁止**、内容反映の自然な見出し（例: 「次の一歩へ」「最初の一歩」「動画PoCで成果差を確かめる」「実装に向けて」「踏み出すための準備」「より深く取り組みたい方へ」）

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

### 自社実践コーナー（H3として H2_X 内に挿入 / または独立H2、ユーザー指示がある時のみ）
- 挿入位置: {{...}}
- 内容: {{...}}
- 推定字数: 300〜500字

### {{記事内容を反映したまとめタイトル（「まとめ」「総括」「結論」「ラップアップ」のいずれかを含める）}}（H2 / 最終から2番目）
- 推定字数: 300〜500字
- 内容メモ:
  - 核メッセージ再掲（2〜3行）
  - 記事全体の論点振り返り（各H2が何を主張したか短く整理）
  - 次の打ち手3つ（箇条書き、表現を多様に：「最初に手をつけるポイント」「すぐ試せる3案」「導入の3ステップ」など）
  - **このセクションには事例（社名・数字）を出さない**。論点の集約に絞る
  - **HookHack / LPHack には触れない**（CTA章で触れる）

### {{記事内容を反映したCTAタイトル（「CTA」「誘導」「お問い合わせ」を使わず、内容を表す自然な見出し）}}（H2 / 最終）
- 推定字数: 200〜400字
- 内容メモ:
  - 読者が今すぐ取れるアクションを1〜2個（一般論ベース）
  - 最後の段落でお題と連動するブランド（HookHack / LPHack / 連動運用 のいずれか）への次の一歩を自然に滲ませる
  - **このセクションにも事例（社名・数字）を出さない**
- タイトル例: 「次の一歩へ」「最初の一歩」「動画PoCで成果差を確かめる」「実装に向けて」「踏み出すための準備」「より深く取り組みたい方へ」
```

Markdown 以外は出力しない。コードフェンス（```）でラップしない。
"""


def blog_prompt(
    topic: str, outline_md: str, cases_csv: str,
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}
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
- 固定文言「で、明日何する？」「明日からできる」「明日のアクション」は**使用禁止**（AIらしい紋切り型に見えるため）。
- 章の内容に即した毎回ユニークな見出しにする。同じ記事内で重複させない。
- 例: 「最初に手をつける1点」「導入時の確認手順」「すぐ試せる3つの工夫」「制作プロセスの棚卸し手順」「次に検証すべき仮説」など、表現を毎回変える。

## 仕様
- 文字数 3,000〜6,000字（冗長な前置き禁止）
- **事例引用の方針**: H2の論点に合う事例があれば社名・数字込みで引用。合わない場合は事例を入れず理論を詳述（強引な当てはめ禁止）
- Markdown は H1/H2/H3 の見出しのみ使う。**`**太字**` の濫用、`| テーブル |` 記法、`-` 箇条書きの多用は禁止**（地の文・散文を主軸にする）
- 区切り線 `---` の多用禁止
- cases.csv に無い数字を創作しない
- **本文中に出典・参照リンクを書かない**（「出典: 〜」「参照: 〜」「ソース: 〜」「（〇〇社公式サイト）」「（https://...）」のような表記は本文中に一切入れない）。
  事例の社名・数字は本文中で言及してOKだが、**ソース表記は記事末尾の「参考文献」セクションに別途まとめて掲載される**ため、本文には含めない

## 品質チェック（書き終えたら満たすこと）
- [ ] タイトルは煽らず、開きたくなる
- [ ] 導入文で読者メリットが明示される（120〜200字、画像なし）
- [ ] 各H2に数字 or 固有名詞（cases.csv にあるもののみ。架空の社名+数字禁止）
- [ ] 中小企業中心の事例構成（Nike/Sephora等のグローバル大手は使わない）
- [ ] 事例企業に業界の一言説明を添えている（「地方の食品EC〇〇社」のように）
- [ ] 各章末のH3「次の一手」見出しは内容に応じてユニーク（「で、明日何する？」「明日からできる○○」のような紋切り型は禁止）
- [ ] 自社実践コーナーは入れるか省くかをお題と章立てに応じて判断（無理に挿入しない）
- [ ] まとめ章は純粋集約（HookHack/LPHack言及なし、事例なし）
- [ ] CTA章はお題に応じたブランド誘導（動画系=HookHack / LP系=LPHack / 連動系=連動運用 / 自社AI系=目的2 / 無関係=誘導なし）
- [ ] CTA章タイトルは「CTA」「お問い合わせ」「誘導」のような事務語ではなく内容反映の自然な見出し
- [ ] 「監修者情報」「目次」「画像プレースホルダ」を本文に書いていない

Markdownのみ出力。前置き・後書き・コードフェンス（```）で囲わない。
"""


def image_caption_prompt(
    topic: str,
    checklist_title: str,
    checklist_items: list[str],
    angle_hint: str = "",
) -> str:
    """まとめチェックリスト画像の下に添える「ご参考に〜」キャプションを生成。
    記事のトーンに揃え、1〜2文・40〜80字の自然な提示文を作る。"""
    items_md = "\n".join(f"- {it}" for it in checklist_items[:10])
    angle_block = f"\n## 切り口（angle）\n{angle_hint.strip()}\n" if (angle_hint and angle_hint.strip()) else ""
    return f"""\
{persona.blog_block()}

## タスク
記事末のまとめチェックリスト画像のすぐ下に添える、短い案内キャプションを1つだけ生成する。
読者が画像を見たときに「保存しておこう」「振り返り用に置いておこう」と思える、温かい提示文。

## お題
{topic}
{angle_block}
## チェックリスト画像の中身
**タイトル**: {checklist_title}
**項目**:
{items_md}

## 出力ルール
- 1〜2文、40〜80字
- 「ご参考に」「振り返り用に」「お手元に置いて」「持ち歩き用に」「ブックマークしておく」のような自然な提示の言い回しから選ぶ（毎回違う言い回しを使う）
- 命令調・誇張禁止（「絶対」「必ず」「今すぐ」「決定版」など使わない）
- 体言止め・絵文字・特殊記号禁止
- 「本記事の」「この記事の」のような事務的フレーズは控えめに（1回まで）
- 出力はキャプション本文のみ。前置き・引用符・装飾・改行は一切付けない（1行で返す）
"""


def image_prompt_for_checklist(title: str, items: list[str]) -> str:
    """チェックリスト画像のOpenAI gpt-image用プロンプト生成。
    エディトリアル / 編集デザイン仕様を英語で埋め込む。日本語テキストはそのまま保持指示。"""
    items_block = "\n".join(f"  - {item}" for item in items)
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

EACH ITEM display (MUST follow exactly):
- **An empty checkbox** on the LEFT side of the item: a square outline ~28x28 pixels, stroke 2px in deep ink black #181818, transparent fill (no checkmark inside, just the empty box)
- The checkbox sits vertically aligned with the first line of the item text
- 16px gap between the checkbox and the start of the item text
- Item text in ink-black sans-serif Japanese typography, to the right of the checkbox
- **DO NOT show any number** (no "01", "02", "1.", etc. anywhere on the item)
- Generous vertical spacing between items
- Thin 1-pixel horizontal hairline in light warm gray between consecutive items (not after the last)

ITEMS — use these EXACT Japanese texts, do not modify, translate, or paraphrase. Render in this exact order:
{items_block}

CRITICAL REQUIREMENTS:
- Preserve EXACT Japanese characters and word order (no replacement, paraphrasing, omission, or summarization)
- All {len(items)} items must be displayed in full (do not skip any)
- **Every item MUST have an empty checkbox on its left side** (this is the defining feature of the design)
- **NO numbers anywhere** — not on the left, not on the right, not above. Numbers are forbidden.
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


def image_refine_prompt(
    topic: str, outline_md: str, blog_md: str,
    current_images_json: str, user_feedback: str,
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    """⑤本文書き上がり後に、画像案リストだけをユーザー指示で再考させる。
    重点セクション (key_sections) は触らず、images 配列のみを返す。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}

## タスク
既存の画像案リストを、ユーザーの再考指示に沿って **作り直す**。
**重点セクション(key_sections)は触らない**。**画像案リスト(images配列)のみ** を返す。

## お題
{topic}

## 章立て (outline)
{outline_md}

## 実際に書き上がった本文 (blog.md) — この内容に整合する画像案にする
{blog_md}

## 現在の画像案（修正対象）
{current_images_json}

## ユーザーの再考指示（最優先で反映）
{user_feedback}

## 守るべきこと
- **本文の内容に直接的に整合する画像案にする**（章タイトルだけでなく、本文中の数字・固有名詞・対立概念・手順を踏まえる）
- diagram_type は `checklist` / `comparison_table` / `process_flow` / `data_chart` のみ
- **合計 3枚程度**（多くて4枚）。記事に対して機械的に多数つけない
- **種類を多様に**：同じ型ばかりにせず、checklist + comparison_table + process_flow など組み合わせる
- 「まとめ」セクション(summary)向けに `checklist` を1枚は維持（記事の核アクション7〜12個）
- **「静止画 vs 動画」のような定型比較表をデフォルトで入れない**。本筋の対比軸がある時だけ comparison_table を使う
- 不要なら image を削減してOK（価値ある図だけ）
- イラスト・装飾画像・写真・人物・抽象アートは禁止
- placement の section_id は outline 内の `### H2_N:` を h2_1, h2_2 ... と呼び、`### 自社実践` は self_practice、`### まとめ` は summary、`### CTA` は cta
- 既存の画像IDは、内容を保持するなら維持。差し替え/新規追加する場合は新IDで（id衝突回避）

## 出力フォーマット
以下のJSON配列のみを返す（key_sections は出力しない）：
```json
[
  {{
    "id": "summary_checklist",
    "diagram_type": "checklist",
    "placement": "after:summary",
    "purpose": "...",
    "size": "1024x1536",
    "checklist": {{
      "title": "...",
      "items": ["...", "...", ...]
    }}
  }},
  {{
    "id": "static_vs_video",
    "diagram_type": "comparison_table",
    "placement": "after:h2_2",
    "purpose": "...",
    "size": "1536x1024",
    "table": {{
      "title": "...",
      "cols": ["指標", "A", "B"],
      "rows": [
        {{"label": "...", "values": ["...", "..."]}},
        ...
      ]
    }}
  }},
  /* process_flow / data_chart の場合は prompt_en（日本語OK）を入れる */
  {{
    "id": "...",
    "diagram_type": "process_flow",
    "placement": "after:h2_3",
    "purpose": "...",
    "size": "1536x1024",
    "prompt_en": "..."
  }}
]
```

JSON配列のみ出力。前置き・コードフェンス禁止。
"""


def review_and_images_prompt(
    topic: str, outline_md: str, angle_md: str,
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
) -> str:
    """④レビュー（key_sectionsのみ）。画像案は⑤本文書き上がり後に image_refine_prompt で本文ベースに提案する設計。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}

## タスク
ブログ記事執筆の前段で、**重要セクションのレビューだけ** を構造化出力する。
画像案はこの段階では出力しない（本文書き上がり後に別途、本文を踏まえて提案する設計）。

### 重要セクションのレビュー
outline の中で「ここが記事の核。読者に最も価値がある」と思うセクションを **1〜2個** 指摘し、なぜそう思うか・執筆時に強調すべき点をコメント。

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
  "images": []
}}

`images` は必ず空配列 `[]` を入れる（後段で本文ベースに提案するため）。
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
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
    disable_hookhack: bool = False,
) -> str:
    """ブログ記事のリード文（120〜200字）をGeminiで生成。"""
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}{_disable_hookhack_block(disable_hookhack)}
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


def consistency_review_prompt(
    topic: str,
    angle_md: str,
    cases_csv: str,
    sections_md: str,
) -> str:
    """⑤執筆後にGeminiで論理整合性をレビューさせるプロンプト。
    OpenAIが書いた本文を「リサーチ視点」で見直し、事例ミスマッチ・根拠不透明な数字・
    論理飛躍・章間矛盾を検出する。文体ではなく **論理だけ** を見る。"""
    return f"""\
あなたは記事のロジック監査担当。OpenAIが書いた本文を、cases.csvの事例と角度（angle）に照らして
**論理整合性のみ** を厳しくチェックする。文体・表現の好みは無視する。

## お題
{topic}

## 確定した記事の角度（angle）
{angle_md}

## 事例データ（CSV / 数字・社名の唯一の正解）
{cases_csv}

## 検証対象の本文（H2セクション群）
{sections_md}

## チェック項目（各H2 + 章間）

### A. 事例ミスマッチ（example_mismatch）
- H2の主張と、引用された事例が逆方向 or 関係薄い
- 例: 「動画が静止画より効く」と書いているのに静止画で成功した事例を引用

### B. 根拠不透明な数字（unsubstantiated_number）
- 本文中の数字（%・倍・件数）が cases.csv に存在しない
- 社名は cases.csv にあるが、その社名に紐づく数字が CSV と一致しない
- 「業界平均で〜」「一般に〜」のような出典不明の概算

### C. 論理飛躍（logical_jump）
- 事例の結果から結論への論理橋渡しが不足（「A社がBをしたら成果出た→だからCをすべき」のC部分が事例から飛んでいる）
- メカニズム説明が抽象的すぎて、なぜそうなるかが読者に伝わらない

### D. 章間矛盾（cross_section_contradiction）
- H2_1 と H2_3 で相反する主張をしている
- 数字や定義が章ごとにブレている

### E. 規模感ミスマッチ（scale_mismatch）
- 引用事例が大手・グローバル企業（Nike / Sephora / HubSpot / Adobe / Salesforce / Apple / Google / Amazon等）で、HookHack/LPHack のターゲット読者層（中小企業・スタートアップ）と規模感がズレている
- 数字のスケール（億円単位の広告予算、グローバル展開の話など）が中小企業読者にとって遠すぎる
- 修正案では cases.csv の中小企業事例への差し替え、または該当部分の理論深掘り化を提案

## 出力ルール（最重要）
- **本当に問題があるものだけ** 報告する（重箱の隅つつき禁止）
- 各H2に必ず1個出す必要はない。問題ゼロなら issues は空配列でOK
- 修正案（suggested_fix）は OpenAI に渡す再生成指示の形で書く（「〜してください」「〜に書き換えて」）

## 出力フォーマット（JSONのみ、前後に何も書かない）
```json
{{
  "issues": [
    {{
      "section_id": "h2_2",
      "issue_type": "example_mismatch",
      "severity": "high",
      "location": "本文中の該当箇所を30字以内で引用",
      "description": "何が問題か。論理がどうズレているか具体的に",
      "suggested_fix": "OpenAIに渡す修正指示。例: 「現在引用している〇〇社の事例は静止画キャンペーンの数字なので、H2の動画優位論と整合しない。cases.csvから動画A/Bテストの事例（〇〇社、CTR 2.1倍）に差し替え、論点と事例の方向を揃えてください」"
    }}
  ]
}}
```

- section_id は「h2_1」「h2_2」「h2_3」「self_practice」「summary」「cta」「sec_N」のいずれか。
- 章間矛盾の場合、section_id は "cross" にして description に関連H2を明記する。
- severity: high（事実誤認・大きな論理破綻）/ medium（読者が引っかかる程度）/ low（細かい改善余地）

JSONのみ出力。前置き・後書き・コードフェンスは禁止。
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
    user_direction: str = "",
    user_revision_request: str = "",
    current_content: str = "",
    disable_hookhack: bool = False,
) -> str:
    written_block = ""
    if written_sections:
        written_block = "\n\n## 既に書いた他セクションの抜粋（重複回避用、内容は引用しない）\n"
        for title, content in written_sections:
            written_block += f"\n### {title}\n{content[:300]}{'...' if len(content) > 300 else ''}\n"

    role_hint = ""
    if is_self_practice:
        role_hint = (
            "\n- このセクションは『HookHack / LPHack 自社実践コーナー』。押し付けがましくなく、読者の学びになる形で 300〜500 字"
            "\n- **ユーザーの再生成指示があれば、上記のロール指針より指示を優先する**"
        )
    elif is_summary:
        role_hint = (
            "\n- このセクションは『まとめ章（純粋な集約）』。以下を1つの自然な流れで書く："
            "\n  1. 記事の核メッセージ再掲（2〜3行）"
            "\n  2. 記事全体の論点振り返り（各H2が何を主張したか、短くまとめる）"
            "\n  3. 次の打ち手3つ（箇条書き、表現を多様に：「最初に手をつけるポイント」「すぐ試せる3案」「導入の3ステップ」など）"
            "\n- **このセクションには事例（社名・数字）を一切出さない**。本文側で既に出した事例を再掲する必要もない。論点の集約に絞る"
            "\n- **HookHack / LPHack には触れない**（CTA章で触れる）"
            "\n- **本セクション内に『CTA』『お問い合わせ』『誘導』のような事務的見出しを作らない**"
            "\n- **ユーザーの再生成指示があれば、上記のロール指針より指示を優先する**"
        )
    elif is_cta:
        role_hint = (
            "\n- このセクションは記事末の『次の一歩』章。ハードセル禁止、200〜400字"
            "\n- **どのブランドを推すかは HOOKHACK_STRATEGY の『お題と HookHack / LPHack 目的の整合性ルール』表に従って自動判定**"
            "  （動画広告系=HookHack / LP・CVR系=LPHack / 広告×LP連動・PDCA・コンバージョン改善=連動運用『動画1本+LP1枚 無料セット』 / "
            "自社AI活用系=目的2 / 無関係なお題=ブランド誘導なし）"
            "\n- 構成: (1) 読者が今すぐ取れるアクションを1〜2個（一般論ベース） → (2) 最後の段落で該当ブランドへの次の一歩を自然な選択肢として滲ませる"
            "\n- **見出しに『CTA』『誘導』『お問い合わせ』『コンタクト』のような事務的単語を使わない**。"
            "代わりに **記事内容に即した自然な見出し** にする（例: 「次の一歩へ」「最初の一歩」「実装に向けて」「踏み出すための準備」「より深く取り組みたい方へ」「アクションプラン」等。記事のお題と連動した語で）"
            "\n- 「弊社サービスは…」「お問い合わせはこちら」のような告知文ではなく、読者視点の選択肢として提示する"
            "\n- **このセクションには事例（社名・数字）を一切出さない**。CTA は集約と誘導に集中する"
            "\n- **記事のお題に合わない例文を勝手に挿入しない**（『静止画運用が…』のような特定論点の例文は、お題が動画広告でない記事には入れない）"
            "\n- **ユーザーの再生成指示があれば、上記のロール指針より指示を優先する**（具体的なブランド・トーン・構造の指定があれば従う）"
        )

    # revision_block はプロンプト末尾で適用するため、ここでは構築のみ。
    # 末尾に置く理由: LLM は長文プロンプトで「末尾の指示」を優先しがち（recency）。
    # 前半に置くと ## 仕様 の長いリストに埋もれて無視されることがある。
    revision_block = ""
    if user_revision_request.strip():
        current_block = ""
        if current_content.strip():
            current_block = f"""

### 現在の本文（書き換え対象、これを土台に修正する）
```markdown
{current_content}
```
"""
        revision_block = f"""

---

## 🚨 最優先: ユーザーの修正指示（これを反映しないと再生成失敗扱い）

このセクションは **再生成** であり、以下のユーザー指示を **必ず本文に反映** する。
**他のどのルール（HOOKHACK_STRATEGY / 人格 / トーン / 事例引用方針 / role_hint の構造例）よりも優先する**。
特にCTA章で role_hint の構造例（「次の一歩」見出し例、「動画PoC」誘導例文）と指示が衝突する場合は、**指示の方を採用** する。

### ユーザーが書いた修正指示（生テキスト）
{user_revision_request.strip()}
{current_block}

### 反映のチェック手順（本文出力前に必ず実行）
1. ユーザー指示を具体的な変更点に分解する（「数字を入れる」=どの段落に？「メカニズムを厚く」=どこに何行追加？）
2. 現在の本文と照らし、**変えるべき箇所**を特定する
3. 変更後の本文を書く時、その特定した箇所を **目に見える形で** 修正する（語尾だけ変えて済ませない）
4. 指示で言及されていない箇所は、既存の良さを保ってOK。ただし「何も変わってない」と読者が感じる出力は禁止

**「変更が反映されていない」と判定される失敗パターン**:
- 指示を無視して既存本文をほぼそのまま再出力
- 指示の方向を一般論で薄めて誤魔化す（例: 「数字を入れる」指示に対して「数値で示しましょう」のような抽象論で逃げる）
- 既存本文の語順を入れ替えるだけで実質変更なし
"""

    # HookHack / LPHack 言及が許されるのは CTA章 と 自社実践コーナー のみ。
    # 通常H2・まとめH2では HookHack / LPHack を一切名指ししない（CTA集約ルール）
    hookhack_scope_hint = ""
    if not is_cta and not is_self_practice:
        hookhack_scope_hint = (
            "\n- **このセクションでは HookHack / LPHack を一切名指ししない**。社名・サービス名・自社事例の言及は禁止。"
            "HookHack / LPHack に関する話題は CTA章でのみ扱う（記事内で1箇所に集約する設計）"
        )

    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}{_disable_hookhack_block(disable_hookhack)}
## タスク
ブログ記事の **このセクション1つだけ** 書く。{hookhack_scope_hint}

## このセクションのタイトル
{section_title}

## 目標字数
{target_chars}字前後（前後20%まで許容）

## このセクションで必ず書くこと（章立てメモ・全項目カバー必須）
{section_memo}

**メモの扱いルール（最重要）**:
- 上記メモの **bullet 1つ1つを「必須カバー項目」として扱う**（「選択肢」「参考」ではない）
- メモにある「事例: 〜」→ その事例を本文に必ず盛り込む（cases.csv に該当社名が無ければ理論深掘りに振る）
- メモにある「示唆: 〜」→ その示唆を本文で必ず展開する
- メモにある「書く要点」「実装手順」「ポイント」「メカニズム」→ 該当箇所として本文に書く
- **メモの項目を1つでも落としたら『要旨未反映』扱いで失敗**。本文を出す前にメモの bullet を1個ずつ照合して、全部反映されているか自己確認する
- メモにない論点を勝手に膨らませて本文を埋めない（メモを軸に組み立てる）
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
- **事例引用の方針**: H2の論点に合う事例が cases.csv にあれば社名・数字込みで1〜2件引用する。
  合う事例が無いor無理がある場合は **事例を入れず、論点のメカニズム・理論・原理を詳しく説明** する。
  強引な事例の当てはめは禁止（説得力が下がる）。理論深掘りでも具体的示唆まで踏み込む
- **ハルシネーション禁止（最重要）**:
  - **数字（％・倍・件数）を書くなら、その社名は必ず cases.csv の `誰が` 列にあるものに限る**（表記揺れも禁止）
  - cases.csv に無い社名 + 数字の組み合わせを書かない（架空の「Acme社が CTR 30%改善」等は厳禁）
  - 業界平均や一般論の数字（「動画広告は一般に CTR 1.5倍」など出典不明の概算）も書かない
  - 該当事例が無いH2では、**社名・数字を一切出さず、メカニズム・原理・実装手順の詳述で本文を組み立てる**
- **事例企業の業界を一言で添える（必須）**: 「〜社」のような社名を出す際、読者が瞬時にどんな会社か分かる業界・業態のミニ説明を社名と一緒に書く。
  例: 「地方の食品ECを運営する〇〇社は…」「BtoBのニッチSaaS〇〇は…」「D2C雑貨の〇〇は…」「業界特化型の中小代理店〇〇は…」
  毎回「株式会社◯◯（業界）」のような形式張った括弧書きにせず、文の流れに自然に溶け込ませる。
  読者が「この会社、何の会社？」と引っかからずに本文の論点に集中できることを優先する。
  **中小企業を主軸**にした事例構成の中では、大手・グローバル企業名（Nike / Sephora / HubSpot等）が出てきたら、cases.csv の該当行を確認し、規模感が記事ターゲット（中小企業）とズレていないかチェックする
- 読者が次に何を試せるかが分かる具体性（「明日からできる」「明日のアクション」のような紋切り型表現は避ける）
- cases.csv に無い数字を創作しない
- 既に書いた他セクションと内容が重複しないよう注意
- **「AIっぽいMarkdown装飾」は禁止**：
  - `**太字**` の濫用は禁止。本当に強調が必要な1〜2箇所だけ。連発しない
  - **Markdownのテーブル記法（`| 列 | 列 |` 形式）は使わない**。比較データは段落の中で「A は X% / B は Y%」のように散文で書く、または番号付きリストで書く
  - `-` 箇条書きの多用も避ける。3〜5項目で必要なときだけ。本文の地の文を主軸にする
- 区切り線 `---` 禁止
- **本文中に出典・参照リンクを書かない**（「出典: 〜」「参照: 〜」「ソース: 〜」「URL:」「（〇〇社公式サイト）」「（https://...）」のような出典表記は本文に一切入れない）。
  事例の社名・数字は本文中で言及してOKだが、**ソース表記は記事末尾の「参考文献」セクションに一括掲載される**ため、本文には含めないこと

## 出力前の自己チェック（最終ゲート、必ず実行）
1. **メモ全項目反映チェック**: 上の「## このセクションで必ず書くこと」の bullet を1つ1つ照合。未反映があれば本文に追加してから出す
2. **目標字数チェック**: {target_chars}字前後（前後20%）に収まっているか
3. **AIっぽさチェック**: 「**太字**」濫用 / テーブル記法 / 過剰な箇条書き が無いか
{revision_block}
Markdown本文のみ。前置き・後書き・コードフェンス（```）禁止。
"""


def posts_prompt(
    topic: str, blog_md: str, n_posts: int = 5,
    angle_hint: str = "", interests_hint: str = "", user_direction: str = "",
    disable_hookhack: bool = False,
) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.posts_block()}
{_topic_context_block(angle_hint, interests_hint, user_direction)}{_disable_hookhack_block(disable_hookhack)}

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
5. **自社実践 or 次の一歩誘導**：HOOKHACK_STRATEGYのお題整合性表に従い、HookHack/LPHack/連動運用/目的2/誘導なしを判定して軽く滲ませる。`[BLOG_URL]` プレースホルダを末尾に入れる

## 文体ルール（必須）
- **1投稿 140字以内**（全角換算）
- 改行で1画面に収まる密度
- 冒頭1行目で手を止めさせる（数字 / 疑問 / 断定）
- 絵文字禁止
- **ハッシュタグは1〜2個必ず入れる**（必須）。業界タグ中心（例: `#広告運用` `#マーケ` `#動画広告` `#AIマーケ` `#クリエイティブ` など）。投稿テーマに沿うものを選ぶ。投稿末尾に置く
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
