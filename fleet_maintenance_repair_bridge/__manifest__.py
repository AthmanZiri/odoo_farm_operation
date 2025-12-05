{
    'name': 'Fleet Maintenance & Repair Bridge',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Bridge between Fleet, Maintenance, and Repair apps',
    'description': """
        This module bridges the gap between Fleet, Maintenance, and Repair applications.
        - Treats Fleet Vehicles as Maintenance Equipment.
        - Synchronizes Vehicle Odometer with Equipment Usage.
        - Allows creating Repair Orders directly from Maintenance Requests.
    """,
    'author': 'Antigravity',
    'depends': ['fleet', 'maintenance', 'repair', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle_views.xml',
        'views/fleet_vehicle_log_services_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_request_views.xml',
        'views/repair_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
