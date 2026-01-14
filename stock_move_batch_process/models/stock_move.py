from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_batch_confirm_issue(self):
        """
        Batch process stock moves:
        - Confirm draft moves.
        - Set quantity for moves in 'To Do' state and validate their pickings.
        """
        # 1. Handle Draft Moves
        draft_moves = self.filtered(lambda m: m.state == 'draft')
        if draft_moves:
            draft_moves._action_confirm()

        # 2. Filter moves in "To Do" states
        todo_moves = self.filtered(lambda m: m.state in ['confirmed', 'assigned', 'partially_available'])
        if not todo_moves:
            if not draft_moves:
                raise UserError(_("No 'To Do' or 'Draft' moves selected."))
            return True

        # 3. Set quantities for selected "To Do" moves
        for move in todo_moves:
            move.quantity = move.product_uom_qty
            # Handle 'picked' field if it exists (Odoo 17+)
            if hasattr(move, 'picked'):
                move.picked = True
            
        # 4. Process Pickings
        pickings = todo_moves.mapped('picking_id')
        for picking in pickings:
            if picking.state not in ['done', 'cancel']:
                # button_validate is the standard way to finalize pickings
                res = picking.button_validate()
                
                # Handle possible wizards (Backorder, etc.)
                if isinstance(res, dict) and res.get('res_model'):
                    res_model = res.get('res_model')
                    if res_model == 'stock.backorder.confirmation':
                        # Automatically create backorders for unselected moves
                        wizard = self.env[res_model].with_context(res.get('context')).create({})
                        if hasattr(wizard, 'process'):
                            wizard.process()
                        elif hasattr(wizard, 'action_process'):
                            wizard.action_process()
                    # Add handling for other common validation wizards if necessary
                
                picking._message_log(body=_("Batch processed via 'Confirm / Issue' action."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Selected moves have been processed.'),
                'sticky': False,
            }
        }

