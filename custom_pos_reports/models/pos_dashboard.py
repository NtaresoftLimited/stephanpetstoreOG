from odoo import models, fields, api
from datetime import datetime, timedelta
import pytz

class PosDashboard(models.TransientModel):
    _name = 'pos.dashboard.data'
    _description = 'POS Dashboard Data'

    @api.model
    def get_dashboard_data(self, *args, **kwargs):
        options = None
        for a in args:
            if isinstance(a, dict):
                options = a
                break
        if not options and 'options' in kwargs:
            options = kwargs['options']
        options = options or {}
        today = fields.Date.context_today(self)
        start = fields.Date.to_date(options.get('date_start') or today)
        end = fields.Date.to_date(options.get('date_end') or today)
        if end < start:
            start, end = end, start

        is_manager = self.env.user.has_group('point_of_sale.group_pos_manager')
        # Enforce current week restriction starting Monday for cashiers (non-managers)
        min_allowed_date = today - timedelta(days=today.weekday())

        if not is_manager:
            if start < min_allowed_date:
                start = min_allowed_date
            if end < min_allowed_date:
                end = min_allowed_date

        tz = pytz.timezone(
            self.env.user.tz
            or self.env.company.partner_id.tz
            or 'Africa/Dar_es_Salaam'
        )
        start_dt = tz.localize(datetime.combine(start, datetime.min.time())).astimezone(
            pytz.UTC).replace(tzinfo=None)
        end_dt = tz.localize(datetime.combine(
            end + timedelta(days=1), datetime.min.time()
        )).astimezone(pytz.UTC).replace(tzinfo=None)

        domain = [('date_order', '>=', start_dt), ('date_order', '<', end_dt),
                  ('state', 'in', ['paid', 'done', 'invoiced'])]
        if options.get('config_ids'):
            domain.append(('config_id', 'in', options['config_ids']))

        pos_configs = False
        # Cashier Access Logic: non-managers only see orders for their assigned store or created by them
        if not is_manager:
            pos_configs = self.env['pos.config'].sudo().search([
                '|', ('basic_employee_ids.user_id', 'in', [self.env.uid]),
                ('advanced_employee_ids.user_id', 'in', [self.env.uid])
            ])
            if pos_configs:
                domain.extend([
                    '|',
                    ('config_id', 'in', pos_configs.ids),
                    ('user_id', '=', self.env.uid)
                ])
            else:
                domain.append(('user_id', '=', self.env.uid))
        orders = self.env['pos.order'].sudo().search(domain)
        sales = sum(orders.mapped('amount_total'))
        items = sum(orders.mapped('lines').mapped('qty'))
        payments, products, customers, categories, staff, trend = {}, {}, {}, {}, {}, {}
        payment_rows = []

        for order in orders:
            day = fields.Datetime.to_datetime(order.date_order).date().isoformat()
            trend.setdefault(day, {'sales': 0.0, 'orders': 0})
            trend[day]['sales'] += order.amount_total; trend[day]['orders'] += 1
            customer = order.partner_id.name or 'Walk-in Customer'
            if customer not in customers:
                customers[customer] = {'orders': 0, 'revenue': 0.0, 'unpaid': 0.0, 'partner_ids': set()}
            customers[customer]['orders'] += 1; customers[customer]['revenue'] += order.amount_total
            if order.partner_id:
                customers[customer]['partner_ids'].add(order.partner_id.id)
            cashier = order.user_id.name or 'Unassigned'
            staff.setdefault(cashier, {'orders': 0, 'revenue': 0.0})
            staff[cashier]['orders'] += 1; staff[cashier]['revenue'] += order.amount_total
            for line in order.lines:
                name = line.product_id.display_name
                products.setdefault(name, {'qty': 0.0, 'revenue': 0.0})
                products[name]['qty'] += line.qty; products[name]['revenue'] += line.price_subtotal_incl
                category = line.product_id.categ_id.complete_name
                categories[category] = categories.get(category, 0.0) + line.price_subtotal_incl
            for payment in order.payment_ids:
                method = payment.payment_method_id
                payment_rows.append({
                    'method': method.name,
                    'amount': payment.amount,
                    'location': order.config_id.name,
                    'is_cash': getattr(method, 'is_cash_count', False),
                    'is_customer_account': method.type == 'pay_later',
                })

        account_payments = self.env['account.payment'].sudo().search([
            ('date', '>=', start), ('date', '<=', end),
            ('company_id', '=', self.env.company.id),
            ('payment_type', '=', 'inbound'),
            ('partner_type', '=', 'customer'),
            ('state', 'in', ('in_process', 'paid')),
            ('pos_payment_method_id', '!=', False),
        ])
        for account_payment in account_payments:
            method = account_payment.pos_payment_method_id
            related_orders = self.env['pos.order'].sudo().search([
                ('account_move', 'in', account_payment.reconciled_invoice_ids.ids),
            ])
            if not related_orders:
                continue
            if not is_manager:
                if pos_configs:
                    if not any(ro.config_id.id in pos_configs.ids or ro.user_id.id == self.env.uid for ro in related_orders):
                        continue
                elif not any(ro.user_id.id == self.env.uid for ro in related_orders):
                    continue
            configs = related_orders.mapped('config_id')
            payment_rows.append({
                'method': method.name,
                'amount': account_payment.amount,
                'location': ', '.join(configs.mapped('name')) or 'Accounting',
                'is_cash': (
                    getattr(method, 'is_cash_count', False)
                    or account_payment.journal_id.type == 'cash'
                ),
                'is_customer_account': False,
            })

        wizard_model = self.env['pos.details.wizard']
        if hasattr(wizard_model, '_summarize_payment_rows'):
            _, payment_totals, _ = wizard_model._summarize_payment_rows(payment_rows)
        else:
            _, payment_totals, _ = self._summarize_payment_rows(payment_rows)

        payment_colors = ('#e8f5e9', '#e3f2fd', '#fff3e0', '#f3e5f5', '#e8eaf6', '#e0f2f1')
        payment_boxes = []
        for index, label in enumerate(sorted(payment_totals)):
            rows = [
                {'location': location, 'amount': amount}
                for location, amount in sorted(payment_totals[label].items())
                if amount
            ]
            payment_boxes.append({
                'name': label,
                'color': payment_colors[index % len(payment_colors)],
                'rows': rows,
                'total': sum(r['amount'] for r in rows)
            })
        partner_map = {}
        for cname, cdata in customers.items():
            cdata['unpaid'] = 0.0
            for pid in cdata.get('partner_ids', []):
                partner_map[pid] = cname
        
        if partner_map:
            invoices = self.env['account.move'].sudo().search([
                ('partner_id', 'in', list(partner_map.keys())),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('not_paid', 'partial'))
            ])
            for inv in invoices:
                cname = partner_map[inv.partner_id.id]
                customers[cname]['unpaid'] += inv.amount_residual
                
        for cdata in customers.values():
            if 'partner_ids' in cdata:
                del cdata['partner_ids']

        expenses_list = []
        expenses_total_val = 0.0
        if 'hr.expense' in self.env:
            domain_hr = [
                ('date', '>=', start),
                ('date', '<=', end),
                ('state', 'in', ('submitted', 'approved', 'done')),
                ('company_id', '=', self.env.company.id),
            ]
            if not is_manager:
                emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
                emp_id = emp.id if emp else (self.env.user.employee_id.id if self.env.user.employee_id else False)
                domain_hr.append('|')
                domain_hr.append(('create_uid', '=', self.env.uid))
                domain_hr.append(('employee_id', '=', emp_id))
            hr_expenses = self.env['hr.expense'].sudo().search(domain_hr, order='date desc, id desc')
            for e in hr_expenses:
                cat_name = e.product_id.name or 'Expense'
                reason = f"{cat_name}: {e.name}" if e.name and e.name != cat_name else cat_name
                dt_str = e.create_date.strftime('%Y-%m-%d %H:%M') if getattr(e, 'create_date', False) else str(e.date or '')
                expenses_list.append({'reason': reason, 'amount': e.total_amount, 'datetime': dt_str})
                expenses_total_val += e.total_amount

        # Product Sales Breakdown (mirrors Daily Sales Report table)
        sales_breakdown = []
        prod_branch_map = {}
        for order in orders:
            branch_name = order.config_id.name or 'Sinza'
            for line in order.lines:
                key = (line.product_id.id, branch_name)
                if key not in prod_branch_map:
                    prod_branch_map[key] = {
                        'name': line.product_id.display_name,
                        'branch': branch_name,
                        'qty': 0.0,
                        'total': 0.0,
                    }
                prod_branch_map[key]['qty'] += line.qty
                prod_branch_map[key]['total'] += line.price_subtotal_incl

        sales_breakdown = sorted(prod_branch_map.values(), key=lambda x: x['total'], reverse=True)

        # Proforma Invoices (mirrors Daily Sales Report Proforma section)
        proforma_list = []
        domain_proforma = [
            '|',
            '&', ('date_order', '>=', start_dt), ('date_order', '<', end_dt),
            '&', ('create_date', '>=', start_dt), ('create_date', '<', end_dt),
            ('state', 'in', ('draft', 'sent', 'sale')),
            ('company_id', '=', self.env.company.id),
        ]
        if not is_manager:
            domain_proforma.append(('user_id', '=', self.env.uid))
        proforma_orders = self.env['sale.order'].sudo().search(
            domain_proforma,
            order='date_order desc, name desc',
            limit=20
        )
        for po in proforma_orders:
            state_label = 'Draft' if po.state == 'draft' else ('Sent' if po.state == 'sent' else 'Confirmed')
            proforma_list.append({
                'number': po.name,
                'customer': po.partner_id.name or 'Walk-in',
                'amount': po.amount_total,
                'date': po.date_order.strftime('%Y-%m-%d %H:%M') if po.date_order else '',
                'state': po.state,
                'state_label': state_label,
            })

        # Invoices (mirrors Daily Sales Report Invoices section)
        invoice_list = []
        domain_inv = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', start),
            ('invoice_date', '<=', end),
            ('company_id', '=', self.env.company.id),
            ('state', '!=', 'cancel'),
        ]
        if not is_manager:
            domain_inv.append(('invoice_user_id', '=', self.env.uid))
        invoices = self.env['account.move'].sudo().search(domain_inv, order='invoice_date desc, name desc', limit=20)
        for inv in invoices:
            status_label = 'Paid' if inv.payment_state == 'paid' else ('Partially Paid' if inv.payment_state == 'partial' else 'Not Paid')
            status_badge = 'success' if inv.payment_state == 'paid' else ('warning' if inv.payment_state == 'partial' else 'danger')
            if inv.state == 'draft':
                status_label = 'Draft'
                status_badge = 'secondary'
            invoice_list.append({
                'number': inv.name or '/',
                'customer': inv.partner_id.name or 'Walk-in',
                'total': inv.amount_total,
                'amount_due': inv.amount_residual,
                'status': status_label,
                'status_badge': status_badge,
            })

        # Total Unpaid (Customer Account tender + unpaid invoice residual, deduplicated)
        pos_invoice_ids = set(orders.mapped('account_move').ids)
        unpaid_pos = sum(
            p.amount for o in orders for p in o.payment_ids
            if getattr(p.payment_method_id, 'type', '') == 'pay_later'
        )
        unpaid_direct = sum(
            inv.amount_residual for inv in invoices
            if inv.id not in pos_invoice_ids
        )
        total_unpaid = unpaid_pos + unpaid_direct

        previous_days = (end - start).days + 1
        domain_prev = [('date_order', '>=', start_dt - timedelta(days=previous_days)), ('date_order', '<', start_dt), ('state', 'in', ['paid', 'done', 'invoiced'])]
        if not is_manager:
            if pos_configs:
                domain_prev.extend(['|', ('config_id', 'in', pos_configs.ids), ('user_id', '=', self.env.uid)])
            else:
                domain_prev.append(('user_id', '=', self.env.uid))
        previous_orders = self.env['pos.order'].sudo().search(domain_prev)
        previous_sales = sum(previous_orders.mapped('amount_total'))

        grooming_stats = {
            'total': 0,
            'pending': 0,
            'confirmed': 0,
            'in_progress': 0,
            'completed': 0,
            'cancelled': 0,
            'overview_total': 0,
            'donut_gradient': 'conic-gradient(#e5e7eb 0% 100%)',
            'recent_appointments': [],
        }
        if 'grooming.appointment' in self.env:
            grooming_domain = [
                ('appointment_date', '>=', start_dt),
                ('appointment_date', '<', end_dt),
            ]
            grooming_groups = self.env['grooming.appointment'].sudo().read_group(
                grooming_domain,
                ['state'],
                ['state'],
                lazy=False,
            )
            state_counts = {
                group['state']: group['__count']
                for group in grooming_groups
                if group.get('state')
            }
            total_count = sum(state_counts.values())
            pending_count = state_counts.get('pending', 0)
            confirmed_count = state_counts.get('confirmed', 0)
            in_prog_count = sum(
                state_counts.get(state, 0)
                for state in ('checked_in', 'in_progress', 'halfway')
            )
            completed_count = state_counts.get('completed', 0)
            cancelled_count = state_counts.get('cancelled', 0)

            # If filtered period has no records, fallback to overall counts for the overview chart
            if total_count == 0:
                all_groups = self.env['grooming.appointment'].sudo().read_group(
                    [],
                    ['state'],
                    ['state'],
                    lazy=False,
                )
                all_counts = {
                    group['state']: group['__count']
                    for group in all_groups
                    if group.get('state')
                }
                pending_count = all_counts.get('pending', 0)
                confirmed_count = all_counts.get('confirmed', 0)
                in_prog_count = sum(
                    all_counts.get(state, 0)
                    for state in ('checked_in', 'in_progress', 'halfway')
                )
                completed_count = all_counts.get('completed', 0)
                cancelled_count = all_counts.get('cancelled', 0)
                total_count = sum(all_counts.values())

            overview_total = pending_count + confirmed_count + in_prog_count + completed_count

            # Conic gradient computation for status donut chart
            if overview_total > 0:
                p_pct = round((pending_count / overview_total) * 100, 2)
                c_pct = round(p_pct + (confirmed_count / overview_total) * 100, 2)
                g_pct = round(c_pct + (in_prog_count / overview_total) * 100, 2)
                gradient = (
                    f'conic-gradient(#eab308 0% {p_pct}%, '
                    f'#06b6d4 {p_pct}% {c_pct}%, '
                    f'#9333ea {c_pct}% {g_pct}%, '
                    f'#10b981 {g_pct}% 100%)'
                )
            else:
                gradient = 'conic-gradient(#e5e7eb 0% 100%)'

            # Recent appointments
            recent_recs = self.env['grooming.appointment'].sudo().search(
                grooming_domain,
                order='appointment_date desc',
                limit=15,
            )
            if not recent_recs:
                recent_recs = self.env['grooming.appointment'].sudo().search(
                    [],
                    order='appointment_date desc',
                    limit=5,
                )

            recent_list = []
            for appt in recent_recs:
                st = appt.state or ''
                badge_class = 'badge-secondary'
                state_label = st
                if st == 'completed':
                    badge_class = 'badge-success-soft'
                    state_label = 'completed'
                elif st == 'pending':
                    badge_class = 'badge-warning-soft'
                    state_label = 'pending'
                elif st == 'cancelled':
                    badge_class = 'badge-gray-soft'
                    state_label = 'cancelled'
                elif st in ('checked_in', 'in_progress', 'halfway'):
                    badge_class = 'badge-purple-soft'
                    state_label = 'in grooming'
                elif st == 'confirmed':
                    badge_class = 'badge-info-soft'
                    state_label = 'confirmed'

                appt_date_str = ''
                if appt.appointment_date:
                    appt_date_str = appt.appointment_date.strftime('%Y-%m-%d %H:%M:%S')

                pet_name = getattr(appt, 'pet_name', '')
                if not pet_name and hasattr(appt, 'pet_id') and appt.pet_id:
                    pet_name = appt.pet_id.name

                recent_list.append({
                    'id': appt.id,
                    'name': appt.name or '',
                    'appointment_date': appt_date_str,
                    'pet_name': pet_name or '-',
                    'customer_name': appt.partner_id.name if appt.partner_id else '-',
                    'state': st,
                    'state_label': state_label,
                    'badge_class': badge_class,
                    'total_price': float(appt.total_price or 0.0),
                })

            grooming_stats.update({
                'total': total_count,
                'pending': pending_count,
                'confirmed': confirmed_count,
                'in_progress': in_prog_count,
                'completed': completed_count,
                'cancelled': cancelled_count,
                'overview_total': overview_total,
                'donut_gradient': gradient,
                'recent_appointments': recent_list,
            })
        return {
            'is_manager': is_manager,
            'min_date': min_allowed_date.isoformat() if not is_manager else False,
            'total_sales': sales,
            'total_orders': len(orders),
            'items_sold': items,
            'total_unpaid': total_unpaid,
            'average_order': sales / len(orders) if orders else 0.0,
            'sales_breakdown': sales_breakdown,
            'trend': [{'name': k, **v} for k, v in sorted(trend.items())],
            'products': [{'name': k, **v} for k, v in sorted(products.items(), key=lambda x: x[1]['revenue'], reverse=True)[:10]],
            'customers': [{'name': k, **v} for k, v in sorted(customers.items(), key=lambda x: x[1]['revenue'], reverse=True)[:10]],
            'categories': [{'name': k, 'revenue': v} for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)],
            'payments': payment_boxes,
            'staff': [{'name': k, **v} for k, v in sorted(staff.items(), key=lambda x: x[1]['revenue'], reverse=True)],
            'expenses_total': expenses_total_val,
            'expenses': expenses_list,
            'proforma_invoices': proforma_list,
            'invoices': invoice_list,
            'grooming': grooming_stats,
            'currency': self.env.company.currency_id.symbol,
            'date_start': str(start), 'date_end': str(end),
        }

    @api.model
    def _summarize_payment_rows(self, payment_rows):
        payments = {}
        by_location = {}
        cash_received = 0.0
        for row in payment_rows:
            method = row.get('method') or 'Unknown'
            amount = float(row.get('amount') or 0.0)
            location = row.get('location') or 'Accounting'
            is_cash = row.get('is_cash', False)

            payments[method] = payments.get(method, 0.0) + amount
            if method not in by_location:
                by_location[method] = {}
            by_location[method][location] = by_location[method].get(location, 0.0) + amount

            if is_cash:
                cash_received += amount

        return payments, by_location, cash_received
