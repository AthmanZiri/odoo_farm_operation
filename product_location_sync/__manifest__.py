{
    'name': 'Product Location Sync',
    'version': '19.0.1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Display stock locations on Product form',
    'description': """
        This module adds a 'Location' field to the Product form view (product.template),
        showing the internal locations where the product (or its variants) are currently in stock.
    """,
    'depends': ['stock', 'product'],
    'data': [
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
