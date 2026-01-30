import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)
MODULE_UNINSTALL_FLAG = '_force_unlink'

class BaseModelExtended(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_model_id(self, model_name):
        return self.env['ir.model'].search([('model', '=', model_name)], limit=1).id

    def unlink(self):
        uninstalling = self._context.get(MODULE_UNINSTALL_FLAG)
        if uninstalling:
            return super(BaseModelExtended, self).unlink()

        if not self._name == 'ir.model':
            _logger.info(
                f"Unlink in BaseModelExtended class for {self._name} --- user id: {self.env.uid}")

            # Models that bypass recycle bin logic
            bypass_models = [
                        'recycle.bin', 'bus.bus', 'mail.message', 'mail.followers',
                        'ir.attachment', 'ir.model.data', 'recycle.bin.audit.log',

                        # Core System Models
                        'ir.model', 'ir.model.fields', 'ir.ui.menu', 'ir.actions.act_window',
                        'ir.config_parameter', 'res.currency',

                        # Technical Models
                        'ir.module.module', 'ir.translation', 'ir.rule', 'ir.cron', 'ir.sequence',
                        'ir.ui.view', 'ir.actions.server',

                        # Accounting Models
                        'account.move', 'account.move.line', 'account.payment', 'account.tax',

                        # Sales and Purchases Models
                        'sale.order.line', 'purchase.order', 'purchase.order.line',

                        # Inventory Models
                        'stock.picking', 'stock.quant', 'stock.location', 'stock.inventory',

                        # Human Resources Models
                        'hr.employee', 'hr.payslip', 'hr.contract',

                        # Manufacturing Models
                        'mrp.production', 'mrp.bom',

                        # Other Critical Models
                        'mail.activity', 'base.language.install', 'res.company'
                    ]


            # Fetch excluded models from configuration  
            excluded_models_param = self.env['ir.config_parameter'].sudo(
            ).get_param('recycle_bin.exclude_models', '')
            excluded_models = excluded_models_param.split(',')

            # If model is in the bypass list or excluded models, perform permanent deletion
            if self._name in bypass_models or self._name in excluded_models:
                _logger.info(
                    f"Model {self._name} is excluded or in the bypass list. Permanently deleting records: {self.ids}")
                return super(BaseModelExtended, self).unlink()

            recycle_bin_env = self.env['recycle.bin']
            all_recycle_data = []
            for record in self:
                _logger.warning(f"--------record: {record}")
                _logger.warning(f"record.read(): {record.read()}")
                if self._name == 'ir.attachment':
                    # Custom handling for attachments before they are unlinked
                    self._handle_attachments_before_unlink(record)
                    continue
                record_data = record.read()[0]
                deleted_data = json.dumps(record_data, default=str)
                recycle_data_main = {
                    'name': record.display_name or '',
                    'model_id': self._get_model_id(self._name),
                    'record_id': record.id,
                    'deleted_datetime': fields.Datetime.now(),
                    'user_id': self.env.uid,
                    'deleted_data': deleted_data,
                    # Initially, do not set parent_id for the main record
                }
                _logger.warning(f"recycle_data_main: {recycle_data_main}")
                if record_data.get("res_id"):
                    res_id_value = record_data.get('res_id', '')
                    if ',' in str(res_id_value):
                        try:
                            _, res_id = res_id_value.split(',')
                            recycle_data_main['parent_record_id'] = int(
                                res_id)  # Convert ID to integer
                        except ValueError:
                            _logger.error(
                                f"Invalid res_id format for ir.property: {res_id_value}")
                            continue
                    else:
                        recycle_data_main['parent_record_id'] = res_id_value

                main_recycle_record = recycle_bin_env.create(recycle_data_main)
                all_recycle_data.append((record, main_recycle_record.id))

            # Step 2: Now handle related records and link them to the main record
            for record, parent_id in all_recycle_data:
                related_records = self._get_related_records_before_unlink()
                for related_record in related_records:
                    related_record_data = related_record.read()[0]
                    related_deleted_data = json.dumps(
                        related_record_data, default=str)
                    recycle_data_related = {
                        'name': related_record.display_name or '',
                        'model_id': self._get_model_id(related_record._name),
                        'record_id': related_record.id,
                        'deleted_datetime': fields.Datetime.now(),
                        'user_id': self.env.uid,
                        'deleted_data': related_deleted_data,
                        'parent_id': parent_id,
                    }
                    recycle_bin_env.create(recycle_data_related)
        else:
            recycle_bin_env = self.env['recycle.bin']
            recycle_bin_env.create({
                'name': self._name,
                'model_id': self._get_model_id('ir.model'),
                'deleted_datetime': fields.Datetime.now(),
                'user_id': self.env.uid,
                "deleted_data": json.dumps({'name': self.name, "model": f"x_{self.name.lower()}"}, default=str)
            })
        
        return super(BaseModelExtended, self).unlink()

    def _handle_attachments_before_unlink(self, attachment):
        _logger.info(f"Handling attachment {attachment.id} before unlinking.")

        recycle_bin_env = self.env['recycle.bin']
        attachment_data = attachment.read(
            fields=['name', 'res_model', 'res_id', 'type', 'url', 'mimetype'])[0]

        deleted_data = json.dumps(attachment_data, default=str)
        recycle_data = {
            'name': attachment_data.get('name', ''),
            'model_id': self._get_model_id('ir.attachment'),
            'record_id': attachment.id,  # Original attachment ID
            'deleted_datetime': fields.Datetime.now(),
            'user_id': self.env.uid,
            'deleted_data': deleted_data,
            'parent_record_id': attachment.res_id,
        }

        recycle_bin_record = recycle_bin_env.create(recycle_data)
        _logger.info(
            f"Created recycle bin record for attachment {attachment.id} with recycle bin ID {recycle_bin_record.id}")

    def _get_related_records_before_unlink(self):
        related_records = []
        for record in self:
            for field in record._fields.values():
                if field.type == 'one2many':
                    comodel_name = field.comodel_name
                    comodel = self.env[comodel_name]
                    inverse_field_name = field.inverse_name
                    inverse_field = comodel._fields.get(inverse_field_name)

                    if isinstance(inverse_field, fields.Many2one) and inverse_field.ondelete == 'cascade':
                        related_records.extend(
                            getattr(record, field.name).sudo())
        return related_records
