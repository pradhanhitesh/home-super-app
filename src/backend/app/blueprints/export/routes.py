import io
import csv
import json
import zipfile
from datetime import date

from flask import send_file
from app.blueprints.export import export_bp
from app.middleware.auth import require_auth, get_current_db_user
from app.extensions import limiter


def _csv_bytes(headers, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _join_list(val):
    if isinstance(val, list):
        return "|".join(str(v) for v in val)
    return val or ""


@export_bp.get("/full")
@require_auth
@limiter.limit("10 per hour")
def full_export():
    from app.models.finance import Expense, Settlement
    from app.models.transaction import Transaction
    from app.models.grocery_item import GroceryItem
    from app.models.reminder import Reminder
    from app.models.note import Note
    from app.models.wellbeing import WellbeingEntry
    from app.models.menstrual import MenstrualCycle

    user = get_current_db_user()
    hid = user.household_id
    today = date.today().isoformat()

    # ── Expenses ─────────────────────────────────────────────────────────────
    expenses = Expense.query.filter_by(household_id=hid).order_by(Expense.expense_date).all()
    exp_rows = [e.to_dict() for e in expenses]
    exp_csv = _csv_bytes(
        ["id", "expense_date", "title", "amount", "category_name", "paid_by_name",
         "split_type", "notes", "is_subscription", "payment_method", "created_at"],
        exp_rows,
    )

    # ── Settlements ───────────────────────────────────────────────────────────
    settlements = Settlement.query.filter_by(household_id=hid).order_by(Settlement.settled_at).all()
    set_rows = [s.to_dict() for s in settlements]
    set_csv = _csv_bytes(
        ["id", "settled_at", "amount", "paid_by_name", "paid_to_name", "note", "created_at"],
        set_rows,
    )

    # ── Transactions (bills/subscriptions/outings) ────────────────────────────
    transactions = Transaction.query.filter_by(household_id=hid).order_by(Transaction.transaction_date).all()
    txn_rows = []
    for t in transactions:
        d = t.to_dict()
        d["tags"] = _join_list(d.get("tags"))
        txn_rows.append(d)
    txn_csv = _csv_bytes(
        ["id", "transaction_type", "transaction_date", "amount", "notes", "tags",
         "paid_by_id", "split_with_id", "split_amount", "created_at"],
        txn_rows,
    )

    # ── Grocery items ─────────────────────────────────────────────────────────
    grocery_items = GroceryItem.query.filter_by(household_id=hid).all()
    groc_rows = [
        {
            "id": str(g.id),
            "transaction_id": str(g.transaction_id),
            "item_name": g.item_name,
            "mrp": float(g.mrp) if g.mrp is not None else "",
            "quantity": float(g.quantity) if g.quantity is not None else "",
            "unit": g.unit.value if g.unit else "",
            "category": g.category or "",
            "created_at": g.created_at.isoformat(),
        }
        for g in grocery_items
    ]
    groc_csv = _csv_bytes(
        ["id", "transaction_id", "item_name", "mrp", "quantity", "unit", "category", "created_at"],
        groc_rows,
    )

    # ── Reminders ─────────────────────────────────────────────────────────────
    reminders = Reminder.query.filter_by(household_id=hid).order_by(Reminder.due_datetime).all()
    rem_rows = [r.to_dict() for r in reminders]
    rem_csv = _csv_bytes(
        ["id", "title", "body", "due_datetime", "repeat", "is_sent", "created_at"],
        rem_rows,
    )

    # ── Notes (JSON — preserves checklist structure) ──────────────────────────
    notes = Note.query.filter_by(household_id=hid).order_by(Note.created_at).all()
    notes_data = [n.to_dict() for n in notes]
    notes_json = json.dumps(notes_data, indent=2, ensure_ascii=False).encode("utf-8")

    # ── Well-being ────────────────────────────────────────────────────────────
    wellbeing = WellbeingEntry.query.filter_by(household_id=hid).order_by(WellbeingEntry.entry_date).all()
    wb_rows = [w.to_dict() for w in wellbeing]
    wb_csv = _csv_bytes(
        ["id", "entry_date", "user_name", "mood", "energy", "sleep_hours", "notes", "remarks", "created_at"],
        wb_rows,
    )

    # ── Menstrual cycles ──────────────────────────────────────────────────────
    menstrual = MenstrualCycle.query.filter_by(household_id=hid).order_by(MenstrualCycle.cycle_start).all()
    men_rows = []
    for m in menstrual:
        d = m.to_dict()
        d["symptoms"] = _join_list(d.get("symptoms"))
        men_rows.append(d)
    men_csv = _csv_bytes(
        ["id", "cycle_start", "cycle_end", "cycle_length", "symptoms", "notes",
         "predicted_next_start", "user_name", "created_at"],
        men_rows,
    )

    # ── Full JSON dump ────────────────────────────────────────────────────────
    dump = {
        "exported_at": today,
        "household_id": str(hid),
        "expenses": exp_rows,
        "settlements": set_rows,
        "transactions": txn_rows,
        "grocery_items": groc_rows,
        "reminders": rem_rows,
        "notes": notes_data,
        "wellbeing": wb_rows,
        "menstrual": men_rows,
    }
    dump_json = json.dumps(dump, indent=2, ensure_ascii=False).encode("utf-8")

    # ── Pack ZIP ──────────────────────────────────────────────────────────────
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("expenses.csv", exp_csv)
        zf.writestr("settlements.csv", set_csv)
        zf.writestr("transactions.csv", txn_csv)
        zf.writestr("grocery_items.csv", groc_csv)
        zf.writestr("reminders.csv", rem_csv)
        zf.writestr("notes.json", notes_json)
        zf.writestr("wellbeing.csv", wb_csv)
        zf.writestr("menstrual.csv", men_csv)
        zf.writestr("dump.json", dump_json)
    zip_buf.seek(0)

    return send_file(
        zip_buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"home-backup-{today}.zip",
    )
