from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError


class SblPOSOrder(models.Model):
    _inherit = "pos.order"

    def _process_saved_order(self, draft):
        res = super()._process_saved_order(draft)
        self.sbl_create_receivable_move_line()
        return res

    def sbl_create_receivable_move_line(self):
        credit_payments = self.payment_ids.filtered(lambda p: p.payment_method_id and p.payment_method_id.sbl_credit_journal)
        if not credit_payments:
            return
        move_line_vals = []
        income_account = self.env['account.account'].with_company(self.env.company).search([
            *self.env['account.account']._check_company_domain(self.env.company.id),
            ('account_type', '=', 'income'),
            ('id', '!=', (self.env.company).account_journal_early_pay_discount_gain_account_id.id)
        ], limit=1)
        for payment in credit_payments:
            move_line_vals += [
                {
                    'date': fields.Date.today(),
                    'account_id': self.company_id.account_default_pos_receivable_account_id.id,
                    'debit': payment.amount,
                    'credit': 0.0,
                    'name': self.pos_reference,
                },
                {
                    'date': fields.Date.today(),
                    'account_id': income_account.id,
                    'debit': 0.0,
                    'credit': payment.amount,
                    'name': self.pos_reference,
                },
            ]
        if move_line_vals:
            move_vals = {
                'date': fields.Date.today(),
                'journal_id': self.env['account.journal'].search([('type', '=', 'sale')], limit=1).id,
                'line_ids': [Command.create(line_vals) for line_vals in move_line_vals],
                'partner_id': self.partner_id.id,
            }
            move = self.env['account.move'].create(move_vals)
            move._post()