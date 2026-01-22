from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_fuel = fields.Boolean(string="Is Fuel")
    fuel_location_id = fields.Many2one(
        "stock.location", string="Filled From", domain="[('usage', '=', 'internal')]"
    )
