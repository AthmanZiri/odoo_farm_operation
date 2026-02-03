from odoo import models, fields, api

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    analytic_plan_id = fields.Many2one(
        'account.analytic.plan', 
        string='Analytic Plan'
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account',
        domain="[('plan_id', '=', analytic_plan_id)]"
    )

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        compute='_compute_analytic_distribution',
        inverse='_inverse_analytic_distribution',
        store=True,
        readonly=False,
        help="Analytic distribution for service cost tracking."
    )
    
    analytic_precision = fields.Integer(
        default=5,
        readonly=True
    )

    @api.onchange('vehicle_id')
    def _onchange_vehicle_analytic(self):
        if self.vehicle_id and self.vehicle_id.analytic_account_id:
            self.analytic_account_id = self.vehicle_id.analytic_account_id.id
            self.analytic_plan_id = self.vehicle_id.analytic_account_id.plan_id.id

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_selection(self):
        if self.analytic_account_id:
            self.analytic_distribution = {str(self.analytic_account_id.id): 100.0}

    @api.depends('analytic_account_id')
    def _compute_analytic_distribution(self):
        for record in self:
            if record.analytic_account_id:
                record.analytic_distribution = {str(record.analytic_account_id.id): 100.0}
            else:
                record.analytic_distribution = False

    def _inverse_analytic_distribution(self):
        for record in self:
            if record.analytic_distribution:
                account_ids = list(record.analytic_distribution.keys())
                if account_ids:
                    account_id = int(account_ids[0])
                    account = self.env['account.analytic.account'].browse(account_id)
                    if account.exists():
                        record.analytic_account_id = account.id
                        record.analytic_plan_id = account.plan_id.id
