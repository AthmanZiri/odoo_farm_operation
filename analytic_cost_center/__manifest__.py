{
    'name': 'Analytic Cost Center Integration',
    'version': '1.0',
    'category': 'Operations',
    'summary': 'Link Vehicles and Equipment to Analytic Accounts for Cost Tracking',
    'author': 'Antigravity',
    'depends': [
        'fleet', 
        'stock', 
        'analytic', 
        'maintenance', 
        'fleet_vehicle_log_fuel', 
        'stock_fleet_allocation'
    ],
    'data': [
        'data/stock_location_data.xml',
        'views/fleet_vehicle_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/stock_picking_views.xml',
        'views/fleet_vehicle_log_fuel_views.xml',
        'views/fleet_service_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
