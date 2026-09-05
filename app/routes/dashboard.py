from flask import flash, request, Blueprint, render_template, url_for
from flask_login import login_required, current_user
from datetime import datetime
from app.models.pm import PM
from app.models.workorder import WorkOrder
from app.models.user import User

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    if current_user.role in ('admin', 'supervisor'):
        today_mine, today_crew = [], []
        if current_user.role == 'supervisor':
            today = datetime.now().date()
            crew = User.query.filter_by(reports_to_id=current_user.id).all()
            crew_ids = [u.id for u in crew]

            def add_row(bucket, kind, title, when, late, url, who=""):
                bucket.append({
                    "kind": kind, "title": title, "when": when,
                    "late": late, "url": url, "who": who,
                })

            for pm in PM.query.all():
                if not pm.next_due or pm.next_due > today:
                    continue
                uid = getattr(pm, "assigned_user_id", None)
                who = ""
                if uid:
                    u = User.query.get(uid)
                    who = u.username if u else ""
                row = ("PM", (pm.main_equipment or "PM"), pm.next_due.strftime("%Y-%m-%d"),
                       pm.next_due < today, url_for("pm.details", id=pm.id), who)
                if uid == current_user.id:
                    add_row(today_mine, *row)
                elif uid in crew_ids:
                    add_row(today_crew, *row)

            for wo in WorkOrder.query.filter(WorkOrder.status != "Completed").all():
                due = wo.expected_completion_date
                if due is not None and due > today:
                    continue
                who = wo.assigned_to.username if wo.assigned_to else "Unassigned"
                row = ("WO", "#{} {}".format(wo.id, wo.equipment or ""),
                       due.strftime("%Y-%m-%d") if due else "Open",
                       bool(due and due < today),
                       url_for("workorder.details", wo_id=wo.id), who)
                if wo.assigned_to_id == current_user.id:
                    add_row(today_mine, *row)
                elif wo.assigned_to_id in crew_ids:
                    add_row(today_crew, *row)

            try:
                from app.models.permit import Permit
                for perm in Permit.query.filter_by(reports_to_id=current_user.id, status="pending").all():
                    who = perm.created_by.username if perm.created_by else ""
                    add_row(today_crew if perm.created_by_id != current_user.id else today_mine,
                            "Permit", "{} #{}".format(perm.type_label(), perm.id),
                            "Needs approval", True,
                            url_for("permits.details", pid=perm.id), who)
            except Exception:
                pass
        plant_pm, plant_wo, plant_perm = [], [], []
        if current_user.role == 'admin':
            today = datetime.now().date()
            for pm in PM.query.all():
                if not pm.next_due or pm.next_due > today:
                    continue
                who = ""
                if getattr(pm, "assigned_user_id", None):
                    u = User.query.get(pm.assigned_user_id)
                    who = u.username if u else ""
                plant_pm.append({
                    "title": (pm.main_equipment or "PM"),
                    "when": pm.next_due.strftime("%Y-%m-%d"),
                    "late": pm.next_due < today,
                    "who": who or "Unassigned",
                    "url": url_for("pm.details", id=pm.id),
                })
            for wo in WorkOrder.query.filter(WorkOrder.status != "Completed").all():
                due = wo.expected_completion_date
                if due is not None and due > today:
                    continue
                plant_wo.append({
                    "title": "#{} {}".format(wo.id, wo.equipment or ""),
                    "when": due.strftime("%Y-%m-%d") if due else "Open",
                    "late": bool(due and due < today),
                    "who": wo.assigned_to.username if wo.assigned_to else "Unassigned",
                    "url": url_for("workorder.details", wo_id=wo.id),
                })
            try:
                from app.models.permit import Permit
                for perm in Permit.query.filter(Permit.status.in_(["pending"])).all():
                    plant_perm.append({
                        "title": "{} #{}".format(perm.type_label(), perm.id),
                        "when": "Pending",
                        "late": True,
                        "who": (perm.created_by.username if perm.created_by else "") +
                               ((" → " + perm.reports_to.username) if perm.reports_to else ""),
                        "url": url_for("permits.details", pid=perm.id),
                    })
            except Exception:
                pass
        return render_template(
            'dashboard/admin.html',
            today_mine=today_mine,
            today_crew=today_crew,
            plant_pm=plant_pm,
            plant_wo=plant_wo,
            plant_perm=plant_perm,
        )



    if current_user.role == 'department':
        return render_template('dashboard/department.html')

    if current_user.role == 'requestor':
        mine = WorkOrder.query.filter_by(created_by_id=current_user.id).order_by(WorkOrder.created_at.desc()).all()
        open_n = sum(1 for w in mine if w.status != 'Completed')
        done_n = sum(1 for w in mine if w.status == 'Completed')
        return render_template('dashboard/requestor.html', open_n=open_n, done_n=done_n, recent=mine[:8])

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
        today_items = []
        for pm in assigned_pms:
            if pm.next_due and pm.next_due <= today:
                today_items.append({
                    "kind": "PM",
                    "title": (pm.main_equipment or "PM") + ((" — " + pm.sub_equipment) if pm.sub_equipment else ""),
                    "when": pm.next_due.strftime("%Y-%m-%d"),
                    "late": pm.next_due < today,
                    "url": url_for("pm.details", id=pm.id),
                })
        for wo in assigned_wos:
            if wo.status == "Completed":
                continue
            due = wo.expected_completion_date
            if due is not None and due > today:
                continue
            today_items.append({
                "kind": "WO",
                "title": "#{} {}".format(wo.id, wo.equipment or ""),
                "when": due.strftime("%Y-%m-%d") if due else "Open",
                "late": bool(due and due < today),
                "url": url_for("workorder.details", wo_id=wo.id),
            })
        try:
            from app.models.permit import Permit
            for perm in Permit.query.filter_by(created_by_id=current_user.id, status="pending").all():
                today_items.append({
                    "kind": "Permit",
                    "title": "{} #{}".format(perm.type_label(), perm.id),
                    "when": "Pending approval",
                    "late": False,
                    "url": url_for("permits.details", pid=perm.id),
                })
        except Exception:
            pass
        return render_template('dashboard/technician.html', stats=stats, today_items=today_items)

    return "Invalid role", 403


@bp.route("/today")
@login_required
def plant_today():
    if current_user.role != "admin":
        flash("Admin only.", "danger")
        return redirect(url_for("dashboard.index"))
    today = datetime.now().date()
    plant_pm, plant_wo, plant_perm = [], [], []
    for pm in PM.query.all():
        if not pm.next_due or pm.next_due > today:
            continue
        who = "Unassigned"
        if getattr(pm, "assigned_user_id", None):
            u = User.query.get(pm.assigned_user_id)
            who = u.username if u else "Unassigned"
        plant_pm.append({
            "title": pm.main_equipment or "PM",
            "when": pm.next_due.strftime("%Y-%m-%d"),
            "late": pm.next_due < today,
            "who": who,
            "url": url_for("pm.details", id=pm.id),
        })
    for wo in WorkOrder.query.filter(WorkOrder.status != "Completed").all():
        due = wo.expected_completion_date
        if due is not None and due > today:
            continue
        plant_wo.append({
            "title": "#{} {}".format(wo.id, wo.equipment or ""),
            "when": due.strftime("%Y-%m-%d") if due else "Open",
            "late": bool(due and due < today),
            "who": wo.assigned_to.username if wo.assigned_to else "Unassigned",
            "url": url_for("workorder.details", wo_id=wo.id),
        })
    try:
        from app.models.permit import Permit
        for perm in Permit.query.filter_by(status="pending").all():
            plant_perm.append({
                "title": "{} #{}".format(perm.type_label(), perm.id),
                "when": "Pending",
                "late": True,
                "who": perm.created_by.username if perm.created_by else "",
                "url": url_for("permits.details", pid=perm.id),
            })
    except Exception:
        pass
    tab = request.args.get("tab") or "wo"
    return render_template(
        "dashboard/plant_today.html",
        tab=tab, plant_pm=plant_pm, plant_wo=plant_wo, plant_perm=plant_perm,
    )


@bp.route("/crew-today")
@login_required
def crew_today():
    if current_user.role != "supervisor":
        flash("Supervisor only.", "danger")
        return redirect(url_for("dashboard.index"))
    today = datetime.now().date()
    today_mine, today_crew = [], []
    crew = User.query.filter_by(reports_to_id=current_user.id).all()
    crew_ids = [u.id for u in crew]

    def add_row(bucket, kind, title, when, late, url, who=""):
        bucket.append({"kind": kind, "title": title, "when": when, "late": late, "url": url, "who": who})

    for pm in PM.query.all():
        if not pm.next_due or pm.next_due > today:
            continue
        uid = getattr(pm, "assigned_user_id", None)
        who = ""
        if uid:
            u = User.query.get(uid)
            who = u.username if u else ""
        args = ("PM", pm.main_equipment or "PM", pm.next_due.strftime("%Y-%m-%d"),
                pm.next_due < today, url_for("pm.details", id=pm.id), who)
        if uid == current_user.id:
            add_row(today_mine, *args)
        elif uid in crew_ids:
            add_row(today_crew, *args)

    for wo in WorkOrder.query.filter(WorkOrder.status != "Completed").all():
        due = wo.expected_completion_date
        if due is not None and due > today:
            continue
        who = wo.assigned_to.username if wo.assigned_to else "Unassigned"
        args = ("WO", "#{} {}".format(wo.id, wo.equipment or ""),
                due.strftime("%Y-%m-%d") if due else "Open",
                bool(due and due < today),
                url_for("workorder.details", wo_id=wo.id), who)
        if wo.assigned_to_id == current_user.id:
            add_row(today_mine, *args)
        elif wo.assigned_to_id in crew_ids:
            add_row(today_crew, *args)

    try:
        from app.models.permit import Permit
        for perm in Permit.query.filter_by(reports_to_id=current_user.id, status="pending").all():
            who = perm.created_by.username if perm.created_by else ""
            add_row(today_crew if perm.created_by_id != current_user.id else today_mine,
                    "Permit", "{} #{}".format(perm.type_label(), perm.id),
                    "Needs approval", True, url_for("permits.details", pid=perm.id), who)
    except Exception:
        pass
    tab = request.args.get("tab") or "crew"
    return render_template("dashboard/crew_today.html", tab=tab, today_mine=today_mine, today_crew=today_crew)
