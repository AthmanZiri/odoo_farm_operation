from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleettyreOperationWizard(models.TransientModel):
    _name = 'fleet.tyre.operation.wizard'
    _description = 'tyre Operation Wizard'

    tyre_id = fields.Many2one('fleet.vehicle.tyre', string='tyre', required=True)
    operation_type = fields.Selection([
        ('mount', 'Mount on Vehicle'),
        ('dismount', 'Dismount from Vehicle'),
        ('inspection', 'Inspection Update'),
        ('gate_check', 'Gate Check'),
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
    
    cost = fields.Float(string='Cost')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    reason = fields.Char(string='Reason')
    method = fields.Selection([
        ('patch', 'Patch'),
        ('plug', 'Plug'),
        ('retread_cold', 'Cold Retread'),
        ('retread_hot', 'Hot Retread'),
        ('scrap', 'Scrap'),
        ('sell', 'Sell'),
        ('other', 'Other')
    ], string='Method')
    
    gate_scan_type = fields.Selection([
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out')
    ], string='Gate Scan Type')

    def _get_vehicle_location(self, vehicle):
        """ Get or create a specific location for the vehicle """
        parent = self.env['stock.location'].sudo().search([('name', '=', 'Fleet/Vehicles')], limit=1)
        if not parent:
            parent = self.env['stock.location'].sudo().create({
                'name': 'Fleet/Vehicles',
                'usage': 'view',
                'location_id': self.env.ref('stock.stock_location_locations').id
            })
        
        name = vehicle.name
        loc = self.env['stock.location'].sudo().search([('name', '=', name), ('location_id', '=', parent.id)], limit=1)
        if not loc:
            loc = self.env['stock.location'].sudo().create({
                'name': name,
                'usage': 'internal',
                'location_id': parent.id
            })
        return loc
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            tyre = self.env['fleet.vehicle.tyre'].browse(self.env.context['active_id'])
            res['tyre_id'] = tyre.id
            if tyre.vehicle_id:
                res['vehicle_id'] = tyre.vehicle_id.id
            # Auto-select logical operation
            if tyre.state == 'available':
                res['operation_type'] = 'mount'
            elif tyre.state == 'mounted':
                res['operation_type'] = 'dismount'
        return res

    def action_apply(self):
        self.ensure_one()
        tyre = self.tyre_id
        
        # History Data
        history_vals = {
            'tyre_id': tyre.id,
            'date': self.date,
            'type': self.operation_type,
            'gate_scan_type': self.gate_scan_type,
            'vehicle_id': self.vehicle_id.id or tyre.vehicle_id.id,
            'odometer': self.odometer,
            'tread_depth': self.tread_depth,
            'note': self.note,
            'cost': self.cost,
            'vendor_id': self.vendor_id.id,
            'reason': self.reason,
            'method': self.method,
        }

        # Stock Move Logic
        source_loc = tyre.lot_id.location_id
        dest_loc = False
        
        if self.operation_type == 'mount':
            if not self.vehicle_id or not self.position:
                raise UserError(_("Vehicle and Position are required for mounting."))
            dest_loc = self._get_vehicle_location(self.vehicle_id)
            tyre.write({
                'state': 'mounted',
                'vehicle_id': self.vehicle_id.id,
                'position': self.position,
                'location_id': False,
            })
        
        elif self.operation_type == 'dismount':
            dest_loc = self.destination_location_id or self.env.ref('stock.stock_location_stock')
            tyre.write({
                'state': 'available',
                'vehicle_id': False,
                'position': False,
                'current_tread_depth': self.tread_depth or tyre.current_tread_depth,
                'location_id': dest_loc.id,
            })
            
        elif self.operation_type == 'gate_check':
            # Just recording a checkpoint. 
            pass

        elif self.operation_type == 'inspection':
            if self.tread_depth:
                tyre.write({'current_tread_depth': self.tread_depth})
                
        elif self.operation_type == 'repair':
            if self.vendor_id:
                # Typically moves to a 'Repair' or 'Supplier' location
                dest_loc = self.vendor_id.property_stock_customer or self.env.ref('stock.stock_location_customers')
            tyre.write({'state': 'repair', 'vehicle_id': False, 'position': False, 'location_id': False})
            
        elif self.operation_type == 'retread':
            if self.vendor_id:
                dest_loc = self.vendor_id.property_stock_customer or self.env.ref('stock.stock_location_customers')
            tyre.write({
                'state': 'retread', 
                'vehicle_id': False, 
                'position': False, 
                'location_id': False,
                'retread_count': tyre.retread_count + 1
            })
            
        elif self.operation_type == 'return_stock':
            dest_loc = self.destination_location_id or self.env.ref('stock.stock_location_stock')
            tyre.write({'state': 'available', 'location_id': dest_loc.id})
            
        elif self.operation_type == 'dispose':
            dest_loc = self.env.ref('stock.stock_location_scrapped')
            tyre.write({
                'state': 'scrap', 
                'vehicle_id': False, 
                'position': False, 
                'location_id': False,
                'disposal_reason': self.reason,
                'disposal_date': self.date,
            })

        if dest_loc and source_loc and source_loc != dest_loc:
            # Create Stock Move
            move = self.env['stock.move'].create({
                'name': f"Tyre {tyre.name}: {self.operation_type}",
                'product_id': tyre.product_id.id,
                'product_uom_qty': 1,
                'product_uom': tyre.product_id.uom_id.id,
                'location_id': source_loc.id,
                'location_dest_id': dest_loc.id,
                'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1).id,
            })
            move._action_confirm()
            move._action_assign()
            # Set lot
            for line in move.move_line_ids:
                line.lot_id = tyre.lot_id.id
                line.quantity = 1
            move._action_done()

        self.env['fleet.vehicle.tyre.history'].create(history_vals)
        return {'type': 'ir.actions.act_window_close'}

