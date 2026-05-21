from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.workorder import WorkOrder
from app.models.user import User
from datetime import datetime

bp = Blueprint('workorder', __name__)


@bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        workorders = WorkOrder.query.order_by(WorkOrder.created_at.desc()).all()
        technicians = User.query.filter_by(role='technician').all()
    else:
        # Technicians only see work orders assigned to them
        workorders = WorkOrder.query.filter_by(assigned_to_id=current_user.id)\
                        .order_by(WorkOrder.created_at.desc()).all()
        technicians = []

    return render_template('workorder/list.html', 
                         workorders=workorders, 
                         technicians=technicians)


@bp.route('/new')
@login_required
def new():
    technicians = User.query.filter_by(role='technician').all() if current_user.role == 'admin' else []
    return render_template('workorder.html', technicians=technicians)


@bp.route('/new', methods=['POST'])
@login_required
def create():
    equipment = request.form.get('equipment')
    description = request.form.get('description')
    assigned_to_id = request.form.get('assigned_to_id')

    if not equipment or not description:
        flash("Equipment and Description are required", "danger")
        return redirect(url_for('workorder.new'))

    try:
        assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    except:
        assigned_to_id = None

    new_wo = WorkOrder(
        equipment=equipment,
        description=description,
        status="Assigned" if assigned_to_id else "Open",
        created_by_id=current_user.id,
        assigned_to_id=assigned_to_id,
        created_at=datetime.utcnow()
    )

    db.session.add(new_wo)
    db.session.commit()

    flash("✅ Work Order created successfully!", "success")
    return redirect(url_for('workorder.index'))


@bp.route('/assign/<int:wo_id>', methods=['POST'])
@login_required
def assign(wo_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Admin only'}), 403

    data = request.get_json()
    assigned_to_id = data.get('assigned_to_id')

    wo = WorkOrder.query.get_or_404(wo_id)
    wo.assigned_to_id = assigned_to_id
    wo.assigned_at = datetime.utcnow()
    wo.status = "Assigned" if assigned_to_id else "Open"

    db.session.commit()
    return jsonify({'success': True})