from odoo import models, fields, api

import io
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
                    # Draw logo on the left side
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
                # Draw text right-aligned on the right side
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


    custom_source_warehouse_id = fields.Many2one(
        'stock.warehouse', 
        string='Source Warehouse',
        compute='_compute_custom_warehouses',
        inverse='_inverse_custom_source_warehouse',
        store=True,
        readonly=False
    )
    custom_destination_warehouse_id = fields.Many2one(
        'stock.warehouse', 
        string='Destination Warehouse',
        compute='_compute_custom_warehouses',
        inverse='_inverse_custom_destination_warehouse',
        store=True,
        readonly=False
    )

    @api.depends('location_id', 'location_dest_id')
    def _compute_custom_warehouses(self):
        for picking in self:
            if picking.location_id:
                picking.custom_source_warehouse_id = picking.location_id.warehouse_id
            if picking.location_dest_id:
                picking.custom_destination_warehouse_id = picking.location_dest_id.warehouse_id

    def _inverse_custom_source_warehouse(self):
        for picking in self:
            if picking.custom_source_warehouse_id and picking.custom_source_warehouse_id.lot_stock_id:
                picking.location_id = picking.custom_source_warehouse_id.lot_stock_id

    def _inverse_custom_destination_warehouse(self):
        for picking in self:
            if picking.custom_destination_warehouse_id and picking.custom_destination_warehouse_id.lot_stock_id:
                picking.location_dest_id = picking.custom_destination_warehouse_id.lot_stock_id

    @api.model
    def create_transfer_from_pos(self, payload):
        """
        Creates a native stock.picking (Internal Transfer) directly from the POS.
        payload = {
            'source_warehouse_id': int,
            'destination_warehouse_id': int,
            'lines': [{'product_id': int, 'qty': float}, ...]
        }
        """
        source_wh = self.env['stock.warehouse'].browse(payload.get('source_warehouse_id'))
        dest_wh = self.env['stock.warehouse'].browse(payload.get('destination_warehouse_id'))
        
        if not source_wh or not dest_wh:
            raise ValueError("Invalid source or destination warehouse.")
            
        src_location = source_wh.lot_stock_id
        dest_location = dest_wh.lot_stock_id
        
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', source_wh.id)
        ], limit=1)
        
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal')
            ], limit=1)
            
        move_ids = []
        for line in payload.get('lines', []):
            product = self.env['product.product'].browse(line['product_id'])
            move_ids.append((0, 0, {
                'name': product.name,
                'product_id': product.id,
                'product_uom_qty': line['qty'],
                'product_uom': product.uom_id.id,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
            }))
            
        picking = self.create({
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'origin': 'POS Stock Request',
            'move_ids': move_ids,
            'custom_source_warehouse_id': source_wh.id,
            'custom_destination_warehouse_id': dest_wh.id,
        })
        
        picking.action_confirm()
        
        # Auto-send WhatsApp notification
        try:
            message = f"Hi Boss! Internal Transfer {picking.name} has been requested:\n📍 *From (Source):* {source_wh.name}\n🏁 *To (Destination):* {dest_wh.name}\nPlease review the attached PDF for your Approval."
            wizard = self.env['whatsapp.transfer.wizard'].create({
                'picking_id': picking.id,
                'phone_number': '+255792079463',
                'message': message,
            })
            wizard.action_send()
        except Exception as e:
            # Catch exceptions so it doesn't break the POS flow if WhatsApp fails
            import logging
            logging.getLogger(__name__).warning("Failed to auto-send WhatsApp from POS: %s", str(e))
            
        return picking.id

    @api.model
    def create_replenishment_from_pos(self, payload):
        """
        Creates a custom grooming.stock.request (Replenishment Request) directly from the POS.
        Destination is strictly Masaki Back Storage (Central Hub).
        """
        # Replenishment is strictly locked to Masaki Back Storage for both POS systems
        dest_wh = self.env['stock.warehouse'].sudo().search([('code', '=', 'MBS')], limit=1)
        if not dest_wh:
            dest_wh = self.env['stock.warehouse'].sudo().search([('name', 'ilike', 'Masaki Back Storage')], limit=1)
        if not dest_wh:
            dest_wh = self.env['stock.warehouse'].sudo().browse(2)
            
        if not dest_wh:
            raise ValueError("Masaki Back Storage warehouse not found.")
            
        lines = []
        for line in payload.get('lines', []):
            lines.append((0, 0, {
                'product_id': line['product_id'],
                'quantity': line['qty']
            }))
            
        request = self.env['grooming.stock.request'].sudo().create({
            'destination_warehouse_id': dest_wh.id,
            'product_line_ids': lines,
            'state': 'submitted'
        })
        
        # Auto-send WhatsApp notification
        try:
            import base64
            import requests
            
            pdf_bytes = request.generate_custom_pdf()
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            file_name = f"Replenishment_Request_{request.name.replace('/', '_')}.pdf"
            
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'type': 'binary',
                'datas': pdf_b64,
                'res_model': 'grooming.stock.request',
                'res_id': request.id,
                'public': True,
            })
            if not attachment.access_token:
                attachment.generate_access_token()
                
            base_url = self.env['ir.config_parameter'].sudo().get_str('web.base.url')
            doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
            
            payload = {
                "to": '+255792079463',
                "text": f"Hi Boss! A new Replenishment Request {request.name} has been submitted from the POS.\n📦 *Destination:* {dest_wh.name} (Central Hub)\nPlease review the attached PDF for your Approval.",
                "documentUrl": doc_url,
                "fileName": file_name
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
                "User-Agent": "Odoo/18.0"
            }
            requests.post("https://wasenderapi.com/api/send-message", json=payload, headers=headers, timeout=30)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to auto-send WhatsApp for Replenishment: %s", str(e))
            
        return request.id

    def action_download_custom_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/print/transfer/{self.id}',
            'target': 'new',
        }

    def action_send_whatsapp(self):
        self.ensure_one()
        return {
            'name': 'Send WhatsApp Message',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': 'stock.picking'}
        }

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            # Update any linked stock request to 'received'
            requests = self.env['grooming.stock.request'].sudo().search([('picking_id', '=', picking.id)])
            for req in requests:
                req.sudo().write({'state': 'received'})

            # Auto-send WhatsApp notification to Boss when receipt / transfer is validated
            if picking.picking_type_code in ('internal', 'incoming') and (requests or (picking.origin and ('POS' in picking.origin or 'SR/' in picking.origin))):
                try:
                    src_name = picking.location_id.display_name or (picking.custom_source_warehouse_id.name if picking.custom_source_warehouse_id else "")
                    dest_name = picking.location_dest_id.display_name or (picking.custom_destination_warehouse_id.name if picking.custom_destination_warehouse_id else "")
                    origin_str = picking.origin or "Replenishment / Transfer"
                    
                    if picking.picking_type_code == 'incoming':
                        msg = (
                            f"✅ *Goods Received in Backstore!*\n\n"
                            f"Receipt *{picking.name}* ({origin_str}) has been received and validated.\n"
                            f"🏁 *Received at:* {dest_name}\n\n"
                            f"Stock has been added to Masaki Back Storage successfully."
                        )
                    else:
                        msg = (
                            f"✅ *Transfer Completed & Validated!*\n\n"
                            f"Internal Transfer *{picking.name}* ({origin_str}) has been approved and validated.\n"
                            f"📍 *From (Source):* {src_name}\n"
                            f"🏁 *To (Destination):* {dest_name}\n\n"
                            f"Stock has been received and successfully updated in the inventory."
                        )
                    
                    wizard = self.env['whatsapp.transfer.wizard'].sudo().create({
                        'picking_id': picking.id,
                        'phone_number': '+255792079463',
                        'message': msg,
                    })
                    wizard.action_send()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning("Failed to auto-send WhatsApp on transfer validation: %s", str(e))
                    
        return res
