from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    fleet_service_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Service')
