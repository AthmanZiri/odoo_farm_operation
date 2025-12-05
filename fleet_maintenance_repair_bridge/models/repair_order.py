from odoo import models, fields

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', help="The maintenance request that generated this repair order.")
    fleet_service_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Service', readonly=True, help="Fleet service that created this repair order.")

