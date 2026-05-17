from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        admin.must_change_password = True
        db.session.commit()
        print("Admin user already existed - forced password change enabled.")
    else:
        admin = User(username='admin', role='admin', must_change_password=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("New admin user created with forced password change.")

    print("Username: admin")
    print("Password: admin123")