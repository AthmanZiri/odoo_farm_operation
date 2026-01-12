from odoo import models, fields

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', help="The vehicle linked to this equipment.")

    def action_view_vehicle(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle',
            'res_model': 'fleet.vehicle',
            'view_mode': 'form',
            'res_id': self.vehicle_id.id,
        }
