from odoo import models, fields, api, _
from odoo.exceptions import UserError

from datetime import timedelta

class FleetWorkOrder(models.Model):
    _name = 'fleet.work.order'
    _description = 'Fleet Job Card / Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Job Card Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True)
    driver_id = fields.Many2one('res.partner', string='Driver', related='vehicle_id.driver_id', store=True, readonly=False)
    odometer = fields.Float(string='Odometer at Entry', help='Odometer reading when the vehicle arrived.')
    odometer_unit = fields.Selection(related='vehicle_id.odometer_unit', string='Unit', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, default=lambda self: self.env['stock.warehouse'].search([], limit=1))
    
    date_open = fields.Datetime(string='Date Opened', default=fields.Datetime.now, tracking=True)
    date_close = fields.Datetime(string='Date Closed', tracking=True)
    
    type = fields.Selection([
        ('breakdown', 'Breakdown'),
        ('preventive', 'Preventive Maintenance')
    ], string='Type', required=True, default='breakdown', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('diagnosis', 'Diagnosis'),
        ('requisition', 'Parts Requisition'),
        ('ready', 'Ready for Work'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, group_expand='_expand_states')
    
    mechanic_ids = fields.Many2many('hr.employee', string='Mechanics')
    
    parts_ids = fields.One2many('fleet.work.order.part', 'work_order_id', string='Parts')
    labor_ids = fields.One2many('fleet.work.order.labor', 'work_order_id', string='Labor')
    
    picking_ids = fields.One2many('stock.picking', 'work_order_id', string='Stock Pickings')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')

    description = fields.Text(string='Description of Issue')
    diagnosis_notes = fields.Text(string='Diagnosis Notes')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.work.order') or _('New')
        return super(FleetWorkOrder, self).create(vals_list)

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for record in self:
            record.picking_count = len(record.picking_ids)

    def action_diagnosis(self):
        self.state = 'diagnosis'

    def action_requisition(self):
        self.state = 'requisition'

    def action_request_parts(self):
        """
        Creates a Stock Picking (Internal Transfer) from Main Store to Workshop/Virtual Location
        for the parts listed in parts_ids.
        """
        self.ensure_one()
        if not self.parts_ids:
            raise UserError(_("Please add parts to the Job Card before requesting."))

        # Assuming a default picking type for Internal Transfers is available. 
        # In a real scenario, this might be a specific 'Workshop Requisition' operation type.
        # We'll try to find one or use a default.
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        if not picking_type:
             raise UserError(_("No Internal Transfer Operation Type found. Please configure Inventory."))

        # Source: Stock, Destination: Expense or Production (or a specific Workshop location)
        # For this implementation, let's assume standard Stock -> Production/Usage for consumption
        # Or Stock -> Workshop Location. 
        # Let's use the default source/dest from the picking type for now, but ideally this is configurable.
        
        # Use the selected warehouse's lot stock location
        location_src_id = self.warehouse_id.lot_stock_id.id
        
        # Destination: Virtual Location for Production/Usage
        location_dest = self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
        location_dest_id = location_dest.id
        if not location_dest_id:
             location_dest_id = picking_type.default_location_dest_id.id

        moves = []
        for part in self.parts_ids:
            moves.append((0, 0, {
                'product_id': part.product_id.id,
                'product_uom_qty': part.quantity,
                'product_uom': part.product_id.uom_id.id,
                'location_id': location_src_id,
                'location_dest_id': location_dest_id,
            }))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location_src_id,
            'location_dest_id': location_dest_id,
            'origin': self.name,
            'move_ids': moves,
            'work_order_id': self.id,
        })
        
        self.state = 'ready' # Or stay in requisition until picking is done? 
        # Let's say we move to 'ready' when parts are requested, but work starts when they arrive.
        # Actually, let's keep it simple.
        
        return {
            'name': _('Stock Picking'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'type': 'ir.actions.act_window',
        }

    def action_start_work(self):
        self.state = 'in_progress'

    def action_close(self):
        self.write({'state': 'done', 'date_close': fields.Datetime.now()})
        # Update vehicle odometer if provided
        if self.odometer > self.vehicle_id.odometer:
            self.vehicle_id.odometer = self.odometer
            
        # Create Work Entries for Mechanics
        work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)
        if work_entry_type:
            for labor in self.labor_ids:
                if labor.employee_id and labor.date and labor.hours > 0:
                    # Calculate start and stop based on date and hours (assuming start at 9:00 AM for simplicity or just duration)
                    # For work entries, we need datetime. Let's assume the work happened at the start of the day or use current time if today.
                    # A better approach for simple logging is just ensuring the hours are recorded. 
                    # But hr.work.entry requires date_start and date_stop.
                    
                    start_dt = fields.Datetime.to_datetime(labor.date).replace(hour=9, minute=0, second=0)
                    end_dt = start_dt + timedelta(hours=labor.hours)
                    
                    self.env['hr.work.entry'].create({
                        'name': f"Workshop: {self.name} - {labor.description or 'Repair'}",
                        'employee_id': labor.employee_id.id,
                        'work_entry_type_id': work_entry_type.id,
                        'date': start_dt.date(),
                        'duration': labor.hours,
                        'state': 'draft', # or 'validated'
                    })

    def action_cancel(self):
        self.state = 'cancel'

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'name': _('Stock Pickings'),
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'type': 'ir.actions.act_window',
        }

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    work_order_id = fields.Many2one('fleet.work.order', string='Work Order', readonly=True)
