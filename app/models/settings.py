from app import db
from datetime import datetime

class PartLocation(db.Model):
    __tablename__ = 'part_locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartLocation {self.name}>'


class PartSublocation(db.Model):
    __tablename__ = 'part_sublocations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    group_label = db.Column(db.String(50), nullable=True)  # e.g. "A", "B", "C"
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartSublocation {self.name}>'
