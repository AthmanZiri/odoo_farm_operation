from odoo.tests import common, tagged

@tagged('post_install', '-at_install')
class TestFleetEquipmentLink(common.TransactionCase):

    def test_vehicle_creation_creates_equipment(self):
        """ Test that creating a vehicle creates a corresponding equipment """
        # Create a vehicle
        vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'}).id}).id,
            'license_plate': 'TEST-123',
        })

        # Check that equipment is created
        self.assertTrue(vehicle.equipment_id, "Equipment should be created for vehicle")
        self.assertEqual(vehicle.equipment_id.name, "Test Model - TEST-123", "Equipment name should match vehicle")
        self.assertEqual(vehicle.equipment_id.vehicle_id, vehicle, "Equipment should function link back to vehicle")
        self.assertEqual(vehicle.equipment_id.category_id.name, "Vehicles", "Equipment category should be 'Vehicles'")
