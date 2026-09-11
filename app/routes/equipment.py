from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from app import db
from sqlalchemy import or_
from app.models.equipment import Equipment

bp = Blueprint('equipment', __name__)

def _blank_to_none(value):
    if value is None:
        return None
    value = value.strip()
    return value or None



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
            serial_number=_blank_to_none(request.form.get('serial_number')),
            model=request.form.get('model'),
            manufacturer=request.form.get('manufacturer'),
            location=request.form.get('location'),
            purchase_date=purchase_date,
            status=request.form.get('status', 'Active'),
            barcode=_blank_to_none(request.form.get('barcode')),
            notes=request.form.get('notes')
        )
        db.session.add(eq)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Could not save. Serial number or barcode may already be in use (leave them blank if you do not have them).", "danger")
            print("Equipment save error:", e)
            return redirect(url_for("equipment.new"))
        flash(f'Equipment {equipment_id} added successfully!', 'success')
        return redirect(url_for('equipment.index'))
  
    return render_template('equipment/new.html')
  

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ('admin', 'supervisor'):
        flash("Only admins can edit equipment.", "danger")
        return redirect(url_for('equipment.index'))
    eq = Equipment.query.get_or_404(id)
  
    if request.method == 'POST':
        eq.name = request.form.get('name')
        eq.serial_number = _blank_to_none(request.form.get('serial_number'))
        eq.model = request.form.get('model')
        eq.manufacturer = request.form.get('manufacturer')
        eq.location = request.form.get('location')
        eq.status = request.form.get('status')
        eq.barcode = _blank_to_none(request.form.get('barcode'))
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
    if current_user.role not in ('admin', 'supervisor'):
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

@bp.route('/details/<int:id>')
@login_required
def details(id):
    if current_user.role not in ('admin', 'supervisor', 'technician'):
        flash("Access denied.", "danger")
        return redirect(url_for('equipment.index'))
    from app.models.workorder import WorkOrder
    from app.models.pm import PM
    from app.models.pm_completion import PMCompletion
    eq = Equipment.query.get_or_404(id)
    wo_q = WorkOrder.query.filter(WorkOrder.status == 'Completed')
    match = []
    if eq.equipment_id:
        match.append(WorkOrder.equipment_id == eq.equipment_id)
    if eq.name:
        match.append(WorkOrder.equipment.ilike(eq.name))
    if match:
        wo_q = wo_q.filter(or_(*match))
    else:
        wo_q = wo_q.filter(WorkOrder.id == -1)
    workorders = wo_q.order_by(WorkOrder.completed_at.desc()).limit(200).all()

    pm_q = PM.query
    pm_match = []
    if getattr(eq, "equipment_id", None):
        pm_match.append(PM.equipment_id == eq.equipment_id)
    if eq.name:
        name = eq.name
        pm_match.append(PM.main_equipment.ilike(name))
        pm_match.append(PM.sub_equipment.ilike(name))
    if getattr(eq, "location", None):
        pm_match.append(PM.main_equipment.ilike(eq.location))
    pms = pm_q.filter(or_(*pm_match)).all() if pm_match else []
    pm_ids = [pm.id for pm in pms]
    completions = []
    if pm_ids:
        completions = (PMCompletion.query.filter(PMCompletion.pm_id.in_(pm_ids))
                       .order_by(PMCompletion.completed_date.desc()).limit(200).all())

    parts = []
    def _when(dt):
        return dt.strftime('%Y-%m-%d') if dt else '—'
    for wo in workorders:
        for pu in (wo.parts_used or []):
            parts.append({
                'when': _when(wo.completed_at),
                'name': pu.get('name') or '—',
                'qty': pu.get('quantity') or pu.get('qty') or '',
                'source': f'WO-{wo.id}',
            })
    for row in completions:
        for pu in (row.parts_used or []):
            parts.append({
                'when': _when(row.completed_date),
                'name': pu.get('name') or '—',
                'qty': pu.get('quantity') or pu.get('qty') or '',
                'source': f'PM-{row.pm_id}',
            })
    from app.models.equipment_document import EquipmentDocument
    from app.models.equipment_bom import EquipmentBOM
    from app.models.part import Part
    documents = (EquipmentDocument.query.filter_by(equipment_id=eq.id)
                 .order_by(EquipmentDocument.uploaded_at.desc()).all())
    bom_rows = (EquipmentBOM.query.filter_by(equipment_id=eq.id)
                .order_by(EquipmentBOM.id.asc()).all())
    bom = []
    for row in bom_rows:
        part = Part.query.get(row.part_id)
        bom.append({"row": row, "part": part})
    return render_template('equipment/details.html', eq=eq, workorders=workorders,
                           completions=completions, parts=parts, documents=documents, bom=bom)


import os
from werkzeug.utils import secure_filename
from app.models.equipment_document import EquipmentDocument

ALLOWED_DOC_EXT = {
    "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt",
    "png", "jpg", "jpeg", "gif", "webp",
}

def _docs_dir(eq_id):
    folder = os.path.join(current_app.instance_path, "equipment_docs", str(eq_id))
    os.makedirs(folder, exist_ok=True)
    return folder

@bp.route("/details/<int:id>/documents", methods=["POST"])
@login_required
def upload_document(id):
    if current_user.role not in ("admin", "supervisor"):
        flash("Only admin or supervisor can upload documents.", "danger")
        return redirect(url_for("equipment.details", id=id))
    eq = Equipment.query.get_or_404(id)
    files = request.files.getlist("files")
    saved = 0
    for f in files:
        if not f or not f.filename:
            continue
        name = secure_filename(f.filename)
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in ALLOWED_DOC_EXT:
            flash(f"Skipped {f.filename}: file type not allowed.", "warning")
            continue
        folder = _docs_dir(eq.id)
        stored = name
        dest = os.path.join(folder, stored)
        base, extra = os.path.splitext(name)
        n = 1
        while os.path.exists(dest):
            stored = f"{base}_{n}{extra}"
            dest = os.path.join(folder, stored)
            n += 1
        f.save(dest)
        title = (request.form.get("title") or "").strip()
        if not title:
            title = f.filename
        doc = EquipmentDocument(
            equipment_id=eq.id,
            original_name=f.filename,
            title=title,
            stored_name=stored,
            content_type=f.mimetype,
            size_bytes=os.path.getsize(dest),
            uploaded_by_id=current_user.id,
        )
        db.session.add(doc)
        saved += 1
    if saved:
        db.session.commit()
        flash(f"Uploaded {saved} file(s).", "success")
    else:
        flash("No files uploaded.", "warning")
    return redirect(url_for("equipment.details", id=id) + "#docs")

@bp.route("/documents/<int:doc_id>/view")
@login_required
def view_document(doc_id):
    if current_user.role not in ("admin", "supervisor", "technician"):
        flash("Access denied.", "danger")
        return redirect(url_for("equipment.index"))
    doc = EquipmentDocument.query.get_or_404(doc_id)
    folder = _docs_dir(doc.equipment_id)
    return send_from_directory(folder, doc.stored_name, as_attachment=False, download_name=doc.original_name)

@bp.route("/documents/<int:doc_id>/download")
@login_required
def download_document(doc_id):
    if current_user.role not in ("admin", "supervisor", "technician"):
        flash("Access denied.", "danger")
        return redirect(url_for("equipment.index"))
    doc = EquipmentDocument.query.get_or_404(doc_id)
    folder = _docs_dir(doc.equipment_id)
    return send_from_directory(folder, doc.stored_name, as_attachment=True, download_name=doc.original_name)

@bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id):
    if current_user.role not in ("admin", "supervisor"):
        flash("Only admin or supervisor can delete documents.", "danger")
        return redirect(url_for("equipment.index"))
    doc = EquipmentDocument.query.get_or_404(doc_id)
    eq_id = doc.equipment_id
    folder = _docs_dir(eq_id)
    path = os.path.join(folder, doc.stored_name)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted.", "success")
    return redirect(url_for("equipment.details", id=eq_id) + "#docs")


from app.models.equipment_bom import EquipmentBOM
from app.models.part import Part

@bp.route("/details/<int:id>/bom", methods=["POST"])
@login_required
def add_bom(id):
    if current_user.role not in ("admin", "supervisor"):
        flash("Only admin or supervisor can edit the BOM.", "danger")
        return redirect(url_for("equipment.details", id=id))
    eq = Equipment.query.get_or_404(id)
    part_id = request.form.get("part_id")
    note = (request.form.get("note") or "").strip() or None
    try:
        qty = int(request.form.get("qty") or 1)
    except ValueError:
        qty = 1
    proprietary = True if request.form.get("proprietary") else False
    part = Part.query.get(part_id) if part_id else None
    if not part:
        flash("Pick a part from search first.", "warning")
        return redirect(url_for("equipment.details", id=id) + "#bom")
    exists = EquipmentBOM.query.filter_by(equipment_id=eq.id, part_id=part.id).first()
    if exists:
        flash("That part is already on this BOM.", "warning")
        return redirect(url_for("equipment.details", id=id) + "#bom")
    db.session.add(EquipmentBOM(
        equipment_id=eq.id,
        part_id=part.id,
        qty=max(1, qty),
        note=note,
        proprietary=proprietary,
    ))
    db.session.commit()
    flash("Part added to BOM.", "success")
    return redirect(url_for("equipment.details", id=id) + "#bom")

@bp.route("/bom/<int:row_id>/delete", methods=["POST"])
@login_required
def delete_bom(row_id):
    if current_user.role not in ("admin", "supervisor"):
        flash("Only admin or supervisor can edit the BOM.", "danger")
        return redirect(url_for("equipment.index"))
    row = EquipmentBOM.query.get_or_404(row_id)
    eq_id = row.equipment_id
    db.session.delete(row)
    db.session.commit()
    flash("Removed from BOM.", "success")
    return redirect(url_for("equipment.details", id=eq_id) + "#bom")
