from app import db
from datetime import datetime

class PartTransaction(db.Model):
    __tablename__ = 'part_transactions'

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.Integer, db.ForeignKey('parts.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # take, receive, wo_use, pm_use
    quantity = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    username = db.Column(db.String(80), nullable=True)  # stored for history even if user deleted
    notes = db.Column(db.String(255), nullable=True)    # optional, for future use
    reference = db.Column(db.String(100), nullable=True)  # e.g. WO-123 or PM-45
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    part = db.relationship('Part', backref=db.backref('transactions', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('part_transactions', lazy='dynamic'))

    def __repr__(self):
        return f'<PartTransaction {self.transaction_type} {self.quantity} of part {self.part_id}>'
