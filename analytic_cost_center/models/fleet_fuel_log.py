from odoo import models, fields, api

class FleetVehicleLogFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    analytic_plan_id = fields.Many2one(
        'account.analytic.plan', 
        string='Analytic Plan'
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account'
    )

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        compute='_compute_analytic_distribution',
        inverse='_inverse_analytic_distribution',
        store=True,
        readonly=False,
        help="Analytic distribution for fuel cost tracking."
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
    def _onchange_analytic_account_vehicle_lookup(self):
        if self.analytic_account_id:
            # Sync plan
            self.analytic_plan_id = self.analytic_account_id.plan_id.id
            
            # Sync distribution
            self.analytic_distribution = {str(self.analytic_account_id.id): 100.0}
            
            # Reverse Lookup
            vehicle = self.env['fleet.vehicle'].search([('analytic_account_id', '=', self.analytic_account_id.id)], limit=1)
            if vehicle:
                self.vehicle_id = vehicle.id

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

    def button_done(self):
        for item in self.filtered(lambda x: x.state == "running"):
            if item.product_id and item.location_id and item.liter > 0:
                move_vals = {
                    "product_id": item.product_id.id,
                    "product_uom_qty": item.liter,
                    "product_uom": item.product_id.uom_id.id,
                    "location_id": item.location_id.id,
                    "location_dest_id": item.location_dest_id.id
                    or self.env.ref("analytic_cost_center.stock_location_consumption").id,
                    "origin": item.vehicle_id.name,
                    "analytic_distribution": item.analytic_distribution,
                }
                move = self.env["stock.move"].create(move_vals)
                move._action_confirm()
                move._action_assign()
                for line in move.move_line_ids:
                    line.quantity = line.quantity_product_uom
                move._action_done()
                item.stock_move_id = move.id

            vals = item._prepare_fleet_vehicle_log_services_vals()
            vals.update({
                'analytic_distribution': item.analytic_distribution,
                'analytic_plan_id': item.analytic_plan_id.id,
                'analytic_account_id': item.analytic_account_id.id,
            })
            item.service_id = self.env["fleet.vehicle.log.services"].create(vals)

            item.state = "done"
        return True
