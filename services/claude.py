import os
import logging
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """## 役割
西洋占星術の鑑定AIです。
入力されたホロスコープデータを読み、
その人の設計図の核心を言語化します。

## 鑑定の原則
- 惑星・星座・ハウス・アスペクトを統合して読む
- 傾向として示す。断定しない
- その人への直接の語りかけで書く
- 答えはその人の中にある。押しつけない

## データの読み方
惑星＝何のエネルギーか
星座＝どんな質で発揮されるか
ハウス＝人生のどの領域に出るか
アスペクト＝惑星同士がどう影響し合うか

重要アスペクトの優先順位：
コンジャンクション＞オポジション＞スクエア＞トライン＞セクスタイル

## 鑑定文の構成

### 1. 核心（200字）
太陽・ASC・MCを統合して
「この人は何者か」を一段落で書く。
専門用語を使わず、その人の言葉で書く。

### 2. 内なる設計（300字）
月・金星・水星を統合して
感情・愛情・思考のパターンを書く。
「あなたは〜する傾向がある」形式で直接語りかける。

### 3. 行動と欲求（200字）
火星・木星・土星を統合して
どう動くか・何が原動力か・どこで止まりやすいかを書く。

### 4. 人生のテーマ（300字）
天王星・海王星・冥王星と
重要なアスペクト（orb3度以内）を統合して
この人生で何が起きているかの大きな流れを書く。

### 5. 今のあなたへ（200字）
上記全体を踏まえて
今この人に最も必要な視点を一段落で書く。
問いかけで終わる。

## 出力ルール
- 各セクションに見出しをつける
- 合計1000〜1200字
- 星座名・ハウス番号は最小限に留める
- 読んだ人が「これ私のことだ」と感じる具体性を持たせる
- 過剰な褒め禁止
- 恐怖・不安を煽る表現禁止"""


def generate_free_reading(chart: dict) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY が設定されていません")
        return None

    # 全惑星データを整形
    planets = {p["name"]: p for p in chart["planets"]}

    def fmt(name):
        p = planets.get(name, {})
        if not p:
            return f"{name}：データなし"
        return f"{name}：{p.get('sign','')} {p.get('degree','')}° 第{p.get('house','')}ハウス"

    planet_lines = "\n".join([
        fmt("太陽"), fmt("月"), fmt("水星"), fmt("金星"), fmt("火星"),
        fmt("木星"), fmt("土星"), fmt("天王星"), fmt("海王星"), fmt("冥王星"),
        fmt("ASC"), fmt("MC"),
    ])

    # orb 3度以内のアスペクトを優先順位順に絞り込む
    priority = {"コンジャンクション": 0, "オポジション": 1, "スクエア": 2,
                "トライン": 3, "セクスタイル": 4}
    tight_aspects = [
        a for a in chart.get("aspects", []) if a.get("orb", 99) <= 3
    ]
    tight_aspects.sort(key=lambda a: (priority.get(a["aspect"], 9), a.get("orb", 99)))

    aspects_text = ""
    if tight_aspects:
        aspects_lines = [
            f"{a['planet1']} {a['symbol']} {a['planet2']}（{a['aspect']}、orb {a['orb']}°）"
            for a in tight_aspects[:8]
        ]
        aspects_text = "\n重要アスペクト（orb3°以内）：\n" + "\n".join(aspects_lines)

    prompt = f"以下のホロスコープデータを読み、鑑定文を書いてください。\n\n{planet_lines}{aspects_text}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude API エラー: {e}")
        return None
