from datetime import datetime

from flask import Blueprint, render_template, request, redirect, flash, url_for, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from sqlalchemy import cast, Integer
from app.models.part import Part
from app.models.settings import (
    PartLocation, PartSublocation,
    PartRow, PartSection, PartShelf, PartSlot,
    PartCabinet, PartCabinetShelf, PartCabinetPosition,
    PartChest, PartDrawer, PartDrawerPosition
)
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPM
from reportlab.lib.units import mm


def _save_main_location_if_new(name):
    name = (name or "").strip()
    if not name:
        return
    if not PartLocation.query.filter_by(name=name).first():
        db.session.add(PartLocation(name=name))




def _maybe_clear_on_order(part):
    """Clear on-order when qty is above min stock (restocked)."""
    try:
        q = int(part.qty if part.qty is not None else 0)
        m = int(part.min_stock if part.min_stock is not None else 0)
    except (TypeError, ValueError):
        return False
    if bool(getattr(part, "on_order", False)) and q > m:
        part.on_order = False
        part.ordered_by = None
        part.ordered_at = None
        return True
    return False



bp = Blueprint("parts", __name__)

# ====================== BARCODE ROUTES ======================
@bp.route('/generate_barcode')
def generate_barcode():
    code = request.args.get('code', '')
    if not code:
        return "No code provided", 400
    import barcode
    from barcode.writer import ImageWriter
    from io import BytesIO
    buffer = BytesIO()
    code128 = barcode.get_barcode_class('code128')
    code128(code, writer=ImageWriter()).write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

@bp.route('/generate_barcode_pdf/<int:id>')
@login_required
def generate_barcode_pdf(id):
    part = Part.query.get_or_404(id)
    code = part.barcode or ''
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Parts Detail")
    c.setFont("Helvetica", 12)
    y = height - 1.5 * inch
    c.drawString(1 * inch, y, f"Name: {part.name or 'N/A'}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Barcode: {code or 'N/A'}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Part Number: {part.part_number or 'N/A'}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Quantity: {part.qty}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Min Stock: {part.min_stock}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Max Stock: {part.max_stock}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Location: {part.location or 'N/A'}")
    y -= 0.25 * inch
    c.drawString(1 * inch, y, f"Sublocation: {part.sublocation or 'N/A'}")
    if code:
        barcode = code128.Code128(code, barHeight=20*mm, barWidth=0.3*mm, humanReadable=True)
        barcode.drawOn(c, (width / 2 - 50*mm), 1 * inch)
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"part_{part.id}.pdf", mimetype='application/pdf')

# ====================== MAIN PARTS PAGE ======================
@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        if not current_user.is_admin():
            flash("You do not have permission to add, edit, or delete parts.", "danger")
            return redirect(url_for("parts.index"))

        # DELETE
        delete_index = request.form.get("delete_index")
        if delete_index:
            part = Part.query.get(int(delete_index))
            if part:
                db.session.delete(part)
                db.session.commit()
                flash("Part deleted successfully.", "success")
            return redirect(url_for("parts.index"))

        # ---------- helper to build bin_location from form ----------
        def _build_bin_location():
            storage_type = request.form.get("storage_type", "").strip()
            if storage_type == "rack":
                r = request.form.get("loc_row", "").strip()
                h = request.form.get("loc_shelf", "").strip()
                p = request.form.get("loc_slot", "").strip()
                if r and h and p:
                    return f"{r}-{h}-{p}"
            elif storage_type == "cabinet":
                c = request.form.get("loc_cabinet", "").strip()
                cs = request.form.get("loc_cabinet_shelf", "").strip()
                cp = request.form.get("loc_cabinet_pos", "").strip()
                if c and cs and cp:
                    return f"{c}-{cs}-{cp}"
            elif storage_type == "chest":
                ch = request.form.get("loc_chest", "").strip()
                d = request.form.get("loc_drawer", "").strip()
                dp = request.form.get("loc_drawer_pos", "").strip()
                if ch and d and dp:
                    return f"{ch}-{d}-{dp}"
            return None

        # EDIT / UPDATE
        index = request.form.get("index")
        if index:
            try:
                part_id = int(index)
                part = Part.query.get(part_id)
                if part:
                    part.barcode = request.form.get("barcode", "").strip() or None
                    part.name = request.form.get("name", "").strip()
                    part.part_number = request.form.get("part_number", "").strip()
                    part.qty = int(request.form.get("qty", 0))
                    _maybe_clear_on_order(part)
                    part.min_stock = int(request.form.get("min_stock", 0))
                    part.max_stock = int(request.form.get("max_stock", 999))

                    part.location = (request.form.get("main_location") or request.form.get("location") or "").strip() or part.location
                    part.sublocation = request.form.get("sublocation", "").strip() or None

                    new_bin = _build_bin_location()
                    if new_bin is not None:
                        part.bin_location = new_bin

                    db.session.commit()
                    flash("Part updated successfully!", "success")
                else:
                    flash("Part not found.", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating part: {str(e)}", "danger")
            return redirect(url_for("parts.index"))

        # ADD NEW PART
        name = request.form.get("name", "").strip()
        if name:
            try:
                location = (request.form.get("main_location") or request.form.get("location") or "").strip()
                sublocation = request.form.get("sublocation", "").strip() or None
                bin_location = _build_bin_location()

                new_part = Part(
                    barcode=request.form.get("barcode", "").strip() or None,
                    name=name,
                    part_number=request.form.get("part_number", "").strip(),
                    qty=int(request.form.get("qty", 0)),
                    min_stock=int(request.form.get("min_stock", 0)),
                    max_stock=int(request.form.get("max_stock", 999)),
                    location=location,
                    bin_location=bin_location,
                    sublocation=sublocation,
                )
                db.session.add(new_part)
                _save_main_location_if_new(request.form.get("main_location"))
                db.session.commit()
                flash("Part added successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding part: {str(e)}", "danger")
            return redirect(url_for("parts.index"))
        else:
            flash("Name is required to add a part.", "danger")
            return redirect(url_for("parts.index"))

    # ====================== GET + SEARCH ======================
    search = request.args.get("search", "").strip().lower()
    low_stock = request.args.get("low_stock", "").lower() in ("1", "true", "yes")
    show_all = request.args.get("show_all", "").lower() in ("1", "true", "yes")

    if search:
        parts = Part.query.filter(
            Part.name.ilike(f"%{search}%") |
            Part.part_number.ilike(f"%{search}%") |
            Part.barcode.ilike(f"%{search}%") |
            Part.location.ilike(f"%{search}%")
        ).all()
    else:
        if low_stock:
            parts = Part.query.filter(Part.qty <= cast(Part.min_stock, Integer)).all()
        else:
            parts = Part.query.all()

    
    # Auto-clear ON ORDER when qty > min_stock
    changed = False
    for _p in list(parts):
        if False and _maybe_clear_on_order(_p):
                changed = True  # disabled auto-clear on page load
    if changed:
        db.session.commit()
        print(f"✅ Cleared on-order for restocked parts")

    items = []
    for i, part in enumerate(parts):
        items.append((
            i,
            {
                "id": part.id,
                "barcode": part.barcode,
                "name": part.name,
                "part_number": part.part_number,
                "qty": part.qty,
                "min_stock": part.min_stock,
                "max_stock": part.max_stock,
                "location": part.location,
                    "bin_location": getattr(part, "bin_location", None),
                "sublocation": part.sublocation,
                "on_order": bool(getattr(part, "on_order", False) or False),
                "ordered_by": getattr(part, "ordered_by", None),
                "ordered_at": (part.ordered_at.strftime("%Y-%m-%d %H:%M") if getattr(part, "ordered_at", None) else None),
            }
        ))
    rows = PartRow.query.order_by(PartRow.code).all()
    sections = PartSection.query.order_by(PartSection.code).all()
    shelves = PartShelf.query.order_by(PartShelf.code).all()
    slots = PartSlot.query.order_by(PartSlot.code).all()
    locations = PartLocation.query.order_by(PartLocation.name).all()
    sublocations = PartSublocation.query.order_by(PartSublocation.name).all()

    cabinets = PartCabinet.query.order_by(PartCabinet.code).all()
    cabinet_shelves = PartCabinetShelf.query.order_by(PartCabinetShelf.code).all()
    cabinet_positions = PartCabinetPosition.query.order_by(PartCabinetPosition.code).all()
    chests = PartChest.query.order_by(PartChest.code).all()
    drawers = PartDrawer.query.order_by(PartDrawer.code).all()
    drawer_positions = PartDrawerPosition.query.order_by(PartDrawerPosition.code).all()

    sections_json = [{"id": s.id, "code": s.code, "row_id": s.row_id} for s in sections]
    sublocations_json = [
        {
            "id": s.id,
            "name": s.name,
            "location_name": s.location.name if s.location else None,
            "location_id": s.location_id
        }
        for s in sublocations
    ]
    cabinet_shelves_json = [{"id": s.id, "code": s.code, "cabinet_id": s.cabinet_id} for s in cabinet_shelves]
    cabinet_positions_json = [{"id": p.id, "code": p.code, "cabinet_shelf_id": p.cabinet_shelf_id} for p in cabinet_positions]
    drawers_json = [{"id": d.id, "code": d.code, "chest_id": d.chest_id} for d in drawers]
    drawer_positions_json = [{"id": p.id, "code": p.code, "drawer_id": p.drawer_id} for p in drawer_positions]

    return render_template(
        "parts.html",
        items=items,
        search=search,
        rows=rows,
        shelves=shelves,
        slots=slots,
        locations=locations,
        sublocations=sublocations,
        sections_json=sections_json,
        sublocations_json=sublocations_json,
        cabinets=cabinets,
        cabinet_shelves=cabinet_shelves,
        cabinet_positions=cabinet_positions,
        chests=chests,
        drawers=drawers,
        drawer_positions=drawer_positions,
        cabinet_shelves_json=cabinet_shelves_json,
        cabinet_positions_json=cabinet_positions_json,
        drawers_json=drawers_json,
        drawer_positions_json=drawer_positions_json,
    )




@bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search by name OR barcode
    parts = Part.query.filter(
        (Part.name.ilike(f'%{query}%')) |
        (Part.barcode.ilike(f'%{query}%')) |
        (Part.part_number.ilike(f'%{query}%'))
    ).limit(10).all()
    
    results = [{
        'id': p.id,
        'name': p.name,
        'quantity': p.qty,
        'location': p.location,
        'barcode': p.barcode
    } for p in parts]
    
    return jsonify(results)


# ====================== MARK ON ORDER ======================
@bp.route("/mark_ordered/<int:id>", methods=["POST"])
@login_required
def mark_ordered(id):
    part = Part.query.get_or_404(id)
    ordered_by = (request.form.get("ordered_by") or "").strip() or current_user.username
    part.on_order = True
    part.ordered_by = ordered_by
    part.ordered_at = datetime.utcnow()
    db.session.commit()
    flash(f"'{part.name}' marked ON ORDER by {part.ordered_by}.", "success")
    return redirect(request.referrer or url_for("parts.index"))


@bp.route("/clear_ordered/<int:id>", methods=["POST"])
@login_required
def clear_ordered(id):
    part = Part.query.get_or_404(id)
    part.on_order = False
    part.ordered_by = None
    part.ordered_at = None
    db.session.commit()
    flash(f"'{part.name}' order status cleared.", "success")
    return redirect(request.referrer or url_for("parts.index"))

