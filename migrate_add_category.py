"""
Run once to add category column to all content tables.
Usage: python migrate_add_category.py

category values: 0=All  1=Dropshipping  2=E-Commerce  3=Online Earning
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

TABLES = ["student_results", "video_reviews", "benefits", "testimonials", "faqs"]

for tbl in TABLES:
    cur.execute(f"SHOW COLUMNS FROM `{tbl}` LIKE 'category'")
    if cur.fetchone():
        print(f"  ⏭  {tbl} — category column already exists, skipped.")
    else:
        cur.execute(f"ALTER TABLE `{tbl}` ADD COLUMN `category` TINYINT(2) NOT NULL DEFAULT 0 COMMENT '0:All | 1:Dropshipping | 2:E-Commerce | 3:Online Earning' AFTER `status`")
        conn.commit()
        print(f"  ✅  {tbl} — category column added.")

cur.close()
conn.close()
print("\n🎉  Migration complete!")
