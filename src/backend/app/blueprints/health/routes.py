from datetime import date, timedelta
from flask import jsonify, request
from app.blueprints.health import health_bp
from app.middleware.auth import require_auth, get_current_db_user
from app.extensions import db


def _predict_next_cycle(cycles_asc):
    """Return predicted next cycle start from list sorted by cycle_start asc."""
    starts = [c.cycle_start for c in cycles_asc]
    if not starts:
        return None
    if len(starts) < 2:
        return starts[-1] + timedelta(days=28)
    gaps = [(starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)]
    recent = gaps[-6:]
    avg = round(sum(recent) / len(recent))
    return starts[-1] + timedelta(days=avg)


# ─── Well-being ───────────────────────────────────────────────────────────────

@health_bp.get("/wellbeing")
@require_auth
def list_wellbeing():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.wellbeing import WellbeingEntry

    month_str = request.args.get("month")
    try:
        if month_str:
            if len(month_str) == 7:
                month_str += "-01"
            ref = date.fromisoformat(month_str).replace(day=1)
        else:
            ref = date.today().replace(day=1)
    except Exception:
        return jsonify({"error": "Invalid month. Use YYYY-MM"}), 400

    entries = WellbeingEntry.query.filter(
        WellbeingEntry.household_id == db_user.household_id,
        db.extract("year", WellbeingEntry.entry_date) == ref.year,
        db.extract("month", WellbeingEntry.entry_date) == ref.month,
    ).order_by(WellbeingEntry.entry_date.desc(), WellbeingEntry.created_at.desc()).all()

    return jsonify([e.to_dict() for e in entries])


@health_bp.post("/wellbeing")
@require_auth
def create_wellbeing():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.wellbeing import WellbeingEntry

    data = request.get_json() or {}
    entry_date_str = data.get("entry_date") or date.today().isoformat()
    mood = data.get("mood")
    energy = data.get("energy")

    if mood is None or energy is None:
        return jsonify({"error": "mood and energy required"}), 400

    try:
        mood = int(mood)
        energy = int(energy)
        if not (1 <= mood <= 10 and 1 <= energy <= 10):
            raise ValueError()
        entry_date = date.fromisoformat(entry_date_str)
    except Exception:
        return jsonify({"error": "mood and energy must be 1–10; entry_date must be YYYY-MM-DD"}), 400

    sleep_hours = data.get("sleep_hours")
    if sleep_hours is not None:
        try:
            sleep_hours = float(sleep_hours)
            if sleep_hours < 0 or sleep_hours > 24:
                raise ValueError()
        except Exception:
            return jsonify({"error": "sleep_hours must be 0–24"}), 400

    # Upsert: one entry per user per day
    existing = WellbeingEntry.query.filter_by(
        household_id=db_user.household_id,
        created_by=db_user.id,
        entry_date=entry_date,
    ).first()

    if existing:
        existing.mood = mood
        existing.energy = energy
        existing.sleep_hours = sleep_hours
        existing.notes = data.get("notes", existing.notes)
        existing.remarks = data.get("remarks", existing.remarks)
        db.session.commit()
        return jsonify(existing.to_dict()), 200

    entry = WellbeingEntry(
        household_id=db_user.household_id,
        created_by=db_user.id,
        entry_date=entry_date,
        mood=mood,
        energy=energy,
        sleep_hours=sleep_hours,
        notes=data.get("notes"),
        remarks=data.get("remarks"),
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@health_bp.put("/wellbeing/<uuid:entry_id>")
@require_auth
def update_wellbeing(entry_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.wellbeing import WellbeingEntry
    entry = WellbeingEntry.query.filter_by(
        id=entry_id, household_id=db_user.household_id, created_by=db_user.id
    ).first_or_404()

    data = request.get_json() or {}

    for field in ("mood", "energy"):
        if field in data:
            val = int(data[field])
            if not (1 <= val <= 10):
                return jsonify({"error": f"{field} must be 1–10"}), 400
            setattr(entry, field, val)

    if "sleep_hours" in data:
        sh = data["sleep_hours"]
        entry.sleep_hours = float(sh) if sh is not None else None

    for field in ("notes", "remarks"):
        if field in data:
            setattr(entry, field, data[field] or None)

    db.session.commit()
    return jsonify(entry.to_dict())


@health_bp.delete("/wellbeing/<uuid:entry_id>")
@require_auth
def delete_wellbeing(entry_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.wellbeing import WellbeingEntry
    entry = WellbeingEntry.query.filter_by(
        id=entry_id, household_id=db_user.household_id, created_by=db_user.id
    ).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return "", 204


# ─── Menstrual cycle ─────────────────────────────────────────────────────────

@health_bp.get("/menstrual")
@require_auth
def list_menstrual():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.menstrual import MenstrualCycle

    cycles = MenstrualCycle.query.filter_by(
        household_id=db_user.household_id
    ).order_by(MenstrualCycle.cycle_start.desc()).all()

    cycles_asc = list(reversed(cycles))
    predicted = _predict_next_cycle(cycles_asc)

    return jsonify({
        "cycles": [c.to_dict() for c in cycles],
        "predicted_next_start": predicted.isoformat() if predicted else None,
        "avg_cycle_length": _avg_cycle_length(cycles_asc),
    })


def _avg_cycle_length(cycles_asc):
    starts = [c.cycle_start for c in cycles_asc]
    if len(starts) < 2:
        return None
    gaps = [(starts[i + 1] - starts[i]).days for i in range(len(starts) - 1)]
    return round(sum(gaps[-6:]) / len(gaps[-6:]))


@health_bp.post("/menstrual")
@require_auth
def create_menstrual():
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.menstrual import MenstrualCycle

    data = request.get_json() or {}
    cycle_start_str = data.get("cycle_start") or date.today().isoformat()

    try:
        cycle_start = date.fromisoformat(cycle_start_str)
    except Exception:
        return jsonify({"error": "cycle_start must be YYYY-MM-DD"}), 400

    cycle_end = None
    if data.get("cycle_end"):
        try:
            cycle_end = date.fromisoformat(data["cycle_end"])
            if cycle_end < cycle_start:
                raise ValueError()
        except Exception:
            return jsonify({"error": "cycle_end must be >= cycle_start"}), 400

    symptoms = data.get("symptoms") or []
    if not isinstance(symptoms, list):
        return jsonify({"error": "symptoms must be an array"}), 400

    cycle = MenstrualCycle(
        household_id=db_user.household_id,
        created_by=db_user.id,
        cycle_start=cycle_start,
        cycle_end=cycle_end,
        symptoms=symptoms,
        notes=data.get("notes"),
    )
    db.session.add(cycle)
    db.session.flush()

    # Compute and store predicted_next_start
    all_cycles_asc = MenstrualCycle.query.filter_by(
        household_id=db_user.household_id
    ).order_by(MenstrualCycle.cycle_start.asc()).all()
    predicted = _predict_next_cycle(all_cycles_asc)
    if predicted:
        cycle.predicted_next_start = predicted

    db.session.commit()
    return jsonify(cycle.to_dict()), 201


@health_bp.put("/menstrual/<uuid:cycle_id>")
@require_auth
def update_menstrual(cycle_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.menstrual import MenstrualCycle
    cycle = MenstrualCycle.query.filter_by(
        id=cycle_id, household_id=db_user.household_id
    ).first_or_404()

    data = request.get_json() or {}

    if "cycle_start" in data:
        try:
            cycle.cycle_start = date.fromisoformat(data["cycle_start"])
        except Exception:
            return jsonify({"error": "Invalid cycle_start"}), 400

    if "cycle_end" in data:
        if data["cycle_end"] is None:
            cycle.cycle_end = None
        else:
            try:
                ce = date.fromisoformat(data["cycle_end"])
                if ce < cycle.cycle_start:
                    raise ValueError()
                cycle.cycle_end = ce
            except Exception:
                return jsonify({"error": "cycle_end must be >= cycle_start"}), 400

    if "symptoms" in data:
        if not isinstance(data["symptoms"], list):
            return jsonify({"error": "symptoms must be an array"}), 400
        cycle.symptoms = data["symptoms"]

    if "notes" in data:
        cycle.notes = data["notes"] or None

    # Recompute prediction for all cycles
    db.session.flush()
    all_cycles_asc = MenstrualCycle.query.filter_by(
        household_id=db_user.household_id
    ).order_by(MenstrualCycle.cycle_start.asc()).all()
    predicted = _predict_next_cycle(all_cycles_asc)
    if predicted:
        # Update prediction on the most recent cycle
        most_recent = all_cycles_asc[-1]
        most_recent.predicted_next_start = predicted

    db.session.commit()
    return jsonify(cycle.to_dict())


@health_bp.delete("/menstrual/<uuid:cycle_id>")
@require_auth
def delete_menstrual(cycle_id):
    db_user = get_current_db_user()
    if not db_user:
        return jsonify({"error": "User not found"}), 404

    from app.models.menstrual import MenstrualCycle
    cycle = MenstrualCycle.query.filter_by(
        id=cycle_id, household_id=db_user.household_id
    ).first_or_404()
    db.session.delete(cycle)
    db.session.commit()
    return "", 204
