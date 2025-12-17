from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allocation_type = fields.Selection([
        ('fleet', 'Fleet Vehicle'),
        ('equipment', 'Maintenance Equipment')
    ], string='Allocation Type', help="Choose whether to allocate this requisition to a Fleet Vehicle or Maintenance Equipment.")

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    fleet_service_type_id = fields.Many2one('fleet.service.type', string='Service Type', help="The type of service to log in Fleet.")
    ordered_by_id = fields.Many2one('res.partner', string='Ordered By')

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            if picking.allocation_type:
                picking._create_fleet_service()
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
            })
            
            # Explicitly write to ensure connection on done records
            self.write({'fleet_service_id': service.id})
            
            # Update cost
            if hasattr(service, 'update_service_cost'):
                # Invalidate cache to ensure picking_ids are seen
                service.invalidate_recordset(['picking_ids']) 
                service.update_service_cost()

    def action_view_fleet_service(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fleet Service',
            'res_model': 'fleet.vehicle.log.services',
            'view_mode': 'form',
            'res_id': self.fleet_service_id.id,
        }
