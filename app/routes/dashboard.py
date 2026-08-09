from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime
from app.models.pm import PM
from app.models.workorder import WorkOrder

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return render_template('dashboard/admin.html')

    if current_user.role == 'department':
        return render_template('dashboard/department.html')

    if current_user.role == 'technician':
        today = datetime.now().date()

        # PM STATS
        assigned_pms = PM.query.filter_by(assigned_user_id=current_user.id).all()
        total_pm = len(assigned_pms)
        due_today_pm = sum(1 for p in assigned_pms if p.next_due == today)
        overdue_pm = sum(1 for p in assigned_pms if p.next_due and p.next_due < today)
        upcoming_pm = sum(1 for p in assigned_pms if p.next_due and p.next_due > today)

        # WORK ORDER STATS
        assigned_wos = WorkOrder.query.filter_by(assigned_to_id=current_user.id).all()
        total_assigned_wo = len(assigned_wos)
        completed_wo = sum(1 for wo in assigned_wos if wo.status == 'Completed')
        past_due_wo = sum(
            1 for wo in assigned_wos
            if wo.expected_completion_date
            and wo.expected_completion_date < today
            and wo.status != 'Completed'
        )

        stats = {
            'total_assigned': total_pm,
            'due_today': due_today_pm,
            'overdue': overdue_pm,
            'upcoming': upcoming_pm,
            'assigned_workorders': total_assigned_wo,
            'completed_workorders': completed_wo,
            'past_due_workorders': past_due_wo,
        }
        return render_template('dashboard/technician.html', stats=stats)

    return "Invalid role", 403
