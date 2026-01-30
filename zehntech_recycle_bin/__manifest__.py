{
    'name': 'Recycle Bin',
    "version": '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'The Recycle Bin app for Odoo allows you to safely recover accidentally deleted records. It features customizable retention periods, role-based access control, and audit logs for enhanced data security and management.',
    'description': """The Recycle Bin module temporarily stores deleted records for recovery, with customizable retention periods. It includes role-based access control, allowing Super Admins to assign permissions. A centralized interface helps manage deleted items, while audit logs ensure transparency. Users can restore or permanently delete records, providing a secure, efficient, and accountable way to handle data deletions.""",
    "author": "Zehntech Technologies Inc.",
    "company": "Zehntech Technologies Inc.",
    "maintainer": "Zehntech Technologies Inc.",
    "contributor": "Zehntech Technologies Inc.",
    "website": "https://www.zehntech.com/",
    "support": "odoo-support@zehntech.com",
    "depends": [  'sale_management', 'contacts','base','web'],
    'data': [
        'security/group_rule.xml',
        'security/ir.model.access.csv',
        'views/recycle_bin_view.xml',
        'data/scheduledaction.xml',
        'data/demo_user.xml',
        'views/recycle_bin_menu.xml',
        'views/setting_view.xml',
        'views/audit_log_view.xml',
        'views/audit_log_menu.xml',
    ],

    'assets': {
    'web.assets_backend': [
        'zehntech_recycle_bin/static/src/js/recycle_bin_notification.js',
        'zehntech_recycle_bin/static/src/js/custom_notification.js',
        ],
    },
    'i18n': [
        'i18n/de.po',    # German translation file
        'i18n/es.po',      # Spanish translation file
        'i18n/fr.po',   # French translation file
        'i18n/ja_JP.po',   # Japanese translation file
    ],
    
    "images": [
            "static/description/banner.gif",
        ],
   
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 0.00,
    'currency': 'USD'
}

