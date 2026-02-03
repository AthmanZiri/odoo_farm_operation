from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account',
        help="The analytic account used as a cost center for this vehicle."
    )

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account',
        help="The analytic account used as a cost center for this equipment."
    )
