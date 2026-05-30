import enum
from app.models.base import MLBase
from app.extensions import db


class Unit(enum.Enum):
    count = "count"
    kg = "kg"
    g = "g"
    ml = "ml"
    L = "L"


class GroceryItem(MLBase):
    __tablename__ = "grocery_items"

    transaction_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("transactions.id"), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    mrp = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Numeric(10, 3), nullable=True)
    unit = db.Column(db.Enum(Unit), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    transaction = db.relationship("Transaction", back_populates="grocery_items")
