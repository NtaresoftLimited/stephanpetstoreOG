# -*- coding: utf-8 -*-
from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._assign_cashier_home_action()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'groups_id' in vals or 'action_id' in vals:
            self._assign_cashier_home_action()
        return res

    def _assign_cashier_home_action(self):
        pos_action = self.env.ref('point_of_sale.action_pos_config_kanban', raise_if_not_found=False)
        if not pos_action:
            return
        for user in self:
            if not user.has_group('base.group_system'):
                is_cashier = (
                    user.has_group('point_of_sale.group_pos_user') or
                    user.has_group('sky_dashboard.group_sky_stock_cashier')
                )
                if is_cashier and user.action_id != pos_action:
                    super(ResUsers, user.sudo()).write({'action_id': pos_action.id})
