from odoo.tests import common, tagged
from odoo import fields

class TestRFIDPersistentGate(common.TransactionCase):

    def setUp(self):
        super(TestRFIDPersistentGate, self).setUp()
        
        # 1. Create Vehicle
        brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Audi'})
        model = self.env['fleet.vehicle.model'].create({'name': 'A4', 'brand_id': brand.id})
        self.vehicle = self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'TEST-888',
            'odometer': 10000.0,
        })
        
        # 2. Create and Mount Tyres
        product = self.env['product.product'].create({'name': 'Test Tyre Product', 'type': 'consu'})
        self.tyre1 = self.env['fleet.vehicle.tyre'].create({
            'name': 'P-TYRE-001',
            'rfid_tag': 'PTAG001',
            'product_id': product.id,
            'current_tread_depth': 10.0
        })
        self.tyre2 = self.env['fleet.vehicle.tyre'].create({
            'name': 'P-TYRE-002',
            'rfid_tag': 'PTAG002',
            'product_id': product.id,
            'current_tread_depth': 10.0
        })
        
        # Mount them
        self.tyre1.write({'state': 'mounted', 'vehicle_id': self.vehicle.id})
        self.tyre2.write({'state': 'mounted', 'vehicle_id': self.vehicle.id})

    def test_gate_check_model_flow(self):
        """ Test creating a Gate Check via the new persistent model """
        
        # 1. Create Draft Gate Check
        gate_check = self.env['fleet.tyre.gate.check'].create({
            'vehicle_id': self.vehicle.id,
            # gate_scan_type should be auto-computed but we set user_id etc
        })
        
        # 2. Verify Onchange (Lines Populated)
        gate_check._onchange_vehicle_id()
        self.assertEqual(len(gate_check.line_ids), 2, "Should populate 2 tyre lines")
        self.assertEqual(gate_check.gate_scan_type, 'check_in', "Default should be check_in")
        
        # 3. Modify Lines (Simulate User Input)
        line1 = gate_check.line_ids.filtered(lambda l: l.tyre_id == self.tyre1)
        line1.new_tread_depth = 8.5
        line1.odometer = 10500.0
        
        # 4. Confirm
        gate_check.action_confirm()
        
        # 5. Verify State
        self.assertEqual(gate_check.state, 'done')
        
        # 6. Verify Tyre History Created
        history = self.env['fleet.vehicle.tyre.history'].search([
            ('tyre_id', '=', self.tyre1.id),
            ('type', '=', 'gate_check')
        ], order='id desc', limit=1)
        
        self.assertTrue(history, "History record should be created")
        self.assertEqual(history.tread_depth, 8.5)
        self.assertEqual(history.odometer, 10500.0)
        self.assertEqual(history.gate_scan_type, 'check_in')
        
        # 7. Verify Tyre Logic Updated
        self.assertEqual(self.tyre1.current_tread_depth, 8.5, "Tyre master data should be updated")

    def test_auto_toggle_logic(self):
        """ Test that creating a second gate check flips the type """
        
        # Check In
        gc1 = self.env['fleet.tyre.gate.check'].create({
            'vehicle_id': self.vehicle.id,
            'gate_scan_type': 'check_in',
            'state': 'done' # Manually set to done or run confirm
        })
        
        # Create second check
        gc2 = self.env['fleet.tyre.gate.check'].create({
            'vehicle_id': self.vehicle.id,
        })
        gc2._onchange_vehicle_id()
        
        self.assertEqual(gc2.gate_scan_type, 'check_out', "Should auto-toggle to check_out")
