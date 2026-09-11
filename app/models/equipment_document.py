from datetime import datetime
from app import db

class EquipmentDocument(db.Model):
    __tablename__ = "equipment_documents"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False, index=True)
    original_name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    stored_name = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(120))
    size_bytes = db.Column(db.Integer)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    equipment = db.relationship("Equipment", backref=db.backref("documents", lazy="dynamic"))
