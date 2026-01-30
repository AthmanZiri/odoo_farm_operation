# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_open_purchase_order_wizard(self):
        return {
            'name': "Auto Confirm Purchase Order",
            'type': "ir.actions.act_window",
            'res_model': "confirm.purchase.wizard",
            'view_mode': "form",
            'target': "new",
            'context': {'purchase_order_ids': self.ids}
        }
