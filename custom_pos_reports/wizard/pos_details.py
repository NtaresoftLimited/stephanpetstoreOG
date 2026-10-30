from odoo import api, fields, models, _
from odoo.exceptions import UserError
import io
import base64
import xlsxwriter
import pytz
from datetime import timedelta

class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'
    
    date_start_only = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_end_only = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    report_type_label = fields.Char(string='Report Type', compute='_compute_report_type_label', store=True)
    is_weekly_report = fields.Boolean(string='Is Weekly Report', compute='_compute_is_weekly_report')

    @api.depends('date_start_only')
    def _compute_is_weekly_report(self):
        for rec in self:
            rec.is_weekly_report = bool(self.env.context.get('weekly_report'))

    @api.depends('date_start_only', 'date_end_only')
    def _compute_report_type_label(self):
        for rec in self:
            # If opened from Weekly menu, always label as Weekly
            if self.env.context.get('weekly_report'):
                rec.report_type_label = "Weekly"
                continue
                
            if rec.date_start_only and rec.date_end_only:
                delta = rec.date_end_only - rec.date_start_only
                if delta.days >= 6:
                    rec.report_type_label = "Weekly"
                else:
                    rec.report_type_label = "Daily"
            else:
                rec.report_type_label = "Daily"

    @api.model
    def default_get(self, fields_list):
        res = super(PosDetails, self).default_get(fields_list)
        if self.env.context.get('weekly_report'):
            today = fields.Date.context_today(self)
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            res.update({
                'date_start_only': start,
                'date_end_only': end,
            })
        return res

    @api.onchange('date_start_only')
    def _onchange_date_start_only(self):
        if self.date_start_only:
            self.start_date = fields.Datetime.to_datetime(self.date_start_only)

    @api.onchange('date_end_only')
    def _onchange_date_end_only(self):
        if self.date_end_only:
            dt = fields.Datetime.to_datetime(self.date_end_only)
            self.end_date = dt + timedelta(days=1, seconds=-1)

    def _clean_reason(self, raw_reason):
        if not raw_reason: return "Cash Out"
        s = str(raw_reason)
        if '-Out-' in s: return s.split('-Out-', 1)[1].strip()
        if '-In-' in s: return s.split('-In-', 1)[1].strip()
        if s.startswith("POS/"):
             parts = s.split('-')
             if len(parts) > 1:
                 return parts[-1].strip()
        return s

    def _get_report_data(self):
        if not self.start_date and self.date_start_only:
            self._onchange_date_start_only()
        if not self.end_date and self.date_end_only:
             self._onchange_date_end_only()

        domain = [
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
            ('state', 'in', ['paid', 'invoiced', 'done']),
        ]
        if self.pos_config_ids:
            domain.append(('config_id', 'in', self.pos_config_ids.ids))

        orders = self.env['pos.order'].search(domain)
        
        # Identify Grooming Products
        grooming_product_ids = []
        if 'grooming.service' in self.env:
            grooming_product_ids = self.env['grooming.service'].search([]).mapped('product_id.id')
        
        products = {}
        grooming_products = {}
        
        for order in orders:
            for line in order.lines:
                key = line.product_id.id
                is_grooming = key in grooming_product_ids
                
                target_dict = grooming_products if is_grooming else products
                
                if key not in target_dict:
                    target_dict[key] = {
                        'name': line.product_id.name,
                        'brand': line.product_id.brand_id.name or '',
                        'qty': 0,
                        'total': 0.0
                    }
                target_dict[key]['qty'] += line.qty
                target_dict[key]['total'] += line.price_subtotal_incl

        # Add backend grooming invoice lines
        backend_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.date_start_only),
            ('invoice_date', '<=', self.date_end_only),
        ])
        for inv in backend_invoices:
            # Skip if it is linked to POS orders to prevent double counting
            if getattr(inv, 'pos_order_ids', None):
                continue
            for line in inv.invoice_line_ids:
                if line.product_id.id in grooming_product_ids:
                    key = line.product_id.id
                    if key not in grooming_products:
                        grooming_products[key] = {
                            'name': line.product_id.name,
                            'brand': line.product_id.brand_id.name or '',
                            'qty': 0,
                            'total': 0.0
                        }
                    grooming_products[key]['qty'] += line.quantity
                    grooming_products[key]['total'] += line.price_total

        payments = {}
        for order in orders:
            for payment in order.payment_ids:
                method = payment.payment_method_id.name
                if method not in payments:
                    payments[method] = 0.0
                payments[method] += payment.amount

        # Add backend grooming invoice payments
        backend_payments = self.env['account.payment'].search([
            ('date', '>=', self.date_start_only),
            ('date', '<=', self.date_end_only),
            ('state', 'in', ['posted', 'in_process', 'paid']),
        ])
        for pay in backend_payments:
            reconciled_invoices = pay.reconciled_invoice_ids
            # Exclude if linked to POS orders to prevent double counting
            if any(getattr(inv, 'pos_order_ids', None) for inv in reconciled_invoices):
                continue
            # Check if this payment is reconciled with any invoice containing grooming products
            is_grooming_payment = any(
                any(line.product_id.id in grooming_product_ids for line in inv.invoice_line_ids)
                for inv in reconciled_invoices
            )
            if is_grooming_payment:
                method = pay.journal_id.name or 'Bank/Other'
                if method not in payments:
                    payments[method] = 0.0
                payments[method] += pay.amount

        # Cash Outs
        session_domain = [
            ('start_at', '<=', self.end_date),
            '|', ('stop_at', '>=', self.start_date), ('stop_at', '=', False)
        ]
        if self.pos_config_ids:
            session_domain.append(('config_id', 'in', self.pos_config_ids.ids))
        
        sessions = self.env['pos.session'].search(session_domain)
        
        expenses = []
        # In Odoo 18, cash outs are statement lines linked to the session
        st_lines = self.env['account.bank.statement.line'].search([
            ('pos_session_id', 'in', sessions.ids),
            ('amount', '<', 0)
        ])
        for line in st_lines:
             raw_reason = line.payment_ref or line.name or 'Cash Out'
             expenses.append({
                 'reason': self._clean_reason(raw_reason),
                 'amount': line.amount
             })

        # Cash In (Positive amounts)
        cash_in_moves = []
        # Query for positive amounts linked to the session
        # We try to exclude sales by checking payment_ref/journal or if it's a payment
        # In Odoo 18, standard sales payments are linked via pos_session_id too.
        # But 'Cash In/Out' usually has a specific label or is not linked to a POS Order directly? 
        # Actually, POS Payments are account.bank.statement.lines in some versions, or account.payments.
        # A safe heuristic for "Cash In" (Put Money In) vs "Sale":
        # Sales usually have a partner or a specific ref format. 
        # "Put Money In" usually has 'Cash In' or user reason.
        
        # Let's fetch all positive lines and filter
        all_pos_lines = self.env['account.bank.statement.line'].search([
            ('pos_session_id', 'in', sessions.ids),
            ('amount', '>', 0)
        ])
        
        # Filter out lines that are likely sales (this is estimation without direct link)
        # Note: In standard Odoo, 'Put Money In' creates a statement line.
        # Sales cache might aggregate.
        # We'll assume any statement line with > 0 is Cash In unless we find it's a sale?
        # Actually, standard 'Cash In' feature is what we want.
        
        for line in all_pos_lines:
             # Basic filter: If it looks like a sale aggregation, ignore? 
             # For now, we include everything > 0 as "Cash In" candidates 
             # But we should rely on the user reason if possible.
             raw_reason = line.payment_ref or line.name or 'Cash In'
             cash_in_moves.append({
                 'reason': self._clean_reason(raw_reason),
                 'amount': line.amount
             })

        total_cash_in = sum(c['amount'] for c in cash_in_moves)
        total_cash_out = sum(e['amount'] for e in expenses)

        # Discounts
        # We need to calculate total discount from lines
        total_discount = 0.0
        for order in orders:
            for line in order.lines:
                if line.discount > 0:
                    # Discount amount = Price Unit * Qty * Discount / 100
                    # (Note: Odoo stores info to calc this)
                    disc_amt = line.qty * line.price_unit * (line.discount / 100.0)
                    total_discount += disc_amt

        # Session Stats
        total_orders = len(orders)
        
        # Update return dict
        return {
            'products': list(products.values()),
            'grooming_products': list(grooming_products.values()),
            'payments': [{'method': k, 'amount': v} for k,v in payments.items()],
            'expenses': expenses,
            'cash_in': cash_in_moves,
            'total_sales': sum(p['total'] for p in products.values()),
            'total_grooming': sum(p['total'] for p in grooming_products.values()),
            'total_cash_out': total_cash_out,
            'total_cash_in': total_cash_in,
            'total_discount': total_discount,
            'total_orders': total_orders,
            'net_cash': sum(p['total'] for p in products.values()) + sum(p['total'] for p in grooming_products.values()) + total_cash_out + total_cash_in
        }

    def action_export_excel(self):
        data = self._get_report_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        report_title = f"{self.report_type_label} Sales Report"
        sheet = workbook.add_worksheet(report_title)
        
        bold_center = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 14})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#6b4e3d', 'color': 'white', 'border': 1})
        cell_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        negative_fmt = workbook.add_format({'border': 1, 'num_format': '[Red]#,##0.00', 'font_color': 'red'})
        
        import os
        from PIL import Image
        company = self.env.company
        if company.logo:
            try:
                raw = base64.b64decode(company.logo)
                im = Image.open(io.BytesIO(raw))
                png_buf = io.BytesIO()
                im.convert("RGBA").save(png_buf, format='PNG')
                png_buf.seek(0)
                sheet.insert_image('A1', 'logo.png', {'image_data': png_buf, 'x_scale': 0.5, 'y_scale': 0.5})
            except Exception:
                pass

        # Background Watermark
        try:
            for p in [
                "/opt/odoo/odoo20-addons/custom_pos_reports/static/src/img/paw_watermark.png",
                "/opt/odoo/custom-addons/custom_pos_reports/static/src/img/paw_watermark.png"
            ]:
                if os.path.exists(p):
                    sheet.set_background(p)
                    break
        except Exception:
            pass

        date_str = str(self.date_start_only)
        if self.report_type_label == "Weekly":
             date_str = f"{self.date_start_only}_to_{self.date_end_only}"
             
        sheet.merge_range('A3:D3', f"{report_title} - {date_str}", bold_center)
        
        row = 5
        sheet.write(row, 0, "Sales by Product", workbook.add_format({'bold': True, 'font_size': 12}))
        row += 1
        headers = ["Product Name", "Brand", "Quantity", "Total (TSh)"]
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_fmt)
        
        row += 1
        for prod in data['products']:
            sheet.write(row, 0, prod['name'], cell_fmt)
            sheet.write(row, 1, prod['brand'], cell_fmt)
            sheet.write(row, 2, prod['qty'], cell_fmt)
            sheet.write(row, 3, prod['total'], money_fmt)
            row += 1
            
        sheet.write(row, 2, "Total Sales (TSh):", workbook.add_format({'bold': True, 'align': 'right'}))
        sheet.write(row, 3, data['total_sales'], workbook.add_format({'bold': True, 'num_format': '#,##0.00'}))
        
        # Grooming Section
        if data['grooming_products']:
            row += 3
            sheet.write(row, 0, "Grooming Services", workbook.add_format({'bold': True, 'font_size': 12}))
            row += 1
            for col, h in enumerate(headers):
                sheet.write(row, col, h, header_fmt)
            
            row += 1
            for prod in data['grooming_products']:
                sheet.write(row, 0, prod['name'], cell_fmt)
                sheet.write(row, 1, prod['brand'], cell_fmt)
                sheet.write(row, 2, prod['qty'], cell_fmt)
                sheet.write(row, 3, prod['total'], money_fmt)
                row += 1
                
            sheet.write(row, 2, "Total Grooming (TSh):", workbook.add_format({'bold': True, 'align': 'right'}))
            sheet.write(row, 3, data['total_grooming'], workbook.add_format({'bold': True, 'num_format': '#,##0.00'}))
        
        row += 3
        sheet.write(row, 0, "Payments Breakdown (TSh)", workbook.add_format({'bold': True, 'font_size': 12}))
        row += 1
        sheet.write(row, 0, "Payment Method", header_fmt)
        sheet.merge_range(row, 1, row, 3, "Amount", header_fmt)
        
        row += 1
        for pay in data['payments']:
            sheet.write(row, 0, pay['method'], cell_fmt)
            sheet.merge_range(row, 1, row, 3, pay['amount'], money_fmt)
            row += 1
            
        row += 3
        sheet.write(row, 0, "Cash In (TSh)", workbook.add_format({'bold': True, 'font_size': 12}))
        row += 1
        sheet.write(row, 0, "Reason", header_fmt)
        sheet.merge_range(row, 1, row, 3, "Amount", header_fmt)
        
        row += 1
        if data.get('cash_in'):
            for cin in data['cash_in']:
                sheet.write(row, 0, cin['reason'], cell_fmt)
                sheet.merge_range(row, 1, row, 3, cin['amount'], money_fmt)
                row += 1
        else:
            sheet.write(row, 0, "No Cash In", cell_fmt)
            sheet.merge_range(row, 1, row, 3, 0.0, money_fmt)
            row += 1
             
        sheet.write(row, 0, "Total Cash In (TSh):", workbook.add_format({'bold': True, 'align': 'right'}))
        sheet.merge_range(row, 1, row, 3, data.get('total_cash_in', 0.0), money_fmt)

        row += 3
        sheet.write(row, 0, "Cash Outs / Expenses (TSh)", workbook.add_format({'bold': True, 'font_size': 12}))
        row += 1
        sheet.write(row, 0, "Reason", header_fmt)
        sheet.merge_range(row, 1, row, 3, "Amount (Negative)", header_fmt)
        
        row += 1
        if data['expenses']:
            for exp in data['expenses']:
                sheet.write(row, 0, exp['reason'], cell_fmt)
                sheet.merge_range(row, 1, row, 3, exp['amount'], negative_fmt)
                row += 1
        else:
            sheet.write(row, 0, "No Expenses", cell_fmt)
            sheet.merge_range(row, 1, row, 3, 0.0, negative_fmt)
            row += 1
             
        sheet.write(row, 0, "Total Expenses (TSh):", workbook.add_format({'bold': True, 'align': 'right'}))
        sheet.merge_range(row, 1, row, 3, data['total_cash_out'], negative_fmt)
        
        row += 2
        sheet.write(row, 0, "Net Cash (TSh):", workbook.add_format({'bold': True, 'align': 'right', 'font_size': 12}))
        sheet.merge_range(row, 1, row, 3, data['net_cash'], workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'font_size': 12}))
        
        sheet.set_column('A:A', 30)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 20)
        
        workbook.close()
        output.seek(0)
        
        date_str = str(self.date_start_only)
        if self.report_type_label == "Weekly":
            date_str = f"{self.date_start_only}_to_{self.date_end_only}"
            
        filename = f"{self.report_type_label}_Sales_Report_{date_str}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'raw': output.getvalue(),
            'res_model': 'pos.details.wizard',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_print_thermal(self):
        # Calls the QWeb PDF (Thermal)
        return self.env.ref('custom_pos_reports.action_report_pos_thermal').report_action(self)

    def action_print_a4(self):
        # Calls the QWeb PDF (A4)
        return self.env.ref('custom_pos_reports.action_report_pos_a4').report_action(self)

    def action_send_whatsapp(self):
        self.ensure_one()
        # Generate the PDF
        report = self.env.ref('custom_pos_reports.action_report_pos_a4')
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('custom_pos_reports.action_report_pos_a4', res_ids=self.ids)
        
        pdf_b64 = base64.b64encode(pdf_content).decode('utf-8')
        file_name = f"Daily_Sales_{self.date_start_only}.pdf"
        
        # Save attachment for URL
        attachment = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'raw': pdf_content,
            'res_model': 'pos.details.wizard',
            'res_id': self.id,
            'public': True,
        })
        if not attachment.access_token:
            attachment.generate_access_token()
            
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
        
        import requests
        url = "https://wasenderapi.com/api/send-message"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
            "User-Agent": "Odoo/18.0"
        }
        
        report_label = "Weekly" if self.is_weekly_report else "Daily"
        message = f"""📊 *{report_label} Sales Report*

Here is the sales report for {self.date_start_only} to {self.date_end_only}.
Please find the PDF attached."""
        
        payload = {
            "to": "+255792079463",
            "text": message,
            "documentUrl": doc_url,
            "fileName": file_name
        }
        
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            res_json = resp.json()
            if not res_json.get("success"):
                raise Exception(res_json.get("message", "Unknown error from WaSender"))
        except Exception as e:
            from odoo.exceptions import UserError
            import logging
            logging.getLogger(__name__).warning("WaSender API Error: %s", str(e))
            raise UserError(f"Failed to send WhatsApp message. Error: {str(e)}")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'WhatsApp Sent',
                'message': 'The Sales PDF was sent to WhatsApp!',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_send_daily_sales_whatsapp(self):
        # Called by cron every day at 22:00
        today = fields.Date.context_today(self)
        wizard = self.create({
            'date_start_only': today,
            'date_end_only': today,
        })
        wizard.action_send_whatsapp()
