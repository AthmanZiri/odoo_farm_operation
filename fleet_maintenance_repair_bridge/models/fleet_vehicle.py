from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    equipment_id = fields.Many2one('maintenance.equipment', string='Maintenance Equipment', readonly=True, help="The equipment linked to this vehicle.")
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count")
    product_id = fields.Many2one('product.product', string="Related Product", help="Product used for Repair Orders linked to this vehicle.")

    def _compute_maintenance_count(self):
        for vehicle in self:
            if vehicle.equipment_id:
                vehicle.maintenance_count = self.env['maintenance.request'].search_count([('equipment_id', '=', vehicle.equipment_id.id)])
            else:
                vehicle.maintenance_count = 0

    @api.model_create_multi
    def create(self, vals_list):
        vehicles = super().create(vals_list)
        for vehicle in vehicles:
            vehicle._create_linked_equipment()
        return vehicles

    def _create_linked_equipment(self):
        """ Creates a maintenance.equipment record for the vehicle. """
        self.ensure_one()
        if not self.equipment_id:
            category = self.env['maintenance.equipment.category'].search([('name', '=', 'Vehicles')], limit=1)
            if not category:
                category = self.env['maintenance.equipment.category'].create({'name': 'Vehicles'})
            
            equipment_vals = {
                'name': f"{self.model_id.name} - {self.license_plate}" if self.license_plate else self.model_id.name,
                'category_id': category.id,
                'vehicle_id': self.id,
                'owner_user_id': self.driver_id.id if self.driver_id else False,
            }
            equipment = self.env['maintenance.equipment'].create(equipment_vals)
            self.equipment_id = equipment.id

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance Requests',
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.equipment_id.id)],
            'context': {'default_equipment_id': self.equipment_id.id},
        }

    def action_view_equipment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'res_id': self.equipment_id.id,
        }

class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    @api.model_create_multi
    def create(self, vals_list):
        odometers = super().create(vals_list)
        for odometer in odometers:
            odometer.vehicle_id._update_equipment_usage(odometer.value)
        return odometers

    def write(self, vals):
        res = super().write(vals)
        if 'value' in vals:
            for odometer in self:
                odometer.vehicle_id._update_equipment_usage(vals['value'])
        return res

    # Helper method on vehicle to update equipment
    def _update_equipment_usage(self, value):
        # This method should be on fleet.vehicle, but called from here.
        # Wait, I can't define it here. I'll define it in FleetVehicle above.
        pass

# Extending FleetVehicle again to add the helper method properly
class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    def _update_equipment_usage(self, odometer_value):
        if self.equipment_id:
            # Assuming 'effective_date' is used for usage or we add a custom field.
            # The requirement says: "Update a custom field or the standard usage field".
            # Standard 'effective_date' is a date field, not usage.
            # 'maintenance.equipment' doesn't have a standard 'usage' field for mileage.
            # I will check if I should add one to equipment.
            # For now, I will assume I need to add 'vehicle_odometer_value' to maintenance.equipment.
            self.equipment_id.write({'vehicle_odometer_value': odometer_value})
