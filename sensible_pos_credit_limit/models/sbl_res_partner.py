# Powered by Sensible Consulting Services
# -*- coding: utf-8 -*-
# © 2025 Sensible Consulting Services (<https://sensiblecs.com/>)
from odoo import fields, models, api


class SblResPartner(models.Model):
    _inherit = 'res.partner'

    sbl_available_credit = fields.Float('Available Credit', compute='_compute_available_credit', digits='Account')

    def _compute_available_credit(self):
        for partner in self:
            partner.sbl_available_credit = partner.credit_limit - partner.credit

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ['sbl_available_credit', 'parent_id']
        return fields
    
    def get_available_credit(self):
        return self.sbl_available_credit