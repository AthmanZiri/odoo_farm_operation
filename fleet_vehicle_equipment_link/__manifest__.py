{
    'name': 'Fleet Vehicle Equipment Link',
    'version': '1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Automatically create Maintenance Equipment from Fleet Vehicles',
    'description': """
        This module automatically creates a Maintenance Equipment record when a Fleet Vehicle is created.
        It also provides bidirectional links between the Vehicle and the Equipment.
    """,
    'author': 'Antigravity',
    'depends': ['fleet', 'maintenance'],
    'data': [
        'views/fleet_vehicle_views.xml',
        'views/maintenance_equipment_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
