from app.models.base import MLBase
from app.extensions import db


class MenstrualCycle(MLBase):
    __tablename__ = "menstrual_cycles"

    cycle_start = db.Column(db.Date, nullable=False)
    cycle_end = db.Column(db.Date, nullable=True)
    symptoms = db.Column(db.ARRAY(db.String), nullable=False, server_default="{}")
    notes = db.Column(db.Text, nullable=True)
    predicted_next_start = db.Column(db.Date, nullable=True)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    creator = db.relationship("User", foreign_keys=[created_by], lazy="joined")

    def to_dict(self):
        return {
            "id": str(self.id),
            "cycle_start": self.cycle_start.isoformat(),
            "cycle_end": self.cycle_end.isoformat() if self.cycle_end else None,
            "cycle_length": (self.cycle_end - self.cycle_start).days if self.cycle_end else None,
            "symptoms": self.symptoms or [],
            "notes": self.notes,
            "predicted_next_start": self.predicted_next_start.isoformat() if self.predicted_next_start else None,
            "created_by": str(self.created_by),
            "user_name": self.creator.display_name if self.creator else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
