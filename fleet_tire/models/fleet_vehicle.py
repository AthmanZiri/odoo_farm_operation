from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    tire_ids = fields.One2many('fleet.vehicle.tire', 'vehicle_id', string='Tires', domain=[('state', '=', 'mounted')])
    tire_count = fields.Integer(compute='_compute_tire_count', string='Tire Count')

    def _compute_tire_count(self):
        for record in self:
            record.tire_count = len(record.tire_ids)

    def action_view_tires(self):
        self.ensure_one()
        return {
            'name': 'Tires',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.tire',
            'view_mode': 'kanban,list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
