from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.pm import PM
from app.models.workorder import WorkOrder   # ← Added

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return render_template('dashboard/admin.html')
    
    elif current_user.role == 'technician':
        today = datetime.now().date()

        # PM Stats (existing)
        assigned_pms = PM.query.filter_by(assigned_user_id=current_user.id).all()

        total_pm = len(assigned_pms)
        due_today_pm = sum(1 for p in assigned_pms if p.next_due == today)
        overdue_pm = sum(1 for p in assigned_pms if p.next_due and p.next_due < today)
        upcoming_pm = sum(1 for p in assigned_pms if p.next_due and p.next_due > today)

        # NEW: Work Order Stats
        assigned_workorders = WorkOrder.query.filter_by(assigned_to_id=current_user.id).count()

        stats = {
            'total_assigned': total_pm,
            'due_today': due_today_pm,
            'overdue': overdue_pm,
            'upcoming': upcoming_pm,
            'assigned_workorders': assigned_workorders   # ← New
        }

        return render_template('dashboard/technician.html', stats=stats)

    else:
        return "Invalid role", 403