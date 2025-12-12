from odoo import models, fields, api

class FleetVehicleTireHistory(models.Model):
    _name = 'fleet.vehicle.tire.history'
    _description = 'Tire Lifecycle History'
    _order = 'date desc, id desc'

    tire_id = fields.Many2one('fleet.vehicle.tire', string='Tire', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    
    type = fields.Selection([
        ('mount', 'Mounted'),
        ('dismount', 'Dismounted'),
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
        ('retread', 'Retread'),
        ('disposal', 'Disposal')
    ], string='Operation Type', required=True)

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    odometer = fields.Float(string='Vehicle Odometer')
    tread_depth = fields.Float(string='Tread Depth (mm)')
    
    note = fields.Text(string='Notes')
    cost = fields.Float(string='Cost')
