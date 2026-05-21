from app import create_app, db
from app.models.user import User
from app.models.workorder import WorkOrder   # This will create the table

app = create_app()
with app.app_context():
    db.create_all()   # Creates all tables including workorder
    print("✅ All tables created successfully!")

    # Create default users
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    tech = User(username='technician1', role='technician')
    tech.set_password('password123')
    db.session.add(tech)

    db.session.commit()
    print("✅ Default users created!")
    print("Login with:")
    print("Admin: admin / admin123")
    print("Technician: technician1 / password123")