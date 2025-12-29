{
    'name': 'Fleet Tyre Management',
    'version': '1.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Manage tyre lifecycle for fleet vehicles',
    'author': 'Athman Ziri',
    'description': """
        Tyre Management System
        ======================
        Track tyre lifecycle from procurement to disposal.
        - RFID Tagging
        - Tread Depth Monitoring
        - Mounting/Dismounting History
        - Stock Integration
    """,
    'depends': ['fleet', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/tyre_operation_wizard_views.xml',
        'views/fleet_tyre_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/product_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_move_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
