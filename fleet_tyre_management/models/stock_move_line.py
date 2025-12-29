from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_tyre = fields.Boolean(related='product_id.is_tyre', readonly=True, store=True)
    rfid_tag = fields.Char(string='RFID Tag')
    initial_tread_depth = fields.Float(string='Initial Tread Depth (mm)')
    manufacture_date = fields.Date(string='Manufacture Date (DOT)')
    expiry_date = fields.Date(string='Expiry Date')

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id.is_tyre and (line.lot_id or line.lot_name):
                lot = line.lot_id
                if not lot and line.lot_name:
                    lot = self.env['stock.lot'].search([
                        ('name', '=', line.lot_name),
                        ('product_id', '=', line.product_id.id),
                        ('company_id', '=', line.company_id.id)
                    ], limit=1)
                
                if lot:
                    lot.sudo().write({
                        'rfid_tag': line.rfid_tag,
                        'initial_tread_depth': line.initial_tread_depth,
                        'manufacture_date': line.manufacture_date,
                        'expiry_date': line.expiry_date,
                    })
                    # Sync location to tyre
                    tyre = self.env['fleet.vehicle.tyre'].sudo().search([('lot_id', '=', lot.id)], limit=1)
                    if tyre and line.location_dest_id:
                        tyre.write({'location_id': line.location_dest_id.id})
        return lines

    def write(self, vals):
        res = super().write(vals)
        for line in self.filtered(lambda l: l.product_id.is_tyre and l.lot_id):
            update_vals = {}
            if 'rfid_tag' in vals: update_vals['rfid_tag'] = vals['rfid_tag']
            if 'initial_tread_depth' in vals: update_vals['initial_tread_depth'] = vals['initial_tread_depth']
            if 'manufacture_date' in vals: update_vals['manufacture_date'] = vals['manufacture_date']
            if 'expiry_date' in vals: update_vals['expiry_date'] = vals['expiry_date']
            if update_vals:
                line.lot_id.sudo().write(update_vals)
            
            # Sync location if changed
            if 'location_dest_id' in vals:
                tyre = self.env['fleet.vehicle.tyre'].sudo().search([('lot_id', '=', line.lot_id.id)], limit=1)
                if tyre:
                    tyre.write({'location_id': vals['location_dest_id']})
        return res