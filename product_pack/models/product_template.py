from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_pack = fields.Boolean(string='Is a Pack', help='Check this if the product is a pack/bundle of other products.')
    pack_line_ids = fields.One2many('product.pack.line', 'pack_id', string='Pack Components')
    
    # Smart button field
    pack_availability_qty = fields.Float(
        string='Pack Availability', 
        compute='_compute_pack_availability', 
        help='Maximum number of packs that can be assembled from available components.'
    )

    @api.depends('is_pack', 'pack_line_ids', 'pack_line_ids.product_id.qty_available')
    def _compute_pack_availability(self):
        for product in self:
            if not product.is_pack or not product.pack_line_ids:
                product.pack_availability_qty = 0.0
                continue
            
            # Find the limiting component
            qty_possible = []
            for line in product.pack_line_ids:
                if line.quantity > 0:
                    # Determine how many sets of this component we have
                    # We look at the product variant's qty_available
                    # Note: This checks 'qty_available' which is On Hand. 
                    # If we should check "Forecasted" or "Free to Use", we might need virtual_available or free_qty.
                    # Prompt says "on-hand quantity".
                    max_sets = line.product_id.qty_available // line.quantity
                    qty_possible.append(max_sets)
            
            if qty_possible:
                product.pack_availability_qty = min(qty_possible)
            else:
                product.pack_availability_qty = 0.0

    def action_compute_pack_price(self):
        """Calculates bundle price based on sum of component list prices."""
        self.ensure_one()
        total_price = sum(line.product_id.lst_price * line.quantity for line in self.pack_line_ids)
        self.list_price = total_price
    
    def action_view_pack_components(self):
        """Optional: View to show components if needed, or just rely on the notebook tab."""
        pass
