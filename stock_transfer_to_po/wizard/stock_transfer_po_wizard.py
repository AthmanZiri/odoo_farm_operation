from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockTransferPoWizard(models.TransientModel):
    _name = 'stock.transfer.po.wizard'
    _description = 'Generate Purchase Request from Shortages'

    line_ids = fields.One2many('stock.transfer.po.wizard.line', 'wizard_id', string='Products')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'line_ids' not in fields_list:
            return res

        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        lines = []

        if active_model == 'stock.picking':
            pickings = self.env['stock.picking'].browse(active_ids)
            for picking in pickings:
                # Filter Logic: Internal Transfers only
                if picking.picking_type_code != 'internal':
                    continue
                
                # Check for waiting or partially available moves
                moves = picking.move_ids.filtered(
                    lambda m: m.state in ['confirmed', 'partially_available'] and not m.is_pack_move
                )
                
                for move in moves:
                     shortage = move.product_uom_qty - move.quantity
                     if shortage > 0:
                         vendor = move.product_id.seller_ids[:1].partner_id if move.product_id.seller_ids else False
                         lines.append((0, 0, {
                             'product_id': move.product_id.id,
                             'quantity': shortage,
                             'partner_id': vendor.id if vendor else False,
                             'picking_id': picking.id,
                             'move_id': move.id,
                         }))

        elif active_model == 'stock.move':
            moves = self.env['stock.move'].browse(active_ids)
            # Filter moves if needed, though user selected them. Maybe just check if they are relevant.
            # User said "list of stock.move that are in waiting".
            valid_moves = moves.filtered(lambda m: m.state in ['confirmed', 'partially_available'] and not m.is_pack_move)
            
            for move in valid_moves:
                 # If selecting specific moves, use the full demand or remaining?
                 # defaulting to shortage logic.
                 shortage = move.product_uom_qty - move.quantity
                 if shortage > 0:
                     vendor = move.product_id.seller_ids[:1].partner_id if move.product_id.seller_ids else False
                     lines.append((0, 0, {
                         'product_id': move.product_id.id,
                         'quantity': shortage,
                         'partner_id': vendor.id if vendor else False,
                         'picking_id': move.picking_id.id,
                         'move_id': move.id,
                     }))
                     
        res['line_ids'] = lines
        return res

    def action_create_po(self):
        # Determine if we should create a Request or PO.
        # User request: Submit purchase request > Store manager accepts > ...
        # So this wizard should create a Stock Purchase Request.
        
        self.ensure_one()
        if not self.line_ids:
            return
            
        # Create one request for the batch
        request_vals = {
            'requester_id': self.env.user.id,
            'state': 'submitted', # Auto-submit as per "Submit purchase request" flow assumption, or leaving draft?
            # "Submit purchase request" implies the action IS submitting.
            'company_id': self.env.company.id,
        }
        request = self.env['stock.purchase.request'].create(request_vals)
        
        for line in self.line_ids:
            # Allow empty vendor for now, enforced at validation/approval
            # if not line.partner_id:
            #     product_name = line.product_id.display_name or _("Unknown Product")
            #     raise UserError(_("Please define a vendor for product %s") % product_name)
            
            self.env['stock.purchase.request.line'].create({
                'request_id': request.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'partner_id': line.partner_id.id if line.partner_id else False,
                'move_id': line.move_id.id,
            })
            
        return {
            'name': _('Purchase Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.purchase.request',
            'view_mode': 'form',
            'res_id': request.id,
        }


class StockTransferPoWizardLine(models.TransientModel):
    _name = 'stock.transfer.po.wizard.line'
    _description = 'Wizard Line'

    wizard_id = fields.Many2one('stock.transfer.po.wizard', string="Wizard")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Shortage Qty', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor')
    picking_id = fields.Many2one('stock.picking', string='Source Transfer', readonly=True)
    move_id = fields.Many2one('stock.move', string='Source Move', readonly=True)
