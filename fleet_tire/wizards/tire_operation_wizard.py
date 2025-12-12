from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleetTireOperationWizard(models.TransientModel):
    _name = 'fleet.tire.operation.wizard'
    _description = 'Tire Operation Wizard'

    tire_id = fields.Many2one('fleet.vehicle.tire', string='Tire', required=True)
    operation_type = fields.Selection([
        ('mount', 'Mount on Vehicle'),
        ('dismount', 'Dismount from Vehicle'),
        ('inspection', 'Inspection Update'),
        ('repair', 'Send to Repair'),
        ('retread', 'Send to Retread'),
        ('return_stock', 'Return to Stock'),
        ('dispose', 'Dispose')
    ], string='Operation', required=True)
    
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    position = fields.Selection([
        ('fl', 'Front Left'),
        ('fr', 'Front Right'),
        ('rl', 'Rear Left'),
        ('rr', 'Rear Right'),
        ('spare', 'Spare'),
        ('other', 'Other')
    ], string='Position')
    
    destination_location_id = fields.Many2one('stock.location', string='Destination Location', domain=[('usage', '=', 'internal')])
    
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    odometer = fields.Float(string='Odometer Reading')
    tread_depth = fields.Float(string='Tread Depth (mm)')
    note = fields.Text(string='Notes')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            tire = self.env['fleet.vehicle.tire'].browse(self.env.context['active_id'])
            res['tire_id'] = tire.id
            if tire.vehicle_id:
                res['vehicle_id'] = tire.vehicle_id.id
            # Auto-select logical operation
            if tire.state == 'available':
                res['operation_type'] = 'mount'
            elif tire.state == 'mounted':
                res['operation_type'] = 'dismount'
        return res

    def action_apply(self):
        self.ensure_one()
        tire = self.tire_id
        
        # History Data
        history_vals = {
            'tire_id': tire.id,
            'date': self.date,
            'type': self.operation_type,
            'vehicle_id': self.vehicle_id.id or tire.vehicle_id.id,
            'odometer': self.odometer,
            'tread_depth': self.tread_depth,
            'note': self.note,
        }

        if self.operation_type == 'mount':
            if not self.vehicle_id or not self.position:
                raise UserError(_("Vehicle and Position are required for mounting."))
            tire.write({
                'state': 'mounted',
                'vehicle_id': self.vehicle_id.id,
                'position': self.position,
                'location_id': False,
            })
        
        elif self.operation_type == 'dismount':
            tire.write({
                'state': 'available',
                'vehicle_id': False,
                'position': False,
                'current_tread_depth': self.tread_depth or tire.current_tread_depth,
                'location_id': self.destination_location_id.id if self.destination_location_id else False,
            })
            
        elif self.operation_type == 'inspection':
            if self.tread_depth:
                tire.write({'current_tread_depth': self.tread_depth})
                
        elif self.operation_type == 'repair':
            tire.write({'state': 'repair', 'vehicle_id': False, 'position': False, 'location_id': False})
            
        elif self.operation_type == 'retread':
            tire.write({'state': 'retread', 'vehicle_id': False, 'position': False, 'location_id': False})
            
        elif self.operation_type == 'return_stock':
            tire.write({'state': 'available', 'location_id': self.destination_location_id.id})
            
        elif self.operation_type == 'dispose':
            tire.write({'state': 'scrap', 'vehicle_id': False, 'position': False, 'location_id': False})

        self.env['fleet.vehicle.tire.history'].create(history_vals)
        return {'type': 'ir.actions.act_window_close'}
