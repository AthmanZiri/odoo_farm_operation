{
    'name': 'Product Bulk Image Import',
    'version': '19.0.1.0.0',
    'summary': 'Import product images in bulk from a ZIP file',
    'description': """
        This module allows users to upload a ZIP file containing product images.
        Images are matched to products based on the filename (Internal Reference).
        - Matches 'CODE.jpg' to product with default_code 'CODE'.
        - Matches 'CODE_1.jpg' to product with default_code 'CODE' (adds as extra image).
    """,
    'category': 'Inventory/Inventory',
    'author': 'JengaSol',
    'depends': ['base', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/import_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
