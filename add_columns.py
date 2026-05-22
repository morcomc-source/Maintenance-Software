from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE workorder ADD COLUMN priority INTEGER'))
        conn.execute(text('ALTER TABLE workorder ADD COLUMN expected_completion_date DATE'))
        conn.commit()
    print('✅ Priority and Expected Completion Date columns added successfully!')