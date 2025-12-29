from odoo import models, fields, api

class FleetVehicletyre(models.Model):
    _name = 'fleet.vehicle.tyre'
    _description = 'Vehicle tyre'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Serial Number', required=True, copy=False, help="Unique Serial Number or Internal ID")
    rfid_tag = fields.Char(string='RFID Tag', copy=False)
    
    product_id = fields.Many2one('product.product', string='tyre Product', required=True, domain=[('type', '=', 'product')])
    lot_id = fields.Many2one('stock.lot', string='Stock Lot/Serial', domain="[('product_id', '=', product_id)]", copy=False)

    brand = fields.Char(string='Brand', help="tyre Brand/Manufacturer")
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

    # Lifecycle Extensions
    retread_count = fields.Integer(string='Retread Count', default=0, tracking=True)
    total_kms = fields.Float(string='Total KMs', compute='_compute_total_kms', store=True, help="Total KMs traveled by this tyre")
    cpk = fields.Float(string='Cost Per KM', compute='_compute_cpk', help="Total Cost / Total KMs")
    
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
    tyre_brand = fields.Char(string='Tyre Brand')
    tyre_dimensions = fields.Char(string='Tyre Dimensions')
    tyre_type = fields.Selection([
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('all_season', 'All Season'),
        ('off_road', 'Off-Road')
    ], string='Tyre Type')

class StockLot(models.Model):
    _inherit = 'stock.lot'

    rfid_tag = fields.Char(string='RFID Tag')
    initial_tread_depth = fields.Float(string='Initial Tread Depth (mm)')
    manufacture_date = fields.Date(string='Manufacture Date (DOT)')
    expiry_date = fields.Date(string='Expiry Date')
    
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
                'brand': lot.tyre_brand,
                'dimensions': lot.tyre_dimensions,
                'tyre_type': lot.tyre_type,
                'initial_tread_depth': lot.initial_tread_depth,
                'manufacture_date': lot.manufacture_date,
            }
            if tyre:
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
        for line in lines.filtered(lambda l: l.product_id.is_tyre and l.lot_id):
            line.lot_id.write({
                'rfid_tag': line.rfid_tag,
                'initial_tread_depth': line.initial_tread_depth,
                'manufacture_date': line.manufacture_date,
                'expiry_date': line.expiry_date,
            })
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
                line.lot_id.write(update_vals)
        return res
