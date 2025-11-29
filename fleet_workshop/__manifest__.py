{
    'name': 'Fleet Workshop & Inventory Management',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Manage internal garage, job cards, inventory, and fueling',
    'description': """
        This module adds a workshop management workflow to the Fleet module.
        - Job Cards for repairs and maintenance
        - Integration with Inventory for parts consumption
        - Fueling logs linked to inventory
        - Service scheduling based on odometer
    """,
    'depends': ['fleet', 'stock', 'hr', 'hr_work_entry'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/fleet_work_order_line_views.xml',
        'views/fleet_work_order_views.xml',
        'views/fleet_fuel_log_views.xml',
        'views/fleet_vehicle_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
