from flask import Blueprint, render_template
from flask_login import login_required
from app.models.equipment import Equipment

bp = Blueprint('equipment', __name__)

@bp.route('/')
@login_required
def index():
    equipments = Equipment.query.all()
    return render_template('equipment.html', equipments=equipments)