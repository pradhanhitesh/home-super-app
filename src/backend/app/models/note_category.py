from app.models.base import MLBase
from app.extensions import db


class NoteCategory(MLBase):
    __tablename__ = "note_categories"

    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#6366f1")
    icon = db.Column(db.String(50), nullable=False, default="bi-tag")
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "color": self.color,
            "icon": self.icon,
            "household_id": str(self.household_id),
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat(),
        }
