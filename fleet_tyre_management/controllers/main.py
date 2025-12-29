from odoo import http, fields
from odoo.http import request
import json

class FleettyreController(http.Controller):

    @http.route('/tyre/gate_scan', type='json', auth='public', methods=['POST'], csrf=False)
    def gate_scan(self, **post):
        """
        Receives JSON payload:
        {
            "rfid_tag": "TAG123",
            "odometer": 12345.6,
            "gate_id": "Gate-A", 
            "timestamp": "2023-10-10 10:00:00"
        }
        """
        data = request.jsonrequest
        rfid_tag = data.get('rfid_tag')
        odometer = data.get('odometer')
        
        if not rfid_tag:
            return {'status': 'error', 'message': 'RFID Tag is required'}
            
        tyre = request.env['fleet.vehicle.tyre'].sudo().search([('rfid_tag', '=', rfid_tag)], limit=1)
        if not tyre:
            return {'status': 'error', 'message': 'tyre not found'}

        # Create History Record (Gate Check)
        vals = {
            'tyre_id': tyre.id,
            'type': 'gate_check',
            'date': fields.Date.today(),
            'odometer': float(odometer) if odometer else tyre.history_ids and tyre.history_ids[0].odometer or 0.0,
            'note': f"Gate Scan at {data.get('gate_id', 'Unknown Gate')}",
            'vehicle_id': tyre.vehicle_id.id if tyre.vehicle_id else False
        }
        
        request.env['fleet.vehicle.tyre.history'].sudo().create(vals)
        
        return {'status': 'success', 'tyre': tyre.name}
