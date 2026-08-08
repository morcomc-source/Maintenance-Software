from app import db


class PM(db.Model):
    __tablename__ = "pm"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.String(50), nullable=True)
    main_equipment = db.Column(db.String(255))
    sub_equipment = db.Column(db.String(255))
    frequency = db.Column(db.String(50))
    last_done = db.Column(db.Date)
    next_due = db.Column(db.Date)
    checklist = db.Column(db.JSON)

    assigned_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    completed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    assigned_user = db.relationship(
        "User",
        foreign_keys=[assigned_user_id],
        backref=db.backref("assigned_pm_items", lazy=True),
    )
    completed_by = db.relationship(
        "User",
        foreign_keys=[completed_by_id],
        backref=db.backref("completed_pms", lazy=True),
    )

    status = db.Column(db.String(50), default="Open")
    started_at = db.Column(db.DateTime, nullable=True)
    paused_at = db.Column(db.DateTime, nullable=True)
    resumed_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    completion_notes = db.Column(db.Text, nullable=True)
    parts_used = db.Column(db.JSON, nullable=True)
    pause_reason = db.Column(db.Text, nullable=True)
    total_work_seconds = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<PM {self.main_equipment}>"
