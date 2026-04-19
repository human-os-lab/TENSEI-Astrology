import os
import logging
import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """## 役割
西洋占星術と脳科学を融合した鑑定AIです。
ユーザーの設計図（ホロスコープ）を読み、自己理解のきっかけを提供します。

## 鑑定の哲学
- 答えはユーザーの内側にある。引き出すだけ
- 設計図を読む。判断しない
- 短く・本質だけ・押しつけない
- わからないことはわからないと言う
- ユーザーの考える力を奪わない

## 禁止事項
- 過剰な褒め／長文の説明／同じ内容の繰り返し
- 運命の決めつけ／恐怖・不安を煽る表現
- 「必ずこうなります」

## 出力スタイル
- 200字以内
- 断定しない。傾向として提示する
- 重要なものに絞る。全部出さない"""


def generate_free_reading(chart: dict) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY が設定されていません")
        return None

    planets = {p["name"]: p for p in chart["planets"]}
    sun = planets.get("太陽", {})
    moon = planets.get("月", {})
    asc = planets.get("ASC", {})

    prompt = (
        f"以下のホロスコープデータから、その人が「どんな人か」を200字以内で読み解いてください。\n"
        f"テキストのみ出力してください（ラベル・タイトル不要）。\n\n"
        f"太陽：{sun.get('sign', '不明')} {sun.get('degree', '')}° 第{sun.get('house', '')}ハウス\n"
        f"月：{moon.get('sign', '不明')} {moon.get('degree', '')}° 第{moon.get('house', '')}ハウス\n"
        f"ASC：{asc.get('sign', '不明')} {asc.get('degree', '')}°"
    )

    if chart.get("aspects"):
        top = chart["aspects"][:3]
        aspects_text = "、".join(
            f"{a['planet1']}と{a['planet2']}の{a['aspect']}" for a in top
        )
        prompt += f"\n主要なアスペクト：{aspects_text}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.error(f"Claude API エラー: {e}")
        return None
