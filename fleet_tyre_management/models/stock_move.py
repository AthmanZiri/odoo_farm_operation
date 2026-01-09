from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        # Sync tyre data from move lines to created lots
        for move in self:
            if move.product_id.is_tyre:
                for line in move.move_line_ids:
                    if line.lot_id:
                        # Prepare vals from line
                        vals = {}
                        if line.rfid_tag: vals['rfid_tag'] = line.rfid_tag
                        if line.initial_tread_depth: vals['initial_tread_depth'] = line.initial_tread_depth
                        if line.manufacture_date: vals['manufacture_date'] = line.manufacture_date
                        if line.expiry_date: vals['expiry_date'] = line.expiry_date
                        
                        if vals:
                            line.lot_id.sudo().write(vals)

                        # Sync Location to Fleet Tyre
                        tyre = self.env['fleet.vehicle.tyre'].search([('lot_id', '=', line.lot_id.id)], limit=1)
                        if tyre:
                            tyre.sudo().write({'location_id': move.location_dest_id.id})
        return res
