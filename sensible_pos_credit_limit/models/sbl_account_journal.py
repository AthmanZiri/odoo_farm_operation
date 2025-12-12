# Powered by Sensible Consulting Services
# -*- coding: utf-8 -*-
# © 2025 Sensible Consulting Services (<https://sensiblecs.com/>)
from odoo import fields, models, api


class SblAccountJournal(models.Model):
    _inherit = 'account.journal'

    sbl_credit_journal = fields.Boolean('Credit Journal')