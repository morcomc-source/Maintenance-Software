from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        admin.must_change_password = True
        db.session.commit()
        print("✅ SUCCESS: Admin is now forced to change password on next login")
    else:
        print("❌ Admin user not found")