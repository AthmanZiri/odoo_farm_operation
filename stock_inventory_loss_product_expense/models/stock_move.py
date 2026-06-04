from odoo import models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_product_expense_account(self):
        """Product expense account, then category, then company default."""
        self.ensure_one()
        fiscal_pos = self.picking_id.fiscal_position_id if self.picking_id else False
        if fiscal_pos:
            accounts = self.product_id.get_product_accounts(fiscal_pos)
        else:
            accounts = self.product_id._get_product_accounts()
        return accounts.get('expense')

    def _get_account_move_line_vals(self):
        lines = super()._get_account_move_line_vals()
        dest = self.location_dest_id
        if dest.usage != 'inventory' or not dest.valuation_account_id:
            return lines

        expense_account = self._get_product_expense_account()
        if not expense_account:
            raise UserError(_(
                "Cannot post inventory loss for %(product)s: no expense account "
                "is configured on the product or its category.",
                product=self.product_id.display_name,
            ))

        for line in lines:
            if line.get('debit'):
                line['account_id'] = expense_account.id
        return lines
