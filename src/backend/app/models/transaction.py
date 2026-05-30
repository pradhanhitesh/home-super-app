import enum
from app.models.base import MLBase
from app.extensions import db


class TransactionType(enum.Enum):
    bill = "bill"
    subscription = "subscription"
    grocery = "grocery"
    outing = "outing"
    vacation = "vacation"
    other = "other"


class Transaction(MLBase):
    __tablename__ = "transactions"

    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.ARRAY(db.String), nullable=False, server_default="{}")
    metadata_ = db.Column("metadata", db.JSON, nullable=False, server_default="{}")

    paid_by_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    split_with_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=True)
    split_amount = db.Column(db.Numeric(12, 2), nullable=True)
    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)

    paid_by = db.relationship("User", foreign_keys=[paid_by_id])
    split_with = db.relationship("User", foreign_keys=[split_with_id])
    grocery_items = db.relationship("GroceryItem", back_populates="transaction", lazy="dynamic")

    def to_dict(self):
        return {
            "id": str(self.id),
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "transaction_date": self.transaction_date.isoformat(),
            "notes": self.notes,
            "tags": self.tags,
            "metadata": self.metadata_,
            "paid_by_id": str(self.paid_by_id),
            "split_with_id": str(self.split_with_id) if self.split_with_id else None,
            "split_amount": str(self.split_amount) if self.split_amount else None,
            "household_id": str(self.household_id),
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
