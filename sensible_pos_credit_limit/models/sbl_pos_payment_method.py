from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SblPosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    sbl_credit_journal = fields.Boolean(related='journal_id.sbl_credit_journal', store=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ['sbl_credit_journal']
        return fields