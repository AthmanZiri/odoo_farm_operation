{
    'name': 'Product Image Hover',
    'version': '1.0',
    'category': 'Product',
    'summary': 'Enlarge product image on hover in Kanban view',
    'description': """
        This module adds a hover effect to product images in the Kanban view,
        enlarging them for better visibility.
    """,
    'depends': ['web', 'product'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'product_image_hover/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
