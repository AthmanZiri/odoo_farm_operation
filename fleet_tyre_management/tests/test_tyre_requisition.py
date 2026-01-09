from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo import fields

class TestTyreRequisition(TransactionCase):
    
    def setUp(self):
        super(TestTyreRequisition, self).setUp()
        self.Requisition = self.env['fleet.tyre.requisition']
        self.Tyre = self.env['fleet.vehicle.tyre']
        self.StockLot = self.env['stock.lot']
        self.StockLocation = self.env['stock.location']
        
        # Locations
        self.loc_stock = self.env.ref('stock.stock_location_stock')
        self.loc_output = self.env.ref('stock.stock_location_output')
        
        # Product
        self.product = self.env['product.product'].create({
            'name': 'Test Tyre Product',
            'type': 'product',
            'is_tyre': True,
        })
        
        # Tyre in Stock
        self.tyre = self.Tyre.create({
            'name': 'REQ-TYRE-001',
            'product_id': self.product.id,
            'current_tread_depth': 10.0,
            'location_id': self.loc_stock.id, # Logic should sync this, but we set initial
        })
        
        # Create Lot for Tyre (usually done via Receipt, let's manually link)
        self.lot = self.StockLot.create({
            'name': 'REQ-LOT-001',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })
        self.tyre.lot_id = self.lot
        
        # Update stock quantity
        self.env['stock.quant']._update_available_quantity(self.product, self.loc_stock, 1.0, lot_id=self.lot)

    def test_requisition_flow(self):
        """ Test Request -> Approve -> Transfer -> Location Update """
        
        # 1. Create Requisition
        req = self.Requisition.create({
            'source_location_id': self.loc_stock.id,
            'dest_location_id': self.loc_output.id,
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
            })]
        })
        
        self.assertEqual(req.state, 'draft')
        
        # 2. Submit
        req.action_submit()
        self.assertEqual(req.state, 'open')
        
        # 3. Approve
        req.action_approve()
        self.assertEqual(req.state, 'done')
        self.assertTrue(req.picking_id, "Picking should be created")
        
        # 4. Validate Transfer (Picking)
        picking = req.picking_id
        picking.action_assign()
        
        # Ensure reserved
        self.assertEqual(picking.state, 'assigned')
        
        # Set Quantity Done (Using button validate logic usually requires wizard or manual move_line update)
        for move in picking.move_ids:
            move.move_line_ids.quantity = 1.0
            move.move_line_ids.lot_id = self.lot # Select specific serial
            
        picking.button_validate()
        
        self.assertEqual(picking.state, 'done')
        
        # 5. Verify Tyre Location Update
        # The stock_move._action_done logic we added should trigger
        self.tyre.invalidate_recordset()
        self.assertEqual(self.tyre.location_id, self.loc_output)
