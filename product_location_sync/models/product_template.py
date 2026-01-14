from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_location_names = fields.Char(
        string='Location',
        compute='_compute_stock_location_names',
        help='Locations where this product (or its variants) is in stock.'
    )

    @api.depends('qty_available') # 'qty_available' changes when stock moves confirm
    def _compute_stock_location_names(self):
        for template in self:
            quants = self.env['stock.quant'].search([
                ('product_tmpl_id', '=', template.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0)
            ])
            locations = quants.mapped('location_id.display_name')
            # Unique locations, sorted
            unique_locations = sorted(list(set(locations)))
            template.stock_location_names = ', '.join(unique_locations)
