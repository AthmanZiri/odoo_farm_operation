# -*- coding: utf-8 -*-
{
    'name': 'Maintenance Worksheet Templates',
    'version': '1.0',
    'category': 'Maintenance',
    'summary': 'Preloaded Maintenance Worksheets for John Deere 8230',
    'description': """
        This module provides preconfigured maintenance worksheet templates for John Deere 8230 tractors.
        It includes checklists for various service intervals (250h, 500h, 750h, 1500h, 2000h, 4500h).
    """,
    'depends': ['maintenance', 'maintenance_worksheet'],
    'data': [
        'data/maintenance_worksheet_jd_8230_data.xml',
        'data/maintenance_worksheet_jd_s660_data.xml',
        'data/maintenance_worksheet_bateman_rb15_data.xml',
        'data/maintenance_worksheet_isuzu_data.xml',
        'data/maintenance_worksheet_motorbike_data.xml',
        'data/maintenance_worksheet_jd_5075_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}
