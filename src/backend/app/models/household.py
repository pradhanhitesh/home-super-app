from app.models.base import MLBase
from app.extensions import db


class Household(MLBase):
    __tablename__ = "households"

    name = db.Column(db.String(100), nullable=False, default="Home")

    users = db.relationship("User", back_populates="household", lazy="dynamic")
