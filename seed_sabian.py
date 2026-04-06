"""
サビアンシンボルをPostgreSQLに一括インポートするスクリプト
Railway のコンソールで一度だけ実行する

使い方：
  python seed_sabian.py
"""

import json
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    # JSONファイル読み込み
    with open("sabian.json", "r", encoding="utf-8") as f:
        symbols = json.load(f)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # テーブル作成
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sabian_symbols (
            id SERIAL PRIMARY KEY,
            degree INTEGER NOT NULL,
            sign VARCHAR(20) NOT NULL,
            symbol VARCHAR(200) NOT NULL,
            keyword VARCHAR(100),
            UNIQUE(degree, sign)
        );
    """)

    # データ投入
    count = 0
    for row in symbols:
        cur.execute("""
            INSERT INTO sabian_symbols (degree, sign, symbol, keyword)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (degree, sign) DO UPDATE
            SET symbol = EXCLUDED.symbol,
                keyword = EXCLUDED.keyword;
        """, (row["degree"], row["sign"], row["symbol"], row.get("keyword")))
        count += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ {count}件のサビアンシンボルをDBに登録しました！")

if __name__ == "__main__":
    main()
