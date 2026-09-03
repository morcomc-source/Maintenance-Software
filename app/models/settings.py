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
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. S01
    name = db.Column(db.String(100), nullable=True)
    row_id = db.Column(db.Integer, db.ForeignKey('part_rows.id'), nullable=True)
    row = db.relationship('PartRow', backref='shelves')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartShelf {self.code}>'

class PartSlot(db.Model):
    __tablename__ = 'part_slots'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. P01 (position)
    name = db.Column(db.String(100), nullable=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey('part_shelves.id'), nullable=True)
    shelf = db.relationship('PartShelf', backref='slots')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartSlot {self.code}>'


# ----- Cabinet → Shelf  |  Chest → Drawer -----
class PartCabinet(db.Model):
    __tablename__ = 'part_cabinets'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartCabinet {self.code}>'

class PartCabinetShelf(db.Model):
    """Shelf inside a cabinet (separate from rack shelves)."""
    __tablename__ = 'part_cabinet_shelves'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    cabinet_id = db.Column(db.Integer, db.ForeignKey('part_cabinets.id'), nullable=False)
    cabinet = db.relationship('PartCabinet', backref='shelves')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartCabinetShelf {self.code}>'

class PartChest(db.Model):
    __tablename__ = 'part_chests'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartChest {self.code}>'

class PartDrawer(db.Model):
    __tablename__ = 'part_drawers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    chest_id = db.Column(db.Integer, db.ForeignKey('part_chests.id'), nullable=True)
    chest = db.relationship('PartChest', backref='drawers')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartDrawer {self.code}>'

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

class PartCabinetPosition(db.Model):
    """Position on a cabinet shelf (P01, P02, ...)."""
    __tablename__ = 'part_cabinet_positions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    cabinet_shelf_id = db.Column(db.Integer, db.ForeignKey('part_cabinet_shelves.id'), nullable=False)
    cabinet_shelf = db.relationship('PartCabinetShelf', backref='positions')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartCabinetPosition {self.code}>'

class PartDrawerPosition(db.Model):
    """Position in a chest drawer (P01, P02, ...)."""
    __tablename__ = 'part_drawer_positions'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    drawer_id = db.Column(db.Integer, db.ForeignKey('part_drawers.id'), nullable=False)
    drawer = db.relationship('PartDrawer', backref='positions')
    created_at = db.Column(db.DateTime, default=datetime.now)
    def __repr__(self):
        return f'<PartDrawerPosition {self.code}>'


class AppSetting(db.Model):
    __tablename__ = 'app_settings'
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    def __repr__(self):
        return f'<AppSetting {self.key}>'
