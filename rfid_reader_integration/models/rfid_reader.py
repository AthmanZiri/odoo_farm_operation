from odoo import models, fields

class RfidReader(models.Model):
    _name = 'rfid.reader'
    _description = 'UHF RFID Reader'

    name = fields.Char(string='Reader Name', required=True)
    ip_address = fields.Char(string='IP Address')
    port = fields.Integer(string='Port', default=6000)
    serial_port = fields.Char(string='Serial Port')
    serial_port = fields.Char(string='Serial Port')
    location_id = fields.Many2one('stock.location', string='Assigned Location')
    usage = fields.Selection([
        ('gate', 'Gate Check'),
        ('inventory', 'Inventory / Location Update')
    ], string="Reader Usage", default='gate', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text()
