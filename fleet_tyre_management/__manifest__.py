{
    'name': 'Tyre Management',
    'version': '1.1',
    'category': 'Human Resources/Fleet',
    'summary': 'Unified Tyre Lifecycle Management',
    'author': 'Athman Ziri',
    'description': """
        Unified Tyre Management System
        ==============================
        Track tyre lifecycle from procurement to disposal in a single hub.
        - Specialized Procurement & Receipt Views
        - RFID & Tread Depth Monitoring
        - Master Data Management (Brands, Products)
        - Inventory Configuration (Warehouse, Locations)
        - Analytical Reporting Dashboards (CPK, Tread Wear)
    """,
    'depends': ['fleet', 'stock', 'purchase', 'board'],
    'data': [
        'security/ir.model.access.csv',
        'data/fleet_axle_config_data.xml',
        'wizards/tyre_operation_wizard_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_tyre_views.xml',
        'views/fleet_axle_config_views.xml',
        'views/fleet_tyre_report_views.xml',
        'views/fleet_tyre_dashboard.xml',
        'views/product_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_move_line_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fleet_tyre_management/static/src/css/tyre_layout_widget.css',
            'fleet_tyre_management/static/src/js/tyre_layout_widget.js',
            'fleet_tyre_management/static/src/xml/tyre_layout_widget.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
