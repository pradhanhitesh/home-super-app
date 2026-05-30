import os
from functools import wraps
from flask import request, jsonify, current_app
import firebase_admin
from firebase_admin import auth, credentials


_firebase_initialized = False


def _load_firebase_credentials():
    """Return a Credential or None. Prefers JSON env var (Render), falls back to file path."""
    sa_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", "")
    if sa_json:
        import json
        return credentials.Certificate(json.loads(sa_json))
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if sa_path and os.path.isfile(sa_path):
        return credentials.Certificate(sa_path)
    return None


def _ensure_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return
    project_id = current_app.config["FIREBASE_PROJECT_ID"]
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = _load_firebase_credentials()
        if cred:
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        else:
            # No service account — token verification still works via Google's public JWKS.
            firebase_admin.initialize_app(options={"projectId": project_id})
    _firebase_initialized = True


def verify_firebase_token(id_token: str) -> dict | None:
    try:
        _ensure_firebase()
        allowed = [e.strip().lower() for e in current_app.config.get("ALLOWED_EMAILS", [])]
        decoded = auth.verify_id_token(id_token)
        email = decoded.get("email", "").lower()
        if allowed and email not in allowed:
            return None
        return decoded
    except Exception:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing authorization header"}), 401
        id_token = auth_header.split(" ", 1)[1]
        decoded = verify_firebase_token(id_token)
        if not decoded:
            return jsonify({"error": "Invalid or unauthorized token"}), 401
        request.current_user = decoded
        return f(*args, **kwargs)
    return decorated


def get_current_db_user():
    """Return the DB User for the Firebase-authenticated caller. Call inside @require_auth routes."""
    from app.models.user import User
    uid = request.current_user.get("uid")
    return User.query.filter_by(firebase_uid=uid).first()
