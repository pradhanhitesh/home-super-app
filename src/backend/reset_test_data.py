"""
Reset test data — deletes all transactional/content rows.
Retains: users, households, alembic_version.
Run from src/backend: python reset_test_data.py
"""
import sys
from app import create_app
from app.extensions import db

# Order matters: FK children before parents
TABLES_TO_TRUNCATE = [
    # Finance (children first)
    "user_category_assignments",
    "user_monthly_budgets",
    "expenses",
    "settlements",
    "transactions",
    "finance_categories",
    # Notes
    "notes",
    "note_categories",
    # Health
    "wellbeing_entries",
    "menstrual_cycles",
    # Reminders
    "reminders",
    # Groceries
    "grocery_items",
]

KEEP = ["users", "households", "alembic_version"]


def main():
    app = create_app()
    with app.app_context():
        confirm = input(
            f"Delete all data from {len(TABLES_TO_TRUNCATE)} tables?\n"
            f"Keep: {', '.join(KEEP)}\n"
            "Type YES to confirm: "
        ).strip()
        if confirm != "YES":
            print("Aborted.")
            sys.exit(0)

        with db.engine.connect() as conn:
            trans = conn.begin()
            try:
                # Disable FK checks temporarily for clean truncation
                conn.execute(db.text("SET session_replication_role = replica;"))
                for table in TABLES_TO_TRUNCATE:
                    conn.execute(db.text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    print(f"  cleared: {table}")
                conn.execute(db.text("SET session_replication_role = DEFAULT;"))
                trans.commit()
                print("\nDone. Users and households intact.")
            except Exception as e:
                trans.rollback()
                print(f"Error: {e}")
                sys.exit(1)


if __name__ == "__main__":
    main()
