"""
Run once to create all admin tables and a default admin user.
Usage:  python init_db.py
Default login: admin@mayapreneur.com / admin123
"""
import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS", ""),
    db=os.getenv("DB_NAME", "webinar_db"),
    charset="utf8mb4",
)
cur = conn.cursor()

TABLES = [
    # ── Admin users ──────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS admin_users (
        id           INT AUTO_INCREMENT PRIMARY KEY,
        email        VARCHAR(255) NOT NULL UNIQUE,
        password     VARCHAR(255) NOT NULL,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── Hero banner carousel ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS hero_slides (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        webinar_slug  VARCHAR(100) NOT NULL,
        youtube_id    VARCHAR(50)  NOT NULL,
        badge_text    VARCHAR(100),
        badge_color   VARCHAR(20)  DEFAULT 'orange',
        title         VARCHAR(300) NOT NULL,
        schedule      VARCHAR(100),
        time_ist      VARCHAR(50),
        platform      VARCHAR(50)  DEFAULT 'Zoom',
        language      VARCHAR(100) DEFAULT 'Kannada & English',
        sort_order    INT          DEFAULT 0,
        status        TINYINT      DEFAULT 1,
        created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── Student result images (scrolling strip) ──────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS student_results (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        image_path  VARCHAR(500) NOT NULL,
        alt_text    VARCHAR(200),
        sort_order  INT       DEFAULT 0,
        status      TINYINT   DEFAULT 1,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── Video reviews ────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS video_reviews (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        student_name  VARCHAR(200) NOT NULL,
        student_role  VARCHAR(200),
        video_type    VARCHAR(10)  DEFAULT 'local',
        video_src     VARCHAR(500) NOT NULL,
        thumbnail     VARCHAR(500),
        duration      VARCHAR(20),
        sort_order    INT       DEFAULT 0,
        status        TINYINT   DEFAULT 1,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── Major benefits ───────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS benefits (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        icon_svg    TEXT,
        title       VARCHAR(200) NOT NULL,
        description TEXT,
        sort_order  INT       DEFAULT 0,
        status      TINYINT   DEFAULT 1,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── Student testimonials ─────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS testimonials (
        id            INT AUTO_INCREMENT PRIMARY KEY,
        student_name  VARCHAR(200) NOT NULL,
        review        TEXT         NOT NULL,
        rating        TINYINT      DEFAULT 5,
        sort_order    INT       DEFAULT 0,
        status        TINYINT   DEFAULT 1,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── FAQs ─────────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS faqs (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        question    VARCHAR(500) NOT NULL,
        answer      TEXT         NOT NULL,
        sort_order  INT       DEFAULT 0,
        status      TINYINT   DEFAULT 1,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]

for sql in TABLES:
    cur.execute(sql)

conn.commit()
print("✅  All tables created.")

# ── Default admin user ───────────────────────────────────────────────────────
cur.execute("SELECT id FROM admin_users WHERE email = %s", ("admin@mayapreneur.com",))
if not cur.fetchone():
    hashed = generate_password_hash("admin123")
    cur.execute(
        "INSERT INTO admin_users (email, password) VALUES (%s, %s)",
        ("admin@mayapreneur.com", hashed),
    )
    conn.commit()
    print("✅  Default admin created → admin@mayapreneur.com / admin123")
else:
    print("ℹ️   Admin user already exists.")

# ── Seed default benefits if empty ──────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM benefits")
if cur.fetchone()[0] == 0:
    default_benefits = [
        ("High Profit Margins",         "Sell trending products with strong margins and minimal upfront investment.",    0),
        ("No Inventory Costs",           "No storage, no stock risk, no warehouse expenses.",                            1),
        ("Multiple Product Earnings",    "Test and sell unlimited products without additional cost.",                    2),
        ("Unlimited Income Potential",   "Your growth depends only on scaling, not inventory.",                         3),
        ("Passive Income Opportunity",   "Automate order fulfillment and focus on growth.",                             4),
    ]
    cur.executemany(
        "INSERT INTO benefits (title, description, sort_order) VALUES (%s, %s, %s)",
        default_benefits,
    )
    conn.commit()
    print("✅  Default benefits seeded.")

# ── Seed default FAQs if empty ───────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM faqs")
if cur.fetchone()[0] == 0:
    default_faqs = [
        ("Will This Workshop Be Live?",               "Yes, this is a completely live workshop where you can interact and ask questions in real-time.",                           0),
        ("Any Hidden Terms & Conditions?",            "No hidden terms. Everything is transparent, and your satisfaction is guaranteed.",                                         1),
        ("How Will I Get The Bonuses?",               "All bonuses will be shared digitally via email and your private dashboard access.",                                        2),
        ("How Will You Remind Me?",                   "We will send reminders via WhatsApp, email, and SMS before the workshop starts.",                                          3),
        ("Do I Need To Bring Anything?",              "Just a notebook and an open mind! Everything else will be provided.",                                                      4),
        ("How Will I Get A Refund?",                  "Simply email our support team within the refund period, and your money will be returned.",                                 5),
        ("I'm a Complete Beginner. Is This For Me?",  "Absolutely! This workshop is designed for beginners with step-by-step guidance.",                                         6),
        ("What Language Is The Workshop In?",         "The workshop is conducted in Kannada & English so everyone can follow along easily.",                                      7),
    ]
    cur.executemany(
        "INSERT INTO faqs (question, answer, sort_order) VALUES (%s, %s, %s)",
        default_faqs,
    )
    conn.commit()
    print("✅  Default FAQs seeded.")

# ── Seed default hero slides if empty ───────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM hero_slides")
if cur.fetchone()[0] == 0:
    default_slides = [
        ("dropshipping-mastery", "OCDUN0Oudtk", "🗓 Batch 1 · Every Monday 7 PM",   "orange", "Build a Dropshipping Store From Scratch",   "Every Monday",    "7 PM IST", "Zoom", "Kannada & English", 0),
        ("ecommerce-business",   "OCDUN0Oudtk", "🗓 Batch 2 · Every Wednesday 7 PM", "blue",   "Launch & Scale Your E-Commerce Business",   "Every Wednesday", "7 PM IST", "Zoom", "Kannada & English", 1),
        ("online-earning",       "OCDUN0Oudtk", "🗓 Batch 3 · Every Sunday 6 PM",    "green",  "Master Multiple Online Income Streams",      "Every Sunday",    "6 PM IST", "Zoom", "Kannada & English", 2),
    ]
    cur.executemany(
        "INSERT INTO hero_slides (webinar_slug, youtube_id, badge_text, badge_color, title, schedule, time_ist, platform, language, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        default_slides,
    )
    conn.commit()
    print("✅  Default hero slides seeded.")

# ── Seed default testimonials if empty ──────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM testimonials")
if cur.fetchone()[0] == 0:
    default_testimonials = [
        ("Praveen Mj",           "Maya Preneur is an amazing platform for those who want to learn drop shipping and E-commerce course, their guidance is amazing and phenomenal. Moreover I really thank you from the bottom of my heart because it is the first platform in Kannada that has taught drop shipping and e-commerce.", 5, 0),
        ("Charles Finny",        "I've seen a lot of other e commerce courses but this app is different. The way Mithun sir and Janvi madam explain every class is easy to understand, especially those who want to learn in Kannada. This is a very good platform. Thank you.", 5, 1),
        ("Kumar",                "I am currently undergoing Mayapreneur Dropshipping training. The sessions so far have been good and informative. I have received valuable knowledge and practical insights. Happy with the learning experience.", 5, 2),
        ("Kumar Muller",         "Its very good valuable course, cheap and best. Special thanks to Mithun sir and Janvee madam. Good knowledge and very good support from everyone.", 5, 3),
        ("Bharath Kumara",       "Really good training. You will get focus and enthusiasm to do business. Trainer Jahnavi doing excellent work. Maya Preneur organized training in professional manner.", 5, 4),
        ("Avinash Kadri Bangera","Teaching is very good. Mithun teaching excellent. I feel very happy with the step by step guidance provided.", 5, 5),
    ]
    cur.executemany(
        "INSERT INTO testimonials (student_name, review, rating, sort_order) VALUES (%s,%s,%s,%s)",
        default_testimonials,
    )
    conn.commit()
    print("✅  Default testimonials seeded.")

cur.close()
conn.close()
print("\n🎉  Database setup complete!")
