import reportlab.rl_config as rl_config
rl_config.renderPMBackend = 'rlPyCairo'
from flask import Blueprint, render_template, request, redirect, flash, url_for, send_file
from flask_login import login_required, current_user
from app import db
from app.models.part import Part
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPM
from reportlab.lib.units import mm
from reportlab.graphics.barcode import createBarcodeDrawing

bp = Blueprint("parts", __name__)

@bp.route('/generate_barcode')
def generate_barcode():
    code = request.args.get('code', '')
    if not code:
        return "No code provided", 400

    # Create the barcode drawing directly
    d = createBarcodeDrawing(
        'Code128',
        value=code,
        barHeight=20*mm,
        barWidth=0.3*mm,
        humanReadable=True
    )

    # Render to PNG buffer
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
    # Add header title here
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, height - 1 * inch, "Parts Detail")
    # Part details
    c.setFont("Helvetica", 12)
    y = height - 1.5 * inch  # Adjusted to start below the title
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
    # Barcode if available, moved to bottom center
    if code:
        barcode = code128.Code128(code, barHeight=20*mm, barWidth=0.3*mm, humanReadable=True)
        barcode.drawOn(c, (width / 2 - 50*mm), 1 * inch) # Centered at bottom
    c.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"part_{part.id}.pdf",
        mimetype='application/pdf'
    )
@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        if not current_user.is_admin(): # Block non-admins from all POST actions
            flash("You do not have permission to add, edit, or delete parts.", "danger")
            return redirect(url_for("parts.index"))
        delete_index = request.form.get("delete_index")
    
        if delete_index:
            try:
                part_id = int(delete_index)
            except ValueError:
                flash("Bad delete request.", "danger")
                return redirect(url_for("parts.index"))
            part = Part.query.get(part_id)
            if part:
                db.session.delete(part)
                db.session.commit()
                flash("Part deleted successfully.", "success")
            else:
                flash("Part not found.", "danger")
            return redirect(url_for("parts.index"))
    
        index = request.form.get("index", "").strip()
        barcode = request.form.get("barcode", "").strip() or None
        name = request.form.get("name", "").strip()
        part_number = request.form.get("part_number", "").strip()
        qty_str = request.form.get("qty", "").strip()
        min_stock_str = request.form.get("min_stock", "0").strip()
        max_stock_str = request.form.get("max_stock", "999").strip()
        location = request.form.get("location", "").strip()
        sublocation = request.form.get("sublocation", "").strip()
    
        # Parse to int with validation
        try:
            qty = int(qty_str) if qty_str else 0
            min_stock = int(min_stock_str) if min_stock_str else 0
            max_stock = int(max_stock_str) if max_stock_str else 999
            if qty < 0 or min_stock < 0 or max_stock < 0:
                raise ValueError("Quantities cannot be negative")
            if min_stock > max_stock:
                raise ValueError("Min stock cannot exceed max stock")
        except ValueError as e:
            flash(f"Invalid quantity input: {str(e)}", "danger")
            return redirect(url_for("parts.index"))
    
        if index:
            try:
                part_id = int(index)
            except ValueError:
                flash("Bad update request.", "danger")
                return redirect(url_for("parts.index"))
            part = Part.query.get(part_id)
            if part:
                # Check for barcode duplicate if changed
                if barcode and barcode != part.barcode and Part.query.filter_by(barcode=barcode).first():
                    flash("Barcode already in use.", "danger")
                    return redirect(url_for("parts.index"))
                part.barcode = barcode
                part.name = name
                part.part_number = part_number
                part.qty = qty
                part.min_stock = min_stock
                part.max_stock = max_stock
                part.location = location
                part.sublocation = sublocation
                try:
                    db.session.commit()
                    flash("Part updated successfully.", "success")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Update failed: {str(e)}", "danger")
            else:
                flash("Part not found.", "danger")
        else:
            if name:
                # Check for barcode duplicate on add
                if barcode and Part.query.filter_by(barcode=barcode).first():
                    flash("Barcode already in use.", "danger")
                    return redirect(url_for("parts.index"))
                new_part = Part(
                    barcode=barcode,
                    name=name,
                    part_number=part_number,
                    qty=qty,
                    min_stock=min_stock,
                    max_stock=max_stock,
                    location=location,
                    sublocation=sublocation,
                )
                db.session.add(new_part)
                db.session.commit()
                flash("Part added successfully.", "success")
            else:
                flash("Name is required.", "danger")
        return redirect(url_for("parts.index"))
    search = request.args.get("search", "").strip().lower()
    show_all = request.args.get("show_all")
    low_stock = request.args.get("low_stock") # New: Check for low_stock param
   
    if current_user.is_admin():
        if low_stock:
            parts = Part.query.filter(Part.qty <= Part.min_stock).all() # Filter low-stock parts
        elif show_all:
            parts = Part.query.all()
        else:
            if search:
                parts = Part.query.filter(
                    Part.barcode.ilike(f"%{search}%")
                    | Part.name.ilike(f"%{search}%")
                    | Part.part_number.ilike(f"%{search}%")
                    | Part.location.ilike(f"%{search}%")
                    | Part.sublocation.ilike(f"%{search}%")
                ).all()
            else:
                parts = Part.query.all() # Default to all for admins
    else: # Technician
        if search:
            parts = Part.query.filter(
                Part.barcode.ilike(f"%{search}%")
                | Part.name.ilike(f"%{search}%")
                | Part.part_number.ilike(f"%{search}%")
                | Part.location.ilike(f"%{search}%")
                | Part.sublocation.ilike(f"%{search}%")
            ).all()
        elif low_stock:
            parts = Part.query.filter(Part.qty <= Part.min_stock).all() # Allow low stock view for tech
        else:
            parts = []
            flash("Use search or scan to find specific parts.", "info")
   
    items = []
    for i, part in enumerate(parts):
        items.append(
            (
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
                },
            )
        )
    return render_template("parts.html", items=items, search=search)