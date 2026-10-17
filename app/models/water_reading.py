from datetime import datetime
from app import db


class WaterReading(db.Model):
    __tablename__ = "water_readings"
    __table_args__ = (
        db.UniqueConstraint("location_code", "reading_date", name="uq_water_loc_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    location_code = db.Column(db.String(20), nullable=False, index=True)
    reading_date = db.Column(db.Date, nullable=False, index=True)
    meter = db.Column(db.BigInteger, nullable=True)
    tds = db.Column(db.Integer, nullable=True)
    usage = db.Column(db.BigInteger, nullable=True)
    is_baseline = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
