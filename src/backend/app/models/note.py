import enum
from app.models.base import MLBase
from app.extensions import db


class NoteType(enum.Enum):
    text = "text"
    checklist = "checklist"


class Note(MLBase):
    __tablename__ = "notes"

    title = db.Column(db.String(300), nullable=False)
    note_type = db.Column(db.Enum(NoteType), nullable=False, default=NoteType.text)
    body = db.Column(db.Text, nullable=True)
    checklist = db.Column(db.JSON, nullable=True)  # [{id, text, done}, ...]
    tags = db.Column(db.ARRAY(db.String), nullable=False, server_default="{}")
    category_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("note_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    author = db.relationship("User", foreign_keys=[created_by], lazy="joined")
    category = db.relationship("NoteCategory", foreign_keys=[category_id], lazy="joined")

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "note_type": self.note_type.value,
            "body": self.body,
            "checklist": self.checklist or [],
            "tags": self.tags or [],
            "category_id": str(self.category_id) if self.category_id else None,
            "category": self.category.to_dict() if self.category else None,
            "created_by": str(self.created_by),
            "author_name": self.author.display_name if self.author else "",
            "household_id": str(self.household_id),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
