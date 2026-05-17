from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='technician') # 'admin' or 'technician'
    must_change_password = db.Column(db.Boolean, default=True) # Force change on first login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(120), unique=True, nullable=True) # Optional (nullable=True)
  
    def set_password(self, password, reset_flag=False):  # <-- change default to False here
        self.password_hash = generate_password_hash(password)
        if reset_flag:
            self.must_change_password = False
  
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
  
    def is_admin(self):
        return self.role == 'admin'
  
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'