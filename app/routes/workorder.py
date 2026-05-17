from flask import Blueprint, render_template
from flask_login import login_required
from app.models.workorder import WorkOrder

bp = Blueprint('workorder', __name__)

@bp.route('/')
@login_required
def index():
    workorders = WorkOrder.query.all()
    return render_template('workorder.html', workorders=workorders)