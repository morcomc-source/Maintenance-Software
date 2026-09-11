from datetime import datetime
from app import db

class EquipmentBOM(db.Model):
    __tablename__ = "equipment_bom"
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False, index=True)
    part_id = db.Column(db.Integer, db.ForeignKey("parts.id"), nullable=False)
    qty = db.Column(db.Integer, default=1)
    note = db.Column(db.String(255))
    proprietary = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
