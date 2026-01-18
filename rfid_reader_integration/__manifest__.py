{
    'name': 'UHF RFID Reader Integration',
    'version': '1.0',
    'category': 'Inventory/IoT',
    'summary': 'Integrates ST-8504 E710 UHF RFID Readers with Odoo',
    'description': """
        This module allows configuration of UHF RFID readers and provides 
        an XML-RPC interface for the Python SDK to push tag scans directly into Odoo.
        
        The Python SDK scripts and manual are included in the 'scripts/python_sdk' folder.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/rfid_reader_views.xml',
        'views/rfid_tag_scan_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
