import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add imports if they don't exist
imports = """import io
import base64
from reportlab.graphics.barcode import code128
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

GREEN = HexColor("#3e220f")
ACCENT = HexColor("#3e220f")
TEXT = HexColor("#17231f")
MUTED = HexColor("#60736c")
BORDER = HexColor("#d8e4df")

def label(c, text, x, y):
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Bold", 7.2)
    c.drawString(x, y, text.upper())

def barcode(c, value, x, y, w, h):
    c.setFillColor(white)
    c.rect(x - 2 * mm, y - 2 * mm, w + 4 * mm, h + 4 * mm, fill=1, stroke=0)
    bc = code128.Code128(value, barHeight=h, barWidth=1.2)
    bc.drawOn(c, x, y)
"""

if "import io" not in code:
    code = code.replace("from odoo.exceptions import UserError\n", "from odoo.exceptions import UserError\n\n" + imports)

# Now add generate_custom_pdf method
pdf_method = """
    def generate_custom_pdf(self):
        self.ensure_one()
        request = self
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        page_w, page_h = A4
        left, right = 15 * mm, page_w - 15 * mm
        usable = right - left
        
        def draw_header(canvas_obj):
            if self.env.company.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(self.env.company.logo)))
                    canvas_obj.drawImage(logo_img, left, page_h - 34 * mm, width=42 * mm, height=20 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica", 7.5)
            text_lines = [
                "+255 786 627 873  |  +255 769 324 445",
                "11 Slipway Rd, Masaki, Dar es Salaam",
                "59 Mikocheni A, Dar es Salaam",
                "info@stephanspetstore.co.tz"
            ]
            y_text = page_h - 15 * mm
            for line in text_lines:
                canvas_obj.drawRightString(right, y_text, line)
                y_text -= 4.5 * mm
            
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, page_h - 38 * mm, right, page_h - 38 * mm)

            title_y, title_h = page_h - 66 * mm, 23 * mm
            canvas_obj.setStrokeColor(BORDER)
            canvas_obj.roundRect(left, title_y, usable, title_h, 3 * mm, stroke=1, fill=0) 
            
            canvas_obj.setStrokeColor(ACCENT)
            canvas_obj.setLineWidth(4)
            canvas_obj.line(left + 1.2, title_y + 2.8 * mm, left + 1.2, title_y + title_h - 2.8 * mm)
            canvas_obj.setLineWidth(1)
            
            canvas_obj.setFillColor(TEXT)
            canvas_obj.setFont("Helvetica-Bold", 20)
            req_name = request.name or "DRAFT"
            canvas_obj.drawString(left + 7 * mm, title_y + 11.5 * mm, req_name)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 7.5)
            canvas_obj.drawString(left + 7 * mm, title_y + 6 * mm, "REPLENISHMENT REQUEST")
            
            barcode(canvas_obj, req_name, right - 58 * mm, title_y + 5.5 * mm, 53 * mm, 12 * mm)

            route_y, route_h = title_y - 27 * mm, 18 * mm
            arrow_w = 16 * mm
            side_w = (usable - arrow_w) / 2
            
            canvas_obj.setStrokeColor(BORDER)
            canvas_obj.roundRect(left, route_y, usable, route_h, 3 * mm, stroke=1, fill=0)
            
            canvas_obj.line(left + side_w, route_y, left + side_w, route_y + route_h)
            canvas_obj.line(left + side_w + arrow_w, route_y, left + side_w + arrow_w, route_y + route_h)
            
            label(canvas_obj, "From Location", left + 4 * mm, route_y + 11.5 * mm)
            label(canvas_obj, "To Location", left + side_w + arrow_w + 4 * mm, route_y + 11.5 * mm)
            
            canvas_obj.setFillColor(TEXT)
            canvas_obj.setFont("Helvetica-Bold", 12)
            source_name = request.source_warehouse_id.name or ""
            dest_name = request.destination_warehouse_id.name or ""
            canvas_obj.drawString(left + 4 * mm, route_y + 5.5 * mm, source_name[:35])
            canvas_obj.drawString(left + side_w + arrow_w + 4 * mm, route_y + 5.5 * mm, dest_name[:35])
            
            canvas_obj.setFillColor(ACCENT)
            canvas_obj.setFont("Helvetica-Bold", 18)
            canvas_obj.drawCentredString(left + side_w + arrow_w / 2, route_y + 5.5 * mm, "→")

            meta_y = route_y - 16 * mm
            schedule_date = request.create_date.strftime("%d %b %Y, %H:%M") if request.create_date else "N/A"
            entries = [("Origin", "POS Request"), ("Status", dict(request._fields['state'].selection).get(request.state, "Draft")), ("Creation Date", schedule_date)]
            
            for index, (heading, value) in enumerate(entries):
                x = left + index * usable / 3 + 4 * mm
                label(canvas_obj, heading, x, meta_y + 6.5 * mm)
                canvas_obj.setFillColor(TEXT)
                canvas_obj.setFont("Helvetica-Bold", 8.5)
                canvas_obj.drawString(x, meta_y + 2 * mm, str(value))
                
            return meta_y - 4 * mm

        def draw_footer(canvas_obj, page_num):
            footer_y = 14 * mm
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, footer_y + 4 * mm, right, footer_y + 4 * mm)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica", 7.5)
            canvas_obj.drawCentredString(page_w / 2, footer_y, "Stephan's Pet Store - Inventory Replenishment Request")
            
            page_text = f"Page {page_num}"
            canvas_obj.drawString(right - stringWidth(page_text, "Helvetica", 7.5), footer_y, page_text)

        def draw_table_header(canvas_obj, y_top):
            header_h = 8 * mm
            col_1, col_2 = usable * 0.58, usable * 0.18
            
            canvas_obj.setFillColor(GREEN)
            canvas_obj.roundRect(left, y_top - header_h, usable, header_h, 2.5 * mm, stroke=0, fill=1)
            canvas_obj.rect(left, y_top - header_h, usable, header_h - 2.5 * mm, stroke=0, fill=1)
            canvas_obj.setFillColor(white)
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.drawString(left + 4 * mm, y_top - 5.4 * mm, "PRODUCT")
            canvas_obj.drawCentredString(left + col_1 + col_2 / 2, y_top - 5.4 * mm, "QUANTITY")
            canvas_obj.drawCentredString(left + col_1 + col_2 + (usable - col_1 - col_2) / 2, y_top - 5.4 * mm, "PRODUCT BARCODE")
            
            return y_top - header_h

        table_top = draw_header(c)
        y_cursor = draw_table_header(c, table_top)
        start_y_cursor = y_cursor
        
        row_h = 11 * mm
        bottom_limit = 28 * mm
        page_num = 1
        col_1, col_2 = usable * 0.58, usable * 0.18

        lines = request.product_line_ids
        
        if not lines:
            c.setStrokeColor(BORDER)
            c.rect(left, y_cursor - row_h, usable, row_h, stroke=1, fill=0)
            y_cursor -= row_h
        
        for index, line in enumerate(lines):
            if y_cursor - row_h < bottom_limit:
                c.setStrokeColor(BORDER)
                c.rect(left, y_cursor, usable, start_y_cursor - y_cursor, stroke=1, fill=0)
                
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                
                table_top = page_h - 20 * mm
                y_cursor = draw_table_header(c, table_top)
                start_y_cursor = y_cursor

            row_top = y_cursor
            y_cursor -= row_h
            
            if row_top < start_y_cursor:
                c.setStrokeColor(BORDER)
                c.line(left, row_top, right, row_top)

            c.setFillColor(TEXT)
            c.setFont("Helvetica-Bold", 8.5)
            prod_name = (line.product_id.name or "")[:55]
            c.drawString(left + 4 * mm, y_cursor + 5.5 * mm, prod_name)
            
            c.setFont("Helvetica", 8.5)
            c.drawCentredString(left + col_1 + col_2 / 2, y_cursor + 4 * mm, str(line.quantity))
            
            c.setFillColor(MUTED)
            bc = line.product_id.barcode or "N/A"
            c.drawCentredString(left + col_1 + col_2 + (usable - col_1 - col_2) / 2, y_cursor + 4 * mm, bc)

        c.setStrokeColor(BORDER)
        c.rect(left, y_cursor, usable, start_y_cursor - y_cursor, stroke=1, fill=0)
        c.line(left + col_1, start_y_cursor, left + col_1, y_cursor)
        c.line(left + col_1 + col_2, start_y_cursor, left + col_1 + col_2, y_cursor)
        
        draw_footer(c, page_num)
        c.save()
        return buffer.getvalue()
"""

if "def generate_custom_pdf(self):" not in code:
    code = code.replace("def action_submit_request(self):", pdf_method + "\n    def action_submit_request(self):")
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: generate_custom_pdf added to stock_request.py")
else:
    print("Already exists")
