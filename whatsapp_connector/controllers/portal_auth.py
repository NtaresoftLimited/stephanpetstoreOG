# -*- coding: utf-8 -*-
import logging
from urllib.parse import urlencode

from odoo import http, _
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.whatsapp_connector.models.res_users import get_config_str

try:  # Odoo 20: session authentication is a module-level function
    from odoo.http.session import authenticate as session_authenticate
except ImportError:  # Odoo 18: request.session.authenticate(db, credential)
    session_authenticate = None

_logger = logging.getLogger(__name__)


class WhatsAppPortalAuthController(http.Controller):
    """WhatsApp OTP login for customer (portal) accounts."""

    SUPPORT_WHATSAPP = '+255 769 324 445'

    @staticmethod
    def _safe_redirect(redirect):
        """Only allow local paths such as '/my' (no scheme, no '//host')."""
        redirect = (redirect or '').strip()
        if not redirect.startswith('/') or redirect.startswith('//') or '\\' in redirect:
            return ''
        return redirect

    def _get_post_login_redirect(self, uid, redirect=None):
        if redirect:
            return redirect
        user = request.env['res.users'].sudo().browse(uid)
        if user.exists() and not user.share:
            return '/odoo'
        return '/my'

    @staticmethod
    def _url(path, **params):
        params = {k: v for k, v in params.items() if v}
        return path + ('?' + urlencode(params) if params else '')

    @staticmethod
    def _clear_wa_session():
        for key in ('wa_auth_user_id', 'wa_auth_login', 'wa_auth_phone'):
            request.session.pop(key, None)

    @staticmethod
    def _authenticate(credential):
        if session_authenticate:
            return session_authenticate(request.session, request.env, credential)
        return request.session.authenticate(request.db, credential)

    @http.route('/web/login/whatsapp', type='http', auth='public', website=True, sitemap=False)
    def web_login_whatsapp(self, redirect=None, **kw):
        ensure_db()
        redirect = self._safe_redirect(redirect)

        if request.session.uid and not kw.get('switch'):
            return request.redirect(self._get_post_login_redirect(request.session.uid, redirect=redirect))

        if kw.get('reset'):
            self._clear_wa_session()

        step = 'otp' if request.session.get('wa_auth_login') else 'phone'
        phone = kw.get('phone') or request.session.get('wa_auth_phone') or ''
        customer_name = (kw.get('customer_name') or '').strip()[:120]
        error = None
        message = None
        Users = request.env['res.users'].sudo()

        if request.httprequest.method == 'POST':
            action = kw.get('action', 'send_otp')

            if action in ('send_otp', 'resend_otp'):
                target_phone = phone if action == 'send_otp' else (request.session.get('wa_auth_phone') or phone)
                try:
                    # Don't provision customer accounts when no code can be delivered anyway.
                    if not request.env['whatsapp.instance'].sudo().get_default_instance():
                        raise UserError(_(
                            "WhatsApp login is temporarily unavailable. Please sign in with your email, "
                            "or message us on WhatsApp at %s.", self.SUPPORT_WHATSAPP))

                    user_sudo, e164_phone = Users.find_or_create_whatsapp_portal_user(
                        target_phone,
                        customer_name=customer_name,
                    )
                    request.session['wa_auth_user_id'] = user_sudo.id
                    request.session['wa_auth_login'] = user_sudo.login
                    request.session['wa_auth_phone'] = e164_phone
                    phone = e164_phone
                    step = 'otp'

                    wait = user_sudo.whatsapp_otp_resend_wait()
                    if wait:
                        message = _(
                            "A code was already sent to %(phone)s. You can request a new one in %(sec)s seconds.",
                            phone=e164_phone, sec=wait,
                        )
                    else:
                        sent_ok, otp_code, gateway_res = user_sudo.generate_and_send_whatsapp_otp(target_phone=e164_phone)
                        if sent_ok:
                            message = _("We sent a 6-digit code to your WhatsApp %s.", e164_phone)
                        else:
                            allow_offline_demo = get_config_str(
                                request.env, 'whatsapp_connector.demo_show_otp_when_gateway_offline', 'False'
                            ) == 'True'
                            if allow_offline_demo:
                                message = _("WhatsApp gateway is offline. Your verification code is: %s", otp_code)
                            else:
                                self._clear_wa_session()
                                step = 'phone'
                                _logger.warning("WhatsApp OTP not delivered to %s: %s", e164_phone, gateway_res)
                                error = _(
                                    "We couldn't send the WhatsApp code right now. Please check the number "
                                    "and try again, or sign in with your email."
                                )
                except UserError as e:
                    step = 'phone' if action == 'send_otp' else step
                    error = e.args[0] if e.args else str(e)
                except Exception:
                    _logger.exception("WhatsApp OTP send error")
                    step = 'phone' if action == 'send_otp' else step
                    error = _("Unable to send WhatsApp code right now. Please try again.")

            elif action == 'verify_otp':
                otp_code = (kw.get('otp') or '').strip()
                login = request.session.get('wa_auth_login')

                if not login:
                    step = 'phone'
                    error = _("Your verification session expired. Please enter your WhatsApp number again.")
                else:
                    try:
                        credential = {'type': 'whatsapp_otp', 'login': login, 'otp': otp_code}
                        auth_info = self._authenticate(credential)
                        self._clear_wa_session()
                        request.params['login_success'] = True
                        return request.redirect(self._get_post_login_redirect(auth_info['uid'], redirect=redirect))
                    except AccessDenied as e:
                        step = 'otp'
                        error = e.args[0] if e.args and e.args[0] else _("Invalid or expired verification code.")
                    except Exception:
                        _logger.exception("WhatsApp OTP verification error")
                        step = 'otp'
                        error = _("Verification failed. Please check the code and try again.")

        resend_wait = 0
        if step == 'otp' and request.session.get('wa_auth_user_id'):
            pending = Users.browse(request.session['wa_auth_user_id']).exists()
            resend_wait = pending.whatsapp_otp_resend_wait() if pending else 0

        values = {
            'step': step,
            'phone': phone,
            'customer_name': customer_name,
            'redirect': redirect,
            'error': error,
            'message': message,
            'resend_wait': resend_wait,
            'email_login_url': self._url('/web/login', redirect=redirect),
            'change_number_url': self._url('/web/login/whatsapp', reset=1, redirect=redirect),
            'support_whatsapp': self.SUPPORT_WHATSAPP,
        }
        response = request.render('whatsapp_connector.whatsapp_login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Cache-Control'] = 'no-store'
        return response


class WhatsAppPosCustomerPortal(CustomerPortal):
    """Extend Odoo Customer Portal with In-Store POS Receipts linked by partner or phone number"""

    def _get_customer_partner_ids(self):
        partner = request.env.user.partner_id
        partner_ids = set([partner.id, partner.commercial_partner_id.id])
        phone = getattr(partner, 'phone', False) or getattr(partner, 'mobile', False) or request.env.user.login
        if phone and hasattr(request.env['res.users'], 'find_matching_partner_ids_by_phone'):
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
