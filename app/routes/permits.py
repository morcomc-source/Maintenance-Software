from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from app import db
from app.models.permit import Permit
from app.models.user import User

bp = Blueprint("permits", __name__, url_prefix="/permits")
STAFF = ("admin", "supervisor", "technician")
APPROVERS = ("admin", "supervisor")
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".pdf"}


def _gate():
    if current_user.role not in STAFF:
        flash("Permits are for maintenance staff only.", "danger")
        return False
    return True


def _can_decide(p):
    if current_user.role == "admin":
        return True
    if current_user.role == "supervisor" and p.reports_to_id == current_user.id:
        return True
    return False


@bp.route("/")
@login_required
def index():
    if not _gate():
        return redirect(url_for("dashboard.index"))
    kind = request.args.get("type") or ""
    q = Permit.query
    if kind in ("hot_work", "confined", "loto"):
        q = q.filter_by(permit_type=kind)
    if current_user.role == "technician":
        q = q.filter_by(created_by_id=current_user.id)
    rows = q.order_by(Permit.created_at.desc()).limit(200).all()
    return render_template("permits/index.html", rows=rows, kind=kind)


@bp.route("/new/<kind>", methods=["GET", "POST"])
@login_required
def new(kind):
    if not _gate():
        return redirect(url_for("dashboard.index"))
    if kind not in ("hot_work", "confined", "loto"):
        flash("Unknown permit type.", "danger")
        return redirect(url_for("permits.index"))
    if request.method == "POST":
        data = {k: request.form.get(k) for k in request.form.keys()}
        status = "logged" if kind == "loto" else "pending"
        p = Permit(
            permit_type=kind,
            status=status,
            location=(request.form.get("location") or "").strip() or None,
            equipment=(request.form.get("equipment") or "").strip() or None,
            work_description=(request.form.get("work_description") or "").strip() or None,
            form_data=data,
            created_by_id=current_user.id,
            reports_to_id=current_user.reports_to_id,
        )
        db.session.add(p)
        db.session.commit()
        saved = []
        folder = Path(current_app.root_path) / "static" / "uploads" / "permits"
        folder.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(request.files.getlist("photos")):
            if not f or not f.filename:
                continue
            ext = Path(f.filename).suffix.lower()
            if ext not in ALLOWED:
                continue
            name = secure_filename(f"p{p.id}_{i+1}{ext}")
            f.save(folder / name)
            saved.append(name)
        if saved:
            p.photos = saved
            db.session.commit()
        if kind != "loto":
            try:
                from app.notify import notify_permit_submitted
                notify_permit_submitted(p)
            except Exception as err:
                print("Permit Slack warning:", err)
        flash("Lockout documented." if kind == "loto" else "Submitted for approval.", "success")
        return redirect(url_for("permits.details", pid=p.id))
    return render_template("permits/new.html", kind=kind)


@bp.route("/<int:pid>")
@login_required
def details(pid):
    if not _gate():
        return redirect(url_for("dashboard.index"))
    p = Permit.query.get_or_404(pid)
    if current_user.role == "technician" and p.created_by_id != current_user.id:
        flash("You can only view your own permits.", "danger")
        return redirect(url_for("permits.index"))
    return render_template("permits/details.html", p=p, can_decide=_can_decide(p))


@bp.route("/<int:pid>/decide", methods=["POST"])
@login_required
def decide(pid):
    if not _gate():
        return redirect(url_for("dashboard.index"))
    p = Permit.query.get_or_404(pid)
    if p.permit_type == "loto":
        flash("Lockout records do not need approval.", "info")
        return redirect(url_for("permits.details", pid=pid))
    if not _can_decide(p):
        flash("You are not the approver for this permit.", "danger")
        return redirect(url_for("permits.details", pid=pid))
    if current_user.id == p.created_by_id and current_user.role != "admin":
        flash("You cannot approve your own permit.", "danger")
        return redirect(url_for("permits.details", pid=pid))
    action = request.form.get("action")
    p.decided_by_id = current_user.id
    p.decided_at = datetime.utcnow()
    p.decision_note = (request.form.get("decision_note") or "").strip() or None
    p.status = "approved" if action == "approve" else "denied"
    db.session.commit()
    flash("Permit " + p.status + ".", "success")
    return redirect(url_for("permits.index"))


@bp.route("/<int:pid>/delete", methods=["POST"])
@login_required
def delete(pid):
    if current_user.role != "admin":
        flash("Admin only.", "danger")
        return redirect(url_for("permits.index"))
    p = Permit.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Permit deleted.", "success")
    return redirect(url_for("permits.index"))
