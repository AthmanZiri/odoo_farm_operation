{
    'name': 'Product Pack & Dynamic Transfer Management',
    'version': '19.0.1.0.0',
    'summary': 'Manage product packs and dynamic transfers (explode/unit)',
    'description': """
        This module allows defining "Pack" products.
        Features:
        - Define Pack components in Product Template.
        - Support for Internal Transfers:
            - Move as a single unit (Pack).
            - Explode into components (cancel pack line, create component lines).
        - Pack Availability calculation.
        - Pack Price calculation.
    """,
    'author': 'Jengasol',
    'category': 'Inventory/Stock',
    'depends': ['stock', 'sale_management', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/stock_picking_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
