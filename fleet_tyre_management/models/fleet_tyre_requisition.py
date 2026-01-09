from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FleetTyreRequisition(models.Model):
    _name = 'fleet.tyre.requisition'
    _description = 'Tyre Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    user_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, required=True, tracking=True)
    date_request = fields.Date(string='Request Date', default=fields.Date.context_today, required=True, tracking=True)
    
    source_location_id = fields.Many2one('stock.location', string='Source Location', domain=[('usage', '=', 'internal')], required=True, tracking=True)
    dest_location_id = fields.Many2one('stock.location', string='Destination Location', domain=[('usage', '=', 'internal')], required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Submitted'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    line_ids = fields.One2many('fleet.tyre.requisition.line', 'requisition_id', string='Lines')
    picking_id = fields.Many2one('stock.picking', string='Transfer', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('fleet.tyre.requisition') or 'New'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'state': 'open'})

    def action_approve(self):
        for req in self:
            if not req.line_ids:
                raise UserError(_("Please add at least one line."))
            
            # Create Stock Picking
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('default_location_src_id', '=', req.source_location_id.id)
            ], limit=1)
            
            # Fallback if specific route not found, just grab any internal type
            if not picking_type:
                 picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)

            vals = {
                'picking_type_id': picking_type.id,
                'location_id': req.source_location_id.id,
                'location_dest_id': req.dest_location_id.id,
                'origin': req.name,
                'move_ids_without_package': []
            }
            
            for line in req.line_ids:
                move_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': req.source_location_id.id,
                    'location_dest_id': req.dest_location_id.id,
                }
                vals['move_ids_without_package'].append((0, 0, move_vals))
            
            picking = self.env['stock.picking'].create(vals)
            picking.action_confirm() # Mark as Todo
            
            req.write({'state': 'done', 'picking_id': picking.id})

    def action_cancel(self):
        self.write({'state': 'cancel'})


class FleetTyreRequisitionLine(models.Model):
    _name = 'fleet.tyre.requisition.line'
    _description = 'Tyre Requisition Line'

    requisition_id = fields.Many2one('fleet.tyre.requisition', string='Requisition', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('is_tyre', '=', True)])
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    # Future: Allow requesting specific Serial?
