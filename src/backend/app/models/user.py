from app.models.base import MLBase
from app.extensions import db


class User(MLBase):
    __tablename__ = "users"

    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    display_name = db.Column(db.String(200), nullable=False, default="")
    photo_url = db.Column(db.Text, nullable=True)
    fcm_token = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)

    household = db.relationship("Household", back_populates="users")

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "is_admin": self.is_admin,
            "household_id": str(self.household_id),
            "created_at": self.created_at.isoformat(),
        }
