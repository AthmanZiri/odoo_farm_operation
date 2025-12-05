from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', help="The vehicle linked to this equipment.")
    vehicle_odometer_value = fields.Float(string="Vehicle Odometer", readonly=True, help="Last known odometer value from the linked vehicle.")
