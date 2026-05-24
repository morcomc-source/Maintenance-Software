import reportlab.rl_config as rl_config
rl_config.renderPMBackend = 'rlPyCairo'

from flask import Blueprint, render_template, request, redirect, flash, url_for, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.part import Part
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPM
from reportlab.lib.units import mm

bp = Blueprint("parts", __name__)

# ====================== BARCODE ROUTES ======================
@bp.route('/generate_barcode')
def generate_barcode():
    code = request.args.get('code', '')
    if not code:
        return "No code provided", 400
    d = code128.Code128(code, barHeight=20*mm, barWidth=0.3*mm, humanReadable=True)
    buffer = BytesIO()
    renderPM.drawToFile(d, buffer, fmt="PNG")
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
                    part.min_stock = int(request.form.get("min_stock", 0))
                    part.max_stock = int(request.form.get("max_stock", 999))
                    part.location = request.form.get("location", "").strip()
                    part.sublocation = request.form.get("sublocation", "").strip()

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
                new_part = Part(
                    barcode=request.form.get("barcode", "").strip() or None,
                    name=name,
                    part_number=request.form.get("part_number", "").strip(),
                    qty=int(request.form.get("qty", 0)),
                    min_stock=int(request.form.get("min_stock", 0)),
                    max_stock=int(request.form.get("max_stock", 999)),
                    location=request.form.get("location", "").strip(),
                    sublocation=request.form.get("sublocation", "").strip(),
                )
                db.session.add(new_part)
                db.session.commit()
                flash("Part added successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding part: {str(e)}", "danger")
        else:
            flash("Name is required to add a part.", "danger")

        return redirect(url_for("parts.index"))

    # ====================== GET + SEARCH ======================
    search = request.args.get("search", "").strip().lower()

    if search:
        parts = Part.query.filter(
            Part.name.ilike(f"%{search}%") |
            Part.part_number.ilike(f"%{search}%") |
            Part.barcode.ilike(f"%{search}%") |
            Part.location.ilike(f"%{search}%")
        ).all()
    else:
        parts = Part.query.all()

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
                "sublocation": part.sublocation,
            }
        ))

    return render_template("parts.html", items=items, search=search)


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