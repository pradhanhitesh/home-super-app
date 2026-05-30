from app.models.base import MLBase
from app.extensions import db


class WellbeingEntry(MLBase):
    __tablename__ = "wellbeing_entries"

    entry_date = db.Column(db.Date, nullable=False)
    mood = db.Column(db.SmallInteger, nullable=False)       # 1–10
    energy = db.Column(db.SmallInteger, nullable=False)     # 1–10
    sleep_hours = db.Column(db.Numeric(4, 1), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    creator = db.relationship("User", foreign_keys=[created_by], lazy="joined")

    def to_dict(self):
        return {
            "id": str(self.id),
            "entry_date": self.entry_date.isoformat(),
            "mood": self.mood,
            "energy": self.energy,
            "sleep_hours": float(self.sleep_hours) if self.sleep_hours is not None else None,
            "notes": self.notes,
            "remarks": self.remarks,
            "created_by": str(self.created_by),
            "user_name": self.creator.display_name if self.creator else None,
            "user_photo": self.creator.photo_url if self.creator else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
