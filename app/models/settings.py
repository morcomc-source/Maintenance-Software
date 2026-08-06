from app import db
from datetime import datetime


class PartLocation(db.Model):
    """Legacy flat location list (kept so old parts still work)."""
    __tablename__ = 'part_locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartLocation {self.name}>'


class PartSublocation(db.Model):
    """Sublocation tied to a main location."""
    __tablename__ = 'part_sublocations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_label = db.Column(db.String(50), nullable=True)  # unused
    location_id = db.Column(db.Integer, db.ForeignKey('part_locations.id'), nullable=True)
    location = db.relationship('PartLocation', backref='sublocations')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartSublocation {self.name}>'



# ----- New hierarchy: Row / Section / Shelf / Slot -----
class PartRow(db.Model):
    __tablename__ = 'part_rows'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. R01
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartRow {self.code}>'


class PartSection(db.Model):
    __tablename__ = 'part_sections'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # e.g. S03
    name = db.Column(db.String(100), nullable=True)
    row_id = db.Column(db.Integer, db.ForeignKey('part_rows.id'), nullable=False)
    row = db.relationship('PartRow', backref='sections')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartSection {self.code}>'


class PartShelf(db.Model):
    __tablename__ = 'part_shelves'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. H01
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartShelf {self.code}>'


class PartSlot(db.Model):
    __tablename__ = 'part_slots'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. P01
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PartSlot {self.code}>'


# PM setup lists
class PMMainEquipment(db.Model):
    __tablename__ = 'pm_main_equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PMMainEquipment {self.name}>'


class PMMachine(db.Model):
    __tablename__ = 'pm_machines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    main_equipment_id = db.Column(db.Integer, db.ForeignKey('pm_main_equipment.id'), nullable=True)
    main_equipment = db.relationship('PMMainEquipment', backref='machines')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PMMachine {self.name}>'


class PMFrequency(db.Model):
    __tablename__ = 'pm_frequencies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PMFrequency {self.name}>'
