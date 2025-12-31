from odoo import models, fields, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_explode_pack(self):
        """
        Identify moves that are packs and explode them into components.
        Only processes moves that are in 'draft', 'confirmed', 'assigned' states.
        """
        for picking in self:
            # We iterate over a copy of moves because we'll be modifying the list (cancelling some, adding others)
            moves_to_process = picking.move_ids.filtered(
                lambda m: m.is_pack_move and m.state in ['draft', 'confirmed', 'assigned', 'partially_available'] and not m.parent_pack_move_id
            )
            
            for move in moves_to_process:
                # Get the pack configuration
                pack = move.product_id.product_tmpl_id
                if not pack.is_pack or not pack.pack_line_ids:
                    continue
                
                # Logic to create component moves
                new_moves_vals = []
                for line in pack.pack_line_ids:
                    qty = line.quantity * move.product_uom_qty
                    
                    vals = {
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty,
                        'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                        'picking_id': picking.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'parent_pack_move_id': move.id, # Link back to the original move
                        'state': 'draft', # Will be confirmed later
                        'origin': move.origin,
                        'procure_method': move.procure_method,
                        'picking_type_id': move.picking_type_id.id,
                    }
                    new_moves_vals.append(vals)
                
                if new_moves_vals:
                    self.env['stock.move'].create(new_moves_vals)
                    # Cancel the original pack move
                    move._action_cancel()

        return True
