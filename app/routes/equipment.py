from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models.equipment import Equipment

bp = Blueprint('equipment', __name__)

@bp.route('/')
@login_required
def index():
    query = request.args.get('q', '').strip()
   
    if query:
        equipment_list = Equipment.query.filter(
            (Equipment.equipment_id.ilike(f'%{query}%')) |
            (Equipment.name.ilike(f'%{query}%')) |
            (Equipment.serial_number.ilike(f'%{query}%')) |
            (Equipment.barcode.ilike(f'%{query}%')) |
            (Equipment.location.ilike(f'%{query}%'))
        ).order_by(Equipment.equipment_id).all()
    else:
        equipment_list = Equipment.query.order_by(Equipment.equipment_id).all()
   
    return render_template('equipment/list.html', equipment_list=equipment_list)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        last_eq = Equipment.query.order_by(Equipment.id.desc()).first()
        next_number = (last_eq.id + 1) if last_eq else 1
        equipment_id = f"EQ-{next_number:04d}"

        purchase_date_str = request.form.get('purchase_date')
        purchase_date = None
        if purchase_date_str:
            try:
                from datetime import datetime
                purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except:
                purchase_date = None

        eq = Equipment(
            equipment_id=equipment_id,
            name=request.form.get('name'),
            serial_number=request.form.get('serial_number'),
            model=request.form.get('model'),
            manufacturer=request.form.get('manufacturer'),
            location=request.form.get('location'),
            purchase_date=purchase_date,
            status=request.form.get('status', 'Active'),
            barcode=request.form.get('barcode'),
            notes=request.form.get('notes')
        )
        db.session.add(eq)
        db.session.commit()
        flash(f'Equipment {equipment_id} added successfully!', 'success')
        return redirect(url_for('equipment.index'))
  
    return render_template('equipment/new.html')
  

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    eq = Equipment.query.get_or_404(id)
  
    if request.method == 'POST':
        eq.name = request.form.get('name')
        eq.serial_number = request.form.get('serial_number')
        eq.model = request.form.get('model')
        eq.manufacturer = request.form.get('manufacturer')
        eq.location = request.form.get('location')
        eq.status = request.form.get('status')
        eq.barcode = request.form.get('barcode')
        eq.notes = request.form.get('notes')
      
        purchase_date_str = request.form.get('purchase_date')
        if purchase_date_str:
            try:
                from datetime import datetime
                eq.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except:
                pass
              
        db.session.commit()
        flash('Equipment updated successfully!', 'success')
        return redirect(url_for('equipment.index'))
  
    return render_template('equipment/edit.html', eq=eq)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash("Only admins can delete equipment.", "danger")
        return redirect(url_for('equipment.index'))
  
    eq = Equipment.query.get_or_404(id)
    db.session.delete(eq)
    db.session.commit()
    flash('Equipment deleted successfully.', 'success')
    return redirect(url_for('equipment.index'))


# ====================== SEARCH FOR WORK ORDER ======================
@bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
   
    results = Equipment.query.filter(
        (Equipment.name.ilike(f'%{query}%')) |
        (Equipment.equipment_id.ilike(f'%{query}%')) |
        (Equipment.barcode.ilike(f'%{query}%'))
    ).limit(10).all()
   
    return jsonify([{
        'id': eq.id,
        'equipment_id': eq.equipment_id,
        'name': eq.name,
        'barcode': eq.barcode
    } for eq in results])