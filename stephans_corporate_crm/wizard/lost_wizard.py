# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CorporateCrmLostWizard(models.TransientModel):
    _name = 'corporate.crm.lost.wizard'
    _description = 'Mark Deal as Lost'

    deal_id = fields.Many2one('corporate.crm.deal', string='Deal / Opportunity', required=True)
    lost_reason_id = fields.Many2one('corporate.crm.lost.reason', string='Lost Reason', required=True)
    lost_feedback = fields.Text(string='Feedback / Reason Details')

    def action_confirm_lost(self):
        self.ensure_one()
        lost_stage = self.env['corporate.crm.stage'].search([('is_lost', '=', True)], limit=1)
        if not lost_stage:
            lost_stage = self.env['corporate.crm.stage'].create({
                'name': 'Lost / Churned',
                'sequence': 99,
                'is_lost': True,
                'fold': True
            })

        self.deal_id.write({
            'stage_id': lost_stage.id,
            'probability': 0.0,
            'lost_reason_id': self.lost_reason_id.id,
            'lost_feedback': self.lost_feedback,
        })

        self.deal_id.message_post(
            body=f"<b>❌ Deal Marked as Lost:</b> {self.lost_reason_id.name}<br/><blockquote>{self.lost_feedback or 'No extra notes provided.'}</blockquote>",
            subtype_xmlid='mail.mt_comment'
        )
        return {'type': 'ir.actions.act_window_close'}
