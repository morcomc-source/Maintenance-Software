from app import db
from datetime import datetime

class Permit(db.Model):
    __tablename__ = "permits"

    id = db.Column(db.Integer, primary_key=True)
    permit_type = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    location = db.Column(db.String(200))
    equipment = db.Column(db.String(200))
    work_description = db.Column(db.Text)
    form_data = db.Column(db.JSON)
    photos = db.Column(db.JSON)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reports_to_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    decided_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decision_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    reports_to = db.relationship("User", foreign_keys=[reports_to_id])
    decided_by = db.relationship("User", foreign_keys=[decided_by_id])

    def type_label(self):
        return {
            "hot_work": "Hot work",
            "confined": "Confined space",
            "loto": "Lockout / Tagout",
        }.get(self.permit_type, self.permit_type)
