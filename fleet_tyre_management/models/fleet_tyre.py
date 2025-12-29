from odoo import models, fields, api

class FleettyreBrand(models.Model):
    _name = 'fleet.tyre.brand'
    _description = 'Tyre Brand'

    name = fields.Char(string='Brand Name', required=True)
    active = fields.Boolean(default=True)

class FleetVehicletyre(models.Model):
    _name = 'fleet.vehicle.tyre'
    _description = 'Vehicle Tyre'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Serial Number', required=True, copy=False, help="Unique Serial Number or Internal ID")
    rfid_tag = fields.Char(string='RFID Tag', copy=False)
    
    product_id = fields.Many2one('product.product', string='Tyre Product', required=True, domain=[('type', '=', 'product')])
    lot_id = fields.Many2one('stock.lot', string='Stock Lot/Serial', domain="[('product_id', '=', product_id)]", copy=False)

    brand_id = fields.Many2one('fleet.tyre.brand', string='Brand', help="Tyre Brand/Manufacturer")
    brand = fields.Char(related='brand_id.name', string='Brand Name', store=True)
    # If product doesn't have brand, we might need a custom field or rely on product name. 
    # Let's add explicit fields for now to allow standalone usage if product is generic.
    
    tyre_type = fields.Selection([
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('all_season', 'All Season'),
        ('off_road', 'Off-Road')
    ], string='tyre Type')
    
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
    location_id = fields.Many2one('stock.location', string='Storage Location', domain=[('usage', '=', 'internal')], tracking=True, help="Where the tyre is currently stored if not mounted.")
    position_id = fields.Many2one('fleet.tyre.position', string='Position', tracking=True, domain="[('config_id', '=', vehicle_axle_config_id)]")
    vehicle_axle_config_id = fields.Many2one(related='vehicle_id.axle_config_id', string='Vehicle Axle Config')
    position_code = fields.Char(related='position_id.code', string='Position Code', store=True)

    current_tread_depth = fields.Float(string='Current Tread Depth (mm)', tracking=True)
    initial_tread_depth = fields.Float(string='Initial Tread Depth (mm)')
    
    purchase_date = fields.Date(string='Purchase Date')
    manufacture_date = fields.Date(string='Manufacture Date (DOT)')
    expiry_date = fields.Date(string='Expiry Date')

    # Lifecycle Extensions
    retread_count = fields.Integer(string='Retread Count', default=0, tracking=True)
    total_kms = fields.Float(string='Total KMs', compute='_compute_total_kms', store=True, help="Total KMs traveled by this tyre")
    cpk = fields.Float(string='Cost Per KM', compute='_compute_cpk', store=True, help="Total Cost / Total KMs")
    
    disposal_reason = fields.Char(string='Disposal Reason', tracking=True)
    disposal_date = fields.Date(string='Disposal Date', tracking=True)
    
    gps_tracker_info = fields.Char(string='GPS Tracker Information', tracking=True)
    
    history_ids = fields.One2many('fleet.vehicle.tyre.history', 'tyre_id', string='History')

    @api.depends('history_ids.odometer', 'history_ids.type')
    def _compute_total_kms(self):
        for tyre in self:
            kms = 0.0
            # Sort history by date/id to process chronologically
            sorted_history = tyre.history_ids.sorted(lambda r: (r.date, r.id))
            last_mount_odo = 0.0
            is_mounted = False
            
            for record in sorted_history:
                if record.type == 'mount':
                    last_mount_odo = record.odometer
                    is_mounted = True
                elif record.type in ('dismount', 'gate_check') and is_mounted:
                    # simplistic calculation: current odo - last mount odo
                    diff = record.odometer - last_mount_odo
                    if diff > 0:
                        kms += diff
                    last_mount_odo = record.odometer # Update for next leg if gate_check
                    if record.type == 'dismount':
                        is_mounted = False
            
            tyre.total_kms = kms

    @api.depends('product_id.standard_price', 'total_kms')
    def _compute_cpk(self):
        for tyre in self:
            cost = tyre.product_id.standard_price or 0.0
            service_costs = sum(tyre.history_ids.mapped('cost'))
            total_cost = cost + service_costs
            if tyre.total_kms > 0:
                tyre.cpk = total_cost / tyre.total_kms
            else:
                tyre.cpk = 0.0

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        return [key for key, val in self._fields['state'].selection]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_tyre = fields.Boolean(string='Is Tyre')
    tyre_brand_id = fields.Many2one('fleet.tyre.brand', string='Tyre Brand')
    tyre_brand = fields.Char(related='tyre_brand_id.name', string='Tyre Brand Name', store=True)
    tyre_dimensions = fields.Char(string='Tyre Dimensions')
    tyre_type = fields.Selection([
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('all_season', 'All Season'),
        ('off_road', 'Off-Road')
    ], string='Tyre Type')


