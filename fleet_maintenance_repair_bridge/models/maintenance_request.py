from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    vehicle_id = fields.Many2one(related='equipment_id.vehicle_id', string='Vehicle', store=True, readonly=True)
    repair_ids = fields.One2many('repair.order', 'maintenance_request_id', string='Repair Orders')
    repair_count = fields.Integer(compute='_compute_repair_count', string="Repair Count")
    fleet_service_id = fields.Many2one('fleet.vehicle.log.services', string='Fleet Service', readonly=True, help="Fleet service that created this maintenance request.")


    @api.depends('repair_ids')
    def _compute_repair_count(self):
        for request in self:
            request.repair_count = len(request.repair_ids)

    def action_create_repair_order(self):
        self.ensure_one()
        if not self.vehicle_id:
            raise UserError(_("This maintenance request is not linked to a vehicle."))

        # Find product for the vehicle
        product = self.vehicle_id.product_id
        if not product:
            # Fallback: Try to find a product with the same name as the vehicle model
            product = self.env['product.product'].search([('name', '=', self.vehicle_id.model_id.name)], limit=1)
        
        if not product:
             raise UserError(_("Please define a related product on the vehicle or ensure a product exists with the vehicle model name."))

        # Find customer (Company or Driver)
        partner = self.vehicle_id.driver_id or self.env.company.partner_id

        repair_vals = {
            'product_id': product.id,
            'partner_id': partner.id,
            'maintenance_request_id': self.id,
            'internal_notes': self.name,
            'schedule_date': self.schedule_date,
        }
        repair_order = self.env['repair.order'].create(repair_vals)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order',
            'res_model': 'repair.order',
            'view_mode': 'form',
            'res_id': repair_order.id,
        }

    def action_view_repair_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Orders',
            'res_model': 'repair.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.repair_ids.ids)],
            'context': {'default_maintenance_request_id': self.id},
        }
