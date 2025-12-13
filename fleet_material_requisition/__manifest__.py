{
    'name': 'Fleet Material Requisition',
    'version': '1.0',
    'category': 'Operations/Fleet',
    'summary': 'Create Material Requisitions (Internal Transfers) from Fleet Services',
    'description': """
        This module allows users to create material requisitions (Internal Stock Transfers) directly from the Fleet Service form.
        It links Fleet Services with Stock Pickings.
    """,
    'depends': ['fleet', 'stock'],
    'data': [
        'views/stock_picking_views.xml',
        'views/fleet_vehicle_log_services_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
