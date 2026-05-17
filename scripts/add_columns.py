from app import create_app  # Import your app factory
from app import db
from app.models.part import Part  # Load model to ensure it's registered
from sqlalchemy import text  # ← New: For executable SQL

app = create_app()  # Create the app instance

with app.app_context():  # Set up context for DB ops
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE part ADD COLUMN min_stock TEXT DEFAULT '0';"))
        print("Added min_stock column.")
    except Exception as e:
        print(f"Min stock already exists or error: {e}")

    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE part ADD COLUMN max_stock TEXT DEFAULT '999';"))
        print("Added max_stock column.")
    except Exception as e:
        print(f"Max stock already exists or error: {e}")

print("Done! Restart your app.")