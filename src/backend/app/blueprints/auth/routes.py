from flask import request, jsonify
from app.blueprints.auth import auth_bp
from app.middleware.auth import verify_firebase_token, require_auth, get_current_db_user
from app.models.user import User
from app.models.household import Household
from app.extensions import db, limiter


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    id_token = (request.json or {}).get("idToken")
    if not id_token:
        return jsonify({"error": "idToken required"}), 400

    decoded = verify_firebase_token(id_token)
    if not decoded:
        return jsonify({"error": "Invalid or unauthorized token"}), 401

    user = User.query.filter_by(firebase_uid=decoded["uid"]).first()
    if not user:
        household = Household.query.first()
        if not household:
            household = Household(name="Home")
            db.session.add(household)
            db.session.flush()

        from flask import current_app
        admin_uid = current_app.config.get("ADMIN_UID", "")
        if admin_uid:
            is_admin = decoded["uid"] == admin_uid
        else:
            is_admin = User.query.filter_by(household_id=household.id).count() == 0

        user = User(
            firebase_uid=decoded["uid"],
            email=decoded["email"],
            display_name=decoded.get("name", ""),
            photo_url=decoded.get("picture", ""),
            household_id=household.id,
            is_admin=is_admin,
        )
        db.session.add(user)
        db.session.commit()
    else:
        # Refresh display name / photo from latest Google token
        changed = False
        if decoded.get("name") and user.display_name != decoded["name"]:
            user.display_name = decoded["name"]
            changed = True
        if decoded.get("picture") and user.photo_url != decoded["picture"]:
            user.photo_url = decoded["picture"]
            changed = True
        if changed:
            db.session.commit()

    return jsonify(user.to_dict())


@auth_bp.get("/me")
@require_auth
def me():
    user = get_current_db_user()
    if not user:
        return jsonify({"error": "User record not found"}), 404
    return jsonify(user.to_dict())
