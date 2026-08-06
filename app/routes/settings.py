from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.settings import (
    PartLocation, PartSublocation,
    PartRow, PartSection, PartShelf, PartSlot,
    PMMainEquipment, PMMachine, PMFrequency
)

bp = Blueprint('settings', __name__, url_prefix='/settings')


def admin_required():
    if current_user.role != 'admin':
        flash("Admin only.", "danger")
        return False
    return True


@bp.route('/')
@login_required
def index():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    return render_template('settings/index.html')


# ====================== PARTS LOCATIONS PAGE ======================
@bp.route('/parts-locations')
@login_required
def parts_locations():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    return render_template(
        'settings/parts_locations.html',
        locations=PartLocation.query.order_by(PartLocation.name).all(),
        sublocations=PartSublocation.query.order_by(PartSublocation.name).all(),
        rows=PartRow.query.order_by(PartRow.code).all(),
        sections=PartSection.query.order_by(PartSection.code).all(),
        shelves=PartShelf.query.order_by(PartShelf.code).all(),
        slots=PartSlot.query.order_by(PartSlot.code).all()
    )


# ----- Main Location -----
@bp.route('/locations/add', methods=['POST'])
@login_required
def add_location():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    name = request.form.get('name', '').strip()
    if not name:
        flash("Location name is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartLocation.query.filter_by(name=name).first():
        flash("That location already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartLocation(name=name))
    db.session.commit()
    flash(f"Location '{name}' added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/locations/delete/<int:id>', methods=['POST'])
@login_required
def delete_location(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    loc = PartLocation.query.get_or_404(id)
    db.session.delete(loc)
    db.session.commit()
    flash("Location deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


# ----- Sublocation -----
@bp.route('/sublocations/add', methods=['POST'])
@login_required
def add_sublocation():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    name = request.form.get('name', '').strip()
    location_id = request.form.get('location_id')
    if not name:
        flash("Sublocation name is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if not location_id:
        flash("Select a main location for this sublocation.", "danger")
        return redirect(url_for('settings.parts_locations'))
    try:
        location_id = int(location_id)
    except Exception:
        flash("Invalid main location.", "danger")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartSublocation(name=name, location_id=location_id))
    db.session.commit()
    flash(f"Sublocation '{name}' added.", "success")
    return redirect(url_for('settings.parts_locations'))

    if PartSublocation.query.filter_by(name=name).first():
        flash("That sublocation already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartSublocation(name=name))
    db.session.commit()
    flash(f"Sublocation '{name}' added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/sublocations/delete/<int:id>', methods=['POST'])
@login_required
def delete_sublocation(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    sub = PartSublocation.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash("Sublocation deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


# ----- Row / Section / Shelf / Slot -----
@bp.route('/rows/add', methods=['POST'])
@login_required
def add_row():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip() or None
    if not code:
        flash("Row code is required (e.g. R01).", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartRow.query.filter_by(code=code).first():
        flash("That row already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartRow(code=code, name=name))
    db.session.commit()
    flash(f"Row {code} added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/rows/delete/<int:id>', methods=['POST'])
@login_required
def delete_row(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    row = PartRow.query.get_or_404(id)
    PartSection.query.filter_by(row_id=row.id).delete()
    db.session.delete(row)
    db.session.commit()
    flash("Row deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/sections/add', methods=['POST'])
@login_required
def add_section():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip() or None
    row_id = request.form.get('row_id')
    if not code or not row_id:
        flash("Section code and Row are required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartSection(code=code, name=name, row_id=int(row_id)))
    db.session.commit()
    flash(f"Section {code} added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/sections/delete/<int:id>', methods=['POST'])
@login_required
def delete_section(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    sec = PartSection.query.get_or_404(id)
    db.session.delete(sec)
    db.session.commit()
    flash("Section deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/shelves/add', methods=['POST'])
@login_required
def add_shelf():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip() or None
    if not code:
        flash("Shelf code is required (e.g. H01).", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartShelf.query.filter_by(code=code).first():
        flash("That shelf already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartShelf(code=code, name=name))
    db.session.commit()
    flash(f"Shelf {code} added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/shelves/delete/<int:id>', methods=['POST'])
@login_required
def delete_shelf(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    item = PartShelf.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Shelf deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/slots/add', methods=['POST'])
@login_required
def add_slot():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip() or None
    if not code:
        flash("Slot code is required (e.g. P01).", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartSlot.query.filter_by(code=code).first():
        flash("That slot already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartSlot(code=code, name=name))
    db.session.commit()
    flash(f"Slot {code} added.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/slots/delete/<int:id>', methods=['POST'])
@login_required
def delete_slot(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    item = PartSlot.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Slot deleted.", "success")
    return redirect(url_for('settings.parts_locations'))


@bp.route('/api/sections/<int:row_id>')
@login_required
def api_sections(row_id):
    secs = PartSection.query.filter_by(row_id=row_id).order_by(PartSection.code).all()
    return jsonify([{"id": s.id, "code": s.code, "name": s.name or ""} for s in secs])


# ====================== PM SETUP ======================
@bp.route('/pm-setup')
@login_required
def pm_setup():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    return render_template(
        'settings/pm_setup.html',
        mains=PMMainEquipment.query.order_by(PMMainEquipment.name).all(),
        machines=PMMachine.query.order_by(PMMachine.name).all(),
        frequencies=PMFrequency.query.order_by(PMFrequency.name).all()
    )


@bp.route('/pm/main/add', methods=['POST'])
@login_required
def add_pm_main():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    name = request.form.get('name', '').strip()
    if not name:
        flash("Name is required.", "danger")
        return redirect(url_for('settings.pm_setup'))
    if PMMainEquipment.query.filter_by(name=name).first():
        flash("That main equipment already exists.", "warning")
        return redirect(url_for('settings.pm_setup'))
    db.session.add(PMMainEquipment(name=name))
    db.session.commit()
    flash(f"Main equipment '{name}' added.", "success")
    return redirect(url_for('settings.pm_setup'))


@bp.route('/pm/main/delete/<int:id>', methods=['POST'])
@login_required
def delete_pm_main(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    item = PMMainEquipment.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Main equipment deleted.", "success")
    return redirect(url_for('settings.pm_setup'))


@bp.route('/pm/machine/add', methods=['POST'])
@login_required
def add_pm_machine():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    name = request.form.get('name', '').strip()
    main_id = request.form.get('main_equipment_id') or None
    if not name:
        flash("Machine name is required.", "danger")
        return redirect(url_for('settings.pm_setup'))
    if PMMachine.query.filter_by(name=name).first():
        flash("That machine already exists.", "warning")
        return redirect(url_for('settings.pm_setup'))
    try:
        main_id = int(main_id) if main_id else None
    except Exception:
        main_id = None
    db.session.add(PMMachine(name=name, main_equipment_id=main_id))
    db.session.commit()
    flash(f"Machine '{name}' added.", "success")
    return redirect(url_for('settings.pm_setup'))


@bp.route('/pm/machine/delete/<int:id>', methods=['POST'])
@login_required
def delete_pm_machine(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    item = PMMachine.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Machine deleted.", "success")
    return redirect(url_for('settings.pm_setup'))


@bp.route('/pm/frequency/add', methods=['POST'])
@login_required
def add_pm_frequency():
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    name = request.form.get('name', '').strip()
    if not name:
        flash("Frequency name is required.", "danger")
        return redirect(url_for('settings.pm_setup'))
    if PMFrequency.query.filter_by(name=name).first():
        flash("That frequency already exists.", "warning")
        return redirect(url_for('settings.pm_setup'))
    db.session.add(PMFrequency(name=name))
    db.session.commit()
    flash(f"Frequency '{name}' added.", "success")
    return redirect(url_for('settings.pm_setup'))


@bp.route('/pm/frequency/delete/<int:id>', methods=['POST'])
@login_required
def delete_pm_frequency(id):
    if not admin_required():
        return redirect(url_for('dashboard.index'))
    item = PMFrequency.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Frequency deleted.", "success")
    return redirect(url_for('settings.pm_setup'))
