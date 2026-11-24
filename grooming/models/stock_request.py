from odoo import models, fields, api, _
from odoo.exceptions import UserError

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

def barcode(c, value, x, y, w, h):
    c.setFillColor(white)
    c.rect(x - 2 * mm, y - 2 * mm, w + 4 * mm, h + 4 * mm, fill=1, stroke=0)
    bc = code128.Code128(value, barHeight=h, barWidth=1.2)
    bc.drawOn(c, x, y)

class GroomingStockRequest(models.Model):
    _name = 'grooming.stock.request'
    _description = 'Inter-Warehouse Stock Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    def _get_default_destination_warehouse(self):
        return self.env['stock.warehouse'].search([('code', '=', 'MBS')], limit=1)

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('transferred', 'Received'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    source_warehouse_id = fields.Many2one('stock.warehouse', string='Source Warehouse', required=False, tracking=True, 
                                          help="The warehouse where the items are coming from (optional).")
    destination_warehouse_id = fields.Many2one('stock.warehouse', string='Destination Warehouse', required=True, tracking=True,
                                               default=_get_default_destination_warehouse,
                                               help="The destination warehouse (Strictly Masaki Back Storage).")
    
    product_line_ids = fields.One2many('grooming.stock.request.line', 'request_id', string='Product Lines')
    picking_id = fields.Many2one('stock.picking', string='Generated Receipt', readonly=True)
    bill_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

    @api.model
    def _get_backstore_warehouse(self):
        """Replenishment only ever restocks Masaki Back Storage (warehouse code MBS)."""
        mbs_wh = self.env['stock.warehouse'].sudo().search([('code', '=', 'MBS')], limit=1)
        if not mbs_wh:
            raise UserError(_("Masaki Back Storage warehouse (code: MBS) was not found."))
        return mbs_wh

    @api.model_create_multi
    def create(self, vals_list):
        mbs_wh = self._get_backstore_warehouse()
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('grooming.stock.request') or _('New')
            # Always Masaki Back Storage, whatever the caller sent (POS, import, script).
            vals['destination_warehouse_id'] = mbs_wh.id
        return super().create(vals_list)

    def write(self, vals):
        if 'destination_warehouse_id' in vals:
            vals = dict(vals, destination_warehouse_id=self._get_backstore_warehouse().id)
        return super().write(vals)

    def action_view_vendor_bill(self):
        self.ensure_one()
        return {
            'name': _('Vendor Bill'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current',
        }
    
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
            
            label(canvas_obj, "Source", left + 4 * mm, route_y + 11.5 * mm)
            label(canvas_obj, "Destination (Central Hub)", left + side_w + arrow_w + 4 * mm, route_y + 11.5 * mm)
            
            canvas_obj.setFillColor(TEXT)
            canvas_obj.setFont("Helvetica-Bold", 12)
            source_name = "Central Replenishment Supplier"
            dest_name = request.destination_warehouse_id.name or "Masaki Back Storage"
            canvas_obj.drawString(left + 4 * mm, route_y + 5.5 * mm, source_name[:35])
            canvas_obj.drawString(left + side_w + arrow_w + 4 * mm, route_y + 5.5 * mm, dest_name[:35])
            
            canvas_obj.setFillColor(ACCENT)
            canvas_obj.setFont("Helvetica-Bold", 18)
            canvas_obj.drawCentredString(left + side_w + arrow_w / 2, route_y + 5.5 * mm, "→")

            meta_y = route_y - 16 * mm
            schedule_date = request.create_date.strftime("%d %b %Y, %H:%M") if request.create_date else "N/A"
            entries = [("Origin", "POS Replenishment"), ("Status", dict(request._fields['state'].selection).get(request.state, "Draft")), ("Creation Date", schedule_date)]
            box_w = usable / len(entries)
            
            for i, (k, v) in enumerate(entries):
                bx = left + i * box_w
                canvas_obj.setStrokeColor(BORDER)
                canvas_obj.roundRect(bx, meta_y, box_w - (2 * mm if i < len(entries) - 1 else 0), 12 * mm, 2 * mm, stroke=1, fill=0)
                label(canvas_obj, k, bx + 3 * mm, meta_y + 7.5 * mm)
                canvas_obj.setFillColor(TEXT)
                canvas_obj.setFont("Helvetica-Bold", 8.5)
                canvas_obj.drawString(bx + 3 * mm, meta_y + 3 * mm, str(v))

            return meta_y - 8 * mm

        def draw_table_header(canvas_obj, y_top):
            col_1 = usable * 0.55
            col_2 = usable * 0.20
            h = 8 * mm
            canvas_obj.setFillColor(HexColor("#f0f4f2"))
            canvas_obj.rect(left, y_top - h, usable, h, fill=1, stroke=0)
            canvas_obj.setStrokeColor(BORDER)
            canvas_obj.rect(left, y_top - h, usable, h, fill=0, stroke=1)
            
            label(canvas_obj, "Product Description", left + 4 * mm, y_top - 5.5 * mm)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica-Bold", 7.2)
            canvas_obj.drawCentredString(left + col_1 + col_2 / 2, y_top - 5.5 * mm, "QTY")
            canvas_obj.drawCentredString(left + col_1 + col_2 + (usable - col_1 - col_2) / 2, y_top - 5.5 * mm, "BARCODE")
            return y_top - h

        def draw_footer(canvas_obj, page_num):
            canvas_obj.setStrokeColor(HexColor("#cbd8d3"))
            canvas_obj.line(left, 15 * mm, right, 15 * mm)
            canvas_obj.setFillColor(MUTED)
            canvas_obj.setFont("Helvetica", 7.5)
            canvas_obj.drawString(left, 10 * mm, "Stephan's Pet Store - Automatic Replenishment System")
            canvas_obj.drawRightString(right, 10 * mm, f"Page {page_num}")

        page_num = 1
        content_top = draw_header(c)
        y_cursor = draw_table_header(c, content_top)
        start_y_cursor = y_cursor

        lines = request.product_line_ids
        row_h = 7.5 * mm
        bottom_limit = 25 * mm
        col_1 = usable * 0.55
        col_2 = usable * 0.20

        if not lines:
            c.setFillColor(MUTED)
            c.setFont("Helvetica", 8.5)
            c.drawString(left + 4 * mm, y_cursor - 5.5 * mm, "No products requested.")
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

    def action_submit_request(self):
        for request in self:
            if not request.product_line_ids:
                raise UserError(_("Please add at least one product line before submitting."))
            request.state = 'submitted'

    APPROVER_GROUPS = (
        'base.group_system',
        'stock.group_stock_manager',
        'point_of_sale.group_pos_manager',
    )

    def _check_approver(self):
        """The view hides the button, but RPC callers must be checked here too."""
        if self.env.su:
            return
        if not any(self.env.user.has_group(group) for group in self.APPROVER_GROUPS):
            raise UserError(_("Only an Administrator, Inventory Manager or POS Manager can approve replenishment requests."))

    def action_approve_request(self):
        self._check_approver()
        approver = self.env.user
        # Approvers are checked above; the receipt and bill are created as superuser so a
        # POS/Inventory manager without accounting rights cannot fail half-way through.
        for request in self.sudo():
            if request.state != 'submitted':
                raise UserError(_("Only submitted requests can be approved."))
            if not request.product_line_ids:
                raise UserError(_("Request %s has no product lines.") % request.name)

            # Destination is always Masaki Back Storage, never the value stored on the request.
            dest_warehouse = self._get_backstore_warehouse()
            if request.destination_warehouse_id != dest_warehouse:
                request.destination_warehouse_id = dest_warehouse

            dest_location = dest_warehouse.lot_stock_id
            supplier_location = self.env['stock.location'].sudo().search([('usage', '=', 'supplier')], limit=1)
            if not dest_location or not supplier_location:
                raise UserError(_("Masaki Back Storage stock location or the Vendors location is missing."))

            # 1. Get or create Default Replenishment Vendor (hidden from POS cashiers)
            Partner = self.env['res.partner'].sudo()
            vendor = Partner.search([('is_replenishment_vendor', '=', True)], limit=1)
            if not vendor:
                vendor = Partner.search([('name', '=', 'Central Replenishment Supplier')], limit=1)
            if not vendor:
                vendor = Partner.create({
                    'name': 'Central Replenishment Supplier',
                    'is_company': True,
                    'supplier_rank': 1,
                    'customer_rank': 0,
                    'is_replenishment_vendor': True,
                })
            else:
                if not vendor.is_replenishment_vendor:
                    vendor.write({'is_replenishment_vendor': True, 'customer_rank': 0, 'supplier_rank': 1})

            # 2. Create Incoming Shipment / Receipt directly into Masaki Back Storage
            picking_type = dest_warehouse.in_type_id or self.env['stock.picking.type'].sudo().search([
                ('code', '=', 'incoming'),
                ('warehouse_id', '=', dest_warehouse.id)
            ], limit=1)
            if not picking_type:
                raise UserError(_("Masaki Back Storage has no Receipts operation type."))

            picking_vals = {
                'picking_type_id': picking_type.id,
                'partner_id': vendor.id,
                'location_id': supplier_location.id,
                'location_dest_id': dest_location.id,
                'origin': request.name,
                'custom_source_warehouse_id': False,
                'custom_destination_warehouse_id': dest_warehouse.id,
                'move_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'uom_id': line.product_id.uom_id.id,
                    'location_id': supplier_location.id if supplier_location else False,
                    'location_dest_id': dest_location.id if dest_location else False,
                }) for line in request.product_line_ids]
            }

            picking = self.env['stock.picking'].sudo().create(picking_vals)
            picking.action_confirm()

            # Set move quantities and validate immediately so stock lands in backstore!
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            picking.button_validate()
            if picking.state != 'done':
                # e.g. a lot/serial-tracked product: validation returned a wizard instead of
                # receiving. Abort so no bill is posted for stock that never arrived.
                raise UserError(_(
                    "The receipt for %s could not be validated automatically, so nothing was received or billed. "
                    "Check the products for lot/serial tracking, then try again."
                ) % request.name)

            request.picking_id = picking.id

            # 3. Create & Automatically Post Vendor Bill
            journal = self.env['account.journal'].sudo().search([
                ('type', '=', 'purchase'),
                ('company_id', '=', picking.company_id.id),
            ], limit=1)
            if not journal:
                raise UserError(_("No purchase journal found to create the vendor bill."))
            bill_lines = []
            for line in request.product_line_ids:
                bill_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.product_id.standard_price or 0.0,
                    'name': line.product_id.display_name or line.product_id.name,
                }))

            bill_vals = {
                'move_type': 'in_invoice',
                'partner_id': vendor.id,
                'invoice_date': fields.Date.context_today(self),
                'journal_id': journal.id,
                'ref': f"Replenishment: {request.name}",
                'invoice_origin': request.name,
                'invoice_line_ids': bill_lines,
            }

            bill = self.env['account.move'].sudo().create(bill_vals)
            try:
                # Savepoint: a failed posting must not leave the transaction half-written.
                with self.env.cr.savepoint():
                    bill.action_post()
            except Exception as e:
                request.message_post(body=_("Vendor Bill was created as a draft, but automatic posting failed: %s") % str(e))

            request.bill_id = bill.id
            request.state = 'received'

            no_cost = request.product_line_ids.mapped('product_id').filtered(lambda p: not p.standard_price)
            body = _("Approved and received by %s.") % approver.name
            if no_cost:
                body += " " + _("These products have no cost, so they were billed at 0: %s") % ", ".join(no_cost.mapped('display_name'))
            request.message_post(body=body)

    def action_cancel(self):
        for request in self:
            if request.state in ('received', 'transferred'):
                raise UserError(_(
                    "Request %s is already received. Return the receipt and reverse the vendor bill instead of cancelling."
                ) % request.name)
            if request.picking_id and request.picking_id.state not in ('done', 'cancel'):
                request.picking_id.action_cancel()
            if request.bill_id and request.bill_id.state == 'draft':
                request.bill_id.button_cancel()
            request.state = 'cancel'


class GroomingStockRequestLine(models.Model):
    _name = 'grooming.stock.request.line'
    _description = 'Inter-Warehouse Stock Request Line'

    request_id = fields.Many2one('grooming.stock.request', string='Request Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
