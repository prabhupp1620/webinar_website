"""
Gallery blueprint — /gallery and /api/gallery/*
"""
from flask import Blueprint, jsonify, render_template, request
from gallery_service import get_gallery_items, get_gallery_types, count_gallery_items, TYPE_LABEL

gallery_bp = Blueprint("gallery", __name__)


# ── Page route ────────────────────────────────────────────────────────────────
@gallery_bp.route("/gallery")
def gallery():
    return render_template("gallery.html")


# ── API: all items (optional ?type= filter) ───────────────────────────────────
@gallery_bp.route("/api/gallery")
def api_gallery():
    """
    GET /api/gallery
    GET /api/gallery?type=session
    GET /api/gallery?type=student
    GET /api/gallery?type=success

    Returns JSON:
    {
        "items": [
            {
                "id": 1,
                "title": "Live Workshop",
                "subtitle": "Dropshipping Masterclass",
                "image_url": "uploads/img.jpg",
                "type": "session",
                "layout": "large"
            },
            ...
        ]
    }
    """
    type_filter = request.args.get("type",   "all").strip().lower()
    limit       = min(int(request.args.get("limit",  8)),  50)  # cap at 50
    offset      = max(int(request.args.get("offset", 0)),  0)
    tf          = type_filter if type_filter != "all" else None

    try:
        items = get_gallery_items(tf, limit, offset)
        total = count_gallery_items(tf)
    except Exception as e:
        return jsonify({"items": [], "has_more": False, "error": str(e)}), 200

    result = []
    for item in items:
        result.append({
            "id":        item["id"],
            "title":     item["title"],
            "subtitle":  item.get("thumbnail") or "",
            "image_url": item["media_path"],
            "type":      TYPE_LABEL.get(item.get("gallery_type"), "student"),
            "layout":    "normal",
        })

    return jsonify({"items": result, "has_more": (offset + limit) < total, "total": total})


# ── API: available filter types ───────────────────────────────────────────────
@gallery_bp.route("/api/gallery/types")
def api_gallery_types():
    """
    GET /api/gallery/types
    Returns the distinct types present in the gallery table.
    { "types": ["session", "student", "success"] }
    """
    types = get_gallery_types()
    return jsonify({"types": types})
