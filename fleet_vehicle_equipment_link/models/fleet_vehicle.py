from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    equipment_id = fields.Many2one('maintenance.equipment', string='Maintenance Equipment', readonly=True, help="The equipment linked to this vehicle.")

    @api.model_create_multi
    def create(self, vals_list):
        vehicles = super(FleetVehicle, self).create(vals_list)
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

    def action_view_equipment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment',
            'res_model': 'maintenance.equipment',
            'view_mode': 'form',
            'res_id': self.equipment_id.id,
        }
