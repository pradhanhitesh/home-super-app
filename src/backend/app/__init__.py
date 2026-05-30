import os
from flask import Flask
from flask_cors import CORS

from app.config import get_config
from app.extensions import db, migrate, redis_client, limiter


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    db.init_app(app)
    migrate.init_app(app, db)
    redis_client.init_app(app)

    app.config["RATELIMIT_STORAGE_URI"] = app.config.get("REDIS_URL", "redis://127.0.0.1:6379/0")
    app.config["RATELIMIT_HEADERS_ENABLED"] = True
    limiter.init_app(app)

    from app.blueprints.auth import auth_bp
    from app.blueprints.finance import finance_bp
    from app.blueprints.reminders import reminders_bp
    from app.blueprints.notes import notes_bp
    from app.blueprints.health import health_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(finance_bp, url_prefix="/api/finance")
    app.register_blueprint(reminders_bp, url_prefix="/api/reminders")
    app.register_blueprint(notes_bp, url_prefix="/api/notes")
    app.register_blueprint(health_bp, url_prefix="/api/health")

    @app.get("/api/ping")
    @limiter.exempt
    def ping():
        return {"status": "ok", "env": app.config.get("FLASK_ENV", "unknown")}

    from app.tasks.reminders import _ensure_firebase_initialized
    _ensure_firebase_initialized(app)
    _start_scheduler(app)

    return app


def _start_scheduler(app):
    """Start background reminder-notification job.

    Guard against double-start when Flask debug reloader forks the process.
    In production (gunicorn --workers 1) this runs once.
    """
    if os.environ.get("WERKZEUG_RUN_MAIN") == "false":
        # Flask reloader parent process — skip; child will start it.
        return

    from apscheduler.schedulers.background import BackgroundScheduler
    from app.tasks.reminders import check_due_reminders

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(check_due_reminders, "interval", seconds=60, args=[app], id="check_reminders")
    scheduler.start()

    import atexit
    atexit.register(scheduler.shutdown)
