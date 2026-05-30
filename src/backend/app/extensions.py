from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import current_app
import redis


db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120 per minute", "1000 per day"],
    storage_options={"socket_connect_timeout": 2},
)


class RedisClient:
    def __init__(self):
        self._client = None

    def init_app(self, app):
        url = app.config.get("REDIS_URL", "redis://127.0.0.1:6379/0")
        self._client = redis.from_url(url, decode_responses=True)

    def __getattr__(self, name):
        return getattr(self._client, name)


redis_client = RedisClient()
