from odoo import models, fields, api

class FleetWorkOrderPart(models.Model):
    _name = 'fleet.work.order.part'
    _description = 'Fleet Work Order Part'

    work_order_id = fields.Many2one('fleet.work.order', string='Work Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('type', 'in', ['product', 'consu'])])
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.list_price

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

class FleetWorkOrderLabor(models.Model):
    _name = 'fleet.work.order.labor'
    _description = 'Fleet Work Order Labor'

    work_order_id = fields.Many2one('fleet.work.order', string='Work Order', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Mechanic/Technician', required=True)
    hours = fields.Float(string='Hours Spent', required=True)
    description = fields.Char(string='Description')
    date = fields.Date(string='Date', default=fields.Date.context_today)
