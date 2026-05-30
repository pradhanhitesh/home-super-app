from flask import Blueprint

reminders_bp = Blueprint("reminders", __name__)

from app.blueprints.reminders import routes  # noqa: E402, F401
