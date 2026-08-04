from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.settings import PartLocation, PartSublocation

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
@login_required
def index():
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return redirect(url_for('dashboard.index'))

    locations = PartLocation.query.order_by(PartLocation.name).all()
    sublocations = PartSublocation.query.order_by(PartSublocation.group_label, PartSublocation.name).all()
    return render_template('settings/index.html', locations=locations, sublocations=sublocations)


@bp.route('/locations/add', methods=['POST'])
@login_required
def add_location():
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return redirect(url_for('dashboard.index'))

    name = request.form.get('name', '').strip()
    if not name:
        flash("Location name is required.", "danger")
        return redirect(url_for('settings.index'))

    if PartLocation.query.filter_by(name=name).first():
        flash("That location already exists.", "warning")
        return redirect(url_for('settings.index'))

    db.session.add(PartLocation(name=name))
    db.session.commit()
    flash(f"Location '{name}' added.", "success")
    return redirect(url_for('settings.index'))


@bp.route('/locations/delete/<int:id>', methods=['POST'])
@login_required
def delete_location(id):
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return redirect(url_for('dashboard.index'))

    loc = PartLocation.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    flash("Location deleted.", "success")
    return redirect(url_for('settings.index'))


@bp.route('/sublocations/add', methods=['POST'])
@login_required
def add_sublocation():
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return redirect(url_for('dashboard.index'))

    name = request.form.get('name', '').strip()
    group = request.form.get('group_label', '').strip() or None

    if not name:
        flash("Sublocation name is required.", "danger")
        return redirect(url_for('settings.index'))

    if PartSublocation.query.filter_by(name=name).first():
        flash("That sublocation already exists.", "warning")
        return redirect(url_for('settings.index'))

    db.session.add(PartSublocation(name=name, group_label=group))
    db.session.commit()
    flash(f"Sublocation '{name}' added.", "success")
    return redirect(url_for('settings.index'))


@bp.route('/sublocations/delete/<int:id>', methods=['POST'])
@login_required
def delete_sublocation(id):
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return redirect(url_for('dashboard.index'))

    sub = PartSublocation.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash("Sublocation deleted.", "success")
    return redirect(url_for('settings.index'))
