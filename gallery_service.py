"""
Gallery service — DB queries for the gallery table.

Actual table schema:
  id, title, media_type, media_path, thumbnail,
  section, gallery_type (1=session, 2=success, 3=student), status, created_at
"""
from db import query

# Maps filter tab name → gallery_type integer in DB
TYPE_MAP = {
    "session": 1,
    "success": 2,
    "student": 3,
}

# Reverse map for serialisation
TYPE_LABEL = {v: k for k, v in TYPE_MAP.items()}


def get_gallery_items(type_filter: str | None = None, limit: int = 8, offset: int = 0) -> list[dict]:
    """
    Return active gallery items with pagination, optionally filtered by type.
    type_filter: 'session' | 'student' | 'success' | None (= all)
    """
    if type_filter and type_filter in TYPE_MAP:
        rows = query(
            "SELECT * FROM gallery WHERE status=1 AND gallery_type=%s ORDER BY id LIMIT %s OFFSET %s",
            (TYPE_MAP[type_filter], limit, offset),
        )
    else:
        rows = query(
            "SELECT * FROM gallery WHERE status=1 ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset),
        )
    return rows or []


def count_gallery_items(type_filter: str | None = None) -> int:
    """Return total count of active gallery items (for pagination)."""
    if type_filter and type_filter in TYPE_MAP:
        row = query(
            "SELECT COUNT(*) AS n FROM gallery WHERE status=1 AND gallery_type=%s",
            (TYPE_MAP[type_filter],), one=True,
        )
    else:
        row = query("SELECT COUNT(*) AS n FROM gallery WHERE status=1", one=True)
    return row["n"] if row else 0


def get_gallery_types() -> list[str]:
    """Return distinct type labels present in the gallery table."""
    rows = query(
        "SELECT DISTINCT gallery_type FROM gallery WHERE status=1 ORDER BY gallery_type"
    )
    return [TYPE_LABEL[r["gallery_type"]] for r in rows if r["gallery_type"] in TYPE_LABEL] if rows else []
