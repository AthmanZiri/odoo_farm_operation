{
    'name': 'Stock Inventory Loss Product Expense',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Accounting',
    'summary': 'Use product expense accounts on inventory loss transfers',
    'description': """
        When stock is moved to an inventory loss location, replace the
        location loss account on journal entry debit lines with the product
        expense account (or the product category expense account as fallback).
    """,
    'author': 'Madrugada Farm',
    'depends': ['stock_account'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
