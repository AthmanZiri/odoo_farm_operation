# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, Command


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'

    @api.depends('employee_id', 'struct_id', 'date_from', 'date_to')
    def _compute_input_line_ids(self):
        super()._compute_input_line_ids()
        for slip in self:
            if not slip.employee_id or not slip.date_from or not slip.date_to or not slip.struct_id:
                continue
            
            loan_ids = self.env['hr.loan'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('state', '=', 'approve')
            ])
            
            input_type_lo = self.env['hr.payslip.input.type'].search([('code', '=', 'LO')], limit=1)
            if not input_type_lo:
                continue

            for loan in loan_ids:
                for loan_line in loan.loan_lines:
                    if slip.date_from <= loan_line.date <= slip.date_to and not loan_line.paid:
                        # Check if it's already there to avoid duplicates if recomputed
                        existing_line = slip.input_line_ids.filtered(
                            lambda l: l.input_type_id == input_type_lo and l.loan_line_id == loan_line
                        )
                        if not existing_line:
                            slip.update({
                                'input_line_ids': [Command.create({
                                    'name': loan.name,
                                    'amount': loan_line.amount,
                                    'input_type_id': input_type_lo.id,
                                    'loan_line_id': loan_line.id,
                                })]
                            })
                        else:
                            existing_line.amount = loan_line.amount

    def action_payslip_done(self):
        """ Compute the loan amount and remaining amount while confirming
            the payslip"""
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            for line in slip.input_line_ids:
                if line.loan_line_id:
                    line.loan_line_id.paid = True
                    line.loan_line_id.loan_id._compute_total_amount()
        return res
