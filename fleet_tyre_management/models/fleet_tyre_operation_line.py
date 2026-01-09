from odoo import models, fields

class FleettyreOperationLine(models.TransientModel):
    _name = 'fleet.tyre.operation.line'
    _description = 'Tyre Operation Line'

    wizard_id = fields.Many2one('fleet.tyre.operation.wizard', string='Wizard', required=True, ondelete='cascade')
    tyre_id = fields.Many2one('fleet.vehicle.tyre', string='Tyre', required=True)
    position_id = fields.Many2one(related='tyre_id.position_id', string='Position', readonly=True)
    
    current_tread_depth = fields.Float(related='tyre_id.current_tread_depth', string='Current Depth', readonly=True)
    tread_depth = fields.Float(string='New Tread Depth (mm)')
    odometer = fields.Float(string='Odometer')
    
    note = fields.Text(string='Note')
