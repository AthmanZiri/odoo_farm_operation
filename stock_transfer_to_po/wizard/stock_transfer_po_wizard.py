from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockTransferPoWizard(models.TransientModel):
    _name = 'stock.transfer.po.wizard'
    _description = 'Generate PO from Shortages'

    line_ids = fields.One2many('stock.transfer.po.wizard.line', 'wizard_id', string='Products')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'line_ids' in fields_list and self.env.context.get('active_model') == 'stock.picking':
            active_ids = self.env.context.get('active_ids', [])
            pickings = self.env['stock.picking'].browse(active_ids)
            lines = []
            for picking in pickings:
                # Filter Logic: Internal Transfers only
                if picking.picking_type_code != 'internal':
                    continue
                
                # Check for waiting or partially available moves
                # We want moves that are confirmed (waiting) or partially_available
                # Exclude pack moves - only purchase actual products (components or non-packs)
                moves = picking.move_ids.filtered(
                    lambda m: m.state in ['confirmed', 'partially_available'] and not m.is_pack_move
                )
                
                for move in moves:
                     # Calculate shortage
                     # confirmed: Demand (product_uom_qty) - Reserved (quantity) should be the shortage.
                     # usually for confirmed, quantity is 0.
                     shortage = move.product_uom_qty - move.quantity
                     
                     if shortage > 0:
                         # Suggest Vendor
                         # product.seller_ids is ordered by sequence, so first one is main vendor
                         vendor = move.product_id.seller_ids[:1].partner_id if move.product_id.seller_ids else False
                         
                         lines.append((0, 0, {
                             'product_id': move.product_id.id,
                             'quantity': shortage,
                             'partner_id': vendor.id if vendor else False,
                             'picking_id': picking.id,
                         }))
            res['line_ids'] = lines
        return res

    def action_create_po(self):
        self.ensure_one()
        if not self.line_ids:
            return
            
        # Group by partner
        grouped = {}
        for line in self.line_ids:
            if not line.partner_id:
                product_name = line.product_id.display_name or _("Unknown Product")
                raise UserError(_("Please define a vendor for product %s") % product_name)
            if line.partner_id not in grouped:
                grouped[line.partner_id] = []
            grouped[line.partner_id].append(line)
        
        orders = self.env['purchase.order']
        for partner, lines in grouped.items():
            # Source Doc: comma separated unique picking names
            pickings = sorted(list(set(l.picking_id.name for l in lines if l.picking_id)))
            
            po_vals = {
                'partner_id': partner.id,
                'origin': ', '.join(pickings),
                'date_order': fields.Datetime.now(),
                'company_id': self.env.company.id,
            }
            po = self.env['purchase.order'].create(po_vals)
            
            for line in lines:
                if not line.product_id:
                    continue
                line_vals = {
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'name': line.product_id.display_name,
                    'date_planned': fields.Datetime.now(),
                }
                # Try to get price from supplier info
                supplier_info = line.product_id._select_seller(
                    partner_id=partner,
                    quantity=line.quantity,
                    date=po.date_order and po.date_order.date(),
                    uom_id=line.product_id.uom_id
                )
                if supplier_info:
                    line_vals['price_unit'] = supplier_info.price
                else:
                    line_vals['price_unit'] = line.product_id.standard_price

                self.env['purchase.order.line'].create(line_vals)
            orders += po
            
        return {
            'name': _('Generated Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', orders.ids)],
        }


class StockTransferPoWizardLine(models.TransientModel):
    _name = 'stock.transfer.po.wizard.line'
    _description = 'Wizard Line'

    wizard_id = fields.Many2one('stock.transfer.po.wizard', string="Wizard")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Shortage Qty', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    picking_id = fields.Many2one('stock.picking', string='Source Transfer', readonly=True)
