from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    recycle_bin_lifecycle = fields.Integer(
        string='Clear Recycle Bin Lifecycle',
        help='Number of days after which recycle bin records will be automatically deleted.',
        config_parameter='recycle_bin.lifecycle_days',
        default=30  # Default lifecycle days
    )

    recycle_bin_exclude_models = fields.Many2many(
        'ir.model',
        string='Exclude Models',
        domain="[('transient', '=', False)]",  # Exclude transient models
        help="Select models to exclude from the recycle bin. Records from these models will be permanently deleted instead of being moved to the recycle bin."
    )

    @api.model
    def get_values(self):
        """Load configuration settings into the transient model."""
        res = super(ResConfigSettings, self).get_values()
        exclude_models_param = self.env['ir.config_parameter'].sudo().get_param('recycle_bin.exclude_models', default='')

        try:
            # Extract model technical names and find corresponding records
            model_names_list = exclude_models_param.split(',') if exclude_models_param else []
            exclude_models = self.env['ir.model'].search([('model', 'in', model_names_list)])

            res.update({
                'recycle_bin_exclude_models': [(6, 0, exclude_models.ids)],
            })
        except Exception as e:
            _logger.error(f"Error loading exclude models configuration: {e}")
            raise UserError(_(
                "An error occurred while loading the excluded models configuration. Please check the settings."
            ))

        return res

    def set_values(self):
        """Save configuration settings from the transient model."""
        super(ResConfigSettings, self).set_values()

        try:
            # Fetch technical names of the selected models
            exclude_model_names = self.recycle_bin_exclude_models.mapped('model')

            # Update the configuration parameter
            self.env['ir.config_parameter'].sudo().set_param(
                'recycle_bin.exclude_models',
                ','.join(exclude_model_names)
            )
        except Exception as e:
            _logger.error(f"Error saving exclude models configuration: {e}")
            raise UserError(_(
                "An error occurred while saving the excluded models configuration. Please try again."
            ))
