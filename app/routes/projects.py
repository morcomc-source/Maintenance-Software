from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from app import db
from app.models.project import Project
from app.models.user import User
from app.models.equipment import Equipment
from app.models.settings import get_setting

bp = Blueprint('projects', __name__)

def _assignment_options():
    raw = get_setting('shutdown_assignment_list', 'Weld Shop\nPress Maintenance\nFacility Maintenance\nOutside Contractor')
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]

@bp.route('/', strict_slashes=False)
@login_required
def index():
    if current_user.role not in ('admin', 'supervisor'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    projects = Project.query.filter_by(status='Open').order_by(Project.created_at.desc()).all()
    return render_template('projects/list.html', projects=projects)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if current_user.role not in ('admin', 'supervisor'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        p = Project(
            priority=request.form.get('priority'),
            project_type=request.form.get('project_type'),
            location=request.form.get('location'),
            project=request.form.get('project'),
            parts_status=request.form.get('parts_status'),
            notes=request.form.get('notes'),
            equipment_id=request.form.get('equipment_id') or None,
            assigned_department=request.form.get('assigned_department') or None,
            created_by_id=current_user.id,
            status='Open',
        )
        db.session.add(p)
        db.session.commit()
        flash('Project added.', 'success')
        return redirect(url_for('projects.index'))
    equipment = Equipment.query.order_by(Equipment.name).all()
    locations = sorted({eq.location for eq in equipment if eq.location})
    users = User.query.filter(User.role.in_(['technician', 'supervisor'])).order_by(User.username).all()
    assignment_options = _assignment_options()
    return render_template('projects/new.html', equipment=equipment, users=users, locations=locations, assignment_options=assignment_options)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ('admin', 'supervisor'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    p = Project.query.get_or_404(id)
    if request.method == 'POST':
        p.priority = request.form.get('priority')
        p.project_type = request.form.get('project_type')
        p.location = request.form.get('location')
        p.project = request.form.get('project')
        p.parts_status = request.form.get('parts_status')
        p.notes = request.form.get('notes')
        p.equipment_id = request.form.get('equipment_id') or None
        p.assigned_department = request.form.get('assigned_department') or None
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('projects.index'))
    equipment = Equipment.query.order_by(Equipment.name).all()
    locations = sorted({eq.location for eq in equipment if eq.location})
    users = User.query.filter(User.role.in_(['technician', 'supervisor'])).order_by(User.username).all()
    assignment_options = _assignment_options()
    return render_template(
        'projects/edit.html',
        project=p,
        equipment=equipment,
        users=users,
        locations=locations,
        assignment_options=assignment_options,
    )

@bp.route('/export')
@login_required
def export():
    if current_user.role not in ('admin', 'supervisor'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    loc = request.args.get('location', '').strip()
    q = Project.query.filter_by(status='Open')
    if loc:
        q = q.filter(Project.location.ilike(f'%{loc}%'))
    projects = q.order_by(Project.created_at.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.title = f"Shutdown Projects" + (f" — {loc}" if loc else "")
    headers = ["Priority", "Type", "Location", "Project", "Parts Status", "Assigned To", "Notes", "Created"]
    ws.append(headers)
    for proj in projects:
        ws.append([
            proj.priority or "",
            proj.project_type or "",
            proj.location or "",
            proj.project or "",
            proj.parts_status or "",
            proj.assigned_department or "",
            proj.notes or "",
            proj.created_at.strftime("%Y-%m-%d") if proj.created_at else "",
        ])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name="shutdown_projects.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.route('/export_pdf')
@login_required
def export_pdf():
    if current_user.role not in ('admin', 'supervisor'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    loc = request.args.get('location', '').strip()
    q = Project.query.filter_by(status='Open')
    if loc:
        q = q.filter(Project.location.ilike(f'%{loc}%'))
    projects = q.order_by(Project.created_at.desc()).all()
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    bio = BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Shutdown Projects" + (f" — {loc}" if loc else ""), styles['Title']), Spacer(1, 12)]
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    wrap_style = ParagraphStyle("wrap", fontSize=8, leading=10, wordWrap="CJK")
    data = [["Priority", "Type", "Location", "Project", "Parts", "Assigned", "Notes"]]
    for proj in projects:
        data.append([
            Paragraph(proj.priority or "", wrap_style),
            Paragraph(proj.project_type or "", wrap_style),
            Paragraph(proj.location or "", wrap_style),
            Paragraph(proj.project or "", wrap_style),
            Paragraph(proj.parts_status or "", wrap_style),
            Paragraph(proj.assigned_department or "", wrap_style),
            Paragraph(proj.notes or "", wrap_style),
        ])
    table = Table(data, colWidths=[55, 55, 95, 95, 65, 85, 180])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    doc.build(story)
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name="shutdown_projects.pdf",
        mimetype="application/pdf",
    )
