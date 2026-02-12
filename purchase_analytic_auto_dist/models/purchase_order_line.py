from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account (100%)',
        help="Selecting an account here will auto-populate the Analytic Distribution to 100% for this account."
    )

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        if self.account_analytic_id:
            # Odoo 17 analytic_distribution is a JSON field: { "account_id": percentage }
            # Percentages are floats (e.g., 100.0)
            self.analytic_distribution = {str(self.account_analytic_id.id): 100.0}
        else:
            self.analytic_distribution = False

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        """Keep the helper field in sync if a single account is selected."""
        if self.analytic_distribution and len(self.analytic_distribution) == 1:
            account_id_str = list(self.analytic_distribution.keys())[0]
            percentage = self.analytic_distribution[account_id_str]
            if percentage == 100.0:
                try:
                    account_id = int(account_id_str)
                    if not self.account_analytic_id or self.account_analytic_id.id != account_id:
                        self.account_analytic_id = account_id
                except ValueError:
                    pass
            else:
                self.account_analytic_id = False
        else:
            # Multiple accounts or empty distribution, clear the helper
            if self.account_analytic_id:
                self.account_analytic_id = False
