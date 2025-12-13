from odoo import models, fields, api

class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    picking_ids = fields.One2many('stock.picking', 'fleet_service_id', string='Requisitions')
    picking_count = fields.Integer(compute='_compute_picking_count', string='Requisition Count')

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for record in self:
            record.picking_count = len(record.picking_ids)

    def action_create_requisition(self):
        self.ensure_one()
        # Find Internal Transfer Operation Type
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id or self.env.company.id)
        ], limit=1)

        return {
            'name': 'Request Material',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'context': {
                'default_fleet_service_id': self.id,
                'default_picking_type_id': picking_type.id if picking_type else False,
                'default_origin': self.description or self.service_type_id.name,
            },
        }

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'name': 'Requisitions',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('fleet_service_id', '=', self.id)],
            'context': {'default_fleet_service_id': self.id},
        }
