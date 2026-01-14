{
    'name': 'Stock Move Batch Process',
    'version': '19.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Batch confirm and issue stock moves from list view',
    'description': """
        This module adds a server action to the stock.move list view
        allowing users to select multiple "To Do" items and confirm or issue them in batch.
    """,
    'author': 'Antigravity',
    'depends': ['stock'],
    'data': [
        'views/stock_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
