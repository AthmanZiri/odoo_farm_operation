from odoo import models, fields, api

class FleetVehicletyreHistory(models.Model):
    _name = 'fleet.vehicle.tyre.history'
    _description = 'tyre Lifecycle History'
    _order = 'date desc, id desc'

    tyre_id = fields.Many2one('fleet.vehicle.tyre', string='tyre', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    
    type = fields.Selection([
        ('mount', 'Mounted'),
        ('dismount', 'Dismounted'),
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
        ('retread', 'Retread'),
        ('gate_check', 'Gate Check'),
        ('return_stock', 'Returned to Stock'),
        ('disposal', 'Disposal')
    ], string='Operation Type', required=True)

    gate_scan_type = fields.Selection([
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out')
    ], string='Gate Scan Type')


    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    odometer = fields.Float(string='Vehicle Odometer')
    tread_depth = fields.Float(string='Tread Depth (mm)')
    
    note = fields.Text(string='Notes')
    cost = fields.Float(string='Cost')
    
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    reason = fields.Char(string='Reason')
    method = fields.Selection([
        ('patch', 'Patch'),
        ('plug', 'Plug'),
        ('retread_cold', 'Cold Retread'),
        ('retread_hot', 'Hot Retread'),
        ('scrap', 'Scrap'),
        ('sell', 'Sell'),
        ('other', 'Other')
    ], string='Method')
