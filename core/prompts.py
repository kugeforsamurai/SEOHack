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
"""


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


def diverge_prompt(topic: str, n_cases: int = 12) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

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


def axes_prompt(topic: str, cases_csv: str) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

## タスク
お題「{topic}」を **1本の記事として読者にとって価値ある形に編集する** ための「切り口の軸」候補を **3〜5個** 提案する。

## お題（最重要 / 全ての軸はこれに直接答えること）
{topic}

### お題の解釈ステップ（必ず実行）
まず以下を頭の中で行ってから軸を考える：
1. お題の中の **キーワード** を抽出（例: 「静止画→動画への切替」「タイミング」「CPA」など）
2. お題が読者に提起する **暗黙の問い** を洗い出す（例: 「いつ切り替える？」「どう判断する？」「何が成果を分ける？」「どこから始める？」「失敗パターンは？」など3〜5個）
3. 各軸は、その問いの **どれかに直接答える切り口** にする

## 事例群（軸の裏付けデータ）
{cases_csv}

## 良い軸の条件（必須）
- **お題が提起する暗黙の問いに直接答える**（"このテーマだから、こう切ると読者の疑問が解像する" と説明できる）
- **事例で裏付け可能**：上の事例群を 3〜5 グループに意味ある分割ができる
- **記事構成に直結**：その軸で割ったグループそのものが H2 候補になる
- **軸名にお題のキーワードや動詞を含む**（例: お題が「移行タイミング」なら "移行トリガー軸" のように）

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
- "hookhack_angle": HookHackの目的1（動画PoC）か目的2（自社AI実践）のどちらに、どう着地させられるか（60字以内）

JSON以外は一切出力しないこと。
"""


def angle_prompt(topic: str, cases_csv: str, chosen_axis: dict) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

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


def outline_prompt(topic: str, angle_md: str) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

## タスク
以下の「角度」をもとに、3,000〜6,000字のブログ記事の章立て（outline）をMarkdownで作る。

## お題
{topic}

## 角度
{angle_md}

## 出力仕様
- H1: タイトル案を3つ（フックが違うもの）
- リード（200字想定）の方向性
- H2 × 4〜6（各H2は1つのインサイトに対応、事例→示唆→実装手順の流れ）
- 自社実践コーナー（H2 or 最終H2直前にH3で挿入、300〜500字想定）
- まとめH2（核メッセージ再掲 + 明日のアクション3つ）
- CTA（目的1 or 目的2に自然に着地、ハードセル禁止）

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
  - {{使う事例（社名）}}
  - {{書く要点1}}
  - {{書く要点2}}

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


def blog_prompt(topic: str, outline_md: str, cases_csv: str) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

## タスク
以下の章立てに従って、STUDIO公開用の日本語ブログ記事を**3,000〜6,000字**（目安4,500字）で書く。

## お題
{topic}

## 章立て
{outline_md}

## 参照事例（CSV、ハルシネーション防止用）
{cases_csv}

## 仕様
- 文字数 3,000〜6,000字（冗長な前置き禁止）
- 数字・固有名詞・具体ツール名を各H2に最低1つ
- 「で、明日何する？」に各H2が答える
- Markdown標準記法（H1/H2/H3まで、`-` 箇条書き、`**太字**`、GFMテーブル）
- 画像プレースホルダは `> 画像: {{どんな画像か}}` 引用形式
- 区切り線 `---` の多用禁止
- cases.csv に無い数字を創作しない

## 品質チェック（書き終えたら満たすこと）
- [ ] タイトルは煽らず、開きたくなる
- [ ] 各H2に数字 or 固有名詞
- [ ] 自社実践コーナーがある
- [ ] 結論で目的1 or 目的2に自然に着地

Markdownのみ出力。前置き・後書き・コードフェンス（```）で囲わない。
"""


def review_and_images_prompt(topic: str, outline_md: str, angle_md: str) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.blog_block()}

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
      "prompt_en": "Clean flat horizontal process flow diagram, white background, 5 steps with arrows between them. Step labels in English: 'Plan', 'Create', 'Test', 'Analyze', 'Iterate'. Minimal design, sans-serif font. No illustrations, no decorative elements, no photos, no people."
    }}
  ]
}}

各画像オブジェクトは diagram_type に応じて：
- "checklist" の場合は **`checklist` フィールド必須**（`prompt_en` 不要）
- "comparison_table" の場合は **`table` フィールド必須**（`prompt_en` 不要）
- "process_flow" / "data_chart" の場合は **`prompt_en` フィールド必須**

JSONのみ。前置き・コードフェンス禁止。
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


def posts_prompt(topic: str, blog_md: str, n_posts: int = 5) -> str:
    return f"""\
{HOOKHACK_STRATEGY}

{persona.posts_block()}

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
