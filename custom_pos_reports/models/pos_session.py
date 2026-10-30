from odoo import models, api, fields

class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_generate_z_report_thermal(self):
        self.ensure_one()
        # Instead of creating a wizard, directly print the SESSION report.
        # This uses the persistent pos.session record, avoiding MissingError on transient wizards.
        return self.env.ref('custom_pos_reports.action_report_session_thermal').report_action(self)

    def _clean_reason(self, raw_reason):
        if not raw_reason: return "Cash Out"
        s = str(raw_reason)
        s = s.replace("POS/", "") # Simple pre-clean
        if '-Out-' in s: return s.split('-Out-', 1)[1].strip()
        if '-In-' in s: return s.split('-In-', 1)[1].strip()
        parts = s.split('-')
        if len(parts) > 1 and parts[0].isdigit(): # Handle 00278-Reason case if not captured above
              return parts[-1].strip()
        return s

    def _get_report_data(self):
        """ Report data logic specific to THIS session """
        self.ensure_one()
        
        # Scoped to orders in this session
        orders = self.order_ids.filtered(lambda o: o.state in ['paid', 'invoiced', 'done'])
        
        products = {}
        for order in orders:
            for line in order.lines:
                key = line.product_id.id
                if key not in products:
                    products[key] = {
                        'name': line.product_id.name,
                        'qty': 0,
                        'total': 0.0
                    }
                products[key]['qty'] += line.qty
                products[key]['total'] += line.price_subtotal_incl

        payments = {}
        for order in orders:
            for payment in order.payment_ids:
                method = payment.payment_method_id.name
                if method not in payments:
                    payments[method] = 0.0
                payments[method] += payment.amount

        # Cash Outs
        expenses = []
        try:
            st_lines = self.env['account.bank.statement.line'].search([
                ('pos_session_id', '=', self.id),
                ('amount', '<', 0)
            ])
            for line in st_lines:
                if True: # Fixed 
                     raw_reason = line.payment_ref or line.name or 'Cash Out'
                     expenses.append({
                         'reason': self._clean_reason(raw_reason),
                         'amount': line.amount
                     })
        except:
            pass

        total_cash_out = sum(e['amount'] for e in expenses)

        return {
            'products': list(products.values()),
            'payments': [{'method': k, 'amount': v} for k,v in payments.items()],
            'expenses': expenses,
            'total_sales': sum(p['total'] for p in products.values()),
            'total_cash_out': total_cash_out,
            'net_cash': sum(p['total'] for p in products.values()) + total_cash_out
        }
