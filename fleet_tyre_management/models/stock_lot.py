from odoo import models, fields, api

class StockLot(models.Model):
    _inherit = 'stock.lot'

    rfid_tag = fields.Char(string='RFID Tag')
    initial_tread_depth = fields.Float(string='Initial Tread Depth (mm)')
    manufacture_date = fields.Date(string='Manufacture Date (DOT)')
    expiry_date = fields.Date(string='Expiry Date')
    
    tyre_brand_id = fields.Many2one(related='product_id.tyre_brand_id', readonly=False, store=True)
    tyre_brand = fields.Char(related='product_id.tyre_brand', readonly=False, store=True)
    tyre_dimensions = fields.Char(related='product_id.tyre_dimensions', readonly=False, store=True)
    tyre_type = fields.Selection(related='product_id.tyre_type', readonly=False, store=True)

    def _create_or_update_tyre(self):
        for lot in self.filtered(lambda l: l.product_id.is_tyre):
            tyre = self.env['fleet.vehicle.tyre'].sudo().search([('lot_id', '=', lot.id)], limit=1)
            vals = {
                'name': lot.name,
                'lot_id': lot.id,
                'product_id': lot.product_id.id,
                'rfid_tag': lot.rfid_tag,
                'brand_id': lot.tyre_brand_id.id if lot.tyre_brand_id else False,
                'brand': lot.tyre_brand,
                'dimensions': lot.tyre_dimensions,
                'tyre_type': lot.tyre_type,
                'initial_tread_depth': lot.initial_tread_depth,
                'current_tread_depth': lot.initial_tread_depth,
                'manufacture_date': lot.manufacture_date,
                'expiry_date': lot.expiry_date,
                'location_id': lot.location_id.id if lot.location_id else False,
                'state': 'available',
            }
            if tyre:
                # For write, don't overwrite current_tread_depth if it was already updated
                # unless it is 0.0 (newly created)
                if 'current_tread_depth' in vals:
                    if tyre.current_tread_depth != 0.0:
                        del vals['current_tread_depth']
                tyre.write(vals)
            else:
                self.env['fleet.vehicle.tyre'].sudo().create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)
        lots._create_or_update_tyre()
        return lots

    def write(self, vals):
        res = super().write(vals)
        self._create_or_update_tyre()
        return res
