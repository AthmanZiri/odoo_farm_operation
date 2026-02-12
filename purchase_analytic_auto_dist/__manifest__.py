{
    'name': 'Purchase Order Analytic Auto-Distribution',
    'version': '1.0',
    'category': 'Inventory/Purchase',
    'summary': 'Auto-populate analytic distribution 100% when an analytic account is selected on PO lines',
    'author': 'Antigravity',
    'depends': ['purchase', 'analytic'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
