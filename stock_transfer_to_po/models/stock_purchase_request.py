from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPurchaseRequest(models.Model):
    _name = 'stock.purchase.request'
    _description = 'Stock Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    requester_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user)
    department = fields.Char(
        string='Department',
        tracking=True,
        help="Department requesting these products. Auto-filled from the "
        "requester's employee record when HR is installed.",
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        tracking=True,
        check_company=True,
        help="Cost center or analytic account charged for this requisition.",
    )
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('stock.purchase.request.line', 'request_id', string='Products')
    purchase_order_ids = fields.One2many('purchase.order', 'request_id', string='Purchase Orders', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    purchase_count = fields.Integer(compute='_compute_purchase_count', string='Purchase Orders')
    move_count = fields.Integer(compute='_compute_move_count', string='Stock Moves')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Stock Transfers')

    @api.depends('purchase_order_ids')
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.purchase_order_ids)
            
    @api.depends('line_ids.move_id')
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.line_ids.mapped('move_id'))

    @api.depends('line_ids.move_id.picking_id')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.line_ids.mapped('move_id.picking_id'))

    def _department_from_requester(self, user):
        """Return department name from the requester's employee, if HR is available."""
        if not user:
            return False
        if 'employee_id' in user._fields:
            employee = user.employee_id
            if employee and employee.department_id:
                return employee.department_id.name
        if 'hr.employee' in self.env:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', user.id)], limit=1
            )
            if employee.department_id:
                return employee.department_id.name
        return False

    @api.onchange('requester_id')
    def _onchange_requester_id(self):
        if self.requester_id:
            department = self._department_from_requester(self.requester_id)
            if department:
                self.department = department

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.purchase.request') or _('New')
            if not vals.get('department') and vals.get('requester_id'):
                user = self.env['res.users'].browse(vals['requester_id'])
                department = self._department_from_requester(user)
                if department:
                    vals['department'] = department
        return super(StockPurchaseRequest, self).create(vals_list)

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('You cannot submit a request without any lines.'))
            rec.state = 'submitted'

    def action_approve(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('No lines to process.'))
        
        # Group by partner (Similar logic to the previous wizard)
        grouped = {}
        for line in self.line_ids:
            if not line.partner_id:
                raise UserError(_('Please define a vendor for product %s') % line.product_id.display_name)
            if line.partner_id not in grouped:
                grouped[line.partner_id] = []
            grouped[line.partner_id].append(line)
        
        orders = self.env['purchase.order']
        for partner, lines in grouped.items():
            po_vals = {
                'partner_id': partner.id,
                'origin': self.name,
                'date_order': fields.Datetime.now(),
                'company_id': self.company_id.id,
                'request_id': self.id,
            }
            po = self.env['purchase.order'].create(po_vals)
            
            for line in lines:
                line_vals = {
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'name': line.product_id.display_name,
                    'date_planned': fields.Datetime.now(),
                }
                # Price logic
                supplier_info = line.product_id._select_seller(
                    partner_id=partner,
                    quantity=line.quantity,
                    date=po.date_order and po.date_order.date(),
                    uom_id=line.product_id.uom_id
                )
                if supplier_info:
                    line_vals['price_unit'] = supplier_info.price
                else:
                    line_vals['price_unit'] = line.product_id.standard_price

                if self.analytic_account_id:
                    line_vals['analytic_distribution'] = {
                        str(self.analytic_account_id.id): 100.0,
                    }

                self.env['purchase.order.line'].create(line_vals)
            orders += po
        
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
        })
        return True

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset_draft(self):
        self.write({'state': 'draft', 'approved_by_id': False})

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'context': {'default_request_id': self.id}
        }

    def action_view_stock_moves(self):
        self.ensure_one()
        moves = self.line_ids.mapped('move_id')
        return {
            'name': _('Stock Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
        }

    def action_view_stock_pickings(self):
        self.ensure_one()
        pickings = self.line_ids.mapped('move_id.picking_id')
        return {
            'name': _('Stock Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pickings.ids)],
        }


class StockPurchaseRequestLine(models.Model):
    _name = 'stock.purchase.request.line'
    _description = 'Stock Purchase Request Line'

    request_id = fields.Many2one('stock.purchase.request', string='Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor')
    move_id = fields.Many2one('stock.move', string='Related Move')
    
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    request_id = fields.Many2one('stock.purchase.request', string='Source Request', readonly=True)
