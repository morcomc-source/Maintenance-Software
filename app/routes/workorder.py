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
    if current_user.role == 'admin':
        workorders = WorkOrder.query.order_by(
            WorkOrder.status == 'Completed',      # Completed at bottom
            (WorkOrder.expected_completion_date < datetime.now().date()).desc(),  # Overdue at top
            WorkOrder.priority.desc(),            # Highest priority first
            WorkOrder.created_at.desc()
        ).all()
        technicians = User.query.filter_by(role='technician').all()
    else:
        workorders = WorkOrder.query.filter_by(assigned_to_id=current_user.id)\
                        .order_by(
                            WorkOrder.status == 'Completed',
                            (WorkOrder.expected_completion_date < datetime.now().date()).desc(),
                            WorkOrder.priority.desc(),
                            WorkOrder.created_at.desc()
                        ).all()
        technicians = []
   
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
    description = request.form.get('description')
    assigned_to_id = request.form.get('assigned_to_id')
    
    if not equipment or not description:
        flash("Equipment and Description are required", "danger")
        return redirect(url_for('workorder.new'))
    
    try:
        assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    except:
        assigned_to_id = None

    # Priority
    try:
        priority = int(request.form.get('priority'))
    except:
        priority = None

    # Expected Completion Date
    expected_str = request.form.get('expected_completion_date')
    expected_completion_date = None
    if expected_str:
        try:
            expected_completion_date = datetime.strptime(expected_str, '%Y-%m-%d').date()
        except ValueError:
            expected_completion_date = None

    new_wo = WorkOrder(
        equipment=equipment,
        description=description,
        status="Assigned" if assigned_to_id else "Open",
        priority=priority,
        expected_completion_date=expected_completion_date,
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
    db.session.commit()
    return jsonify({'success': True})


# ====================== COMPLETE WORK ORDER ======================
@bp.route('/complete/<int:wo_id>', methods=['POST'])
@login_required
def complete(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403
    
    data = request.get_json()
    notes = data.get('notes', '')
    parts_used = data.get('parts_used', [])
    
    try:
        for item in parts_used:
            part_name = item.get('name')
            quantity_used = int(item.get('quantity', 0))
            
            if quantity_used <= 0:
                continue
                
            part = Part.query.filter_by(name=part_name).first()
            if part:
                if part.qty < quantity_used:
                    return jsonify({'success': False, 'error': f'Not enough stock for {part_name}'}), 400
                
                part.qty -= quantity_used   # Deduct from stock
            else:
                print(f"⚠️ Part not found: {part_name}")
        
        # Update Work Order
        wo.status = "Completed"
        wo.completed_by_id = current_user.id
        wo.completed_at = datetime.utcnow()
        wo.completion_notes = notes.strip() if notes else None
        wo.parts_used = parts_used
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print("Complete Error:", str(e))   # This will show in terminal
        return jsonify({'success': False, 'error': str(e)}), 500

# ====================== PAUSE ======================
@bp.route('/pause/<int:wo_id>', methods=['POST'])
@login_required
def pause(wo_id):
    wo = WorkOrder.query.get_or_404(wo_id)
    
    if current_user.role == 'technician' and wo.assigned_to_id != current_user.id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403
    
    wo.status = "On Hold"
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