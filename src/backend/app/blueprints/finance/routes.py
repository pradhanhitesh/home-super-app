from datetime import date, timedelta
from flask import jsonify, request
from app.blueprints.finance import finance_bp
from app.middleware.auth import require_auth, get_current_db_user
from app.extensions import db


def _month_start(d=None):
    d = d or date.today()
    return d.replace(day=1)


def _prev_month_start(d):
    first = d.replace(day=1)
    return (first - timedelta(days=1)).replace(day=1)


def _parse_month(month_str):
    """Accept 'YYYY-MM' or 'YYYY-MM-DD', return first of that month."""
    if not month_str:
        return _month_start()
    if len(month_str) == 7:
        month_str += "-01"
    return date.fromisoformat(month_str).replace(day=1)


def _rollover_budgets_for_user(household_id, user_id, month, actor_id):
    """Copy previous month's budgets for any category not yet set this month."""
    from app.models.finance import UserMonthlyBudget
    prev = _prev_month_start(month)
    prev_budgets = UserMonthlyBudget.query.filter_by(
        household_id=household_id, user_id=user_id, month=prev
    ).all()
    if not prev_budgets:
        return
    existing = {
        b.category_id
        for b in UserMonthlyBudget.query.filter_by(
            household_id=household_id, user_id=user_id, month=month
        ).all()
    }
    added = False
    for b in prev_budgets:
        if b.category_id not in existing:
            db.session.add(UserMonthlyBudget(
                household_id=household_id,
                created_by=actor_id,
                user_id=user_id,
                category_id=b.category_id,
                month=month,
                amount=b.amount,
            ))
            added = True
    if added:
        db.session.commit()


def _compute_shares(expense, user_id_strs):
    """Return {uid_str: float} share for each user in household."""
    from app.models.finance import SplitType
    amount = float(expense.amount)
    if expense.split_type == SplitType.none:
        return {str(expense.paid_by): amount}
    if expense.split_type == SplitType.equal:
        share = amount / max(len(user_id_strs), 1)
        return {uid: share for uid in user_id_strs}
    if expense.split_type == SplitType.amount:
        # split_ratio stores {uid: exact_amount}
        ratio = expense.split_ratio or {}
        return {uid: float(ratio.get(uid, 0)) for uid in user_id_strs}
    # custom ratio
    ratio = expense.split_ratio or {}
    total_parts = sum(ratio.values()) or 1
    return {uid: amount * (ratio.get(uid, 0) / total_parts) for uid in user_id_strs}


# ─── Settings ────────────────────────────────────────────────────────────────

@finance_bp.get("/settings")
@require_auth
def get_settings():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import FinanceCategory, UserCategoryAssignment, UserMonthlyBudget
    from app.models.user import User

    month = _month_start()
    hid = db_user.household_id
    users = User.query.filter_by(household_id=hid).all()

    for u in users:
        _rollover_budgets_for_user(hid, u.id, month, db_user.id)

    categories = FinanceCategory.query.filter_by(household_id=hid).order_by(FinanceCategory.name).all()
    assignments = UserCategoryAssignment.query.filter_by(household_id=hid).all()
    budgets = UserMonthlyBudget.query.filter_by(household_id=hid, month=month).all()

    return jsonify({
        "categories": [c.to_dict() for c in categories],
        "assignments": [a.to_dict() for a in assignments],
        "budgets": [b.to_dict() for b in budgets],
        "users": [u.to_dict() for u in users],
        "current_user_id": str(db_user.id),
        "is_admin": db_user.is_admin,
        "month": month.isoformat(),
    })


# ─── Categories ──────────────────────────────────────────────────────────────

@finance_bp.post("/categories")
@require_auth
def create_category():
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import FinanceCategory
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400

    cat = FinanceCategory(
        household_id=db_user.household_id,
        created_by=db_user.id,
        name=name,
        icon=data.get("icon", "bi-tag"),
        color=data.get("color", "#6b7280"),
        is_shared=bool(data.get("is_shared", True)),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@finance_bp.put("/categories/<uuid:cat_id>")
@require_auth
def update_category(cat_id):
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import FinanceCategory
    cat = FinanceCategory.query.filter_by(id=cat_id, household_id=db_user.household_id).first_or_404()
    data = request.get_json() or {}
    if "name" in data and data["name"].strip():
        cat.name = data["name"].strip()
    if "icon" in data:
        cat.icon = data["icon"]
    if "color" in data:
        cat.color = data["color"]
    if "is_shared" in data:
        cat.is_shared = bool(data["is_shared"])
    db.session.commit()
    return jsonify(cat.to_dict())


@finance_bp.delete("/categories/<uuid:cat_id>")
@require_auth
def delete_category(cat_id):
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import FinanceCategory
    cat = FinanceCategory.query.filter_by(id=cat_id, household_id=db_user.household_id).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    return "", 204


# ─── Assignments ──────────────────────────────────────────────────────────────

@finance_bp.post("/assignments")
@require_auth
def create_assignment():
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import UserCategoryAssignment, FinanceCategory
    from app.models.user import User

    data = request.get_json() or {}
    user_id = data.get("user_id")
    category_id = data.get("category_id")
    if not user_id or not category_id:
        return jsonify({"error": "user_id and category_id required"}), 400

    if not User.query.filter_by(id=user_id, household_id=db_user.household_id).first():
        return jsonify({"error": "User not in household"}), 404
    if not FinanceCategory.query.filter_by(id=category_id, household_id=db_user.household_id).first():
        return jsonify({"error": "Category not found"}), 404

    existing = UserCategoryAssignment.query.filter_by(user_id=user_id, category_id=category_id).first()
    if existing:
        return jsonify(existing.to_dict()), 200

    a = UserCategoryAssignment(
        household_id=db_user.household_id,
        created_by=db_user.id,
        user_id=user_id,
        category_id=category_id,
    )
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict()), 201


@finance_bp.delete("/assignments/<uuid:assignment_id>")
@require_auth
def delete_assignment(assignment_id):
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import UserCategoryAssignment
    a = UserCategoryAssignment.query.filter_by(id=assignment_id, household_id=db_user.household_id).first_or_404()
    db.session.delete(a)
    db.session.commit()
    return "", 204


# ─── Budgets ─────────────────────────────────────────────────────────────────

@finance_bp.post("/budgets")
@require_auth
def set_budget():
    db_user = get_current_db_user()
    if not db_user or not db_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403

    from app.models.finance import UserMonthlyBudget, FinanceCategory
    from app.models.user import User

    data = request.get_json() or {}
    user_id = data.get("user_id")
    category_id = data.get("category_id") or None  # None = total budget
    month_str = data.get("month")
    amount = data.get("amount")

    if not user_id or amount is None or not month_str:
        return jsonify({"error": "user_id, month, amount required"}), 400

    try:
        month = _parse_month(month_str)
        amount = float(amount)
        if amount < 0:
            raise ValueError()
    except Exception:
        return jsonify({"error": "Invalid month or amount"}), 400

    if not User.query.filter_by(id=user_id, household_id=db_user.household_id).first():
        return jsonify({"error": "User not in household"}), 404

    if category_id and not FinanceCategory.query.filter_by(id=category_id, household_id=db_user.household_id).first():
        return jsonify({"error": "Category not found"}), 404

    # Upsert: find existing row (NULL-safe filter)
    q = UserMonthlyBudget.query.filter_by(user_id=user_id, month=month)
    if category_id:
        q = q.filter(UserMonthlyBudget.category_id == category_id)
    else:
        q = q.filter(UserMonthlyBudget.category_id.is_(None))
    existing = q.first()

    if existing:
        existing.amount = amount
    else:
        existing = UserMonthlyBudget(
            household_id=db_user.household_id,
            created_by=db_user.id,
            user_id=user_id,
            category_id=category_id,
            month=month,
            amount=amount,
        )
        db.session.add(existing)
    db.session.commit()
    return jsonify(existing.to_dict()), 200


# ─── Expenses ────────────────────────────────────────────────────────────────

@finance_bp.get("/expenses")
@require_auth
def list_expenses():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Expense

    try:
        month = _parse_month(request.args.get("month"))
    except Exception:
        return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

    expenses = Expense.query.filter(
        Expense.household_id == db_user.household_id,
        db.extract("year", Expense.expense_date) == month.year,
        db.extract("month", Expense.expense_date) == month.month,
    ).order_by(Expense.expense_date.desc(), Expense.created_at.desc()).all()

    return jsonify([e.to_dict() for e in expenses])


@finance_bp.post("/expenses")
@require_auth
def create_expense():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Expense, SplitType, PaymentMethod, FinanceCategory

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    amount = data.get("amount")
    category_id = data.get("category_id")
    paid_by = data.get("paid_by") or str(db_user.id)
    expense_date_str = data.get("expense_date") or date.today().isoformat()
    split_type_str = data.get("split_type", "equal")
    split_ratio = data.get("split_ratio")
    payment_method_str = data.get("payment_method", "card")

    if not title:
        return jsonify({"error": "Title required"}), 400
    if amount is None:
        return jsonify({"error": "Amount required"}), 400
    if not category_id:
        return jsonify({"error": "Category required"}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"error": "Amount must be positive"}), 400

    if not FinanceCategory.query.filter_by(id=category_id, household_id=db_user.household_id).first():
        return jsonify({"error": "Category not found"}), 404

    try:
        split_type = SplitType(split_type_str)
        payment_method = PaymentMethod(payment_method_str)
        expense_date = date.fromisoformat(expense_date_str)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if split_type.value == "amount":
        total_parts = sum(float(v) for v in (split_ratio or {}).values())
        if abs(total_parts - amount) > 0.01:
            return jsonify({"error": f"Split amounts must sum to ₹{amount:.2f} (got ₹{total_parts:.2f})"}), 400

    expense = Expense(
        household_id=db_user.household_id,
        created_by=db_user.id,
        category_id=category_id,
        title=title,
        amount=amount,
        paid_by=paid_by,
        split_type=split_type,
        split_ratio=split_ratio,
        expense_date=expense_date,
        notes=data.get("notes"),
        is_subscription=bool(data.get("is_subscription", False)),
        payment_method=payment_method,
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201


@finance_bp.put("/expenses/<uuid:expense_id>")
@require_auth
def update_expense(expense_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Expense, SplitType, PaymentMethod

    expense = Expense.query.filter_by(id=expense_id, household_id=db_user.household_id).first_or_404()
    data = request.get_json() or {}

    if "title" in data and data["title"].strip():
        expense.title = data["title"].strip()
    if "amount" in data:
        try:
            expense.amount = float(data["amount"])
        except Exception:
            return jsonify({"error": "Invalid amount"}), 400
    if "category_id" in data:
        expense.category_id = data["category_id"]
    if "paid_by" in data:
        expense.paid_by = data["paid_by"]
    if "split_type" in data:
        try:
            expense.split_type = SplitType(data["split_type"])
        except ValueError:
            return jsonify({"error": "Invalid split_type"}), 400
    if "split_ratio" in data:
        expense.split_ratio = data["split_ratio"]
    if "expense_date" in data:
        try:
            expense.expense_date = date.fromisoformat(data["expense_date"])
        except Exception:
            return jsonify({"error": "Invalid expense_date"}), 400
    if "notes" in data:
        expense.notes = data["notes"]
    if "is_subscription" in data:
        expense.is_subscription = bool(data["is_subscription"])
    if "payment_method" in data:
        try:
            expense.payment_method = PaymentMethod(data["payment_method"])
        except ValueError:
            return jsonify({"error": "Invalid payment_method"}), 400

    if expense.split_type.value == "amount":
        total_parts = sum(float(v) for v in (expense.split_ratio or {}).values())
        exp_amount = float(expense.amount)
        if abs(total_parts - exp_amount) > 0.01:
            return jsonify({"error": f"Split amounts must sum to ₹{exp_amount:.2f} (got ₹{total_parts:.2f})"}), 400

    db.session.commit()
    return jsonify(expense.to_dict())


@finance_bp.delete("/expenses/<uuid:expense_id>")
@require_auth
def delete_expense(expense_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Expense
    expense = Expense.query.filter_by(id=expense_id, household_id=db_user.household_id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return "", 204


# ─── Summary ─────────────────────────────────────────────────────────────────

@finance_bp.get("/summary")
@require_auth
def get_summary():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Expense, UserMonthlyBudget, FinanceCategory, UserCategoryAssignment, Settlement
    from app.models.user import User

    try:
        month = _parse_month(request.args.get("month"))
    except Exception:
        return jsonify({"error": "Invalid month"}), 400

    hid = db_user.household_id
    users = User.query.filter_by(household_id=hid).all()
    user_ids = [str(u.id) for u in users]
    user_map = {str(u.id): u for u in users}

    for u in users:
        _rollover_budgets_for_user(hid, u.id, month, db_user.id)

    # This month's expenses for spending breakdown
    month_expenses = Expense.query.filter(
        Expense.household_id == hid,
        db.extract("year", Expense.expense_date) == month.year,
        db.extract("month", Expense.expense_date) == month.month,
    ).all()

    # All-time expenses and settlements for running balance
    all_expenses = Expense.query.filter_by(household_id=hid).all()
    all_settlements = Settlement.query.filter_by(household_id=hid).all()

    # ── Spending per user per category (this month) ──
    spending = {uid: {} for uid in user_ids}
    for expense in month_expenses:
        shares = _compute_shares(expense, user_ids)
        cat_id = str(expense.category_id)
        for uid, share in shares.items():
            if uid in spending:
                spending[uid][cat_id] = spending[uid].get(cat_id, 0) + share

    # ── Running balance (all time) ──
    # debt_matrix[debtor_uid][creditor_uid] = amount debtor owes creditor
    debt = {uid: {uid2: 0.0 for uid2 in user_ids if uid2 != uid} for uid in user_ids}
    for expense in all_expenses:
        shares = _compute_shares(expense, user_ids)
        payer_id = str(expense.paid_by)
        for uid, share in shares.items():
            if uid != payer_id and uid in debt and payer_id in debt.get(uid, {}):
                debt[uid][payer_id] += share
    for s in all_settlements:
        pb = str(s.paid_by)
        pt = str(s.paid_to)
        amt = float(s.amount)
        if pb in debt and pt in debt[pb]:
            debt[pb][pt] = max(0.0, debt[pb][pt] - amt)

    # Simplify to net balance for 2-user household
    balance = None
    if len(user_ids) == 2:
        a, b = user_ids[0], user_ids[1]
        a_owes = debt.get(a, {}).get(b, 0)
        b_owes = debt.get(b, {}).get(a, 0)
        net = a_owes - b_owes
        if abs(net) > 0.005:
            debtor, creditor = (a, b) if net > 0 else (b, a)
            balance = {
                "debtor_id": debtor,
                "debtor_name": user_map[debtor].display_name,
                "creditor_id": creditor,
                "creditor_name": user_map[creditor].display_name,
                "amount": round(abs(net), 2),
            }

    # ── Budgets ──
    budgets = UserMonthlyBudget.query.filter_by(household_id=hid, month=month).all()
    budget_map = {}  # (uid, cat_id_or_None) -> float
    for b in budgets:
        budget_map[(str(b.user_id), str(b.category_id) if b.category_id else None)] = float(b.amount)

    # ── Assignments ──
    assignments = UserCategoryAssignment.query.filter_by(household_id=hid).all()
    user_cats = {}
    for a in assignments:
        user_cats.setdefault(str(a.user_id), set()).add(str(a.category_id))

    cat_map = {str(c.id): c for c in FinanceCategory.query.filter_by(household_id=hid).all()}

    # ── User summaries ──
    user_summaries = []
    for u in users:
        uid = str(u.id)
        assigned_cats = user_cats.get(uid, set())
        total_budget = budget_map.get((uid, None), 0)
        total_spent = sum(spending[uid].values())
        cat_breakdowns = []
        for cat_id in assigned_cats:
            cat = cat_map.get(cat_id)
            if not cat:
                continue
            spent = spending[uid].get(cat_id, 0)
            budget = budget_map.get((uid, cat_id), 0)
            cat_breakdowns.append({
                "category_id": cat_id,
                "category_name": cat.name,
                "category_color": cat.color,
                "category_icon": cat.icon,
                "is_shared": cat.is_shared,
                "budget": budget,
                "spent": round(spent, 2),
                "remaining": round(budget - spent, 2) if budget else None,
                "pct": round(min(spent / budget * 100, 100), 1) if budget else None,
            })
        cat_breakdowns.sort(key=lambda x: x["category_name"])
        user_summaries.append({
            "user_id": uid,
            "user_name": u.display_name,
            "total_budget": total_budget,
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_budget - total_spent, 2) if total_budget else None,
            "total_pct": round(min(total_spent / total_budget * 100, 100), 1) if total_budget else None,
            "categories": cat_breakdowns,
        })

    # ── Shared categories (for dashboard) ──
    # Admin controls visibility via is_shared flag, regardless of user assignments
    shared_cats = [c for c in cat_map.values() if c.is_shared]
    shared_summary = []
    for cat in sorted(shared_cats, key=lambda c: c.name):
        cid = str(cat.id)
        total_spent = sum(spending.get(uid, {}).get(cid, 0) for uid in user_ids)
        shared_summary.append({
            "category_id": cid,
            "category_name": cat.name,
            "category_color": cat.color,
            "category_icon": cat.icon,
            "total_spent": round(total_spent, 2),
        })

    return jsonify({
        "month": month.isoformat(),
        "users": user_summaries,
        "balance": balance,
        "shared_categories": shared_summary,
    })


# ─── Settlements ─────────────────────────────────────────────────────────────

@finance_bp.get("/settlements")
@require_auth
def list_settlements():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Settlement
    settlements = Settlement.query.filter_by(
        household_id=db_user.household_id
    ).order_by(Settlement.settled_at.desc()).all()
    return jsonify([s.to_dict() for s in settlements])


@finance_bp.post("/settlements")
@require_auth
def create_settlement():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Settlement
    from app.models.user import User

    data = request.get_json() or {}
    paid_by = data.get("paid_by") or str(db_user.id)
    paid_to = data.get("paid_to")
    amount = data.get("amount")
    settled_at_str = data.get("settled_at") or date.today().isoformat()

    if not paid_to or amount is None:
        return jsonify({"error": "paid_to and amount required"}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except Exception:
        return jsonify({"error": "Invalid amount"}), 400

    if not User.query.filter_by(id=paid_to, household_id=db_user.household_id).first():
        return jsonify({"error": "Recipient not in household"}), 404

    try:
        settled_at = date.fromisoformat(settled_at_str)
    except Exception:
        return jsonify({"error": "Invalid settled_at"}), 400

    s = Settlement(
        household_id=db_user.household_id,
        created_by=db_user.id,
        paid_by=paid_by,
        paid_to=paid_to,
        amount=amount,
        note=data.get("note"),
        settled_at=settled_at,
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201


@finance_bp.delete("/settlements/<uuid:settlement_id>")
@require_auth
def delete_settlement(settlement_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.finance import Settlement
    s = Settlement.query.filter_by(id=settlement_id, household_id=db_user.household_id).first_or_404()
    db.session.delete(s)
    db.session.commit()
    return "", 204
