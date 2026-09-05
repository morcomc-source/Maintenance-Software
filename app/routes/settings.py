from flask import jsonify,  Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.settings import (
    PartLocation, PartSublocation,
    PartRow, PartSection, PartShelf, PartSlot,
    PartCabinet, PartCabinetShelf, PartChest, PartDrawer, PartCabinetPosition, PartDrawerPosition,
    PMMainEquipment, PMMachine, PMFrequency,
    AppSetting,
)

bp = Blueprint('settings', __name__, url_prefix='/settings')


def admin_required():
    if current_user.role not in ('admin', 'supervisor'):
        flash("Admin only.", "danger")
        return False
    return True

def slack_admin_required():
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
        slots=PartSlot.query.order_by(PartSlot.code).all(),
        cabinets=PartCabinet.query.order_by(PartCabinet.code).all(),
        cabinet_shelves=PartCabinetShelf.query.order_by(PartCabinetShelf.code).all(),
        chests=PartChest.query.order_by(PartChest.code).all(),
        drawers=PartDrawer.query.order_by(PartDrawer.code).all()
    ,
        cabinet_positions=PartCabinetPosition.query.order_by(PartCabinetPosition.code).all(),
        drawer_positions=PartDrawerPosition.query.order_by(PartDrawerPosition.code).all())


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
    PartShelf.query.filter_by(row_id=row.id).delete()
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
    code = (request.form.get('code') or '').strip().upper()
    name = (request.form.get('name') or '').strip() or None
    if not code:
        flash("Shelf code is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartShelf.query.filter_by(code=code).first():
        flash("That shelf code already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartShelf(code=code, name=name, row_id=None))
    db.session.commit()
    flash(f"Shelf '{code}' added.", "success")
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
    code = (request.form.get('code') or '').strip().upper()
    name = (request.form.get('name') or '').strip() or None
    if not code:
        flash("Position code is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartSlot.query.filter_by(code=code).first():
        flash("That position code already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartSlot(code=code, name=name, shelf_id=None))
    db.session.commit()
    flash(f"Position '{code}' added.", "success")
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


@bp.route('/api/shelves/<int:section_id>')
@login_required
def api_shelves(section_id):
    items = PartShelf.query.filter_by(section_id=section_id).order_by(PartShelf.code).all()
    return jsonify([{"id": s.id, "code": s.code} for s in items])

@bp.route('/api/slots/<int:shelf_id>')
@login_required
def api_slots(shelf_id):
    items = PartSlot.query.filter_by(shelf_id=shelf_id).order_by(PartSlot.code).all()
    return jsonify([{"id": s.id, "code": s.code} for s in items])


# ----- Cabinet / Cabinet Shelf / Chest / Drawer -----
@bp.route('/cabinets/add', methods=['POST'])
@login_required
def add_cabinet():
    code = (request.form.get('code') or '').strip().upper()
    name = (request.form.get('name') or '').strip() or None
    if not code:
        flash("Cabinet code is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartCabinet.query.filter_by(code=code).first():
        flash("That cabinet already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartCabinet(code=code, name=name))
    db.session.commit()
    flash(f"Cabinet '{code}' added.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/cabinets/delete/<int:id>', methods=['POST'])
@login_required
def delete_cabinet(id):
    item = PartCabinet.query.get_or_404(id)
    PartCabinetShelf.query.filter_by(cabinet_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    flash("Cabinet deleted.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/cabinet-shelves/add', methods=['POST'])
@login_required
def add_cabinet_shelf():
    code = (request.form.get('code') or '').strip().upper()
    cabinet_id = request.form.get('cabinet_id')
    if not code or not cabinet_id:
        flash("Cabinet and shelf code are required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartCabinetShelf(code=code, cabinet_id=int(cabinet_id)))
    db.session.commit()
    flash(f"Cabinet shelf '{code}' added.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/cabinet-shelves/delete/<int:id>', methods=['POST'])
@login_required
def delete_cabinet_shelf(id):
    item = PartCabinetShelf.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Cabinet shelf deleted.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/chests/add', methods=['POST'])
@login_required
def add_chest():
    code = (request.form.get('code') or '').strip().upper()
    name = (request.form.get('name') or '').strip() or None
    if not code:
        flash("Chest code is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartChest.query.filter_by(code=code).first():
        flash("That chest already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartChest(code=code, name=name))
    db.session.commit()
    flash(f"Chest '{code}' added.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/chests/delete/<int:id>', methods=['POST'])
@login_required
def delete_chest(id):
    item = PartChest.query.get_or_404(id)
    PartDrawer.query.filter_by(chest_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    flash("Chest deleted.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/drawers/add', methods=['POST'])
@login_required
def add_drawer():
    code = (request.form.get('code') or '').strip().upper()
    if not code:
        flash("Drawer code is required.", "danger")
        return redirect(url_for('settings.parts_locations'))
    if PartDrawer.query.filter_by(code=code).first():
        flash("That drawer code already exists.", "warning")
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartDrawer(code=code, chest_id=None))
    db.session.commit()
    flash(f"Drawer '{code}' added.", "success")
    return redirect(url_for('settings.parts_locations'))

@bp.route('/drawers/delete/<int:id>', methods=['POST'])
@login_required
def delete_drawer(id):
    item = PartDrawer.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Drawer deleted.", "success")
    return redirect(url_for('settings.parts_locations'))

# ----- Cabinet Positions (like rack slots) -----
@bp.route('/cabinet-positions/add', methods=['POST'])
@login_required
def add_cabinet_position():
    if current_user.role != 'admin':
        flash('Admin only.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    shelf_id = request.form.get('cabinet_shelf_id')
    code = (request.form.get('code') or '').strip().upper()
    if not shelf_id or not code:
        flash('Shelf and position code required.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartCabinetPosition(code=code, cabinet_shelf_id=int(shelf_id)))
    db.session.commit()
    flash(f'Cabinet position {code} added.', 'success')
    return redirect(url_for('settings.parts_locations'))

@bp.route('/cabinet-positions/delete/<int:id>', methods=['POST'])
@login_required
def delete_cabinet_position(id):
    if current_user.role != 'admin':
        flash('Admin only.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    pos = PartCabinetPosition.query.get_or_404(id)
    db.session.delete(pos)
    db.session.commit()
    flash('Cabinet position deleted.', 'success')
    return redirect(url_for('settings.parts_locations'))

# ----- Drawer Positions (like rack slots) -----
@bp.route('/drawer-positions/add', methods=['POST'])
@login_required
def add_drawer_position():
    if current_user.role != 'admin':
        flash('Admin only.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    drawer_id = request.form.get('drawer_id')
    code = (request.form.get('code') or '').strip().upper()
    if not drawer_id or not code:
        flash('Drawer and position code required.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    db.session.add(PartDrawerPosition(code=code, drawer_id=int(drawer_id)))
    db.session.commit()
    flash(f'Drawer position {code} added.', 'success')
    return redirect(url_for('settings.parts_locations'))

@bp.route('/drawer-positions/delete/<int:id>', methods=['POST'])
@login_required
def delete_drawer_position(id):
    if current_user.role != 'admin':
        flash('Admin only.', 'danger')
        return redirect(url_for('settings.parts_locations'))
    pos = PartDrawerPosition.query.get_or_404(id)
    db.session.delete(pos)
    db.session.commit()
    flash('Drawer position deleted.', 'success')
    return redirect(url_for('settings.parts_locations'))


@bp.route('/slack', methods=['GET', 'POST'])
@login_required
def slack():
    if not slack_admin_required():
        return redirect(url_for('dashboard.index'))
    from app.notify import get_setting, set_setting
    if request.method == 'POST':
        url = (request.form.get('slack_webhook_url') or '').strip()
        token = (request.form.get('slack_bot_token') or '').strip()
        enabled = '1' if request.form.get('slack_enabled') else '0'
        set_setting('slack_webhook_url', url)
        set_setting('slack_bot_token', token)
        set_setting('slack_enabled', enabled)
        flash('Slack settings saved.', 'success')
        return redirect(url_for('settings.slack'))
    webhook = get_setting('slack_webhook_url', '')
    bot_token = get_setting('slack_bot_token', '')
    enabled = get_setting('slack_enabled', '1') != '0'
    return render_template('settings/slack.html', webhook=webhook, bot_token=bot_token, enabled=enabled)

@bp.route('/slack/test', methods=['POST'])
@login_required
def slack_test():
    if not slack_admin_required():
        return redirect(url_for('dashboard.index'))
    from app.notify import send_slack, slack_ready
    if not slack_ready():
        flash('Save a webhook URL and leave Slack enabled first.', 'danger')
        return redirect(url_for('settings.slack'))
    ok = send_slack('Maintenance Desk test message. If you see this, Slack is connected.')
    flash('Test message sent. Check the Slack channel.' if ok else 'Could not send. Check the webhook URL.', 'success' if ok else 'danger')
    return redirect(url_for('settings.slack'))


@bp.route('/slack/test-dm', methods=['POST'])
@login_required
def slack_test_dm():
    if not slack_admin_required():
        return redirect(url_for('dashboard.index'))
    from app.notify import send_dm_to_app_user, bot_ready
    if not bot_ready():
        flash("Save a bot token (xoxb-...) first.", "danger")
        return redirect(url_for("settings.slack"))
    if not (current_user.email or "").strip():
        flash("Your user has no email. Set it in Manage Users to match your Slack email.", "danger")
        return redirect(url_for("settings.slack"))
    ok = send_dm_to_app_user(current_user.id, "Maintenance Desk test DM. If you see this, DMs work.")
    flash("Test DM sent. Check Slack direct messages." if ok else "DM failed. Email must match Slack, and bot scopes must include chat:write, im:write, users:read.email.", "success" if ok else "danger")
    return redirect(url_for("settings.slack"))


@bp.route("/request-routing", methods=["GET", "POST"])
@login_required
def request_routing():
    if current_user.role != "admin":
        flash("Admin only.", "danger")
        return redirect(url_for("settings.index"))
    from app.models.user import User
    from app.notify import get_setting, set_setting
    keys = ("route_facility", "route_press", "route_mobile")
    if request.method == "POST":
        for k in keys:
            set_setting(k, request.form.get(k) or "")
        flash("Routing saved.", "success")
        return redirect(url_for("settings.request_routing"))
    supervisors = User.query.filter(User.role.in_(["supervisor", "admin"])).order_by(User.username).all()
    routes = {k: get_setting(k, "") or "" for k in keys}
    return render_template("settings/routing.html", supervisors=supervisors, routes=routes)
