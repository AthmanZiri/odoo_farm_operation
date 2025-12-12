from odoo import models, fields, api

class FleetVehicleTire(models.Model):
    _name = 'fleet.vehicle.tire'
    _description = 'Vehicle Tire'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Serial Number', required=True, copy=False, help="Unique Serial Number or Internal ID")
    rfid_tag = fields.Char(string='RFID Tag', copy=False)
    
    product_id = fields.Many2one('product.product', string='Tire Product', required=True, domain=[('detailed_type', '=', 'product')])
    lot_id = fields.Many2one('stock.lot', string='Stock Lot/Serial', domain="[('product_id', '=', product_id)]", copy=False)

    brand = fields.Char(related='product_id.brand_id.name', string='Brand', store=True, readonly=False) # Assuming generic or product brand
    # If product doesn't have brand, we might need a custom field or rely on product name. 
    # Let's add explicit fields for now to allow standalone usage if product is generic.
    
    tire_type = fields.Selection([
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('all_season', 'All Season'),
        ('off_road', 'Off-Road')
    ], string='Tire Type')
    
    dimensions = fields.Char(string='Dimensions', help="e.g. 265/65 R17")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'In Stock'),
        ('mounted', 'Mounted on Vehicle'),
        ('repair', 'In Repair'),
        ('retread', 'Sent for Retread'),
        ('scrap', 'Scrapped/Disposed')
    ], string='Status', default='draft', tracking=True, group_expand='_read_group_stage_ids')

    vehicle_id = fields.Many2one('fleet.vehicle', string='Current Vehicle', tracking=True)
    location_id = fields.Many2one('stock.location', string='Storage Location', domain=[('usage', '=', 'internal')], tracking=True, help="Where the tire is currently stored if not mounted.")
    position = fields.Selection([
        ('fl', 'Front Left'),
        ('fr', 'Front Right'),
        ('rl', 'Rear Left'),
        ('rr', 'Rear Right'),
        ('spare', 'Spare'),
        ('other', 'Other')
    ], string='Position', tracking=True)

    current_tread_depth = fields.Float(string='Current Tread Depth (mm)', tracking=True)
    initial_tread_depth = fields.Float(string='Initial Tread Depth (mm)')
    
    purchase_date = fields.Date(string='Purchase Date')
    manufacture_date = fields.Date(string='Manufacture Date (DOT)')
    
    history_ids = fields.One2many('fleet.vehicle.tire.history', 'tire_id', string='History')

    @api.model
    def create(self, vals):
        # Sync with Stock Lot if needed
        return super().create(vals)
    
    def _read_group_stage_ids(self, stages, domain, order):
        return [key for key, val in self._fields['state'].selection]
