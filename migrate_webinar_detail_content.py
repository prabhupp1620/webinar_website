"""
Migration script: create and populate webinar_topics, webinar_curriculum, webinar_who_for.

Run once:
    python migrate_webinar_detail_content.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from db import get_db

# ── Hardcoded seed data (mirrors _CAT in app.py) ──────────────────────────────
TOPICS = [
    # category 1 — Dropshipping
    (1, "🔍", "Product Research",   "Find winning products & profitable niches using free tools",              1),
    (1, "🏪", "Store Setup",         "Build a professional Shopify/WooCommerce store step by step",             2),
    (1, "🤝", "Indian Suppliers",    "Connect with reliable Indian suppliers & wholesalers",                    3),
    (1, "📦", "Order Fulfilment",    "Automate order processing without touching inventory",                    4),
    (1, "📣", "Ads & Marketing",     "Run profitable Facebook & Instagram ads for your store",                  5),
    (1, "💰", "Profit Strategy",     "Set pricing, manage margins, and scale to ₹50K/month",                   6),
    # category 2 — E-Commerce
    (2, "🏬", "Platform Selection",   "Choose the right platform — Amazon, Flipkart or Meesho",                1),
    (2, "📝", "Listing Optimization", "Write product listings that rank and convert",                           2),
    (2, "💸", "Pricing & Margins",    "Set competitive prices while maintaining healthy profit",                3),
    (2, "📊", "Catalogue Management", "Manage your product catalogue like a professional seller",               4),
    (2, "🔄", "Returns & RTO",        "Handle returns and reduce RTO losses effectively",                       5),
    (2, "📈", "Scaling to ₹1L/month","Strategies to grow from first sale to consistent income",                6),
    # category 3 — Online Earning
    (3, "💻", "Freelancing",               "Get clients on Fiverr, Upwork & LinkedIn from India",              1),
    (3, "🔗", "Affiliate Marketing",       "Earn commissions by promoting products you love",                  2),
    (3, "📱", "Social Media Monetization", "Turn Instagram & YouTube into income streams",                     3),
    (3, "📦", "Digital Products",          "Create and sell eBooks, templates & courses",                      4),
    (3, "🤖", "AI Tools for Income",       "Use AI tools to work faster and earn more",                        5),
    (3, "🌐", "Passive Income Setup",      "Build systems that earn even while you sleep",                     6),
]

CURRICULUM = [
    # category 1 — Dropshipping
    (1, 1, "Introduction to Dropshipping", "What is dropshipping & why it works in India\nSuccess stories from Kannada students",                        1),
    (1, 2, "Finding Winning Products",     "Product research tools (free & paid)\nNiche selection strategy",                                              2),
    (1, 3, "Building Your Store",          "Platform setup walkthrough (live demo)\nBranding & design basics",                                            3),
    (1, 4, "Getting Your First Order",     "Listing products correctly\nRunning your first ad campaign",                                                  4),
    # category 2 — E-Commerce
    (2, 1, "E-Commerce Fundamentals",   "How Indian e-commerce platforms work\nSeller account registration walkthrough",                                  1),
    (2, 2, "Product & Catalogue Setup", "Product photography tips\nWriting SEO-optimised product titles & descriptions",                                  2),
    (2, 3, "Pricing & Inventory",       "Pricing formulas for profit\nManaging stock and warehouse logistics",                                             3),
    (2, 4, "Growth & Scaling",          "Platform ads (Sponsored listings)\nHandling reviews and growing seller rating",                                  4),
    # category 3 — Online Earning
    (3, 1, "Online Earning Mindset",     "Why most people fail online & how to avoid it\nChoosing the right income stream for your skills",               1),
    (3, 2, "Freelancing & Gig Work",     "Setting up profiles on Fiverr & Upwork\nLanding your first paid client",                                        2),
    (3, 3, "Affiliate & Content Income", "How affiliate marketing works in India\nStarting a YouTube channel or blog for income",                         3),
    (3, 4, "Scaling & Automating",       "Creating digital products for passive income\nUsing AI tools to multiply your output",                          4),
]

WHO_FOR = [
    # category 1 — Dropshipping
    (1, "🎓", "Students & Freshers",     "Earn while you study without quitting college",            1),
    (1, "👩‍💼", "Job Seekers",           "Build a business while searching for a job",               2),
    (1, "🏠", "Homemakers",              "Run a store from home on your own schedule",               3),
    (1, "👨‍💻", "Working Professionals", "Build a side income alongside your 9-to-5",               4),
    # category 2 — E-Commerce
    (2, "🏭", "Small Manufacturers", "Sell your products directly to millions online",              1),
    (2, "🛍️", "Resellers",          "Source products and sell them at a profit on major platforms", 2),
    (2, "👩‍💼", "Entrepreneurs",     "Launch a full-fledged e-commerce brand from scratch",         3),
    (2, "🎓", "Beginners",           "No prior experience needed — we start from the basics",       4),
    # category 3 — Online Earning
    (3, "🎓", "Students",                "Earn from your laptop during college hours",              1),
    (3, "👩‍🎨", "Creative Professionals", "Monetize your skills in design, writing, or video",     2),
    (3, "👨‍💼", "Job Seekers",            "Earn while searching — build income independence",       3),
    (3, "🏠", "Stay-at-Home Parents",    "Work on your own time from home",                        4),
]

DDL = """
CREATE TABLE IF NOT EXISTS webinar_topics (
    id         INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    category   TINYINT(2) NOT NULL COMMENT '1:Dropshipping|2:E-Commerce|3:Online Earning',
    icon       VARCHAR(20)  DEFAULT '',
    title      VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order INT DEFAULT 0,
    status     TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS webinar_curriculum (
    id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    category    TINYINT(2) NOT NULL,
    step_number TINYINT NOT NULL,
    title       VARCHAR(200) NOT NULL,
    points      TEXT COMMENT 'Newline-separated bullet points',
    sort_order  INT DEFAULT 0,
    status      TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS webinar_who_for (
    id          INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    category    TINYINT(2) NOT NULL,
    icon        VARCHAR(30)  DEFAULT '',
    label       VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order  INT DEFAULT 0,
    status      TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def run():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Create tables
            for stmt in DDL.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)

            # Skip population if data already exists
            cur.execute("SELECT COUNT(*) AS cnt FROM webinar_topics")
            if cur.fetchone()["cnt"] == 0:
                cur.executemany(
                    "INSERT INTO webinar_topics (category, icon, title, description, sort_order) VALUES (%s,%s,%s,%s,%s)",
                    TOPICS,
                )
                print(f"Inserted {len(TOPICS)} webinar_topics rows.")
            else:
                print("webinar_topics already has data — skipping insert.")

            cur.execute("SELECT COUNT(*) AS cnt FROM webinar_curriculum")
            if cur.fetchone()["cnt"] == 0:
                cur.executemany(
                    "INSERT INTO webinar_curriculum (category, step_number, title, points, sort_order) VALUES (%s,%s,%s,%s,%s)",
                    CURRICULUM,
                )
                print(f"Inserted {len(CURRICULUM)} webinar_curriculum rows.")
            else:
                print("webinar_curriculum already has data — skipping insert.")

            cur.execute("SELECT COUNT(*) AS cnt FROM webinar_who_for")
            if cur.fetchone()["cnt"] == 0:
                cur.executemany(
                    "INSERT INTO webinar_who_for (category, icon, label, description, sort_order) VALUES (%s,%s,%s,%s,%s)",
                    WHO_FOR,
                )
                print(f"Inserted {len(WHO_FOR)} webinar_who_for rows.")
            else:
                print("webinar_who_for already has data — skipping insert.")

            conn.commit()
            print("Migration complete.")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
