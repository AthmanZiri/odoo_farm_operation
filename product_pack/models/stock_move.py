from odoo import models, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_pack_move = fields.Boolean(
        string='Is Pack Move', 
        help='This move is for a Pack product.',
        related='product_id.is_pack',
        store=True,
        readonly=True
    )
    parent_pack_move_id = fields.Many2one(
        'stock.move', 
        string='Parent Pack Move', 
        help='If this move was generated from exploding a pack, this is the original pack move.'
    )
