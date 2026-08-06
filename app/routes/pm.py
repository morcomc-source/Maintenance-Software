from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.pm import PM
from app.models.pm_completion import PMCompletion   # ← Important for history
from app.models.user import User
from app.models.settings import PMMainEquipment, PMMachine, PMFrequency
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
from sqlalchemy import or_, cast, String

bp = Blueprint("pm", __name__)


@bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Delete
        delete_index = request.form.get("delete_index")
        if delete_index:
            pm = PM.query.get(int(delete_index))
            if pm:
                db.session.delete(pm)
                db.session.commit()
                flash("PM deleted.", "success")
            return redirect(url_for('pm.index'))

        # Add or Update
        index = request.form.get("index")
        main_equipment = request.form.get("main_equipment")
        sub_equipment = request.form.get("sub_equipment")
        frequency = request.form.get("frequency")
        last_done_str = request.form.get("last_done")
        last_done = None
        if last_done_str:
            try:
                last_done = datetime.strptime(last_done_str, "%Y-%m-%d").date()
            except:
                last_done = None

        next_due = last_done
        if last_done and frequency:
            try:
                delta_map = {
                    "Daily": relativedelta(days=1),
                    "Weekly": relativedelta(weeks=1),
                    "Bi-Weekly": relativedelta(weeks=2),
                    "Monthly": relativedelta(months=1),
                    "Quarterly": relativedelta(months=3),
                    "Bi-Annually": relativedelta(months=6),
                    "Annually": relativedelta(years=1)
                }
                delta = delta_map.get(frequency)
                if delta:
                    next_due = last_done + delta
            except:
                next_due = last_done

        # Build checklist
        checklist = []
        item_list = request.form.getlist("checklist_item[]")
        type_list = request.form.getlist("checklist_type[]")
        for i in range(len(item_list)):
            text = item_list[i].strip()
            if text:
                item_type = type_list[i] if i < len(type_list) else "task"
                if item_type == "title":
                    checklist.append({"type": "title", "item": text})
                else:
                    checklist.append({"type": "task", "item": text, "completed": False})

        assigned_user_id = request.form.get('assigned_user')

        if index:  # Update
            try:
                index = int(index)
                pm = PM.query.get(index)
                if pm:
                    pm.main_equipment = main_equipment
                    pm.sub_equipment = sub_equipment or ""
                    pm.frequency = frequency
                    pm.last_done = last_done
                    pm.next_due = next_due
                    pm.checklist = checklist
                    pm.assigned_user_id = int(assigned_user_id) if assigned_user_id else None
                    db.session.commit()
                    flash("PM updated.", "success")
            except:
                flash("Invalid ID", "danger")
        else:  # Add new
            if main_equipment and frequency:
                new_pm = PM(
                    main_equipment=main_equipment,
                    sub_equipment=sub_equipment or "",
                    frequency=frequency,
                    last_done=last_done,
                    next_due=next_due,
                    checklist=checklist,
                    assigned_user_id=int(assigned_user_id) if assigned_user_id else None
                )
                db.session.add(new_pm)
                db.session.commit()
                flash("PM added.", "success")
            else:
                flash("Name is required.", "danger")
        return redirect(url_for("pm.index"))

    # GET - show all PMs
    search = request.args.get('search')
    query = PM.query.outerjoin(User)
    if search:
        query = query.filter(
            or_(
                PM.main_equipment.ilike(f'%{search}%'),
                PM.sub_equipment.ilike(f'%{search}%'),
                PM.frequency.ilike(f'%{search}%'),
                cast(PM.last_done, String).ilike(f'%{search}%'),
                cast(PM.next_due, String).ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )

    if current_user.role == 'technician':
        query = query.filter(PM.assigned_user_id == current_user.id)

    pms = query.all()
    items = []
    for pm in pms:
        items.append({
            'id': pm.id,
            'main_equipment': pm.main_equipment,
            'sub_equipment': pm.sub_equipment,
            'frequency': pm.frequency,
            'last_done': pm.last_done.strftime('%Y-%m-%d') if pm.last_done else None,
            'next_due': pm.next_due.strftime('%Y-%m-%d') if pm.next_due else None,
            'checklist': pm.checklist or [],
            'assigned_user_id': pm.assigned_user_id,
            'assigned_to': pm.assigned_user.username if pm.assigned_user else 'N/A'
        })

    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    technicians = User.query.filter_by(role='technician').all() if current_user.role == 'admin' else []

    pm_mains = PMMainEquipment.query.order_by(PMMainEquipment.name).all()
    pm_machines = PMMachine.query.order_by(PMMachine.name).all()
    pm_frequencies = PMFrequency.query.order_by(PMFrequency.name).all()
    machines_json = [
        {
            "id": m.id,
            "name": m.name,
            "main_name": m.main_equipment.name if m.main_equipment else None
        }
        for m in pm_machines
    ]
    return render_template(
        "pm.html",
        items=items,
        today=today,
        tomorrow=tomorrow,
        technicians=technicians,
        search=search,
        pm_mains=pm_mains,
        pm_machines=pm_machines,
        pm_frequencies=pm_frequencies,
        machines_json=machines_json
    )


# ====================== COMPLETE PM (with Full History) ======================
@bp.route("/complete_pm/<int:id>", methods=["POST"])
@login_required
def complete_pm(id):
    pm = PM.query.get_or_404(id)
    
    if current_user.role == 'technician' and current_user.id != pm.assigned_user_id:
        return jsonify({'success': False, 'error': 'Not assigned'}), 403

    data = request.get_json()
    completed_tasks = data.get('completed', [])
    notes = data.get('notes', '')

    # Re-build checklist
    checklist = list(pm.checklist) if pm.checklist else []
    task_idx = 0
    for item in checklist:
        if item.get('type') == 'task':
            if task_idx < len(completed_tasks):
                item['completed'] = bool(completed_tasks[task_idx])
                task_idx += 1

    # === SAVE FULL HISTORY ===
    completion = PMCompletion(
        pm_id=pm.id,
        completed_by_id=current_user.id,
        notes=notes.strip() if notes else None,
        checklist_results=checklist
    )
    db.session.add(completion)

    # Update main PM
    pm.checklist = checklist
    today = datetime.now().date()
    pm.last_done = today

    if pm.frequency:
        delta_map = {
            "Daily": relativedelta(days=1),
            "Weekly": relativedelta(weeks=1),
            "Bi-Weekly": relativedelta(weeks=2),
            "Monthly": relativedelta(months=1),
            "Quarterly": relativedelta(months=3),
            "Bi-Annually": relativedelta(months=6),
            "Annually": relativedelta(years=1)
        }
        delta = delta_map.get(pm.frequency)
        if delta:
            pm.next_due = today + delta

    db.session.commit()
    return jsonify({'success': True})


# ====================== PM HISTORY ======================
@bp.route('/history/<int:pm_id>')
@login_required
def history(pm_id):
    pm = PM.query.get_or_404(pm_id)
    
    if current_user.role == 'technician' and current_user.id != pm.assigned_user_id:
        flash("You can only view history for PMs assigned to you.", "danger")
        return redirect(url_for('pm.index'))

    completions = PMCompletion.query.filter_by(pm_id=pm_id)\
                    .order_by(PMCompletion.completed_date.desc()).all()

    return render_template('pm_history.html', 
                         pm=pm,
                         completions=completions,
                         title=f"History - {pm.main_equipment}")


# ====================== EXPORT PDF ======================
@bp.route('/export_pm_pdf/<int:id>')
@login_required
def export_pm_pdf(id):
    pm = PM.query.get_or_404(id)
    if current_user.role == 'technician' and current_user.id != pm.assigned_user_id:
        flash("Access denied.", "danger")
        return redirect(url_for('pm.index'))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 20)
    c.drawString(1 * inch, height - 1 * inch, "Preventative Maintenance Report")
    c.setFont("Helvetica", 14)
    y = height - 1.8 * inch

    c.drawString(1 * inch, y, f"Main Equipment: {pm.main_equipment}")
    y -= 0.4 * inch
    c.drawString(1 * inch, y, f"Sub Equipment: {pm.sub_equipment or 'N/A'}")
    y -= 0.4 * inch
    c.drawString(1 * inch, y, f"Frequency: {pm.frequency}")
    y -= 0.4 * inch
    c.drawString(1 * inch, y, f"Last Done: {pm.last_done or 'N/A'}")
    y -= 0.4 * inch
    c.drawString(1 * inch, y, f"Next Due: {pm.next_due or 'N/A'}")
    y -= 0.8 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, y, "Checklist")
    y -= 0.5 * inch
    c.setFont("Helvetica", 12)

    def draw_checkbox(x, y_pos, checked=False):
        size = 12
        c.rect(x, y_pos - 2, size, size, stroke=1, fill=0)
        if checked:
            c.setStrokeColorRGB(0, 0.6, 0)
            c.setLineWidth(1.5)
            c.line(x + 2, y_pos + 2, x + 5, y_pos + 7)
            c.line(x + 5, y_pos + 7, x + 10, y_pos - 2)
            c.setLineWidth(1)

    if pm.checklist:
        for item in pm.checklist:
            if item['type'] == 'title':
                c.setFont("Helvetica-Bold", 13)
                c.drawString(1 * inch, y, item['item'])
                c.setFont("Helvetica", 12)
            else:
                checked = item.get('completed', False)
                draw_checkbox(1 * inch, y, checked)
                c.drawString(1 * inch + 0.45 * inch, y, item['item'])
            y -= 0.4 * inch
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
    else:
        c.drawString(1 * inch, y, "No checklist items.")

    c.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"PM_{pm.main_equipment.replace(' ', '_')}_{id}.pdf",
        mimetype='application/pdf'
    )


# ====================== MANAGE USERS ======================
@bp.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash("Access denied.", "danger")
        return redirect(url_for('pm.index'))

    if request.method == 'POST':
        # Add User
        if request.form.get('add_user'):
            username = request.form.get('username')
            email = request.form.get('email') or None
            password = request.form.get('password')
            role = request.form.get('role')

            if not username or not password or not role:
                flash("Username, password, and role are required.", "danger")
            elif User.query.filter_by(username=username).first():
                flash("Username already taken.", "danger")
            else:
                new_user = User(username=username, email=email, role=role)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash(f"User '{username}' added successfully!", "success")

        # Update User (from modal)
        elif request.form.get('update_user'):
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user:
                user.username = request.form.get('username')
                user.email = request.form.get('email') or None
                user.role = request.form.get('role')
                password = request.form.get('password')
                if password and password.strip():
                    user.set_password(password)
                db.session.commit()
                flash("User updated successfully!", "success")

        # Delete User
        elif request.form.get('delete_user'):
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user and user.id != current_user.id:
                db.session.delete(user)
                db.session.commit()
                flash("User deleted successfully.", "success")
            else:
                flash("Cannot delete this user.", "danger")

    users = User.query.all()
    users_list = [{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users]
   
    return render_template('users.html', users=users, users_json=users_list)

# ====================== DELETE PM HISTORY RECORD (Admin Only) ======================
@bp.route('/history/delete/<int:completion_id>', methods=['POST'])
@login_required
def delete_history(completion_id):
    if current_user.role != 'admin':
        flash("Only admins can delete history records.", "danger")
        return redirect(url_for('pm.index'))

    completion = PMCompletion.query.get_or_404(completion_id)
    pm_id = completion.pm_id
    db.session.delete(completion)
    db.session.commit()
    flash("History record deleted.", "success")
    return redirect(url_for('pm.history', pm_id=pm_id))
