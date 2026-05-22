from app import db
from datetime import datetime

class WorkOrder(db.Model):
    __tablename__ = 'workorder'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    equipment = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Open")
    
    # Priority & Due Date
    priority = db.Column(db.Integer)
    expected_completion_date = db.Column(db.Date)
    
    # Assignment
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Completion fields (needed for notes to show)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completion_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_at = db.Column(db.DateTime, nullable=True)
    
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_workorders')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_workorders')
    completed_by = db.relationship('User', foreign_keys=[completed_by_id], backref='completed_workorders')

    def __repr__(self):
        return f'<WorkOrder {self.id} - {self.equipment}>'