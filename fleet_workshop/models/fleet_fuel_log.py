from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    stock_move_id = fields.Many2one('stock.move', string='Stock Move', readonly=True)
    location_id = fields.Many2one('stock.location', string='Source Location', help="Location from where fuel is taken (e.g., Bulk Tank).")
    pump_attendant_id = fields.Many2one('hr.employee', string='Pump Attendant')
    driver_id = fields.Many2one('res.partner', related='vehicle_id.driver_id', string='Driver', store=True, readonly=True)
    
    product_id = fields.Many2one('product.product', string='Fuel Product', domain=[('type', 'in', ['product', 'consu'])])
    
    # Fields that might be missing since we are on services model now
    liter = fields.Float(string='Liters')
    price_per_liter = fields.Float(string='Price per Liter')

    @api.onchange('liter', 'price_per_liter')
    def _onchange_liter_price(self):
        if self.liter and self.price_per_liter:
            self.amount = self.liter * self.price_per_liter

    def action_create_stock_move(self):
        self.ensure_one()
        if self.stock_move_id:
            raise UserError(_("Stock move already created for this fuel log."))
        
        if not self.product_id:
            raise UserError(_("Please select a Fuel Product to track inventory."))
            
        if not self.location_id:
            raise UserError(_("Please select a Source Location (Bulk Tank)."))

        # Destination: Usage/Consumption (Virtual Location)
        location_dest = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
        location_dest_id = location_dest.id
        if not location_dest_id:
             raise UserError(_("Could not find a Virtual Production location."))

        move = self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'product_uom_qty': self.liter,
            'product_uom': self.product_id.uom_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'origin': _('Fuel Log %s') % self.id,
        })
        
        move._action_confirm()
        move._action_assign()
        move.move_line_ids.write({'quantity': self.liter}) # Set done quantity
        move._action_done()
        
        self.stock_move_id = move.id
