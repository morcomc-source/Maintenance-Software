from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    db.create_all()
    
    # Admin
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Technician
    tech = User(username='technician1', role='technician')
    tech.set_password('password123')
    db.session.add(tech)
    
    db.session.commit()
    print('✅ Users created successfully!')
    print('Admin -> username: admin | password: admin123')
    print('Technician -> username: technician1 | password: password123')