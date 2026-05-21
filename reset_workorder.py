from app import create_app, db
from app.models.workorder import WorkOrder
from app.models.user import User
from datetime import datetime

app = create_app()
with app.app_context():
    # Drop only the workorder table
    WorkOrder.__table__.drop(db.engine, checkfirst=True)
    
    # Create it fresh with the correct columns
    WorkOrder.__table__.create(db.engine)
    
    print("✅ WorkOrder table recreated successfully!")

    # Recreate users
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    tech = User(username='technician1', role='technician')
    tech.set_password('password123')
    db.session.add(tech)

    db.session.commit()
    print("✅ Users recreated!")
    print("Admin: admin / admin123")
    print("Technician: technician1 / password123")