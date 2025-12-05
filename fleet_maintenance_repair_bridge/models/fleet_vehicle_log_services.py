from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request', readonly=True, help="Maintenance request created from this service.")
    repair_order_id = fields.Many2one('repair.order', string='Repair Order', readonly=True, help="Repair order created from this service.")

    def action_create_maintenance_request(self):
        """Create a maintenance request from this fleet service."""
        self.ensure_one()
        
        if self.maintenance_request_id:
            raise UserError(_("A maintenance request has already been created for this service."))
        
        if not self.vehicle_id:
            raise UserError(_("This service is not linked to a vehicle."))
        
        if not self.vehicle_id.equipment_id:
            raise UserError(_("The vehicle is not linked to any maintenance equipment. Please ensure the vehicle has been properly set up."))
        
        # Create maintenance request
        request_vals = {
            'name': self.description or f"Service: {self.service_type_id.name if self.service_type_id else 'General Service'}",
            'equipment_id': self.vehicle_id.equipment_id.id,
            'schedule_date': self.date,
            'fleet_service_id': self.id,
            'description': f"Created from Fleet Service: {self.description or ''}\nCost: {self.amount}\nVendor: {self.vendor_id.name if self.vendor_id else 'N/A'}",
        }
        
        maintenance_request = self.env['maintenance.request'].create(request_vals)
        self.maintenance_request_id = maintenance_request.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Request',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'res_id': maintenance_request.id,
        }

    def action_create_repair_order(self):
        """Create a repair order from this fleet service."""
        self.ensure_one()
        
        if self.repair_order_id:
            raise UserError(_("A repair order has already been created for this service."))
        
        if not self.vehicle_id:
            raise UserError(_("This service is not linked to a vehicle."))
        
        # Find product for the vehicle
        product = self.vehicle_id.product_id
        if not product:
            # Fallback: Try to find a product with the same name as the vehicle model
            product = self.env['product.product'].search([('name', '=', self.vehicle_id.model_id.name)], limit=1)
        
        if not product:
            raise UserError(_("Please define a related product on the vehicle or ensure a product exists with the vehicle model name."))
        
        # Find customer (Company or Driver)
        partner = self.vehicle_id.driver_id if self.vehicle_id.driver_id else self.env.company.partner_id
        
        repair_vals = {
            'product_id': product.id,
            'partner_id': partner.id,
            'fleet_service_id': self.id,
            'internal_notes': self.description or f"Service: {self.service_type_id.name if self.service_type_id else 'General Service'}",
            'schedule_date': self.date,
        }
        
        repair_order = self.env['repair.order'].create(repair_vals)
        self.repair_order_id = repair_order.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order',
            'res_model': 'repair.order',
            'view_mode': 'form',
            'res_id': repair_order.id,
        }

    def action_view_maintenance_request(self):
        """View the linked maintenance request."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Request',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'res_id': self.maintenance_request_id.id,
        }

    def action_view_repair_order(self):
        """View the linked repair order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Order',
            'res_model': 'repair.order',
            'view_mode': 'form',
            'res_id': self.repair_order_id.id,
        }
