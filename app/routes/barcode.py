from flask import Blueprint, request, send_file
import io
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image

bp = Blueprint('barcode', __name__)

# Generate single barcode image
@bp.route('/generate')
def generate_barcode():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    barcode = Code128(code, writer=ImageWriter())
    buffer = io.BytesIO()
    barcode.write(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', download_name=f"{code}.png")


# Generate PDF with barcode
@bp.route('/generate_pdf')
def generate_barcode_pdf():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Part Barcode: {code}")
    
    # Generate barcode image
    barcode = Code128(code, writer=ImageWriter())
    img_buffer = io.BytesIO()
    barcode.write(img_buffer)
    img_buffer.seek(0)
    img = Image.open(img_buffer)
    
    c.drawInlineImage(img, 100, 550, width=400, height=120)
    
    c.save()
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"barcode_{code}.pdf"
    )