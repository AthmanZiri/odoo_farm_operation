{
    'name': 'Stock Transfer to PO',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Generate Purchase Orders from Internal Transfer Shortages',
    'description': """
        This module allows users to generate Purchase Orders directly from Internal Transfers (stock.picking).
        It identifies products with shortages (waiting or partially available) and groups them by vendor in a wizard before creating POs.
    """,
    'author': 'Antigravity',
    'depends': ['stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_transfer_po_wizard_views.xml',
        'views/stock_picking_views.xml',
        'data/ir_sequence_data.xml',
        'views/stock_purchase_request_views.xml',
        'views/stock_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
