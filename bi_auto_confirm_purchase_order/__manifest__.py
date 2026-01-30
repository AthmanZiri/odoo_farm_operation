# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': "Auto Confirm Purchase Orders | Mass Validate PO | Auto Process Purchase Orders",
    'version': '19.0.0.0',
    'category': 'Purchases',
    'summary': "auto process PO automation mass PO confirmation mass confirm purchase quick validate po quick confirm po bulk confirmation bulk purchase order validation of bulk po One click confirm po Auto confirm purchase receipt Auto confirm bill auto confirm transfer",
    'description': """Auto Confirm Purchase Orders Odoo App is designed to simplifies and automates the entire purchase workflow, eliminating manual intervention and ensuring a smooth procurement workflow. This odoo module enhances operational efficiency by automatically confirms the purchase order, validates the receipt, and processes the vendor bill by validating and marking it as paid—completing the full purchase cycle instantly. The app also supports bulk actions, allowing users to confirm and process multiple purchase orders at once, making it perfect for high-volume procurement operations. This automation minimizes the risk of human error, speeds up the supply chain process, and ensures timely communication with vendors.""",
    'author': "BROWSEINFO",
    'website': 'https://www.browseinfo.com/demo-request?app=bi_auto_confirm_purchase_order&version=19&edition=Community',
    'depends': ['base', 'purchase', 'stock'],
    'data': [
        "security/ir.model.access.csv",
        "wizard/auto_confirm_purchase_wizard_view.xml",
        "views/purchase_order_server_action_view.xml",
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://www.browseinfo.com/demo-request?app=bi_auto_confirm_purchase_order&version=19&edition=Community',
    "images": ['static/description/Auto-confirm-Purchase-order.gif'],
}

