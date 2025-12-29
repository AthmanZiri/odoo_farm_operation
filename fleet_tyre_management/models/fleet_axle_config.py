from odoo import models, fields, api

class FleetTyreAxleConfig(models.Model):
    _name = 'fleet.tyre.axle.config'
    _description = 'Tyre Axle Configuration'

    name = fields.Char(string='Name', required=True, help="e.g. 4x2 Truck, 18-Wheeler")
    position_ids = fields.One2many('fleet.tyre.position', 'config_id', string='Wheel Positions')
    image_layout = fields.Image(string='Layout Image', help="Schematic image of the axle layout")

class FleetTyrePosition(models.Model):
    _name = 'fleet.tyre.position'
    _description = 'Wheel Position'
    _order = 'sequence, id'

    config_id = fields.Many2one('fleet.tyre.axle.config', string='Configuration', ondelete='cascade')
    name = fields.Char(string='Name', required=True, help="e.g. Axle 1 Left")
    code = fields.Char(string='Code', required=True, help="Short code e.g. 1L, 2RO")
    sequence = fields.Integer(string='Sequence', default=10)
    
    axle_number = fields.Integer(string='Axle Number', required=True, help="1 for front-most axle")
    side = fields.Selection([
        ('left', 'Left'),
        ('right', 'Right'),
        ('center', 'Center')
    ], string='Side', required=True)
    
    is_dual = fields.Boolean(string='Is Dual Wheel', help="True if this is part of a dual wheel setup")
    position_type = fields.Selection([
        ('steer', 'Steer'),
        ('drive', 'Drive'),
        ('tag', 'Tag/Lift')
    ], string='Position Type', default='drive')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} ({record.name})"
            result.append((record.id, name))
        return result
