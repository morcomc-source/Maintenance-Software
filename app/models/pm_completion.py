from app import db
from datetime import datetime

class PMCompletion(db.Model):
    __tablename__ = 'pm_completion'
   
    id = db.Column(db.Integer, primary_key=True)
    pm_id = db.Column(db.Integer, db.ForeignKey('pm.id'), nullable=False)
   
    completed_date = db.Column(db.DateTime, default=datetime.now)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
   
    notes = db.Column(db.Text, nullable=True)
    checklist_results = db.Column(db.JSON, nullable=True)
   
    # Relationships
    pm = db.relationship('PM', backref=db.backref('completions', lazy=True, cascade="all, delete-orphan"))
    completed_by = db.relationship('User', backref='pm_completions')
   
    def __repr__(self):
        return f'<PMCompletion pm:{self.pm_id} on {self.completed_date}>'
