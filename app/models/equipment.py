from app import db

class Equipment(db.Model):
    __tablename__ = 'equipment'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Operational')
    last_maintenance = db.Column(db.Date)
    
    def __repr__(self):
        return f'<Equipment {self.name}>'