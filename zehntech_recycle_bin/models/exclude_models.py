from odoo import models, fields

class RecycleBinExcludeModel(models.Model):
    _name = 'recycle.bin.exclude.model'
    _description = 'Recycle Bin Excluded Models'

    name = fields.Char(string='Name', required=True)
    model = fields.Char(string='Model', required=True, help="Technical name of the model to exclude")