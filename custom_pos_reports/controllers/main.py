# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.report import ReportController

class CustomPosReportController(ReportController):
    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True, readonly=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if reportname == 'custom_pos_reports.report_pos_thermal' and docids:
            try:
                ids = [int(i) for i in docids.split(',') if i.isdigit()]
                session = request.env['pos.session'].browse(ids)
                wizard = request.env['pos.details.wizard'].browse(ids)
                if session.exists() and not wizard.exists():
                    reportname = 'custom_pos_reports.report_session_thermal'
            except Exception:
                pass
        return super().report_routes(reportname, docids=docids, converter=converter, **data)
