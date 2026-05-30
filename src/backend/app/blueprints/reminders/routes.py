from datetime import datetime
from flask import request, jsonify
from app.blueprints.reminders import reminders_bp
from app.middleware.auth import require_auth, get_current_db_user
from app.models.reminder import Reminder, RepeatInterval
from app.extensions import db

_REPEAT_VALUES = [e.value for e in RepeatInterval]


def _parse_due(raw: str):
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


@reminders_bp.get("/")
@require_auth
def list_reminders():
    user = get_current_db_user()
    reminders = (
        Reminder.query
        .filter_by(household_id=user.household_id)
        .order_by(Reminder.due_datetime.asc())
        .all()
    )
    return jsonify([r.to_dict() for r in reminders])


@reminders_bp.post("/")
@require_auth
def create_reminder():
    user = get_current_db_user()
    data = request.get_json() or {}

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400

    due = _parse_due(data.get("due_datetime", ""))
    if not due:
        return jsonify({"error": "due_datetime required (ISO 8601)"}), 400

    repeat_val = data.get("repeat", "none")
    if repeat_val not in _REPEAT_VALUES:
        return jsonify({"error": f"repeat must be one of: {_REPEAT_VALUES}"}), 400

    reminder = Reminder(
        title=title,
        body=data.get("body", ""),
        due_datetime=due,
        repeat=RepeatInterval[repeat_val],
        household_id=user.household_id,
        created_by=user.id,
    )
    db.session.add(reminder)
    db.session.commit()
    return jsonify(reminder.to_dict()), 201


@reminders_bp.get("/<uuid:reminder_id>")
@require_auth
def get_reminder(reminder_id):
    user = get_current_db_user()
    reminder = Reminder.query.filter_by(id=reminder_id, household_id=user.household_id).first()
    if not reminder:
        return jsonify({"error": "Not found"}), 404
    return jsonify(reminder.to_dict())


@reminders_bp.put("/<uuid:reminder_id>")
@require_auth
def update_reminder(reminder_id):
    user = get_current_db_user()
    reminder = Reminder.query.filter_by(id=reminder_id, household_id=user.household_id).first()
    if not reminder:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json() or {}
    if "title" in data:
        title = (data["title"] or "").strip()
        if title:
            reminder.title = title
    if "body" in data:
        reminder.body = data["body"]
    if "due_datetime" in data:
        due = _parse_due(data["due_datetime"])
        if due:
            reminder.due_datetime = due
            reminder.is_sent = False
    if "repeat" in data and data["repeat"] in _REPEAT_VALUES:
        reminder.repeat = RepeatInterval[data["repeat"]]

    db.session.commit()
    return jsonify(reminder.to_dict())


@reminders_bp.delete("/<uuid:reminder_id>")
@require_auth
def delete_reminder(reminder_id):
    user = get_current_db_user()
    reminder = Reminder.query.filter_by(id=reminder_id, household_id=user.household_id).first()
    if not reminder:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(reminder)
    db.session.commit()
    return jsonify({"deleted": True})


@reminders_bp.post("/fcm-token")
@require_auth
def register_fcm_token():
    """Store the browser FCM push token for the current user."""
    user = get_current_db_user()
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "token required"}), 400
    user.fcm_token = token
    db.session.commit()
    return jsonify({"registered": True})
