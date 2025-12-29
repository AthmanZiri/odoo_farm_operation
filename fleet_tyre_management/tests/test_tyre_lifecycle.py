from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo import fields

class TestFleettyre(TransactionCase):
    
    def setUp(self):
        super(TestFleettyre, self).setUp()
        self.tyre = self.env['fleet.vehicle.tyre']
        self.Wizard = self.env['fleet.tyre.operation.wizard']
        self.Vehicle = self.env['fleet.vehicle']
        
        # Create Dummy Product
        self.product = self.env['product.product'].create({
            'name': 'Test tyre 265/65',
            'type': 'product',
            'standard_price': 100.0,
        })
        
        # Create Vehicle
        self.vehicle = self.Vehicle.create({
            'model_id': self.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': self.env['fleet.vehicle.model.brand'].create({'name': 'Toyota'}).id}).id,
            'license_plate': 'KAA 123A',
        })
        
        # Create tyre
        self.tyre = self.tyre.create({
            'name': 'tyre001',
            'product_id': self.product.id,
            'initial_tread_depth': 10.0,
            'current_tread_depth': 10.0,
        })

    def test_lifecycle_flow(self):
        """ Test full lifecycle: Mount -> Dismount -> Repair -> Retread -> Dispose """
        
        # 1. Mount
        wizard = self.Wizard.with_context(active_id=self.tyre.id).create({
            'tyre_id': self.tyre.id,
            'operation_type': 'mount',
            'vehicle_id': self.vehicle.id,
            'position': 'fl',
            'date': fields.Date.today(),
            'odometer': 1000.0,
        })
        wizard.action_apply()
        
        self.assertEqual(self.tyre.state, 'mounted')
        self.assertEqual(self.tyre.vehicle_id, self.vehicle)
        self.assertEqual(self.tyre.position, 'fl')
        
        # 2. Gate Check (Add kms)
        wizard_gate = self.Wizard.with_context(active_id=self.tyre.id).create({
            'tyre_id': self.tyre.id,
            'operation_type': 'gate_check',
            'gate_scan_type': 'check_out',
            'odometer': 1500.0,
        })
        wizard_gate.action_apply()

        
        # 3. Dismount
        wizard_dismount = self.Wizard.with_context(active_id=self.tyre.id).create({
            'tyre_id': self.tyre.id,
            'operation_type': 'dismount',
            'odometer': 2000.0,
            'tread_depth': 8.0,
        })
        wizard_dismount.action_apply()
        
        self.assertEqual(self.tyre.state, 'available')
        self.assertEqual(self.tyre.current_tread_depth, 8.0)
        self.assertEqual(self.tyre.total_kms, 1000.0) # (1500-1000) + (2000-1500) = 500+500 = 1000
        
        # 4. Retread
        self.assertEqual(self.tyre.retread_count, 0)
        wizard_retread = self.Wizard.with_context(active_id=self.tyre.id).create({
            'tyre_id': self.tyre.id,
            'operation_type': 'retread',
            'cost': 50.0,
        })
        wizard_retread.action_apply()
        
        self.assertEqual(self.tyre.state, 'retread')
        self.assertEqual(self.tyre.retread_count, 1)
        
        # 5. Dispose
        wizard_dispose = self.Wizard.with_context(active_id=self.tyre.id).create({
            'tyre_id': self.tyre.id,
            'operation_type': 'dispose',
            'reason': 'Worn out',
        })
        wizard_dispose.action_apply()
        
        self.assertEqual(self.tyre.state, 'scrap')
        self.assertEqual(self.tyre.disposal_reason, 'Worn out')

    def test_cpk_calculation(self):
        """ Test Cost Per Kilometer Calculation """
        # Initial Cost = 100
        
        # Mount at 1000km
        self.Wizard.create({
            'tyre_id': self.tyre.id,
            'operation_type': 'mount',
            'vehicle_id': self.vehicle.id,
            'position': 'fl',
            'odometer': 1000.0,
        }).action_apply()
        
        # Dismount at 2000km
        self.Wizard.create({
            'tyre_id': self.tyre.id,
            'operation_type': 'dismount',
            'odometer': 2000.0,
        }).action_apply()
        
        # Total KMs = 1000
        # Total Cost = 100 (Purchase)
        # CPK = 100 / 1000 = 0.1
        
        self.tyre._compute_total_kms()
        self.tyre._compute_cpk()
        self.assertEqual(self.tyre.total_kms, 1000.0)
        self.assertAlmostEqual(self.tyre.cpk, 0.1)
        
        # Add Repair Cost
        self.Wizard.create({
            'tyre_id': self.tyre.id,
            'operation_type': 'repair',
            'cost': 20.0
        }).action_apply()
        
        # Total Cost = 100 + 20 = 120
        # CPK = 120 / 1000 = 0.12
        self.tyre._compute_cpk() # retrigger
        self.assertAlmostEqual(self.tyre.cpk, 0.12)
