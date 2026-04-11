"""
Migration v2 — adds new columns for webinars, student_results, video_reviews.
Usage: python migrate_webinar_v2.py
"""
import os, pymysql
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST","localhost"), port=int(os.getenv("DB_PORT",3306)),
    user=os.getenv("DB_USER","root"),     password=os.getenv("DB_PASS",""),
    db=os.getenv("DB_NAME","webinar_db"), charset="utf8mb4",
)
cur = conn.cursor()

def add_col(table, column, definition):
    cur.execute(f"SHOW COLUMNS FROM `{table}` LIKE '{column}'")
    if cur.fetchone():
        print(f"  ⏭  {table}.{column} — already exists, skipped.")
    else:
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
        conn.commit()
        print(f"  ✅  {table}.{column} — added.")

# ── mdt_webinars ──────────────────────────────────────────────────────────────
add_col("mdt_webinars", "webinar_day",
        "TINYINT(1) NULL DEFAULT NULL COMMENT '0:Sun|1:Mon|2:Tue|3:Wed|4:Thu|5:Fri|6:Sat — only when scheduletype=2'")

add_col("mdt_webinars", "webinar_datetime",
        "DATETIME NULL DEFAULT NULL COMMENT 'Scheduled event date & time (datetime picker)'")

add_col("mdt_webinars", "webinar_discount",
        "INT(5) NOT NULL DEFAULT 0 COMMENT 'Discount/offer amount (0 = no discount)'")

add_col("mdt_webinars", "webinar_offer_title",
        "VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'Offer or promo label e.g. Early Bird 50% OFF'")

add_col("mdt_webinars", "webinar_video",
        "VARCHAR(500) NOT NULL DEFAULT '' COMMENT 'Uploaded promo video path'")

# ── student_results ───────────────────────────────────────────────────────────
add_col("student_results", "video_path",
        "VARCHAR(500) NOT NULL DEFAULT '' COMMENT 'Optional uploaded video path'")

print("\n🎉  Migration v2 complete!")
cur.close()
conn.close()
