import enum
from app.extensions import db
from app.models.base import MLBase


class SplitType(enum.Enum):
    none = "none"
    equal = "equal"
    custom = "custom"
    amount = "amount"


class PaymentMethod(enum.Enum):
    cash = "cash"
    card = "card"


class FinanceCategory(MLBase):
    __tablename__ = "finance_categories"

    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False, default="bi-tag")
    color = db.Column(db.String(20), nullable=False, default="#6b7280")
    is_shared = db.Column(db.Boolean, nullable=False, default=True)

    assignments = db.relationship("UserCategoryAssignment", back_populates="category", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", back_populates="category")
    budgets = db.relationship("UserMonthlyBudget", back_populates="category")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "is_shared": self.is_shared,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserCategoryAssignment(MLBase):
    __tablename__ = "user_category_assignments"
    __table_args__ = (db.UniqueConstraint("user_id", "category_id", name="uq_user_category"),)

    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("finance_categories.id", ondelete="CASCADE"), nullable=False)

    category = db.relationship("FinanceCategory", back_populates="assignments")
    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "category_id": str(self.category_id),
        }


class UserMonthlyBudget(MLBase):
    __tablename__ = "user_monthly_budgets"

    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    # NULL category_id = total monthly budget for that user
    category_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True)
    month = db.Column(db.Date, nullable=False)  # always 1st of month
    amount = db.Column(db.Numeric(12, 2), nullable=False)

    user = db.relationship("User", foreign_keys=[user_id])
    category = db.relationship("FinanceCategory", back_populates="budgets")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "category_id": str(self.category_id) if self.category_id else None,
            "month": self.month.isoformat(),
            "amount": float(self.amount),
        }


class Expense(MLBase):
    __tablename__ = "expenses"

    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("finance_categories.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(300), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    split_type = db.Column(db.Enum(SplitType), nullable=False, default=SplitType.equal)
    # {"user_id_str": ratio_int, ...}  only for split_type=custom
    split_ratio = db.Column(db.JSON, nullable=True)
    expense_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    is_subscription = db.Column(db.Boolean, nullable=False, default=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False, default=PaymentMethod.card)

    category = db.relationship("FinanceCategory", back_populates="expenses")
    payer = db.relationship("User", foreign_keys=[paid_by], lazy="joined")
    creator = db.relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": str(self.id),
            "category_id": str(self.category_id) if self.category_id else None,
            "category_name": self.category.name if self.category else "Uncategorized",
            "category_color": self.category.color if self.category else "#9ca3af",
            "category_icon": self.category.icon if self.category else "bi-tag",
            "title": self.title,
            "amount": float(self.amount),
            "paid_by": str(self.paid_by),
            "paid_by_name": self.payer.display_name if self.payer else None,
            "split_type": self.split_type.value,
            "split_ratio": self.split_ratio,
            "expense_date": self.expense_date.isoformat(),
            "notes": self.notes,
            "is_subscription": self.is_subscription,
            "payment_method": self.payment_method.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Settlement(MLBase):
    __tablename__ = "settlements"

    household_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("households.id"), nullable=False)
    created_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    paid_by = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    paid_to = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    note = db.Column(db.Text, nullable=True)
    settled_at = db.Column(db.Date, nullable=False)

    payer = db.relationship("User", foreign_keys=[paid_by], lazy="joined")
    payee = db.relationship("User", foreign_keys=[paid_to], lazy="joined")

    def to_dict(self):
        return {
            "id": str(self.id),
            "paid_by": str(self.paid_by),
            "paid_by_name": self.payer.display_name if self.payer else None,
            "paid_to": str(self.paid_to),
            "paid_to_name": self.payee.display_name if self.payee else None,
            "amount": float(self.amount),
            "note": self.note,
            "settled_at": self.settled_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
