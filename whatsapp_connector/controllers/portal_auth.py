# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class WhatsAppPortalAuthController(http.Controller):
    """WhatsApp OTP Authentication Controller for Odoo 18 Native Customer Portal"""

    def _get_post_login_redirect(self, uid, redirect=None):
        if redirect:
            return redirect
        user = request.env['res.users'].sudo().browse(uid)
        if user.exists() and not user.share:
            return '/odoo'
        return '/my'

    @http.route('/web/login/whatsapp', type='http', auth='public', website=True, sitemap=False)
    def web_login_whatsapp(self, redirect=None, **kw):
        ensure_db()

        if request.httprequest.method == 'GET' and request.session.uid and not kw.get('switch'):
            return request.redirect(self._get_post_login_redirect(request.session.uid, redirect=redirect))

        if kw.get('reset'):
            request.session.pop('wa_auth_user_id', None)
            request.session.pop('wa_auth_login', None)
            request.session.pop('wa_auth_phone', None)

        step = 'otp' if request.session.get('wa_auth_login') else 'phone'
        phone = kw.get('phone') or request.session.get('wa_auth_phone') or ''
        customer_name = kw.get('customer_name') or ''
        error = None
        message = None

        if request.httprequest.method == 'POST':
            action = kw.get('action', 'send_otp')

            if action in ('send_otp', 'resend_otp'):
                target_phone = phone if action == 'send_otp' else (request.session.get('wa_auth_phone') or phone)
                try:
                    user_sudo, e164_phone = request.env['res.users'].sudo().find_or_create_whatsapp_portal_user(
                        target_phone,
                        customer_name=customer_name,
                    )
                    sent_ok, otp_code, gateway_res = user_sudo.generate_and_send_whatsapp_otp(target_phone=e164_phone)

                    request.session['wa_auth_user_id'] = user_sudo.id
                    request.session['wa_auth_login'] = user_sudo.login
                    request.session['wa_auth_phone'] = e164_phone

                    step = 'otp'
                    phone = e164_phone
                    if sent_ok:
                        message = _("We sent a 6-digit verification code to your WhatsApp (%s).") % e164_phone
                    else:
                        allow_offline_demo = request.env['ir.config_parameter'].sudo().get_param(
                            'whatsapp_connector.demo_show_otp_when_gateway_offline', 'True'
                        ) == 'True'
                        if allow_offline_demo:
                            message = _(
                                "WhatsApp gateway is currently offline/paused. "
                                "Your verification code is: %s"
                            ) % otp_code
                        else:
                            step = 'phone'
                            error = _("WhatsApp gateway is currently unavailable (%s).") % gateway_res
                except UserError as e:
                    step = 'phone' if action == 'send_otp' else step
                    error = str(e)
                except Exception:
                    _logger.exception("WhatsApp OTP send error")
                    step = 'phone' if action == 'send_otp' else step
                    error = _("Unable to send WhatsApp code right now. Please try again.")

            elif action == 'verify_otp':
                otp_code = (kw.get('otp') or '').strip()
                login = request.session.get('wa_auth_login')

                if not login and phone:
                    try:
                        user_sudo, e164_phone = request.env['res.users'].sudo().find_or_create_whatsapp_portal_user(phone)
                        login = user_sudo.login
                        phone = e164_phone
                    except Exception:
                        login = None

                if not login:
                    step = 'phone'
                    error = _("Your verification session expired. Please enter your WhatsApp number again.")
                else:
                    try:
                        credential = {
                            'type': 'whatsapp_otp',
                            'login': login,
                            'otp': otp_code,
                        }
                        auth_info = request.session.authenticate(request.db, credential)
                        request.session.pop('wa_auth_user_id', None)
                        request.session.pop('wa_auth_login', None)
                        request.session.pop('wa_auth_phone', None)
                        request.params['login_success'] = True
                        return request.redirect(self._get_post_login_redirect(auth_info['uid'], redirect=redirect))
                    except AccessDenied as e:
                        step = 'otp'
                        error = e.args[0] if e.args and e.args[0] else _("Invalid or expired verification code.")
                    except Exception:
                        _logger.exception("WhatsApp OTP verification error")
                        step = 'otp'
                        error = _("Verification failed. Please check the code and try again.")

        values = {
            'step': step,
            'phone': phone,
            'customer_name': customer_name,
            'redirect': redirect or '',
            'error': error,
            'message': message,
        }
        response = request.render('whatsapp_connector.whatsapp_login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response


class WhatsAppPosCustomerPortal(CustomerPortal):
    """Extend Odoo Customer Portal with In-Store POS Receipts linked by partner or phone number"""

    def _get_customer_partner_ids(self):
        partner = request.env.user.partner_id
        partner_ids = set([partner.id, partner.commercial_partner_id.id])
        phone = partner.phone or partner.mobile or request.env.user.login
        if phone:
            matched_ids = request.env['res.users'].sudo().find_matching_partner_ids_by_phone(phone)
            partner_ids.update(matched_ids)
        return list(partner_ids)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'pos_order_count' in counters:
            partner_ids = self._get_customer_partner_ids()
            values['pos_order_count'] = request.env['pos.order'].sudo().search_count([
                ('partner_id', 'in', partner_ids),
                ('state', 'in', ['paid', 'done', 'invoiced']),
            ])
        return values

    @http.route(['/my/pos_orders', '/my/pos_orders/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_pos_orders(self, page=1, **kw):
        partner_ids = self._get_customer_partner_ids()
        PosOrder = request.env['pos.order'].sudo()
        domain = [
            ('partner_id', 'in', partner_ids),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        order_count = PosOrder.search_count(domain)
        pager = portal_pager(
            url='/my/pos_orders',
            total=order_count,
            page=page,
            step=10,
        )
        orders = PosOrder.search(
            domain,
            order='date_order desc, id desc',
            limit=10,
            offset=pager['offset'],
        )
        return request.render('whatsapp_connector.portal_my_pos_orders', {
            'pos_orders': orders,
            'page_name': 'pos_orders',
            'pager': pager,
            'default_url': '/my/pos_orders',
        })

    @http.route('/my/pos_orders/<int:order_id>', type='http', auth='user', website=True)
    def portal_my_pos_order_detail(self, order_id, **kw):
        partner_ids = self._get_customer_partner_ids()
        order = request.env['pos.order'].sudo().search([
            ('id', '=', order_id),
            ('partner_id', 'in', partner_ids),
        ], limit=1)
        if not order:
            return request.redirect('/my/pos_orders')
        return request.render('whatsapp_connector.portal_pos_order_detail', {
            'pos_order': order,
            'page_name': 'pos_order',
        })
