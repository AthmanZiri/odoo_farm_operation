from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    tyre_ids = fields.One2many('fleet.vehicle.tyre', 'vehicle_id', string='tyres', domain=[('state', '=', 'mounted')])
    tyre_count = fields.Integer(compute='_compute_tyre_count', string='tyre Count')

    def _compute_tyre_count(self):
        for record in self:
            record.tyre_count = len(record.tyre_ids)

    def action_view_tyres(self):
        self.ensure_one()
        return {
            'name': 'tyres',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.tyre',
            'view_mode': 'kanban,list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
