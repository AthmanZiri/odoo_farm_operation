from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    fleet_service_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Service')

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.fleet_service_id:
                picking.fleet_service_id.update_service_cost()
        return res

