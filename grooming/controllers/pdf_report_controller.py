from odoo import http
from odoo.http import request

class InternalTransferReportController(http.Controller):
    
    @http.route(['/print/transfer/<int:picking_id>'], type='http', auth='user')
    def print_internal_transfer(self, picking_id, **kw):
        picking = request.env['stock.picking'].browse(picking_id)
        if not picking.exists():
            return request.not_found()

        pdf_data = picking.generate_custom_pdf()

        safe_filename = (picking.name or "Transfer").replace("/", "_").replace("\\", "_")
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_data)),
            ('Content-Disposition', f'attachment; filename="Internal_Transfer_{safe_filename}.pdf"')
        ]
        return request.make_response(pdf_data, headers=pdfhttpheaders)
