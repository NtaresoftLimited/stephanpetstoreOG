import re

# 1. Update stock_picking.py
with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    stock_code = f.read()

drawing_logic = '''import io
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

def barcode(c, value, x, y, width, height):
    item = code128.Code128(value, barHeight=height, barWidth=0.34 * mm, humanReadable=False)
    scale = min(1.0, width / item.width)
    c.saveState()
    c.translate(x, y)
    c.scale(scale, 1)
    item.drawOn(c, 0, 0)
    c.restoreState()

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def generate_custom_pdf(self):
        self.ensure_one()
        picking = self
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        page_w, page_h = A4
        left, right = 15 * mm, page_w - 15 * mm
        usable = right - left
        
        def draw_header(canvas_obj):
            if picking.company_id.logo:
                try:
                    logo_img = ImageReader(io.BytesIO(base64.b64decode(picking.company_id.logo)))
                    canvas_obj.drawImage(logo_img, right - 42 * mm, page_h - 34 * mm, width=42 * mm, height=20 * mm, preserveAspectRatio=True, anchor="sw", mask="auto")
                except Exception:
                    pass
                
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(left, page_h - 15 * mm, "Stephan's Pet Store")
            
            canvas_obj.setFont("Helvetica", 7.5)
            text_lines = [
                "+255 786 627 873  |  +255 769 324 445",
                "11 Slipway Rd, Masaki, Dar es Salaam",
                "59 Mikocheni A, Dar es Salaam",
                "info@stephanspetstore.co.tz"
            ]
            y_text = page_h - 20 * mm
            for line in text_lines:
                canvas_obj.drawString(left, y_text, line)
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
            picking_name = picking.name or "DRAFT"
            canvas_obj.drawString(left + 7 * mm, title_y + 11.5 * mm, picking_name)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 7.5)
            canvas_obj.drawString(left + 7 * mm, title_y + 6 * mm, "INTERNAL TRANSFER")
            
            barcode(canvas_obj, picking_name, right - 58 * mm, title_y + 5.5 * mm, 53 * mm, 12 * mm)

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
            source_name = picking.location_id.display_name or ""
            dest_name = picking.location_dest_id.display_name or ""
            canvas_obj.drawString(left + 4 * mm, route_y + 5.5 * mm, source_name[:35])
            canvas_obj.drawString(left + side_w + arrow_w + 4 * mm, route_y + 5.5 * mm, dest_name[:35])
            
            canvas_obj.setFillColor(ACCENT)
            canvas_obj.setFont("Helvetica-Bold", 18)
            canvas_obj.drawCentredString(left + side_w + arrow_w / 2, route_y + 5.5 * mm, "→")

            meta_y = route_y - 16 * mm
            schedule_date = picking.scheduled_date.strftime("%d %b %Y, %H:%M") if picking.scheduled_date else "N/A"
            entries = [("Origin", picking.origin or "Manual"), ("Status", picking.state.capitalize() if picking.state else "Draft"), ("Scheduled Date", schedule_date)]
            
            for index, (heading, value) in enumerate(entries):
                x = left + index * usable / 3 + 4 * mm
                label(canvas_obj, heading, x, meta_y + 6.5 * mm)
                canvas_obj.setFillColor(TEXT)
                canvas_obj.setFont("Helvetica-Bold", 8.5)
                canvas_obj.drawString(x, meta_y + 2 * mm, value)
                
            return meta_y - 4 * mm

        def draw_footer(canvas_obj, page_num):
            footer_y = 14 * mm
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, footer_y + 4 * mm, right, footer_y + 4 * mm)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica", 7.5)
            canvas_obj.drawCentredString(page_w / 2, footer_y, "Stephan's Pet Store - Inventory Operations Internal Transfer")
            
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

        moves = picking.move_ids
        
        if not moves:
            c.setStrokeColor(BORDER)
            c.rect(left, y_cursor - row_h, usable, row_h, stroke=1, fill=0)
            y_cursor -= row_h
        
        for index, move in enumerate(moves):
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
            c.setFont("Helvetica", 8.5)
            product_name = move.product_id.display_name or ""
            c.drawString(left + 4 * mm, row_top - 7 * mm, product_name[:65])
            
            qty = move.quantity if move.state == 'done' else move.product_uom_qty
            uom = move.product_uom.name or ""
            c.drawCentredString(left + col_1 + col_2 / 2, row_top - 7 * mm, f"{qty} {uom}")
            
            if move.product_id.barcode:
                barcode(c, move.product_id.barcode, right - 42 * mm, row_top - 9 * mm, 37 * mm, 7 * mm)

        if moves:
            c.setStrokeColor(BORDER)
            c.rect(left, y_cursor, usable, start_y_cursor - y_cursor, stroke=1, fill=0)
            
        draw_footer(c, page_num)

        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
'''

stock_code = stock_code.replace("class StockPicking(models.Model):\n    _inherit = 'stock.picking'", drawing_logic)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
    f.write(stock_code)

# 2. Update pdf_report_controller.py
controller_code = '''from odoo import http
from odoo.http import request

class InternalTransferReportController(http.Controller):
    
    @http.route(['/print/transfer/<int:picking_id>'], type='http', auth='user')
    def print_internal_transfer(self, picking_id, **kw):
        picking = request.env['stock.picking'].browse(picking_id)
        if not picking.exists():
            return request.not_found()

        pdf_data = picking.generate_custom_pdf()

        safe_filename = (picking.name or "Transfer").replace("/", "_").replace("\\\\", "_")
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_data)),
            ('Content-Disposition', f'attachment; filename="Internal_Transfer_{safe_filename}.pdf"')
        ]
        return request.make_response(pdf_data, headers=pdfhttpheaders)
'''
with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\controllers\pdf_report_controller.py', 'w', encoding='utf-8') as f:
    f.write(controller_code)

# 3. Update whatsapp_transfer_wizard.py
wizard_code = '''from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64

class WhatsappTransferWizard(models.TransientModel):
    _name = 'whatsapp.transfer.wizard'
    _description = 'Send Transfer via WhatsApp'

    picking_id = fields.Many2one('stock.picking', required=True)
    phone_number = fields.Char(string='Phone Number', required=True, help="Include country code, e.g. 255786...")
    message = fields.Text(string='Message', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(WhatsappTransferWizard, self).default_get(fields_list)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.picking':
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            res['picking_id'] = picking.id
            res['message'] = f"Hello! The Internal Transfer {picking.name} is attached to this message."
            res['phone_number'] = '+255792079463'
        return res

    def action_send(self):
        self.ensure_one()
        url = "https://wasenderapi.com/api/send-message"
        
        pdf_bytes = self.picking_id.generate_custom_pdf()
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        payload = {
            "to": self.phone_number,
            "text": self.message,
            "documentBase64": pdf_b64,
            "fileName": f"Internal_Transfer_{self.picking_id.name.replace('/', '_')}.pdf"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
            "User-Agent": "Odoo/18.0"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            if not res_json.get("success") and res_json.get("status") == "error":
                raise UserError(f"API Error: {res_json.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Failed to connect to WaSender API: {str(e)}")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'WhatsApp Sent',
                'message': 'Your PDF has been successfully sent via WaSender!',
                'type': 'success',
                'sticky': False,
            }
        }
'''
with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py', 'w', encoding='utf-8') as f:
    f.write(wizard_code)
