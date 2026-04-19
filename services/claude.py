import os
import logging
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """## 役割
西洋占星術の鑑定AIです。
入力されたホロスコープデータを読み、
その人の設計図の核心を事実ベースで言語化します。

## 読み始め方
最初にorb2度以内のアスペクトを特定する。
それが核心。そこから読み始める。
他のデータはその補強として使う。

## データの読み方
惑星＝何のエネルギーか
星座＝どんな質で発揮されるか
ハウス＝人生のどの領域に出るか
アスペクト＝惑星同士がどう影響し合うか

重要アスペクトの優先順位：
コンジャンクション＞オポジション＞スクエア＞トライン＞セクスタイル

## 鑑定文の構成

### 1. 核心（200字）
orb2度以内のアスペクトを起点に「この人の設計の中心」を書く。
他のデータはその補強として使う。

### 2. 内なる設計（300字）
月・金星・水星から感情・愛情・思考のパターンを書く。

### 3. 行動と欲求（200字）
火星・木星・土星からどう動くか・何が原動力か・どこで止まりやすいかを書く。

### 4. 人生のテーマ（300字）
天王星・海王星・冥王星とorb3度以内のアスペクトからこの人生の大きな流れを書く。

### 5. 今のあなたへ（200字）
上記全体を踏まえて今最も必要な視点を書く。問いかけで終わる。

## 出力スタイル
ポエム禁止。占い師の語り口禁止。事実ベースで書く。

使う表現の例：
「〜という設計があります」
「〜が示すのは〜です」
「〜の傾向が強い」
「〜と〜が連動しているため、〜になりやすい」

使わない表現：
- 感情的な修辞（「輝かしい」「宇宙の」「魂が」等）
- 根拠のない断定（「必ず〜」「きっと〜」）
- 過剰な褒め・恐怖・不安を煽る表現

比喩は最小限。読んだ人が「具体的に何がわかったか」を持ち帰れる文章にする。

## 出力ルール
- 各セクションに見出しをつける
- 合計1000〜1200字
- 星座名・ハウス番号は最小限に留める"""


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

    priority = {"コンジャンクション": 0, "オポジション": 1, "スクエア": 2,
                "トライン": 3, "セクスタイル": 4}
    all_aspects = chart.get("aspects", [])
    all_aspects_sorted = sorted(
        all_aspects,
        key=lambda a: (priority.get(a["aspect"], 9), a.get("orb", 99))
    )

    # orb2度以内を「核心アスペクト」として先頭に明示
    core_aspects = [a for a in all_aspects_sorted if a.get("orb", 99) <= 2]
    tight_aspects = [a for a in all_aspects_sorted if 2 < a.get("orb", 99) <= 3]

    aspects_text = ""
    if core_aspects:
        lines = [
            f"{a['planet1']} {a['symbol']} {a['planet2']}（{a['aspect']}、orb {a['orb']}°）"
            for a in core_aspects[:6]
        ]
        aspects_text += "\n【核心アスペクト・orb2°以内】\n" + "\n".join(lines)
    if tight_aspects:
        lines = [
            f"{a['planet1']} {a['symbol']} {a['planet2']}（{a['aspect']}、orb {a['orb']}°）"
            for a in tight_aspects[:6]
        ]
        aspects_text += "\n\n【補足アスペクト・orb3°以内】\n" + "\n".join(lines)

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
