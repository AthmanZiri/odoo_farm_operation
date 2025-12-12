# Powered by Sensible Consulting Services
# -*- coding: utf-8 -*-
# © 2025 Sensible Consulting Services (<https://sensiblecs.com/>)
{
    'name': 'POS Credit Limit',
    'version': '19.0.1.0',
    'summary': '''define a credit limit for each customer directly from their contact record''',
    'description': '''Sensible POS Credit Limit
        Credit Limit for Customers
            You can define a credit limit for each customer directly from their contact record in Odoo.
            This credit limit restricts the total amount a customer can charge at the POS, ensuring they do not exceed the agreed-upon amount.
        POS Validation
            When processing transactions in the POS interface, the system checks if the customer has exceeded their credit limit.
            If the customer tries to make a purchase that exceeds the available credit, a warning or blocking message is displayed, preventing the sale from going through.
    ''',
    'category': 'Sales/Point of Sale',
    'author': 'Sensible Consulting Services',
    'website': 'https://sensiblecs.com',
    'license': 'AGPL-3',
    'depends': ['pos_sale'],
    'data': [
        'views/sbl_view_account_journal_view.xml',
        'views/sbl_res_partner_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'sensible_pos_credit_limit/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
}
