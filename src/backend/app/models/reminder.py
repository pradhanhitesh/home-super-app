import enum
from app.models.base import MLBase
from app.extensions import db


class RepeatInterval(enum.Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class Reminder(MLBase):
    __tablename__ = "reminders"

    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=True)
    due_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    repeat = db.Column(db.Enum(RepeatInterval), nullable=False, default=RepeatInterval.none)
    is_sent = db.Column(db.Boolean, nullable=False, default=False)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "body": self.body or "",
            "due_datetime": self.due_datetime.isoformat(),
            "repeat": self.repeat.value,
            "is_sent": self.is_sent,
            "created_by": str(self.created_by),
            "household_id": str(self.household_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
