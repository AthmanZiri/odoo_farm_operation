from odoo import models, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id_pack(self):
        if self.product_id and self.product_id.is_pack and self.product_id.pack_line_ids:
            description_lines = [self.name or self.product_id.display_name]
            description_lines.append("Pack Components:")
            for line in self.product_id.pack_line_ids:
                description_lines.append(f"- {line.quantity} x {line.product_id.display_name}")
            self.name = '\n'.join(description_lines)
