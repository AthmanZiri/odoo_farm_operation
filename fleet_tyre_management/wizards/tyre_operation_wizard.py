from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleettyreOperationWizard(models.TransientModel):
    _name = 'fleet.tyre.operation.wizard'
    _description = 'Tyre Operation Wizard'

    tyre_id = fields.Many2one('fleet.vehicle.tyre', string='Tyre', required=True)
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
    vehicle_axle_config_id = fields.Many2one(related='vehicle_id.axle_config_id')
    position_id = fields.Many2one('fleet.tyre.position', string='Position', domain="[('config_id', '=', vehicle_axle_config_id)]")
    
    related_tyre_ids = fields.Many2many('fleet.vehicle.tyre', string='Other Tyres', help="Select other tyres on the same vehicle to update.")
    
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
                'location_id': self.env.ref('stock.stock_location_stock').location_id.id
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
    
    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        if self.operation_type == 'gate_check' and self.vehicle_id:
            # Auto-select other tyres on the same vehicle
            other_tyres = self.env['fleet.vehicle.tyre'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('id', '!=', self.tyre_id.id),
                ('state', '=', 'mounted')
            ])
            self.related_tyre_ids = [(6, 0, other_tyres.ids)]
        else:
            self.related_tyre_ids = [(5, 0, 0)]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Priority 1: Handle explicit context from Visual Widget
        if self.env.context.get('default_position_id'):
            res['position_id'] = self.env.context['default_position_id']
        if self.env.context.get('default_operation_type'):
            res['operation_type'] = self.env.context['default_operation_type']
        if self.env.context.get('default_tyre_id'):
            res['tyre_id'] = self.env.context['default_tyre_id']

        # Priority 2: Standard Odoo Context (Active Model)
        if self.env.context.get('active_model') == 'fleet.vehicle.tyre' and self.env.context.get('active_id'):
            tyre = self.env['fleet.vehicle.tyre'].browse(self.env.context['active_id'])
            res.setdefault('tyre_id', tyre.id)
            if tyre.vehicle_id:
                res.setdefault('vehicle_id', tyre.vehicle_id.id)
            # Auto-select logical operation
            if tyre.state == 'available':
                res.setdefault('operation_type', 'mount')
            elif tyre.state == 'mounted':
                res.setdefault('operation_type', 'dismount')
        
        elif self.env.context.get('active_model') == 'fleet.vehicle' and self.env.context.get('active_id'):
             vehicle = self.env['fleet.vehicle'].browse(self.env.context['active_id'])
             res.setdefault('vehicle_id', vehicle.id)
             if not res.get('operation_type'):
                 res['operation_type'] = 'mount'
        
        # Auto-fill tread depth from tyre if available
        if res.get('tyre_id') and not res.get('tread_depth'):
            tyre = self.env['fleet.vehicle.tyre'].browse(res['tyre_id'])
            res['tread_depth'] = tyre.current_tread_depth

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
        
        # Collect all tyres to process (Self + Selected Related)
        tyres_to_process = [tyre]
        if self.operation_type == 'gate_check':
            tyres_to_process.extend(self.related_tyre_ids)

        for t in tyres_to_process:
             # Create history for each (adjust logic if needed per tyre)
             vals = history_vals.copy()
             vals['tyre_id'] = t.id
             self.env['fleet.vehicle.tyre.history'].create(vals)
             
        # Stock Move Logic - ONLY for the main tyre_id (wizard context)
        # We generally don't move "related" tyres in bulk logic for mount/dismount yet, 
        # this bulk feature is primarily for Gate Check as per requirements.
        
        # Stock Move Logic
        source_loc = tyre.lot_id.location_id
        dest_loc = False
        
        if self.operation_type == 'mount':
            if not self.vehicle_id or not self.position_id:
                raise UserError(_("Vehicle and Position are required for mounting."))
            
            # Constraint 1: Position Occupied
            existing_tyre = self.env['fleet.vehicle.tyre'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('position_id', '=', self.position_id.id),
                ('state', '=', 'mounted')
            ], limit=1)
            if existing_tyre:
                raise UserError(_("Position %s is already occupied by tyre %s. Please dismount it first.") % (self.position_id.name, existing_tyre.name))

            # Constraint 2 & 3: Axle Balance & Mixing
            partner_tyres = self.env['fleet.vehicle.tyre'].search([
                ('vehicle_id', '=', self.vehicle_id.id),
                ('position_id.axle_number', '=', self.position_id.axle_number),
                ('state', '=', 'mounted')
            ])
            for partner in partner_tyres:
                # Tread Depth Check
                diff = abs((self.tread_depth or tyre.current_tread_depth) - partner.current_tread_depth)
                if diff > 3.0:
                    raise UserError(_("Unbalanced Axle! Tread depth difference between new tyre (%s mm) and %s (%s mm) is %s mm (Limit: 3mm).") % (
                        (self.tread_depth or tyre.current_tread_depth), partner.name, partner.current_tread_depth, diff))
                
                # Mixing Check (Brand)
                # Ensure we handle cases where product/brand might be missing to avoid crash
                if partner.product_id and tyre.product_id and partner.product_id.tyre_brand_id != tyre.product_id.tyre_brand_id:
                     raise UserError(_("Tyre Mixing! You are mounting a %s tyre on the same axle as a %s tyre.") % (tyre.product_id.tyre_brand_id.name, partner.product_id.tyre_brand_id.name))

            dest_loc = self._get_vehicle_location(self.vehicle_id)
            tyre.write({
                'state': 'mounted',
                'vehicle_id': self.vehicle_id.id,
                'position_id': self.position_id.id,
                'location_id': False,
            })
        
        elif self.operation_type == 'dismount':
            dest_loc = self.destination_location_id or self.env.ref('stock.stock_location_stock')
            tyre.write({
                'state': 'available',
                'vehicle_id': False,
                'position_id': False,
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
            tyre.write({'state': 'repair', 'vehicle_id': False, 'position_id': False, 'location_id': False})
            
        elif self.operation_type == 'retread':
            if self.vendor_id:
                dest_loc = self.vendor_id.property_stock_customer or self.env.ref('stock.stock_location_customers')
            tyre.write({
                'state': 'retread', 
                'vehicle_id': False, 
                'position_id': False, 
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
                'position_id': False, 
                'location_id': False,
                'disposal_reason': self.reason,
                'disposal_date': self.date,
            })

        if dest_loc and source_loc and source_loc != dest_loc:
            # Create Stock Move
            move = self.env['stock.move'].create({
                'description_picking': f"Tyre {tyre.name}: {self.operation_type}",
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


        # History creation for main tyre is handled in the loop above
        # self.env['fleet.vehicle.tyre.history'].create(history_vals)
        return {'type': 'ir.actions.act_window_close'}

