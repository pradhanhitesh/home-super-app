import uuid
from flask import request, jsonify
from app.blueprints.notes import notes_bp
from app.middleware.auth import require_auth, get_current_db_user
from app.models.note import Note, NoteType
from app.models.note_category import NoteCategory
from app.extensions import db


# ─── Note Categories ─────────────────────────────────────────────────────────

@notes_bp.get("/categories")
@require_auth
def list_categories():
    user = get_current_db_user()
    cats = NoteCategory.query.filter_by(household_id=user.household_id).order_by(NoteCategory.name).all()
    return jsonify([c.to_dict() for c in cats])


@notes_bp.post("/categories")
@require_auth
def create_category():
    user = get_current_db_user()
    if not user.is_admin:
        return jsonify({"error": "Admin only"}), 403

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400

    cat = NoteCategory(
        name=name,
        color=data.get("color", "#6366f1"),
        icon=data.get("icon", "bi-tag"),
        household_id=user.household_id,
        created_by=user.id,
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@notes_bp.put("/categories/<uuid:cat_id>")
@require_auth
def update_category(cat_id):
    user = get_current_db_user()
    if not user.is_admin:
        return jsonify({"error": "Admin only"}), 403

    cat = NoteCategory.query.filter_by(id=cat_id, household_id=user.household_id).first()
    if not cat:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json() or {}
    if "name" in data:
        n = (data["name"] or "").strip()
        if n:
            cat.name = n
    if "color" in data and data["color"]:
        cat.color = data["color"]
    if "icon" in data and data["icon"]:
        cat.icon = data["icon"]

    db.session.commit()
    return jsonify(cat.to_dict())


@notes_bp.delete("/categories/<uuid:cat_id>")
@require_auth
def delete_category(cat_id):
    user = get_current_db_user()
    if not user.is_admin:
        return jsonify({"error": "Admin only"}), 403

    cat = NoteCategory.query.filter_by(id=cat_id, household_id=user.household_id).first()
    if not cat:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(cat)
    db.session.commit()
    return jsonify({"deleted": True})


# ─── Notes ───────────────────────────────────────────────────────────────────

@notes_bp.get("/")
@require_auth
def list_notes():
    user = get_current_db_user()
    notes = (
        Note.query
        .filter_by(household_id=user.household_id)
        .order_by(Note.updated_at.desc())
        .all()
    )
    return jsonify([n.to_dict() for n in notes])


@notes_bp.post("/")
@require_auth
def create_note():
    user = get_current_db_user()
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400

    note_type_str = data.get("note_type", "text")
    try:
        note_type = NoteType(note_type_str)
    except ValueError:
        return jsonify({"error": "note_type must be 'text' or 'checklist'"}), 400

    checklist = None
    if note_type == NoteType.checklist:
        raw = data.get("checklist") or []
        if not isinstance(raw, list):
            return jsonify({"error": "checklist must be an array"}), 400
        checklist = [
            {"id": item.get("id") or str(uuid.uuid4()), "text": str(item.get("text", "")), "done": bool(item.get("done", False))}
            for item in raw
            if item.get("text", "").strip()
        ]

    category_id = data.get("category_id") or None
    if category_id:
        cat = NoteCategory.query.filter_by(id=category_id, household_id=user.household_id).first()
        if not cat:
            category_id = None

    note = Note(
        title=title,
        note_type=note_type,
        body=data.get("body") or None,
        checklist=checklist,
        tags=data.get("tags") or [],
        category_id=category_id,
        household_id=user.household_id,
        created_by=user.id,
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201


@notes_bp.get("/<uuid:note_id>")
@require_auth
def get_note(note_id):
    user = get_current_db_user()
    note = Note.query.filter_by(id=note_id, household_id=user.household_id).first()
    if not note:
        return jsonify({"error": "Not found"}), 404
    return jsonify(note.to_dict())


@notes_bp.put("/<uuid:note_id>")
@require_auth
def update_note(note_id):
    user = get_current_db_user()
    note = Note.query.filter_by(id=note_id, household_id=user.household_id).first()
    if not note:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json() or {}

    if "title" in data:
        t = (data["title"] or "").strip()
        if t:
            note.title = t

    if "note_type" in data:
        try:
            note.note_type = NoteType(data["note_type"])
        except ValueError:
            return jsonify({"error": "note_type must be 'text' or 'checklist'"}), 400

    if "body" in data:
        note.body = data["body"] or None

    if "checklist" in data:
        raw = data["checklist"] or []
        if not isinstance(raw, list):
            return jsonify({"error": "checklist must be an array"}), 400
        note.checklist = [
            {"id": item.get("id") or str(uuid.uuid4()), "text": str(item.get("text", "")), "done": bool(item.get("done", False))}
            for item in raw
            if item.get("text", "").strip()
        ]

    if "tags" in data:
        note.tags = data["tags"] or []

    if "category_id" in data:
        cid = data["category_id"]
        if cid is None:
            note.category_id = None
        else:
            cat = NoteCategory.query.filter_by(id=cid, household_id=user.household_id).first()
            note.category_id = cat.id if cat else note.category_id

    db.session.commit()
    return jsonify(note.to_dict())


@notes_bp.delete("/<uuid:note_id>")
@require_auth
def delete_note(note_id):
    user = get_current_db_user()
    note = Note.query.filter_by(id=note_id, household_id=user.household_id).first()
    if not note:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"deleted": True})
