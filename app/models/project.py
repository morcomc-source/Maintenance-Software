from datetime import datetime
from app import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    priority = db.Column(db.String(20))          # High, Medium, Low
    project_type = db.Column(db.String(20))      # Shut Down, Anytime
    location = db.Column(db.String(100))         # free text fallback
    project = db.Column(db.Text, nullable=False) # the job description
    parts_status = db.Column(db.String(50))      # Here, On Order, No Parts Needed, In Progress
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open')  # Open / Completed

    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=True)
    assigned_department = db.Column(db.String(100))
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    equipment = db.relationship('Equipment', backref='projects')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])
