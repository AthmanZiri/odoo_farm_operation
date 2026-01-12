from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError

@tagged('post_install', '-at_install')
class TestStockPurchaseRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'seller_ids': [(0, 0, {'partner_id': cls.vendor.id, 'price': 10.0})],
        })
        cls.picking_type = cls.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

    def test_create_request_from_move(self):
        # Create a move
        move = cls.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': cls.product.id,
            'product_uom_qty': 10,
            'product_uom': cls.product.uom_id.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.stock_location.id, # Internal transfer
            'picking_type_id': cls.picking_type.id,
        })
        move._action_confirm()
        
        # Simulate wizard action
        wizard = cls.env['stock.transfer.po.wizard'].with_context(
            active_model='stock.move',
            active_ids=[move.id]
        ).create({})
        # Trigger default_get logic by reading or re-creating with values if needed, 
        # but create() calls default_get automatically.
        # Check if lines populate
        
        # Wait, create() calls default_get but existing values override. 
        # We need to rely on default_get return or manually call it to simulate frontend
        defaults = cls.env['stock.transfer.po.wizard'].default_get(['line_ids'])
        # Only works if active_ids in context
        
        wizard = cls.env['stock.transfer.po.wizard'].with_context(
            active_model='stock.move',
            active_ids=[move.id]
        ).create({})
        # The wizard's default_get should have populated line_ids
        
        # Actually create() doesn't auto-populate One2many from default_get unless specified in view or context? 
        # In Odoo backend, default_get is called by the client.
        # So let's call default_get explicitly
        res = wizard.default_get(['line_ids'])
        wizard.line_ids = res.get('line_ids', [])
        
        self.assertTrue(wizard.line_ids, "Wizard should have lines")
        self.assertEqual(wizard.line_ids.product_id, cls.product)
        self.assertEqual(wizard.line_ids.quantity, 10.0) # Shortage is full amount as qs=0
        
        # Create Request
        action = wizard.action_create_po()
        request_id = action['res_id']
        request = cls.env['stock.purchase.request'].browse(request_id)
        
        self.assertEqual(request.state, 'submitted')
        self.assertEqual(len(request.line_ids), 1)
        
        # Approve Request
        request.action_approve()
        self.assertEqual(request.state, 'approved')
        self.assertTrue(request.purchase_order_ids)
        po = request.purchase_order_ids[0]
        self.assertEqual(po.partner_id, cls.vendor)
        self.assertEqual(po.request_id, request)

