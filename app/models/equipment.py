from app import db
from datetime import datetime

class Equipment(db.Model):
    __tablename__ = 'equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.String(50), unique=True, nullable=False)  # Public ID like EQ-0001
    
    name = db.Column(db.String(150), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=True)
    model = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    location = db.Column(db.String(100))
    purchase_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), default='Active')
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Equipment {self.equipment_id} - {self.name}>'