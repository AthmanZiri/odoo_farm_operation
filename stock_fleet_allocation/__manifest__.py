{
    'name': 'Stock Fleet Allocation',
    'version': '1.0',
    'category': 'Inventory/Fleet',
    'summary': 'Allocate Stock Pickings to Fleet Vehicles or Maintenance Equipment',
    'description': """
        This module allows users to allocate Stock Pickings (Internal Requisitions) to Fleet Vehicles or Maintenance Equipment.
        Upon validation, it automatically creates a Fleet Service log.
    """,
    'author': 'Athman Ziri',
    'depends': ['stock', 'fleet', 'maintenance', 'fleet_material_requisition'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
