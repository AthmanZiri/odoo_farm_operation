# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ConfirmPurchaseWizard(models.Model):
    _name = "confirm.purchase.wizard"
    _description = "Auto Confirm Purchase Order"

    purchase_order_ids = fields.Many2many("purchase.order", string="Selected Purchase Order")
    account_journal_id = fields.Many2one("account.journal", string="Select Journal",
                                         domain="[('type', 'in', ['bank', 'cash'])]")
    stock_warehouse_id = fields.Many2one("stock.warehouse", string="Select Warehouse")

    def default_get(self, fields_list):
        res = super(ConfirmPurchaseWizard, self).default_get(fields_list)
        purchase_activate_ids = self.env.context.get('active_ids', [])
        if purchase_activate_ids:
            purchase_orders = self.env["purchase.order"].browse(purchase_activate_ids)
            res['purchase_order_ids'] = [(6, 0, purchase_orders.ids)]
        return res

    def button_action_confirm_purchase(self):
        if any(record.state not in ['draft', 'sent'] for record in self.purchase_order_ids):
            raise UserError(_("Please select Purchase orders which are in Quotation stage."))

        for record in self.purchase_order_ids:
            if record.state in ['draft', 'sent']:
                record.button_confirm()
                for rec in record:
                    stock_picking_obj = self.env['stock.picking']
                    stock_picking_ids = stock_picking_obj.search([('origin', '=', rec.name)])
                    for pick in stock_picking_ids:
                        for qty in pick.move_ids:
                            stock_picking_ids.write({
                                'location_dest_id': self.stock_warehouse_id.lot_stock_id.id
                            })
                            qty.write({
                                'quantity': qty.product_uom_qty
                            })
                        pick.button_validate()
                        account_move_obj = self.env['account.move']
                        vals = {
                            'move_type': 'in_invoice',
                            'invoice_origin': rec.name,
                            'purchase_id': rec.id,
                            'partner_id': rec.partner_id.id,
                            'invoice_date': date.today(),
                        }
                        res = account_move_obj.create(vals)
                        purchase_order_lines = rec.order_line
                        po_new_lines = []
                        for po_line in purchase_order_lines.filtered(lambda l: not l.display_type):
                            po_new_lines.append((0, 0, po_line._prepare_account_move_line(res)))
                        res.write({
                            'invoice_line_ids': po_new_lines,
                            'purchase_id': False
                        })
                        res.action_post()
                        res.action_register_payment()
                        account_payment_vals = {
                            'journal_id': self.account_journal_id.id,
                            'payment_date': date.today(),
                        }
                        account_payment_registers_id = self.env['account.payment.register'].with_context(
                            active_model='account.move', active_ids=res.ids).create(account_payment_vals)
                        account_payment_registers_id.action_create_payments()
