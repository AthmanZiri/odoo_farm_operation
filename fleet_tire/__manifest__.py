{
    'name': 'Fleet Tire Management',
    'version': '1.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Manage tire lifecycle for fleet vehicles',
    'description': """
        Tire Management System
        ======================
        Track tire lifecycle from procurement to disposal.
        - RFID Tagging
        - Tread Depth Monitoring
        - Mounting/Dismounting History
        - Stock Integration
    """,
    'depends': ['fleet', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/tire_operation_wizard_views.xml',
        'views/fleet_tire_views.xml',
        'views/fleet_vehicle_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
