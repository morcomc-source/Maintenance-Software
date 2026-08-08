# app/models/part.py (update this file)
from app import db

class Part(db.Model):
    __tablename__ = 'parts'  # ← If table is 'parts', add this to match
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(100), nullable=True)
    qty = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(100), nullable=True)
    bin_location = db.Column(db.String(120), nullable=True)
    sublocation = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    min_stock = db.Column(db.String(50), default='0')  # ← Add this
    max_stock = db.Column(db.String(50), default='999')  # ← Add this
    
    
    # On-order tracking
    on_order = db.Column(db.Boolean, default=False)
    ordered_by = db.Column(db.String(80), nullable=True)
    ordered_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Part {self.name}: {self.qty}>"