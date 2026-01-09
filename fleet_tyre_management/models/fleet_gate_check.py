from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleetTyreGateCheck(models.Model):
    _name = 'fleet.tyre.gate.check'
    _description = 'Tyre Gate Check'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user, tracking=True)
    
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True)
    
    gate_scan_type = fields.Selection([
        ('check_in', 'Check-in'),
        ('check_out', 'Check-out')
    ], string='Scan Type', required=True, tracking=True)
    
    line_ids = fields.One2many('fleet.tyre.gate.check.line', 'check_id', string='Tyres')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.tyre.gate.check') or 'New'
        return super().create(vals_list)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if not self.vehicle_id:
            return

        # 1. Infer Scan Type
        # Check the last gate check for ANY tyre on this vehicle? Or just the vehicle generally?
        # Logic: If the vehicle was last checked IN, we check OUT.
        # We can look at the last done gate check for this vehicle.
        last_check = self.search([
            ('vehicle_id', '=', self.vehicle_id.id),
            ('state', '=', 'done')
        ], limit=1, order='date desc, id desc')
        
        if last_check and last_check.gate_scan_type == 'check_in':
            self.gate_scan_type = 'check_out'
        else:
            self.gate_scan_type = 'check_in'


        # 2. Populate Lines
        lines = []
        # Clear existing lines
        self.line_ids = [(5, 0, 0)]
        
        mounted_tyres = self.env['fleet.vehicle.tyre'].search([
            ('vehicle_id', '=', self.vehicle_id.id),
            ('state', '=', 'mounted')
        ])
        
        for tyre in mounted_tyres:
            lines.append((0, 0, {
                'tyre_id': tyre.id,
                'new_tread_depth': tyre.current_tread_depth, # Default to old value
                'odometer': self.vehicle_id.odometer, # Default to vehicle odometer
            }))
        self.line_ids = lines

    def action_confirm(self):
        for check in self:
            if check.state != 'draft':
                 continue
            
            # Create History Records
            for line in check.line_ids:
                vals = {
                    'tyre_id': line.tyre_id.id,
                    'type': 'gate_check',
                    'gate_scan_type': check.gate_scan_type,
                    'date': check.date,
                    'odometer': line.odometer,
                    'tread_depth': line.new_tread_depth,
                    'note': f"Gate Check: {check.name}",
                    'vehicle_id': check.vehicle_id.id
                }
                self.env['fleet.vehicle.tyre.history'].create(vals)
                
                # Update Tyre Master Data
                if line.new_tread_depth != line.current_tread_depth:
                     line.tyre_id.write({'current_tread_depth': line.new_tread_depth})

            check.write({'state': 'done'})


class FleetTyreGateCheckLine(models.Model):
    _name = 'fleet.tyre.gate.check.line'
    _description = 'Tyre Gate Check Line'

    check_id = fields.Many2one('fleet.tyre.gate.check', string='Gate Check', required=True, ondelete='cascade')
    tyre_id = fields.Many2one('fleet.vehicle.tyre', string='Tyre', required=True)
    position_id = fields.Many2one(related='tyre_id.position_id', string='Position', readonly=True)
    current_tread_depth = fields.Float(related='tyre_id.current_tread_depth', string='Current Depth', readonly=True)
    
    new_tread_depth = fields.Float(string='New Tread Depth (mm)')
    odometer = fields.Float(string='Odometer')
