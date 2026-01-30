from odoo import models, fields, api

class RecycleBinAuditLog(models.Model):
    _name = 'recycle.bin.audit.log'
    _description = 'Recycle Bin Audit Log'
    _order = 'timestamp desc'

    action = fields.Selection([
        ('restore', 'Restore Record'),
        ('delete', 'Delete Record'),
        ('create', 'Create Record'),
    ], 
    string='Action', 
    help="Specifies the type of action performed on the recycle bin record (e.g., Restore, Delete, Create).")

    user_id = fields.Many2one(
        'res.users', 
        string='Performed By', 
        default=lambda self: self.env.user, 
        help="Indicates the user who performed this action.")

    timestamp = fields.Datetime(
        string='Timestamp', 
        default=fields.Datetime.now, 
        help="The date and time when this action was performed.")

    recycle_bin_id = fields.Many2one(
        'recycle.bin', 
        string='Recycle Bin Record', 
        help="The related record in the recycle bin that this action refers to.")

    details = fields.Text(
        string='Details', 
        help="Additional information or comments regarding this action.")

