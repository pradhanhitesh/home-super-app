from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta


def _ensure_firebase_initialized(app):
    """Initialize Firebase Admin SDK if not already done.

    The auth middleware only initializes Firebase on HTTP requests.
    The scheduler runs in a background thread with no request context,
    so we must call this explicitly before using firebase_admin.messaging.
    """
    import os
    import json
    import firebase_admin
    from firebase_admin import credentials

    try:
        firebase_admin.get_app()
    except ValueError:
        project_id = app.config["FIREBASE_PROJECT_ID"]
        sa_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", "")
        sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if sa_json:
            cred = credentials.Certificate(json.loads(sa_json))
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        elif sa_path and os.path.isfile(sa_path):
            cred = credentials.Certificate(sa_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        else:
            firebase_admin.initialize_app(options={"projectId": project_id})


def _send_fcm(title: str, body: str, token: str) -> bool:
    try:
        from firebase_admin import messaging
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body or "You have a reminder!"),
            token=token,
        )
        messaging.send(msg)
        return True
    except Exception as exc:
        print(f"[FCM] send failed: {exc}")
        return False


def _advance_due(reminder):
    from app.models.reminder import RepeatInterval
    now = datetime.now(timezone.utc)
    dt = reminder.due_datetime
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if reminder.repeat == RepeatInterval.daily:
        while dt <= now:
            dt += timedelta(days=1)
    elif reminder.repeat == RepeatInterval.weekly:
        while dt <= now:
            dt += timedelta(weeks=1)
    elif reminder.repeat == RepeatInterval.monthly:
        while dt <= now:
            dt += relativedelta(months=1)
    reminder.due_datetime = dt


def check_due_reminders(app):
    """Background job: find due reminders, send FCM, advance repeating ones."""
    with app.app_context():
        from app.models.reminder import Reminder, RepeatInterval
        from app.models.user import User
        from app.extensions import db

        _ensure_firebase_initialized(app)

        now = datetime.now(timezone.utc)
        due = Reminder.query.filter(
            Reminder.due_datetime <= now,
            Reminder.is_sent == False,  # noqa: E712
        ).all()

        for reminder in due:
            users = User.query.filter_by(household_id=reminder.household_id).all()
            for user in users:
                if user.fcm_token:
                    _send_fcm(reminder.title, reminder.body, user.fcm_token)

        if due:
            for reminder in due:
                if reminder.repeat == RepeatInterval.none:
                    reminder.is_sent = True
                else:
                    _advance_due(reminder)
            db.session.commit()
