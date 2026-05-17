from app import db
from app.models.user import User

class PM(db.Model):
    __tablename__ = 'pm'  # Keep to match your existing DB table
    id = db.Column(db.Integer, primary_key=True)
    main_equipment = db.Column(db.String(255))
    sub_equipment = db.Column(db.String(255))
    frequency = db.Column(db.String(50))
    last_done = db.Column(db.Date)
    next_due = db.Column(db.Date)
    checklist = db.Column(db.JSON)  # Assuming JSON for checklist
   
    # Assigned user relationship (single assignment)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_user = db.relationship('User', backref='assigned_pm_items', lazy=True)  # Unique backref name to avoid conflict
   
    def __repr__(self):
        return f'<PM {self.main_equipment}>'