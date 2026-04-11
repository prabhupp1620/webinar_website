"""
Admin blueprint — /admin/*
All routes require login (session['admin_id']).
"""
import os
import functools
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, session, flash, g
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from db import query, execute

admin_bp = Blueprint("admin", __name__, template_folder="templates/admin")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_IMG = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_VID = {"mp4", "mov", "avi", "webm", "mkv"}


# ── Helpers ───────────────────────────────────────────────────────────────────
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


def save_upload(field_name):
    """Save uploaded image, return relative path or None."""
    file = request.files.get(field_name)
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_IMG:
            fname = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, fname))
            return f"uploads/{fname}"
    return None


def save_video(field_name):
    """Save uploaded video file, return relative path or None."""
    file = request.files.get(field_name)
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED_VID:
            fname = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, fname))
            return f"uploads/{fname}"
    return None


# ── Auth ──────────────────────────────────────────────────────────────────────
@admin_bp.route("/", methods=["GET", "POST"])
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = query("SELECT * FROM admin_users WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user["password"], password):
            session["admin_id"]    = user["id"]
            session["admin_email"] = user["email"]
            return redirect(url_for("admin.dashboard"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "webinars":        query("SELECT COUNT(*) AS n FROM mdt_webinars",   one=True)["n"],
        "student_results": query("SELECT COUNT(*) AS n FROM student_results",one=True)["n"],
        "video_reviews":   query("SELECT COUNT(*) AS n FROM video_reviews",  one=True)["n"],
        "benefits":        query("SELECT COUNT(*) AS n FROM benefits",       one=True)["n"],
        "testimonials":    query("SELECT COUNT(*) AS n FROM testimonials",   one=True)["n"],
        "faqs":            query("SELECT COUNT(*) AS n FROM faqs",           one=True)["n"],
        "gallery":         query("SELECT COUNT(*) AS n FROM gallery",        one=True)["n"],
    }
    return render_template("dashboard.html", stats=stats)


# ══════════════════════════════════════════════════════════════════════════════
# WEBINARS  (uses existing mdt_webinars table)
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/webinars")
@login_required
def webinars():
    rows = query("SELECT * FROM mdt_webinars ORDER BY webinar_id DESC")
    return render_template("webinars.html", rows=rows)


@admin_bp.route("/webinars/add", methods=["GET", "POST"])
@login_required
def webinar_add():
    if request.method == "POST":
        video_path = save_video("webinar_video_file") or request.form.get("webinar_video", "")
        stype    = int(request.form.get("webinar_scheduletype", 1))
        day      = request.form.get("webinar_day")      if stype == 2 else None
        wtime    = request.form.get("webinar_time", "") if stype in (1, 2) else ""
        wdatetime= request.form.get("webinar_datetime") if stype == 3 else None
        fees     = request.form.get("webinar_fees", 0) or 0
        slug = (request.form.get("webinar_slug") or "").strip().lower() or None
        execute(
            """INSERT INTO mdt_webinars
               (webinar_name, webinar_slug, webinar_scheduletype, webinar_day, webinar_time,
                webinar_startingtime, webinar_datetime, webinar_lanuage, webinar_platform,
                webinar_fees, webinar_discount, webinar_offer_title, webinar_categories,
                webinar_discription, webinar_video, webinar_status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                request.form["webinar_name"], slug, stype, day, wtime,
                request.form.get("webinar_startingtime", ""), wdatetime,
                request.form["webinar_lanuage"], request.form["webinar_platform"],
                fees, request.form.get("webinar_discount", 0),
                request.form.get("webinar_offer_title", ""),
                request.form["webinar_categories"],
                request.form.get("webinar_discription", ""),
                video_path, request.form.get("webinar_status", 1),
            ),
        )
        flash("Webinar added.", "success")
        return redirect(url_for("admin.webinars"))
    return render_template("webinar_form.html", row=None)


@admin_bp.route("/webinars/edit/<int:wid>", methods=["GET", "POST"])
@login_required
def webinar_edit(wid):
    row = query("SELECT * FROM mdt_webinars WHERE webinar_id=%s", (wid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.webinars"))
    if request.method == "POST":
        video_path = save_video("webinar_video_file") or request.form.get("webinar_video", row.get("webinar_video",""))
        stype     = int(request.form.get("webinar_scheduletype", 1))
        day       = request.form.get("webinar_day")      if stype == 2 else None
        wtime     = request.form.get("webinar_time", "") if stype in (1, 2) else ""
        wdatetime = request.form.get("webinar_datetime") if stype == 3 else None
        fees      = request.form.get("webinar_fees", 0) or 0
        slug = (request.form.get("webinar_slug") or "").strip().lower() or None
        execute(
            """UPDATE mdt_webinars SET
               webinar_name=%s, webinar_slug=%s,
               webinar_scheduletype=%s, webinar_day=%s, webinar_time=%s,
               webinar_startingtime=%s, webinar_datetime=%s,
               webinar_lanuage=%s, webinar_platform=%s, webinar_fees=%s,
               webinar_discount=%s, webinar_offer_title=%s,
               webinar_categories=%s, webinar_discription=%s,
               webinar_video=%s, webinar_status=%s, webinar_updateOn=NOW()
               WHERE webinar_id=%s""",
            (
                request.form["webinar_name"], slug, stype, day, wtime,
                request.form.get("webinar_startingtime", ""), wdatetime,
                request.form["webinar_lanuage"], request.form["webinar_platform"],
                fees, request.form.get("webinar_discount", 0),
                request.form.get("webinar_offer_title", ""),
                request.form["webinar_categories"],
                request.form.get("webinar_discription", ""),
                video_path, request.form.get("webinar_status", 1), wid,
            ),
        )
        flash("Webinar updated.", "success")
        return redirect(url_for("admin.webinars"))
    return render_template("webinar_form.html", row=row)


@admin_bp.route("/webinars/delete/<int:wid>", methods=["POST"])
@login_required
def webinar_delete(wid):
    execute("DELETE FROM mdt_webinars WHERE webinar_id=%s", (wid,))
    flash("Webinar deleted.", "success")
    return redirect(url_for("admin.webinars"))


# ══════════════════════════════════════════════════════════════════════════════
# HERO SLIDES
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/hero-slides")
@login_required
def hero_slides():
    rows = query("SELECT * FROM hero_slides ORDER BY sort_order")
    return render_template("hero_slides.html", rows=rows)


@admin_bp.route("/hero-slides/add", methods=["GET", "POST"])
@login_required
def hero_slide_add():
    if request.method == "POST":
        execute(
            """INSERT INTO hero_slides
               (webinar_slug,youtube_id,badge_text,badge_color,title,
                schedule,time_ist,platform,language,sort_order,status)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                request.form["webinar_slug"], request.form["youtube_id"],
                request.form["badge_text"],   request.form["badge_color"],
                request.form["title"],        request.form["schedule"],
                request.form["time_ist"],     request.form["platform"],
                request.form["language"],     request.form.get("sort_order", 0),
                request.form.get("status", 1),
            ),
        )
        flash("Slide added.", "success")
        return redirect(url_for("admin.hero_slides"))
    return render_template("hero_slide_form.html", row=None)


@admin_bp.route("/hero-slides/edit/<int:sid>", methods=["GET", "POST"])
@login_required
def hero_slide_edit(sid):
    row = query("SELECT * FROM hero_slides WHERE id=%s", (sid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.hero_slides"))
    if request.method == "POST":
        execute(
            """UPDATE hero_slides SET
               webinar_slug=%s,youtube_id=%s,badge_text=%s,badge_color=%s,
               title=%s,schedule=%s,time_ist=%s,platform=%s,language=%s,
               sort_order=%s,status=%s WHERE id=%s""",
            (
                request.form["webinar_slug"], request.form["youtube_id"],
                request.form["badge_text"],   request.form["badge_color"],
                request.form["title"],        request.form["schedule"],
                request.form["time_ist"],     request.form["platform"],
                request.form["language"],     request.form.get("sort_order", 0),
                request.form.get("status", 1), sid,
            ),
        )
        flash("Slide updated.", "success")
        return redirect(url_for("admin.hero_slides"))
    return render_template("hero_slide_form.html", row=row)


@admin_bp.route("/hero-slides/delete/<int:sid>", methods=["POST"])
@login_required
def hero_slide_delete(sid):
    execute("DELETE FROM hero_slides WHERE id=%s", (sid,))
    flash("Slide deleted.", "success")
    return redirect(url_for("admin.hero_slides"))


# ══════════════════════════════════════════════════════════════════════════════
# STUDENT RESULTS
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/student-results")
@login_required
def student_results():
    rows = query("SELECT * FROM student_results ORDER BY sort_order")
    return render_template("student_results.html", rows=rows)


@admin_bp.route("/student-results/add", methods=["GET", "POST"])
@login_required
def student_result_add():
    if request.method == "POST":
        img_path = save_upload("image_file") or request.form.get("image_path", "")
        execute(
            "INSERT INTO student_results (image_path, alt_text, status, category) VALUES (%s,%s,%s,%s)",
            (img_path, request.form.get("alt_text",""), request.form.get("status",1), request.form.get("category",0)),
        )
        flash("Student result added.", "success")
        return redirect(url_for("admin.student_results"))
    return render_template("student_result_form.html", row=None)


@admin_bp.route("/student-results/edit/<int:rid>", methods=["GET", "POST"])
@login_required
def student_result_edit(rid):
    row = query("SELECT * FROM student_results WHERE id=%s", (rid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.student_results"))
    if request.method == "POST":
        img_path = save_upload("image_file") or request.form.get("image_path", row["image_path"])
        execute(
            "UPDATE student_results SET image_path=%s, alt_text=%s, status=%s, category=%s WHERE id=%s",
            (img_path, request.form.get("alt_text",""), request.form.get("status",1), request.form.get("category",0), rid),
        )
        flash("Student result updated.", "success")
        return redirect(url_for("admin.student_results"))
    return render_template("student_result_form.html", row=row)


@admin_bp.route("/student-results/delete/<int:rid>", methods=["POST"])
@login_required
def student_result_delete(rid):
    execute("DELETE FROM student_results WHERE id=%s", (rid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.student_results"))


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO REVIEWS
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/video-reviews")
@login_required
def video_reviews():
    rows = query("SELECT * FROM video_reviews ORDER BY sort_order")
    return render_template("video_reviews.html", rows=rows)


@admin_bp.route("/video-reviews/add", methods=["GET", "POST"])
@login_required
def video_review_add():
    if request.method == "POST":
        thumb      = save_upload("thumb_file") or request.form.get("thumbnail", "")
        vid_upload = save_video("video_file")
        video_src  = vid_upload or request.form.get("video_src", "")
        video_type = "local" if vid_upload else request.form.get("video_type", "local")
        execute(
            """INSERT INTO video_reviews
               (student_name,student_role,video_type,video_src,thumbnail,duration,status,category)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                request.form["student_name"], request.form.get("student_role",""),
                video_type, video_src,
                thumb, request.form.get("duration",""),
                request.form.get("status",1), request.form.get("category",0),
            ),
        )
        flash("Video review added.", "success")
        return redirect(url_for("admin.video_reviews"))
    return render_template("video_review_form.html", row=None)


@admin_bp.route("/video-reviews/edit/<int:vid>", methods=["GET", "POST"])
@login_required
def video_review_edit(vid):
    row = query("SELECT * FROM video_reviews WHERE id=%s", (vid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.video_reviews"))
    if request.method == "POST":
        thumb      = save_upload("thumb_file") or request.form.get("thumbnail", row["thumbnail"])
        vid_upload = save_video("video_file")
        video_src  = vid_upload or request.form.get("video_src", row["video_src"])
        video_type = "local" if vid_upload else request.form.get("video_type", row["video_type"])
        execute(
            """UPDATE video_reviews SET
               student_name=%s,student_role=%s,video_type=%s,video_src=%s,
               thumbnail=%s,duration=%s,status=%s,category=%s WHERE id=%s""",
            (
                request.form["student_name"], request.form.get("student_role",""),
                video_type, video_src,
                thumb, request.form.get("duration",""),
                request.form.get("status",1), request.form.get("category",0), vid,
            ),
        )
        flash("Video review updated.", "success")
        return redirect(url_for("admin.video_reviews"))
    return render_template("video_review_form.html", row=row)


@admin_bp.route("/video-reviews/delete/<int:vid>", methods=["POST"])
@login_required
def video_review_delete(vid):
    execute("DELETE FROM video_reviews WHERE id=%s", (vid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.video_reviews"))


# ══════════════════════════════════════════════════════════════════════════════
# BENEFITS
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/benefits")
@login_required
def benefits():
    rows = query("SELECT * FROM benefits ORDER BY sort_order")
    return render_template("benefits.html", rows=rows)


@admin_bp.route("/benefits/add", methods=["GET", "POST"])
@login_required
def benefit_add():
    if request.method == "POST":
        execute(
            "INSERT INTO benefits (title,description,sort_order,status,category) VALUES (%s,%s,%s,%s,%s)",
            (request.form["title"], request.form.get("description",""),
             request.form.get("sort_order",0), request.form.get("status",1),
             request.form.get("category",0)),
        )
        flash("Benefit added.", "success")
        return redirect(url_for("admin.benefits"))
    return render_template("benefit_form.html", row=None)


@admin_bp.route("/benefits/edit/<int:bid>", methods=["GET", "POST"])
@login_required
def benefit_edit(bid):
    row = query("SELECT * FROM benefits WHERE id=%s", (bid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.benefits"))
    if request.method == "POST":
        execute(
            "UPDATE benefits SET title=%s, description=%s, sort_order=%s, status=%s, category=%s WHERE id=%s",
            (request.form["title"], request.form.get("description",""),
             request.form.get("sort_order",0), request.form.get("status",1),
             request.form.get("category",0), bid),
        )
        flash("Benefit updated.", "success")
        return redirect(url_for("admin.benefits"))
    return render_template("benefit_form.html", row=row)


@admin_bp.route("/benefits/delete/<int:bid>", methods=["POST"])
@login_required
def benefit_delete(bid):
    execute("DELETE FROM benefits WHERE id=%s", (bid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.benefits"))


# ══════════════════════════════════════════════════════════════════════════════
# TESTIMONIALS
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/testimonials")
@login_required
def testimonials():
    rows = query("SELECT * FROM testimonials ORDER BY sort_order")
    return render_template("testimonials.html", rows=rows)


@admin_bp.route("/testimonials/add", methods=["GET", "POST"])
@login_required
def testimonial_add():
    if request.method == "POST":
        execute(
            "INSERT INTO testimonials (student_name,review,rating,sort_order,status,category) VALUES (%s,%s,%s,%s,%s,%s)",
            (request.form["student_name"], request.form["review"],
             request.form.get("rating",5), request.form.get("sort_order",0),
             request.form.get("status",1), request.form.get("category",0)),
        )
        flash("Testimonial added.", "success")
        return redirect(url_for("admin.testimonials"))
    return render_template("testimonial_form.html", row=None)


@admin_bp.route("/testimonials/edit/<int:tid>", methods=["GET", "POST"])
@login_required
def testimonial_edit(tid):
    row = query("SELECT * FROM testimonials WHERE id=%s", (tid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.testimonials"))
    if request.method == "POST":
        execute(
            "UPDATE testimonials SET student_name=%s, review=%s, rating=%s, sort_order=%s, status=%s, category=%s WHERE id=%s",
            (request.form["student_name"], request.form["review"],
             request.form.get("rating",5), request.form.get("sort_order",0),
             request.form.get("status",1), request.form.get("category",0), tid),
        )
        flash("Testimonial updated.", "success")
        return redirect(url_for("admin.testimonials"))
    return render_template("testimonial_form.html", row=row)


@admin_bp.route("/testimonials/delete/<int:tid>", methods=["POST"])
@login_required
def testimonial_delete(tid):
    execute("DELETE FROM testimonials WHERE id=%s", (tid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.testimonials"))


# ══════════════════════════════════════════════════════════════════════════════
# FAQs
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/faqs")
@login_required
def faqs():
    rows = query("SELECT * FROM faqs ORDER BY sort_order")
    return render_template("faqs.html", rows=rows)


@admin_bp.route("/faqs/add", methods=["GET", "POST"])
@login_required
def faq_add():
    if request.method == "POST":
        execute(
            "INSERT INTO faqs (question,answer,sort_order,status,category) VALUES (%s,%s,%s,%s,%s)",
            (request.form["question"], request.form["answer"],
             request.form.get("sort_order",0), request.form.get("status",1),
             request.form.get("category",0)),
        )
        flash("FAQ added.", "success")
        return redirect(url_for("admin.faqs"))
    return render_template("faq_form.html", row=None)


@admin_bp.route("/faqs/edit/<int:fid>", methods=["GET", "POST"])
@login_required
def faq_edit(fid):
    row = query("SELECT * FROM faqs WHERE id=%s", (fid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.faqs"))
    if request.method == "POST":
        execute(
            "UPDATE faqs SET question=%s, answer=%s, sort_order=%s, status=%s, category=%s WHERE id=%s",
            (request.form["question"], request.form["answer"],
             request.form.get("sort_order",0), request.form.get("status",1),
             request.form.get("category",0), fid),
        )
        flash("FAQ updated.", "success")
        return redirect(url_for("admin.faqs"))
    return render_template("faq_form.html", row=row)


@admin_bp.route("/faqs/delete/<int:fid>", methods=["POST"])
@login_required
def faq_delete(fid):
    execute("DELETE FROM faqs WHERE id=%s", (fid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.faqs"))


# ══════════════════════════════════════════════════════════════════════════════
# GALLERY
# ══════════════════════════════════════════════════════════════════════════════
@admin_bp.route("/gallery")
@login_required
def gallery():
    rows = query("SELECT * FROM gallery ORDER BY id DESC")
    return render_template("admin_gallery.html", rows=rows)


@admin_bp.route("/gallery/add", methods=["GET", "POST"])
@login_required
def gallery_add():
    if request.method == "POST":
        media_type = request.form.get("media_type", "image")
        if media_type == "image":
            media_path = save_upload("media_file") or request.form.get("media_path", "")
        else:
            media_path = save_video("media_file") or request.form.get("media_path", "")
        thumb = save_upload("thumb_file") or request.form.get("thumbnail", "")
        execute(
            "INSERT INTO gallery (title, media_type, media_path, thumbnail, section, gallery_type, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (request.form.get("title",""), media_type, media_path, thumb,
             request.form.get("section", 0), request.form.get("gallery_type", 1), request.form.get("status", 1)),
        )
        flash("Gallery item added.", "success")
        return redirect(url_for("admin.gallery"))
    return render_template("admin_gallery_form.html", row=None)


@admin_bp.route("/gallery/edit/<int:gid>", methods=["GET", "POST"])
@login_required
def gallery_edit(gid):
    row = query("SELECT * FROM gallery WHERE id=%s", (gid,), one=True)
    if not row:
        flash("Not found.", "error"); return redirect(url_for("admin.gallery"))
    if request.method == "POST":
        media_type = request.form.get("media_type", "image")
        if media_type == "image":
            media_path = save_upload("media_file") or request.form.get("media_path", row["media_path"])
        else:
            media_path = save_video("media_file") or request.form.get("media_path", row["media_path"])
        thumb = save_upload("thumb_file") or request.form.get("thumbnail", row["thumbnail"])
        execute(
            "UPDATE gallery SET title=%s, media_type=%s, media_path=%s, thumbnail=%s, section=%s, gallery_type=%s, status=%s WHERE id=%s",
            (request.form.get("title",""), media_type, media_path, thumb,
             request.form.get("section", 0), request.form.get("gallery_type", 1), request.form.get("status", 1), gid),
        )
        flash("Gallery item updated.", "success")
        return redirect(url_for("admin.gallery"))
    return render_template("admin_gallery_form.html", row=row)


@admin_bp.route("/gallery/delete/<int:gid>", methods=["POST"])
@login_required
def gallery_delete(gid):
    execute("DELETE FROM gallery WHERE id=%s", (gid,))
    flash("Deleted.", "success")
    return redirect(url_for("admin.gallery"))
