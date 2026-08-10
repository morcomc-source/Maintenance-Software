from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.workorder import WorkOrder
from app.models.user import User
from app.models.part import Part
from datetime import datetime

bp = Blueprint('workorder', __name__)


@bp.route('/')
@login_required
def index():
    query = request.args.get('q', '').strip()
    
    # Main list = incomplete only (completed live on Work Order History)
    base = WorkOrder.query.filter(WorkOrder.status != 'Completed')

    if query:
        base = base.filter(
            (WorkOrder.equipment.ilike(f'%{query}%')) |
            (WorkOrder.equipment_id.ilike(f'%{query}%'))
        )

    if current_user.role != 'admin':
        base = base.filter_by(assigned_to_id=current_user.id)

    workorders = base.order_by(
        (WorkOrder.expected_completion_date < datetime.now().date()).desc(),
        WorkOrder.priority.desc(),
        WorkOrder.created_at.desc()
    ).all()
    
    technicians = User.query.filter_by(role='technician').all() if current_user.role == 'admin' else []
    today = datetime.now().date()
    
    return render_template('workorder/list.html',
                         workorders=workorders,
                         technicians=technicians,
                         today=today)

@bp.route('/new')
@login_required
def new():
    technicians = User.query.filter_by(role='technician').all() if current_user.role == 'admin' else []
    return render_template('workorder.html', technicians=technicians)

@bp.route('/new', methods=['POST'])
@login_required
def create():
    equipment = request.form.get('equipment')
    equipment_id = request.form.get('equipment_id')
    description = request.form.get('description')
    assigned_to_id = request.form.get('assigned_to_id')
    
    # NEW: Get Priority and Expected Date from form
    priority = request.form.get('priority')
    expected_str = request.form.get('expected_completion_date')

    if not equipment or not description:
        flash("Equipment and Description are required", "danger")
        return redirect(url_for('workorder.new'))

    try:
        assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    except:
        assigned_to_id = None

    # Convert priority to int
    try:
        priority = int(priority) if priority else None
    except:
        priority = None

    # Convert expected date
    expected_completion_date = None
    if expected_str:
        try:
            expected_completion_date = datetime.strptime(expected_str, '%Y-%m-%d').date()
        except ValueError:
            expected_completion_date = None

    new_wo = WorkOrder(
        equipment=equipment,
        equipment_id=equipment_id,
        description=description,
        status="Assigned" if assigned_to_id else "Open",
        priority=priority,
        expected_completion_date=expected_completion_date,
        created_by_id=current_user.id,
        assigned_to_id=assigned_to_id,
        created_at=datetime.utcnow()
    )
   
    try:
        db.session.add(new_wo)
        db.session.commit()
        flash("✅ Work Order created successfully!", "success")
        return redirect(url_for('workorder.index'))
    except Exception as e:
        db.session.rollback()
        flash("Error saving work order. Please try again.", "danger")
        print("Work Order Save Error:", str(e))
        return redirect(url_for('workorder.new'))

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


# ====================== EDIT WORK ORDER ======================
@bp.route('/edit/<int:wo_id>')
@login_required
def edit(wo_id):
    if current_user.role != 'admin':
        flash("Only admins can edit work orders.", "danger")
        return redirect(url_for('workorder.index'))
  
    wo = WorkOrder.query.get_or_404(wo_id)
    technicians = User.query.filter_by(role='technician').all()
    return render_template('workorder/edit.html', wo=wo, technicians=technicians)


@bp.route('/edit/<int:wo_id>', methods=['POST'])
@login_required
def update(wo_id):
    if current_user.role != 'admin':
        flash("Only admins can edit work orders.", "danger")
        return redirect(url_for('workorder.index'))
  
    wo = WorkOrder.query.get_or_404(wo_id)
  
    wo.equipment = request.form.get('equipment')
    wo.description = request.form.get('description')
    wo.status = request.form.get('status')
  
    try:
        wo.priority = int(request.form.get('priority'))
    except:
        wo.priority = None
      
    expected_str = request.form.get('expected_completion_date')
    if expected_str:
        try:
            wo.expected_completion_date = datetime.strptime(expected_str, '%Y-%m-%d').date()
        except ValueError:
            wo.expected_completion_date = None
    else:
        wo.expected_completion_date = None
  
    assigned_to_id = request.form.get('assigned_to_id')
    wo.assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    if wo.assigned_to_id:
        wo.assigned_at = datetime.utcnow()
        wo.status = "Assigned"
  
    db.session.commit()
    flash("Work Order updated successfully!", "success")
    return redirect(url_for('workorder.index'))


# ====================== DETAILS ======================
@bp.route('/details/<int:wo_id>')
@login_required
def details(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    
    # Force load relationships
    if wo.completed_by_id:
        wo.completed_by = User.query.get(wo.completed_by_id)
    
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        flash("You can only view your assigned work orders.", "danger")
        return redirect(url_for('workorder.index'))
   
    return render_template('workorder/details.html', wo=wo)


# ====================== IN PROGRESS ======================
@bp.route('/in_progress/<int:wo_id>', methods=['POST'])
@login_required
def mark_in_progress(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403
    
    wo.status = "In Progress"
    now = datetime.utcnow()
    if not wo.started_at:
        wo.started_at = now
    else:
        wo.resumed_at = now
    wo.paused_at = None
    wo.pause_reason = None
    wo.pause_reason = None
    db.session.commit()
    return jsonify({'success': True})


# ====================== COMPLETE WORK ORDER ======================

@bp.route('/complete/<int:wo_id>', methods=['POST'])
@login_required
def complete(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403

    data = request.get_json(silent=True) or {}
    notes = data.get('notes', '')
    parts_used = data.get('parts_used', [])

    try:
        # Deduct parts if Part model available + log transaction
        try:
            from app.models.part import Part
            from app.models.part_transaction import PartTransaction
            for pu in parts_used or []:
                part_name = pu.get('name')
                qty = int(pu.get('quantity') or 0)
                if not part_name or qty <= 0:
                    continue
                part = Part.query.filter(Part.name.ilike(part_name)).first()
                if part:
                    part.qty = max(0, int(part.qty or 0) - qty)
                    db.session.add(PartTransaction(
                        part_id=part.id,
                        transaction_type='wo_use',
                        quantity=qty,
                        user_id=current_user.id,
                        username=current_user.username,
                        reference=f'WO-{wo.id}',
                        notes=None,
                    ))
        except Exception as part_err:
            print("Part deduct warning:", part_err)

        now = datetime.utcnow()
        # Accumulate active work time (if currently in progress, not paused)
        last_start = wo.resumed_at or wo.started_at
        if last_start:
            if wo.paused_at is None or (wo.resumed_at and wo.paused_at and wo.resumed_at >= wo.paused_at):
                delta = int((now - last_start).total_seconds())
                if delta > 0:
                    wo.total_work_seconds = (wo.total_work_seconds or 0) + delta

        wo.status = "Completed"
        wo.completed_by_id = current_user.id
        wo.completed_at = now
        wo.completion_notes = notes.strip() if notes else None
        wo.parts_used = parts_used if parts_used else wo.parts_used
        wo.paused_at = None
        wo.pause_reason = None

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print("Complete Error:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500


# ====================== PAUSE ======================

@bp.route('/pause/<int:wo_id>', methods=['POST'])
@login_required
def pause(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403

    data = request.get_json(silent=True) or {}
    reason = (data.get('reason') or data.get('pause_reason') or '').strip()
    if not reason:
        return jsonify({'success': False, 'error': 'Pause reason is required'}), 400

    now = datetime.utcnow()

    # Add active segment since last start/resume into total
    last_start = wo.resumed_at or wo.started_at
    if last_start and (wo.paused_at is None or (wo.resumed_at and wo.paused_at and wo.resumed_at >= wo.paused_at)):
        delta = int((now - last_start).total_seconds())
        if delta > 0:
            wo.total_work_seconds = (wo.total_work_seconds or 0) + delta

    wo.status = "On Hold"
    wo.paused_at = now
    wo.pause_reason = reason
    db.session.commit()
    return jsonify({'success': True})


# ====================== DELETE WORK ORDER (Admin Only) ======================
@bp.route('/delete/<int:wo_id>', methods=['POST'])
@login_required
def delete(wo_id):
    if current_user.role != 'admin':
        flash("Only admins can delete work orders.", "danger")
        return redirect(url_for('workorder.index'))
   
    wo = WorkOrder.query.get_or_404(wo_id)
    db.session.delete(wo)
    db.session.commit()
    flash("Work Order deleted successfully.", "success")
    return redirect(url_for('workorder.index'))


# ====================== WORK ORDER HISTORY (completed) ======================
@bp.route("/history")
@login_required
def history():
    """List completed work orders with filters."""
    from datetime import datetime, timedelta
    from sqlalchemy.orm import joinedload

    q = (request.args.get("q") or "").strip()
    user = (request.args.get("user") or "").strip()
    date_from = (request.args.get("from") or "").strip()
    date_to = (request.args.get("to") or "").strip()

    query = WorkOrder.query.options(
        joinedload(WorkOrder.completed_by),
        joinedload(WorkOrder.assigned_to),
    ).filter(WorkOrder.status == "Completed")

    if current_user.role == "technician":
        query = query.filter(
            (WorkOrder.completed_by_id == current_user.id) |
            (WorkOrder.assigned_to_id == current_user.id)
        )

    if user:
        query = query.join(User, WorkOrder.completed_by_id == User.id).filter(
            User.username.ilike(f"%{user}%")
        )

    if q:
        query = query.filter(
            (WorkOrder.equipment.ilike(f"%{q}%")) |
            (WorkOrder.equipment_id.ilike(f"%{q}%")) |
            (WorkOrder.description.ilike(f"%{q}%"))
        )

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(WorkOrder.completed_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(WorkOrder.completed_at < dt_to)
        except ValueError:
            pass

    workorders = query.order_by(WorkOrder.completed_at.desc()).limit(500).all()

    usernames = [
        u[0] for u in db.session.query(User.username)
        .join(WorkOrder, WorkOrder.completed_by_id == User.id)
        .filter(WorkOrder.status == "Completed")
        .distinct().order_by(User.username).all()
        if u[0]
    ]

    return render_template(
        "workorder/history.html",
        workorders=workorders,
        usernames=usernames,
        filters={"q": q, "user": user, "from": date_from, "to": date_to},
    )
