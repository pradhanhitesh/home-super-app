import uuid
from datetime import datetime, timezone
from app.extensions import db


class MLBase(db.Model):
    """Base model enforcing ML-ready data contract on every table."""
    __abstract__ = True

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
