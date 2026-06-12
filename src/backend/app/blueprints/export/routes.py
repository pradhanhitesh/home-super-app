import io
import csv
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import send_file, request
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


@export_bp.post("/restore")
@require_auth
@limiter.limit("5 per hour")
def full_restore():
    from app.extensions import db
    from app.models.finance import (
        Expense, Settlement, SplitType, PaymentMethod, FinanceCategory,
    )
    from app.models.transaction import Transaction, TransactionType
    from app.models.grocery_item import GroceryItem, Unit
    from app.models.reminder import Reminder, RepeatInterval
    from app.models.note import Note, NoteType
    from app.models.wellbeing import WellbeingEntry
    from app.models.menstrual import MenstrualCycle
    from app.models.user import User

    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400
    f = request.files["file"]
    if not f.filename.endswith(".zip"):
        return {"error": "Must upload a .zip file"}, 400

    user = get_current_db_user()
    hid = user.household_id

    try:
        with zipfile.ZipFile(io.BytesIO(f.read())) as zf:
            with zf.open("dump.json") as jf:
                dump = json.load(jf)
    except KeyError:
        return {"error": "dump.json not found in ZIP — use a backup created by this app"}, 400
    except (zipfile.BadZipFile, json.JSONDecodeError) as e:
        return {"error": f"Invalid backup file: {e}"}, 400

    # Build name → current household user map
    hh_users = User.query.filter_by(household_id=hid).all()
    name_to_user = {u.display_name: u for u in hh_users}

    # Build old_uuid → display_name from every entity that exports both
    old_uid_to_name: dict[str, str] = {}
    for e in dump.get("expenses", []):
        if e.get("paid_by") and e.get("paid_by_name"):
            old_uid_to_name[e["paid_by"]] = e["paid_by_name"]
    for s in dump.get("settlements", []):
        if s.get("paid_by") and s.get("paid_by_name"):
            old_uid_to_name[s["paid_by"]] = s["paid_by_name"]
        if s.get("paid_to") and s.get("paid_to_name"):
            old_uid_to_name[s["paid_to"]] = s["paid_to_name"]
    for w in dump.get("wellbeing", []):
        if w.get("created_by") and w.get("user_name"):
            old_uid_to_name[w["created_by"]] = w["user_name"]
    for m in dump.get("menstrual", []):
        if m.get("created_by") and m.get("user_name"):
            old_uid_to_name[m["created_by"]] = m["user_name"]
    for n in dump.get("notes", []):
        if n.get("created_by") and n.get("author_name"):
            old_uid_to_name[n["created_by"]] = n["author_name"]

    def resolve_user(old_uid: str | None):
        if old_uid:
            name = old_uid_to_name.get(old_uid)
            if name and name in name_to_user:
                return name_to_user[name]
        return user  # fallback: restoring user

    # Category name → FinanceCategory (create missing ones)
    existing_cats = FinanceCategory.query.filter_by(household_id=hid).all()
    cat_name_map: dict[str, FinanceCategory] = {c.name: c for c in existing_cats}

    def get_or_create_cat(name: str | None):
        if not name or name == "Uncategorized":
            return None
        if name not in cat_name_map:
            new_cat = FinanceCategory(
                household_id=hid,
                created_by=user.id,
                name=name,
                icon="bi-tag",
                color="#6b7280",
                is_shared=True,
            )
            db.session.add(new_cat)
            db.session.flush()
            cat_name_map[name] = new_cat
        return cat_name_map[name]

    def _date(s):
        if not s:
            return None
        try:
            return date.fromisoformat(str(s)[:10])
        except ValueError:
            return None

    def _dt(s):
        if not s:
            return None
        try:
            return datetime.fromisoformat(str(s))
        except ValueError:
            return None

    def _dec(v):
        if v is None or v == "":
            return None
        try:
            return Decimal(str(v))
        except InvalidOperation:
            return None

    counts: dict[str, int] = {}

    # Transactions first (grocery_items FK depends on them)
    old_txn_id_to_new: dict[str, Transaction] = {}
    for t in dump.get("transactions", []):
        paid_by_user = resolve_user(t.get("paid_by_id"))
        split_with_uid = t.get("split_with_id")
        split_user = resolve_user(split_with_uid) if split_with_uid else None

        try:
            txn_type = TransactionType(t["transaction_type"])
        except (KeyError, ValueError):
            txn_type = TransactionType.other

        tags = t.get("tags") or []
        if isinstance(tags, str):
            tags = [x for x in tags.split("|") if x]

        new_txn = Transaction(
            transaction_type=txn_type,
            amount=_dec(t.get("amount")) or Decimal(0),
            transaction_date=_date(t.get("transaction_date")) or date.today(),
            notes=t.get("notes"),
            tags=tags,
            metadata_=t.get("metadata") or {},
            paid_by_id=paid_by_user.id,
            split_with_id=split_user.id if split_user and str(split_user.id) != str(paid_by_user.id) else None,
            split_amount=_dec(t.get("split_amount")),
            household_id=hid,
            created_by=user.id,
        )
        db.session.add(new_txn)
        db.session.flush()
        old_txn_id_to_new[t["id"]] = new_txn
    counts["transactions"] = len(old_txn_id_to_new)

    # Grocery items
    groc_count = 0
    for g in dump.get("grocery_items", []):
        new_txn = old_txn_id_to_new.get(g.get("transaction_id"))
        if not new_txn:
            continue
        unit_val = g.get("unit")
        try:
            unit = Unit(unit_val) if unit_val else None
        except ValueError:
            unit = None
        db.session.add(GroceryItem(
            transaction_id=new_txn.id,
            item_name=g["item_name"],
            mrp=_dec(g.get("mrp")),
            quantity=_dec(g.get("quantity")),
            unit=unit,
            category=g.get("category"),
            household_id=hid,
            created_by=user.id,
        ))
        groc_count += 1
    counts["grocery_items"] = groc_count

    # Expenses
    exp_count = 0
    for e in dump.get("expenses", []):
        cat = get_or_create_cat(e.get("category_name"))
        paid_by_user = resolve_user(e.get("paid_by"))
        try:
            split_type = SplitType(e.get("split_type", "equal"))
        except ValueError:
            split_type = SplitType.equal
        try:
            payment_method = PaymentMethod(e.get("payment_method", "card"))
        except ValueError:
            payment_method = PaymentMethod.card

        split_ratio = e.get("split_ratio")
        if split_ratio and isinstance(split_ratio, dict):
            split_ratio = {str(resolve_user(k).id): v for k, v in split_ratio.items()}

        db.session.add(Expense(
            household_id=hid,
            created_by=user.id,
            category_id=cat.id if cat else None,
            title=e["title"],
            amount=_dec(e.get("amount")) or Decimal(0),
            paid_by=paid_by_user.id,
            split_type=split_type,
            split_ratio=split_ratio,
            expense_date=_date(e.get("expense_date")) or date.today(),
            notes=e.get("notes"),
            is_subscription=bool(e.get("is_subscription", False)),
            payment_method=payment_method,
        ))
        exp_count += 1
    counts["expenses"] = exp_count

    # Settlements
    set_count = 0
    for s in dump.get("settlements", []):
        paid_by_user = resolve_user(s.get("paid_by"))
        paid_to_user = resolve_user(s.get("paid_to"))
        db.session.add(Settlement(
            household_id=hid,
            created_by=user.id,
            paid_by=paid_by_user.id,
            paid_to=paid_to_user.id,
            amount=_dec(s.get("amount")) or Decimal(0),
            note=s.get("note"),
            settled_at=_date(s.get("settled_at")) or date.today(),
        ))
        set_count += 1
    counts["settlements"] = set_count

    # Reminders
    rem_count = 0
    for r in dump.get("reminders", []):
        due = _dt(r.get("due_datetime"))
        if not due:
            continue
        try:
            repeat = RepeatInterval(r.get("repeat", "none"))
        except ValueError:
            repeat = RepeatInterval.none
        db.session.add(Reminder(
            household_id=hid,
            created_by=user.id,
            title=r["title"],
            body=r.get("body") or "",
            due_datetime=due,
            repeat=repeat,
            is_sent=bool(r.get("is_sent", False)),
        ))
        rem_count += 1
    counts["reminders"] = rem_count

    # Notes (note_categories not restored — category_id set to NULL)
    note_count = 0
    for n in dump.get("notes", []):
        try:
            note_type = NoteType(n.get("note_type", "text"))
        except ValueError:
            note_type = NoteType.text
        tags = n.get("tags") or []
        if isinstance(tags, str):
            tags = [x for x in tags.split("|") if x]
        db.session.add(Note(
            household_id=hid,
            created_by=user.id,
            title=n["title"],
            note_type=note_type,
            body=n.get("body"),
            checklist=n.get("checklist"),
            tags=tags,
            category_id=None,
        ))
        note_count += 1
    counts["notes"] = note_count

    # Wellbeing
    wb_count = 0
    for w in dump.get("wellbeing", []):
        wb_user = resolve_user(w.get("created_by"))
        db.session.add(WellbeingEntry(
            household_id=hid,
            created_by=wb_user.id,
            entry_date=_date(w.get("entry_date")) or date.today(),
            mood=int(w.get("mood") or 5),
            energy=int(w.get("energy") or 5),
            sleep_hours=_dec(w.get("sleep_hours")),
            notes=w.get("notes"),
            remarks=w.get("remarks"),
        ))
        wb_count += 1
    counts["wellbeing"] = wb_count

    # Menstrual cycles
    men_count = 0
    for m in dump.get("menstrual", []):
        cycle_start = _date(m.get("cycle_start"))
        if not cycle_start:
            continue
        symptoms = m.get("symptoms") or []
        if isinstance(symptoms, str):
            symptoms = [x for x in symptoms.split("|") if x]
        men_user = resolve_user(m.get("created_by"))
        db.session.add(MenstrualCycle(
            household_id=hid,
            created_by=men_user.id,
            cycle_start=cycle_start,
            cycle_end=_date(m.get("cycle_end")),
            symptoms=symptoms,
            notes=m.get("notes"),
            predicted_next_start=_date(m.get("predicted_next_start")),
        ))
        men_count += 1
    counts["menstrual"] = men_count

    db.session.commit()
    return {"restored": counts}, 200
