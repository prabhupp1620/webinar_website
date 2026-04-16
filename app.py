import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

from db import execute, query

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

# ── DB migrations (run once, safe to re-run) ──────────────────────────────────
def run_migrations():
    migrations = [
        "ALTER TABLE mdt_webinars ADD COLUMN webinar_slug VARCHAR(150) DEFAULT NULL",
        "ALTER TABLE mdt_webinars ADD UNIQUE INDEX idx_webinar_slug (webinar_slug)",
    ]
    for sql in migrations:
        try:
            execute(sql)
        except Exception:
            pass  # Column/index already exists

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "mayapreneur64@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MAIL_TO   = os.getenv("MAIL_TO",   "mayapreneur64@gmail.com")


# ── Register blueprints ───────────────────────────────────────────────────────
from admin import admin_bp
from gallery_bp import gallery_bp
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(gallery_bp)

run_migrations()


# ── Email helper ──────────────────────────────────────────────────────────────
def send_email(name: str, email: str, phone: str, message: str) -> bool:
    has_message = bool(message.strip())
    if has_message:
        subject = "New Contact Enquiry – MayaPreneur"
        body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333">
        <h2 style="color:#2e7d32">Contact Enquiry</h2>
        <table cellpadding="8" style="border-collapse:collapse;width:100%">
          <tr><td><strong>Name</strong></td><td>{name}</td></tr>
          <tr><td><strong>Email</strong></td><td>{email}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{phone}</td></tr>
          <tr><td><strong>Message</strong></td><td>{message.replace(chr(10), '<br>')}</td></tr>
        </table></body></html>"""
    else:
        subject = "New Subscription – MayaPreneur"
        body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333">
        <h2 style="color:#1565c0">New Subscriber</h2>
        <table cellpadding="8" style="border-collapse:collapse;width:100%">
          <tr><td><strong>Name</strong></td><td>{name}</td></tr>
          <tr><td><strong>Email</strong></td><td>{email}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{phone}</td></tr>
        </table></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"]  = subject
    msg["From"]     = SMTP_USER
    msg["To"]       = MAIL_TO
    msg["Reply-To"] = email
    msg.attach(MIMEText(body, "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo(); server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, MAIL_TO, msg.as_string())
        return True
    except Exception as e:
        app.logger.error("Email send failed: %s", e)
        return False


# ── Public routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("maya_os.html")


@app.route("/webinars")
def maya_preneur():
    hero_slides    = query("SELECT * FROM mdt_webinars WHERE webinar_status=1 ORDER BY webinar_id")
    student_results= query("SELECT * FROM student_results WHERE status=1 ORDER BY sort_order")
    video_reviews  = query("SELECT * FROM video_reviews  WHERE status=1 ORDER BY sort_order")
    all_benefits   = query("SELECT * FROM benefits WHERE status=1 ORDER BY category, sort_order")
    testimonials   = query("SELECT * FROM testimonials   WHERE status=1 ORDER BY sort_order")
    faqs           = query("SELECT * FROM faqs           WHERE status=1 ORDER BY sort_order")

    # Group benefits by category for the tabbed section
    benefits_by_cat = {1: [], 2: [], 3: []}
    for b in all_benefits:
        cat = b.get("category") or 1
        if cat in benefits_by_cat:
            benefits_by_cat[cat].append(b)

    return render_template("index.html",
        hero_slides=hero_slides,
        student_results=student_results,
        video_reviews=video_reviews,
        benefits=all_benefits,
        benefits_by_cat=benefits_by_cat,
        testimonials=testimonials,
        faqs=faqs,
    )


@app.route("/api/testimonials")
def api_testimonials():
    """Return paginated testimonials. ?page=1&per_page=8"""
    page     = max(1, int(request.args.get("page", 1)))
    per_page = max(1, int(request.args.get("per_page", 8)))
    offset   = (page - 1) * per_page
    total    = query("SELECT COUNT(*) as cnt FROM testimonials WHERE status=1", one=True)["cnt"]
    rows     = query(
        "SELECT * FROM testimonials WHERE status=1 ORDER BY sort_order, id LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    items = []
    for r in rows:
        items.append({
            "id":           r["id"],
            "student_name": r["student_name"],
            "review":       r["review"],
            "rating":       r["rating"] or 5,
        })
    return jsonify({
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "has_more": (offset + per_page) < total,
        "items":    items,
    })


@app.route("/api/student-results")
def api_student_results():
    """Return latest 4 active student results as JSON."""
    rows = query("SELECT * FROM student_results WHERE status=1 ORDER BY sort_order, id DESC LIMIT 4")
    total = query("SELECT COUNT(*) as cnt FROM student_results WHERE status=1", one=True)["cnt"]
    results = []
    for r in rows:
        results.append({
            "id":         r["id"],
            "image_path": r["image_path"],
            "alt_text":   r["alt_text"] or "",
            "category":   r["category"],
        })
    return jsonify({"total": total, "results": results})


@app.route("/api/video-reviews")
def api_video_reviews():
    """Return paginated video reviews. ?page=1&per_page=8&category=all|1|2|3"""
    page     = max(1, int(request.args.get("page", 1)))
    per_page = max(1, int(request.args.get("per_page", 8)))
    category = request.args.get("category", "all").strip()
    offset   = (page - 1) * per_page

    # category filter: 1=dropshipping, 2=ecommerce, 3=earning
    if category and category != "all":
        try:
            cat_id = int(category)
            total = query("SELECT COUNT(*) as cnt FROM video_reviews WHERE status=1 AND category=%s", (cat_id,), one=True)["cnt"]
            rows  = query("SELECT * FROM video_reviews WHERE status=1 AND category=%s ORDER BY sort_order, id LIMIT %s OFFSET %s", (cat_id, per_page, offset))
        except (ValueError, TypeError):
            total = 0
            rows  = []
    else:
        total = query("SELECT COUNT(*) as cnt FROM video_reviews WHERE status=1", one=True)["cnt"]
        rows  = query("SELECT * FROM video_reviews WHERE status=1 ORDER BY sort_order, id LIMIT %s OFFSET %s", (per_page, offset))

    items = []
    for r in rows:
        items.append({
            "id":           r["id"],
            "student_name": r["student_name"],
            "student_role": r["student_role"] or "",
            "video_type":   r["video_type"] or "local",
            "video_src":    r["video_src"],
            "thumbnail":    r["thumbnail"] or "",
            "duration":     r["duration"] or "",
            "category":     r["category"] or 1,
        })
    return jsonify({
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "has_more": (offset + per_page) < total,
        "items":    items,
    })


@app.route("/api/benefits")
def api_benefits():
    """Return active benefits grouped by category as JSON."""
    rows = query("SELECT * FROM benefits WHERE status=1 ORDER BY category, sort_order")
    grouped = {1: [], 2: [], 3: []}
    for r in rows:
        cat = r.get("category", 1) or 1
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "id":          r["id"],
            "title":       r["title"],
            "description": r["description"],
            "icon_svg":    r["icon_svg"],
            "sort_order":  r["sort_order"],
        })
    return jsonify({
        "dropshipping": grouped[1],
        "ecommerce":    grouped[2],
        "online_earning": grouped[3],
    })


@app.route("/api/webinars")
def api_webinars():
    """Return active webinars as JSON for dynamic front-end use."""
    rows = query("SELECT * FROM mdt_webinars WHERE webinar_status=1 ORDER BY webinar_id")
    webinars = []
    for r in rows:
        webinars.append({
            "id":             r["webinar_id"],
            "name":           r["webinar_name"],
            "slug":           r["webinar_slug"],
            "category":       r["webinar_categories"],
            "platform":       r["webinar_platform"],
            "language":       r["webinar_lanuage"],
            "description":    r["webinar_discription"],
            "fees":           r["webinar_fees"],
            "discount":       r["webinar_discount"],
            "offer_title":    r["webinar_offer_title"],
            "starting_time":  r["webinar_startingtime"],
            "schedule_type":  r["webinar_scheduletype"],
            "video":          r["webinar_video"],
            "status":         r["webinar_status"],
        })
    return jsonify({"count": len(webinars), "webinars": webinars})


@app.route("/lead", methods=["POST"])
def lead():
    name     = request.form.get("name",     "").strip()
    email    = request.form.get("email",    "").strip()
    phone    = request.form.get("phone",    "").strip()
    interest = request.form.get("interest", "").strip()
    if not name or not phone:
        return ("", 400)
    message = f"[MAYA OS Lead] Interest: {interest}" if interest else "[MAYA OS Lead]"
    send_email(name, email or "—", phone, message)
    return ("", 204)



@app.route("/reviews")
def reviews():
    return render_template("reviews.html")


@app.route("/checkout")
def checkout():
    return redirect(url_for("onboarding"))

@app.route("/onboarding")
def onboarding():
    webinar_id   = request.args.get("webinar_id", "")
    webinar_name = request.args.get("webinar_name", "")
    webinar_slug = request.args.get("webinar_slug", "")
    return render_template("onboarding.html",
        webinar_id=webinar_id,
        webinar_name=webinar_name,
        webinar_slug=webinar_slug,
    )

@app.route("/api/enquiry", methods=["POST"])
def api_enquiry():
    data = request.get_json(silent=True) or {}
    full_name    = (data.get("full_name") or "").strip()
    email        = (data.get("email") or "").strip()
    phone        = (data.get("phone") or "").strip()
    city         = (data.get("city") or "").strip()
    webinar_id   = data.get("webinar_id") or None
    webinar_name = (data.get("webinar_name") or "").strip() or None
    webinar_slug = (data.get("webinar_slug") or "").strip() or None
    source       = (data.get("source") or "homepage").strip()

    errors = {}
    if not full_name:
        errors["full_name"] = "Name is required"
    if not email or "@" not in email:
        errors["email"] = "Valid email is required"
    if not phone or len(phone.replace(" ", "").replace("-", "")) < 10:
        errors["phone"] = "Valid 10-digit phone number is required"
    if errors:
        return jsonify({"success": False, "errors": errors}), 422

    try:
        wid = int(webinar_id) if webinar_id else None
    except (ValueError, TypeError):
        wid = None

    execute(
        "INSERT INTO enquiries (full_name, email, phone, city, webinar_id, webinar_name, webinar_slug, source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (full_name, email, phone, city or None, wid, webinar_name, webinar_slug, source)
    )
    return jsonify({"success": True, "message": "Registration successful!"})


@app.route("/thank-you")
def thank_you():
    status = request.args.get("status", "")
    return render_template("thank-you.html", status=status)


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")


@app.route("/refund-policy")
def refund_policy():
    return render_template("refund-policy.html")


@app.route("/terms-of-use")
def terms_of_use():
    return render_template("terms-of-use.html")


@app.route("/video-reviews")
def video_reviews_page():
    return render_template("video-reviews.html")


@app.route("/webinar/<slug>")
def webinar_detail(slug):
    # ── Per-category static content (topics, curriculum, who_for, faqs) ────────
    _CAT = {
        1: {
            "color": "orange", "accent": "#ff8c1a", "glow": "rgba(255,140,26,0.18)",
            "type_tag": "🛒 Dropshipping Webinar",
            "subtitle": "Build a Dropshipping Store From Scratch",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_08.55.31_-_A_modern_dropshipping_concept_image_showing_a_mobile_phone_with_a_shopping_app_interface_featuring_a_variety_of_products_like_clothing_electronics.webp?v=1727325143&width=1500",
            "topics": [
                {"icon": "🔍", "title": "Product Research",   "desc": "Find winning products & profitable niches using free tools"},
                {"icon": "🏪", "title": "Store Setup",         "desc": "Build a professional Shopify/WooCommerce store step by step"},
                {"icon": "🤝", "title": "Indian Suppliers",    "desc": "Connect with reliable Indian suppliers & wholesalers"},
                {"icon": "📦", "title": "Order Fulfilment",    "desc": "Automate order processing without touching inventory"},
                {"icon": "📣", "title": "Ads & Marketing",     "desc": "Run profitable Facebook & Instagram ads for your store"},
                {"icon": "💰", "title": "Profit Strategy",     "desc": "Set pricing, manage margins, and scale to ₹50K/month"},
            ],
            "who_for": [
                {"icon": "🎓", "label": "Students & Freshers",     "desc": "Earn while you study without quitting college"},
                {"icon": "👩‍💼", "label": "Job Seekers",           "desc": "Build a business while searching for a job"},
                {"icon": "🏠", "label": "Homemakers",              "desc": "Run a store from home on your own schedule"},
                {"icon": "👨‍💻", "label": "Working Professionals", "desc": "Build a side income alongside your 9-to-5"},
            ],
            "curriculum": [
                {"step": "01", "title": "Introduction to Dropshipping", "points": ["What is dropshipping & why it works in India", "Success stories from Kannada students"]},
                {"step": "02", "title": "Finding Winning Products",     "points": ["Product research tools (free & paid)", "Niche selection strategy"]},
                {"step": "03", "title": "Building Your Store",          "points": ["Platform setup walkthrough (live demo)", "Branding & design basics"]},
                {"step": "04", "title": "Getting Your First Order",     "points": ["Listing products correctly", "Running your first ad campaign"]},
            ],
            "faqs": [
                {"q": "Do I need any investment to start dropshipping?",    "a": "You only need a small amount for your store subscription and initial ad spend. No inventory cost. Many students start with less than ₹5,000."},
                {"q": "Can I do this while working a full-time job?",       "a": "Absolutely! Dropshipping can be managed part-time. Many of our students run their stores in 1–2 hours a day."},
                {"q": "Is this workshop only in Kannada?",                  "a": "The workshop is conducted in Kannada & English so everyone from Karnataka can follow along comfortably."},
                {"q": "Will I get a recording if I miss the live session?", "a": "Yes, registered participants get access to the session recording within 24 hours after the live workshop."},
                {"q": "What is your refund policy?",                        "a": "We offer a 200% money-back guarantee. If you don't find the workshop valuable, we'll refund your full amount — no questions asked."},
            ],
        },
        2: {
            "color": "blue", "accent": "#3b82f6", "glow": "rgba(59,130,246,0.18)",
            "type_tag": "🏪 E-Commerce Webinar",
            "subtitle": "Launch & Scale Your E-Commerce Business",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_22.00.40_-_An_e-commerce_concept_image_representing_Amazon_Flipkart_and_Meesho._The_image_features_the_logos_of_these_platforms_placed_above_a_variety_of_produ.webp?v=1769059036&width=1500",
            "topics": [
                {"icon": "🏬", "title": "Platform Selection",   "desc": "Choose the right platform — Amazon, Flipkart or Meesho"},
                {"icon": "📝", "title": "Listing Optimization", "desc": "Write product listings that rank and convert"},
                {"icon": "💸", "title": "Pricing & Margins",    "desc": "Set competitive prices while maintaining healthy profit"},
                {"icon": "📊", "title": "Catalogue Management", "desc": "Manage your product catalogue like a professional seller"},
                {"icon": "🔄", "title": "Returns & RTO",        "desc": "Handle returns and reduce RTO losses effectively"},
                {"icon": "📈", "title": "Scaling to ₹1L/month","desc": "Strategies to grow from first sale to consistent income"},
            ],
            "who_for": [
                {"icon": "🏭", "label": "Small Manufacturers", "desc": "Sell your products directly to millions online"},
                {"icon": "🛍️", "label": "Resellers",          "desc": "Source products and sell them at a profit on major platforms"},
                {"icon": "👩‍💼", "label": "Entrepreneurs",     "desc": "Launch a full-fledged e-commerce brand from scratch"},
                {"icon": "🎓", "label": "Beginners",           "desc": "No prior experience needed — we start from the basics"},
            ],
            "curriculum": [
                {"step": "01", "title": "E-Commerce Fundamentals",   "points": ["How Indian e-commerce platforms work", "Seller account registration walkthrough"]},
                {"step": "02", "title": "Product & Catalogue Setup", "points": ["Product photography tips", "Writing SEO-optimised product titles & descriptions"]},
                {"step": "03", "title": "Pricing & Inventory",       "points": ["Pricing formulas for profit", "Managing stock and warehouse logistics"]},
                {"step": "04", "title": "Growth & Scaling",          "points": ["Platform ads (Sponsored listings)", "Handling reviews and growing seller rating"]},
            ],
            "faqs": [
                {"q": "Which platform is best to start — Amazon, Flipkart or Meesho?", "a": "It depends on your product category and budget. We cover all three platforms and help you choose the right one for your specific situation."},
                {"q": "Do I need GST registration to sell online?",  "a": "For most platforms in India, a GST number is required. We guide you through the registration process during the workshop."},
                {"q": "How much initial investment is needed?",       "a": "You can start selling on Meesho with near-zero investment. For Amazon/Flipkart, ₹10,000–₹20,000 is a comfortable starting point."},
                {"q": "Can I sell from a small town or rural area?", "a": "Yes! As long as you have internet access and a bank account, you can sell from anywhere in India."},
                {"q": "Will I get support after the workshop?",      "a": "Yes. You get access to our private community where you can ask questions and get guidance from mentors and fellow students."},
            ],
        },
        3: {
            "color": "green", "accent": "#22c55e", "glow": "rgba(34,197,94,0.18)",
            "type_tag": "💰 Online Earning Webinar",
            "subtitle": "Master Multiple Ways to Earn Money Online",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_08.54.19_-_A_vibrant_and_dynamic_image_representing_dropshipping._It_includes_a_globe_in_the_background_with_various_shopping_carts_boxes_and_package_icons_aro.webp?v=1727325076&width=1500",
            "topics": [
                {"icon": "💻", "title": "Freelancing",               "desc": "Get clients on Fiverr, Upwork & LinkedIn from India"},
                {"icon": "🔗", "title": "Affiliate Marketing",       "desc": "Earn commissions by promoting products you love"},
                {"icon": "📱", "title": "Social Media Monetization", "desc": "Turn Instagram & YouTube into income streams"},
                {"icon": "📦", "title": "Digital Products",          "desc": "Create and sell eBooks, templates & courses"},
                {"icon": "🤖", "title": "AI Tools for Income",       "desc": "Use AI tools to work faster and earn more"},
                {"icon": "🌐", "title": "Passive Income Setup",      "desc": "Build systems that earn even while you sleep"},
            ],
            "who_for": [
                {"icon": "🎓", "label": "Students",                "desc": "Earn from your laptop during college hours"},
                {"icon": "👩‍🎨", "label": "Creative Professionals", "desc": "Monetize your skills in design, writing, or video"},
                {"icon": "👨‍💼", "label": "Job Seekers",            "desc": "Earn while searching — build income independence"},
                {"icon": "🏠", "label": "Stay-at-Home Parents",    "desc": "Work on your own time from home"},
            ],
            "curriculum": [
                {"step": "01", "title": "Online Earning Mindset",     "points": ["Why most people fail online & how to avoid it", "Choosing the right income stream for your skills"]},
                {"step": "02", "title": "Freelancing & Gig Work",     "points": ["Setting up profiles on Fiverr & Upwork", "Landing your first paid client"]},
                {"step": "03", "title": "Affiliate & Content Income", "points": ["How affiliate marketing works in India", "Starting a YouTube channel or blog for income"]},
                {"step": "04", "title": "Scaling & Automating",       "points": ["Creating digital products for passive income", "Using AI tools to multiply your output"]},
            ],
            "faqs": [
                {"q": "How soon can I start earning after the workshop?", "a": "Many students land their first freelance client or affiliate sale within 2–4 weeks of applying what they learn. Results depend on effort and consistency."},
                {"q": "Do I need special skills or a degree?",            "a": "No degree needed. We teach you how to identify and monetize the skills you already have, and how to learn new ones quickly."},
                {"q": "Is affiliate marketing legal in India?",           "a": "Yes, affiliate marketing is completely legal in India. We cover compliant practices and help you choose legitimate affiliate programs."},
                {"q": "How much can I realistically earn?",               "a": "Beginners typically earn ₹5,000–₹20,000/month within the first 3 months. With consistency, many of our students reach ₹50,000+/month."},
                {"q": "Do I need a website to start earning online?",     "a": "Not necessarily. You can start earning through freelancing platforms and social media without a website. We cover both options."},
            ],
        },
    }

    # ── 1. Try DB first (slug stored per webinar) ───────────────────────────────
    row = query("SELECT * FROM mdt_webinars WHERE webinar_slug=%s AND webinar_status=1", (slug,), one=True)
    if row:
        cat = int(row.get("webinar_categories") or 1)
        cc  = _CAT.get(cat, _CAT[1])
        fees = row.get("webinar_fees") or 49
        desc = (row.get("webinar_discription") or "").strip()
        webinar = {
            "id":          row["webinar_id"],
            "slug":        slug,
            "color":       cc["color"],
            "accent":      cc["accent"],
            "glow":        cc["glow"],
            "type_tag":    cc["type_tag"],
            "title":       row["webinar_name"],
            "subtitle":    desc[:100] if desc else cc["subtitle"],
            "description": desc or cc["subtitle"],
            "schedule":    row.get("webinar_startingtime") or "",
            "time":        row.get("webinar_startingtime") or "",
            "platform":    row.get("webinar_platform") or "Zoom",
            "language":    row.get("webinar_lanuage") or "Kannada & English",
            "duration":    "3+ Hours",
            "price":       f"₹{fees}/-",
            "youtube_id":  cc["youtube_id"],
            "image":       cc["image"],
            "meta_title":  f"{row['webinar_name']} – MayaPreneur",
            "meta_desc":   desc or f"Join the {row['webinar_name']} live workshop on {row.get('webinar_platform','Zoom')}. Register now.",
            "topics":      cc["topics"],
            "who_for":     cc["who_for"],
            "curriculum":  cc["curriculum"],
            "faqs":        cc["faqs"],
        }
        return render_template("webinar-detail.html", w=webinar)

    # ── 2. Hardcoded fallback (backward compat for old slugs) ───────────────────
    webinars = {
        "dropshipping-mastery": {
            "id": None, "slug": "dropshipping-mastery",
            "color": "orange",
            "accent": "#ff8c1a",
            "glow": "rgba(255,140,26,0.18)",
            "type_tag": "🛒 Dropshipping Webinar",
            "title": "Dropshipping Mastery Workshop",
            "subtitle": "Build a Dropshipping Store From Scratch",
            "description": "India's first live Dropshipping workshop in Kannada. Learn how to set up your own online store, source winning products, and start earning — without holding any inventory. Completely beginner-friendly.",
            "schedule": "Every Monday",
            "time": "7 PM IST",
            "platform": "Zoom",
            "language": "Kannada & English",
            "duration": "3+ Hours",
            "price": "₹49/-",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_08.55.31_-_A_modern_dropshipping_concept_image_showing_a_mobile_phone_with_a_shopping_app_interface_featuring_a_variety_of_products_like_clothing_electronics.webp?v=1727325143&width=1500",
            "meta_title": "Dropshipping Mastery Live Workshop in Kannada – MayaPreneur",
            "meta_desc": "Join India's first live Dropshipping workshop in Kannada. Learn to build a store, find products & earn online. Every Monday 7 PM on Zoom. Register at ₹49.",
            "topics": [
                {"icon": "🔍", "title": "Product Research",    "desc": "Find winning products & profitable niches using free tools"},
                {"icon": "🏪", "title": "Store Setup",          "desc": "Build a professional Shopify/WooCommerce store step by step"},
                {"icon": "🤝", "title": "Indian Suppliers",     "desc": "Connect with reliable Indian suppliers & wholesalers"},
                {"icon": "📦", "title": "Order Fulfilment",     "desc": "Automate order processing without touching inventory"},
                {"icon": "📣", "title": "Ads & Marketing",      "desc": "Run profitable Facebook & Instagram ads for your store"},
                {"icon": "💰", "title": "Profit Strategy",      "desc": "Set pricing, manage margins, and scale to ₹50K/month"},
            ],
            "who_for": [
                {"icon": "🎓", "label": "Students & Freshers",      "desc": "Earn while you study without quitting college"},
                {"icon": "👩‍💼", "label": "Job Seekers",            "desc": "Build a business while searching for a job"},
                {"icon": "🏠", "label": "Homemakers",               "desc": "Run a store from home on your own schedule"},
                {"icon": "👨‍💻", "label": "Working Professionals",  "desc": "Build a side income alongside your 9-to-5"},
            ],
            "curriculum": [
                {"step": "01", "title": "Introduction to Dropshipping", "points": ["What is dropshipping & why it works in India", "Success stories from Kannada students"]},
                {"step": "02", "title": "Finding Winning Products",     "points": ["Product research tools (free & paid)", "Niche selection strategy"]},
                {"step": "03", "title": "Building Your Store",          "points": ["Platform setup walkthrough (live demo)", "Branding & design basics"]},
                {"step": "04", "title": "Getting Your First Order",     "points": ["Listing products correctly", "Running your first ad campaign"]},
            ],
            "faqs": [
                {"q": "Do I need any investment to start dropshipping?",    "a": "You only need a small amount for your store subscription and initial ad spend. No inventory cost. Many students start with less than ₹5,000."},
                {"q": "Can I do this while working a full-time job?",       "a": "Absolutely! Dropshipping can be managed part-time. Many of our students run their stores in 1–2 hours a day."},
                {"q": "Is this workshop only in Kannada?",                  "a": "The workshop is conducted in Kannada & English so everyone from Karnataka can follow along comfortably."},
                {"q": "Will I get a recording if I miss the live session?", "a": "Yes, registered participants get access to the session recording within 24 hours after the live workshop."},
                {"q": "What is your refund policy?",                        "a": "We offer a 200% money-back guarantee. If you don't find the workshop valuable, we'll refund your full amount — no questions asked."},
            ],
        },
        "ecommerce-business": {
            "id": None, "slug": "ecommerce-business",
            "color": "blue",
            "accent": "#3b82f6",
            "glow": "rgba(59,130,246,0.18)",
            "type_tag": "🏪 E-Commerce Webinar",
            "title": "E-Commerce Business Workshop",
            "subtitle": "Launch & Scale Your E-Commerce Business",
            "description": "Learn to sell on Amazon, Flipkart, and Meesho with expert guidance. From store setup and product listing to pricing strategy and scaling — all taught live in Kannada & English.",
            "schedule": "Every Wednesday",
            "time": "7 PM IST",
            "platform": "Zoom",
            "language": "Kannada & English",
            "duration": "3+ Hours",
            "price": "₹49/-",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_22.00.40_-_An_e-commerce_concept_image_representing_Amazon_Flipkart_and_Meesho._The_image_features_the_logos_of_these_platforms_placed_above_a_variety_of_produ.webp?v=1769059036&width=1500",
            "meta_title": "E-Commerce Business Live Workshop in Kannada – MayaPreneur",
            "meta_desc": "Learn to sell on Amazon, Flipkart & Meesho in Kannada. Live workshop every Wednesday 7 PM on Zoom. Store setup, listings & scaling. Register at ₹49.",
            "topics": [
                {"icon": "🏬", "title": "Platform Selection",      "desc": "Choose the right platform — Amazon, Flipkart or Meesho"},
                {"icon": "📝", "title": "Listing Optimization",    "desc": "Write product listings that rank and convert"},
                {"icon": "💸", "title": "Pricing & Margins",       "desc": "Set competitive prices while maintaining healthy profit"},
                {"icon": "📊", "title": "Catalogue Management",    "desc": "Manage your product catalogue like a professional seller"},
                {"icon": "🔄", "title": "Returns & RTO",           "desc": "Handle returns and reduce RTO losses effectively"},
                {"icon": "📈", "title": "Scaling to ₹1L/month",   "desc": "Strategies to grow from first sale to consistent income"},
            ],
            "who_for": [
                {"icon": "🏭", "label": "Small Manufacturers",  "desc": "Sell your products directly to millions online"},
                {"icon": "🛍️", "label": "Resellers",           "desc": "Source products and sell them at a profit on major platforms"},
                {"icon": "👩‍💼", "label": "Entrepreneurs",      "desc": "Launch a full-fledged e-commerce brand from scratch"},
                {"icon": "🎓", "label": "Beginners",            "desc": "No prior experience needed — we start from the basics"},
            ],
            "curriculum": [
                {"step": "01", "title": "E-Commerce Fundamentals",   "points": ["How Indian e-commerce platforms work", "Seller account registration walkthrough"]},
                {"step": "02", "title": "Product & Catalogue Setup", "points": ["Product photography tips", "Writing SEO-optimised product titles & descriptions"]},
                {"step": "03", "title": "Pricing & Inventory",       "points": ["Pricing formulas for profit", "Managing stock and warehouse logistics"]},
                {"step": "04", "title": "Growth & Scaling",          "points": ["Platform ads (Sponsored listings)", "Handling reviews and growing seller rating"]},
            ],
            "faqs": [
                {"q": "Which platform is best to start — Amazon, Flipkart or Meesho?", "a": "It depends on your product category and budget. We cover all three platforms and help you choose the right one for your specific situation."},
                {"q": "Do I need GST registration to sell online?",    "a": "For most platforms in India, a GST number is required. We guide you through the registration process during the workshop."},
                {"q": "How much initial investment is needed?",         "a": "You can start selling on Meesho with near-zero investment. For Amazon/Flipkart, ₹10,000–₹20,000 is a comfortable starting point."},
                {"q": "Can I sell from a small town or rural area?",   "a": "Yes! As long as you have internet access and a bank account, you can sell from anywhere in India."},
                {"q": "Will I get support after the workshop?",        "a": "Yes. You get access to our private community where you can ask questions and get guidance from mentors and fellow students."},
            ],
        },
        "online-earning": {
            "id": None, "slug": "online-earning",
            "color": "green",
            "accent": "#22c55e",
            "glow": "rgba(34,197,94,0.18)",
            "type_tag": "💰 Online Earning Webinar",
            "title": "Online Earning Streams Workshop",
            "subtitle": "Master Multiple Ways to Earn Money Online",
            "description": "Discover proven methods to earn money online — freelancing, affiliate marketing, digital products, and social media monetization. Learn practical strategies that work for Indians, taught live in Kannada & English.",
            "schedule": "Every Sunday",
            "time": "6 PM IST",
            "platform": "Zoom",
            "language": "Kannada & English",
            "duration": "3+ Hours",
            "price": "₹49/-",
            "youtube_id": "OCDUN0Oudtk",
            "image": "https://mayapreneurs.online/cdn/shop/files/DALL_E_2024-09-19_08.54.19_-_A_vibrant_and_dynamic_image_representing_dropshipping._It_includes_a_globe_in_the_background_with_various_shopping_carts_boxes_and_package_icons_aro.webp?v=1727325076&width=1500",
            "meta_title": "Online Earning Streams Live Workshop in Kannada – MayaPreneur",
            "meta_desc": "Learn freelancing, affiliate marketing & digital products in Kannada. Live workshop every Sunday 6 PM on Zoom. Multiple income streams. Register at ₹49.",
            "topics": [
                {"icon": "💻", "title": "Freelancing",              "desc": "Get clients on Fiverr, Upwork & LinkedIn from India"},
                {"icon": "🔗", "title": "Affiliate Marketing",      "desc": "Earn commissions by promoting products you love"},
                {"icon": "📱", "title": "Social Media Monetization","desc": "Turn Instagram & YouTube into income streams"},
                {"icon": "📦", "title": "Digital Products",         "desc": "Create and sell eBooks, templates & courses"},
                {"icon": "🤖", "title": "AI Tools for Income",      "desc": "Use AI tools to work faster and earn more"},
                {"icon": "🌐", "title": "Passive Income Setup",     "desc": "Build systems that earn even while you sleep"},
            ],
            "who_for": [
                {"icon": "🎓", "label": "Students",               "desc": "Earn from your laptop during college hours"},
                {"icon": "👩‍🎨", "label": "Creative Professionals","desc": "Monetize your skills in design, writing, or video"},
                {"icon": "👨‍💼", "label": "Job Seekers",           "desc": "Earn while searching — build income independence"},
                {"icon": "🏠", "label": "Stay-at-Home Parents",   "desc": "Work on your own time from home"},
            ],
            "curriculum": [
                {"step": "01", "title": "Online Earning Mindset",       "points": ["Why most people fail online & how to avoid it", "Choosing the right income stream for your skills"]},
                {"step": "02", "title": "Freelancing & Gig Work",       "points": ["Setting up profiles on Fiverr & Upwork", "Landing your first paid client"]},
                {"step": "03", "title": "Affiliate & Content Income",   "points": ["How affiliate marketing works in India", "Starting a YouTube channel or blog for income"]},
                {"step": "04", "title": "Scaling & Automating",         "points": ["Creating digital products for passive income", "Using AI tools to multiply your output"]},
            ],
            "faqs": [
                {"q": "How soon can I start earning after the workshop?", "a": "Many students land their first freelance client or affiliate sale within 2–4 weeks of applying what they learn. Results depend on effort and consistency."},
                {"q": "Do I need special skills or a degree?",            "a": "No degree needed. We teach you how to identify and monetize the skills you already have, and how to learn new ones quickly."},
                {"q": "Is affiliate marketing legal in India?",           "a": "Yes, affiliate marketing is completely legal in India. We cover compliant practices and help you choose legitimate affiliate programs."},
                {"q": "How much can I realistically earn?",               "a": "Beginners typically earn ₹5,000–₹20,000/month within the first 3 months. With consistency, many of our students reach ₹50,000+/month."},
                {"q": "Do I need a website to start earning online?",     "a": "Not necessarily. You can start earning through freelancing platforms and social media without a website. We cover both options."},
            ],
        },
    }
    webinar = webinars.get(slug)
    if not webinar:
        return redirect(url_for("maya_preneur"))
    return render_template("webinar-detail.html", w=webinar)


@app.route("/contact-us")
def contact_page():
    return render_template("contact.html")


@app.route("/contact", methods=["POST"])
def contact():
    name    = request.form.get("name",    "").strip()
    email   = request.form.get("email",   "").strip()
    phone   = request.form.get("phone",   "").strip()
    message = request.form.get("message", "").strip()
    subject = request.form.get("subject", "").strip()
    if subject:
        message = f"[{subject}]\n{message}" if message else f"[{subject}]"

    if not name or not email or not phone:
        return redirect(url_for("contact_page") + "?error=missing_fields")

    success = send_email(name, email, phone, message)
    if success:
        return redirect(url_for("contact_page") + "?status=success")
    else:
        return redirect(url_for("contact_page") + "?error=email_failed")


if __name__ == "__main__":
    app.run(debug=True)
