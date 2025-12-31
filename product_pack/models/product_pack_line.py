from odoo import models, fields, api

class ProductPackLine(models.Model):
    _name = 'product.pack.line'
    _description = 'Product Pack Line'

    pack_id = fields.Many2one('product.template', string='Pack', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id', readonly=True)
