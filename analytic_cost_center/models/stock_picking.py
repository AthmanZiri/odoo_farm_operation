import json
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_plan_id = fields.Many2one(
        'account.analytic.plan', 
        string='Analytic Plan',
        help="Select the analytic plan for cost tracking."
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 
        string='Analytic Account',
        domain="[('plan_id', '=', analytic_plan_id)]",
        help="Select the analytic account for cost tracking."
    )

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        compute='_compute_analytic_distribution',
        inverse='_inverse_analytic_distribution',
        store=True,
        readonly=False,
        help="Analytic distribution for cost centers."
    )
    
    analytic_precision = fields.Integer(
        default=5,
        readonly=True
    )

    @api.onchange('fleet_vehicle_id', 'equipment_id')
    def _onchange_vehicle_equipment_analytic(self):
        for record in self:
            obj = record.fleet_vehicle_id or record.equipment_id
            if obj and obj.analytic_account_id:
                record.analytic_account_id = obj.analytic_account_id.id
                record.analytic_plan_id = obj.analytic_account_id.plan_id.id

    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_reverse_lookup(self):
        if self.analytic_account_id:
            # Sync distribution
            self.analytic_distribution = {str(self.analytic_account_id.id): 100.0}
            
            # Automate Destination Location for Consumption
            consumption_loc = self.env.ref('analytic_cost_center.stock_location_consumption', raise_if_not_found=False)
            if consumption_loc:
                self.location_dest_id = consumption_loc.id

            # Reverse Lookup: Search for Vehicle
            vehicle = self.env['fleet.vehicle'].search([('analytic_account_id', '=', self.analytic_account_id.id)], limit=1)
            if vehicle:
                self.fleet_vehicle_id = vehicle.id
                self.allocation_type = 'fleet'
                return
            
            # Reverse Lookup: Search for Equipment
            equipment = self.env['maintenance.equipment'].search([('analytic_account_id', '=', self.analytic_account_id.id)], limit=1)
            if equipment:
                self.equipment_id = equipment.id
                self.allocation_type = 'equipment'

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

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking.analytic_distribution:
                picking.move_ids.write({'analytic_distribution': picking.analytic_distribution})
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if 'analytic_distribution' in vals:
            self.move_ids.write({'analytic_distribution': vals['analytic_distribution']})
        return res

    def _create_fleet_service(self):
        self.ensure_one()
        vehicle = None
        
        if self.allocation_type == 'fleet' and self.fleet_vehicle_id:
            vehicle = self.fleet_vehicle_id
        elif self.allocation_type == 'equipment' and self.equipment_id:
            if hasattr(self.equipment_id, 'vehicle_id') and self.equipment_id.vehicle_id:
                vehicle = self.equipment_id.vehicle_id
        
        if vehicle and self.fleet_service_type_id:
            description = self.note or ""
            if self.origin:
                description = f"{description} (Origin: {self.origin})"
            
            service = self.env['fleet.vehicle.log.services'].create({
                'vehicle_id': vehicle.id,
                'service_type_id': self.fleet_service_type_id.id,
                'date': self.date_done or fields.Date.today(),
                'description': description.strip() or f"Allocation from {self.name}",
                'vendor_id': self.partner_id.id if self.partner_id else False,
                'analytic_distribution': self.analytic_distribution,
                'analytic_plan_id': self.analytic_plan_id.id,
                'analytic_account_id': self.analytic_account_id.id,
            })
            
            self.write({'fleet_service_id': service.id})
            
            if hasattr(service, 'update_service_cost'):
                service.invalidate_recordset(['picking_ids']) 
                service.update_service_cost()

class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_distribution = fields.Json(
        string='Analytic Distribution',
        help="Analytic distribution inherited from picking or set manually."
    )
    analytic_precision = fields.Integer(
        default=5,
        readonly=True
    )
