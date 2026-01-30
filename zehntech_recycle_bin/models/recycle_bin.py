from odoo import api, fields, models, _
import json
import logging
import base64
from datetime import datetime, timedelta
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class RecycleBin(models.Model):
    _name = 'recycle.bin'
    _description = 'Module to store deleted records'

    name = fields.Char(
        string='Name of Record',
        readonly=True,
        help="The name of the deleted record as it appeared before deletion."
    )
    model_id = fields.Many2one(
        'ir.model',
        readonly=True,
        help="The model (database table) to which the deleted record belonged."
    )
    record_id = fields.Integer(
        string='Deleted Record ID',
        readonly=True,
        help="The unique identifier (ID) of the deleted record."
    )
    parent_record_id = fields.Integer(
        string='Deleted Parent Record ID',
        readonly=True,
        help="The unique identifier (ID) of the parent record, if applicable."
    )
    deleted_datetime = fields.Datetime(
        string='Record Deleted at',
        readonly=True,
        help="The date and time when the record was deleted."
    )
    user_id = fields.Many2one(
        'res.users',
        string="Deleted by",
        readonly=True,
        help="The user who deleted the record."
    )
    deleted_data = fields.Char(
        string='Record Data',
        readonly=False,
        help="The serialized data (JSON format) of the deleted record."
    )
    parent_id = fields.Many2one(
        'recycle.bin',
        string='Parent Record',
        readonly=True,
        help="A reference to the parent record, if this record is related to another deleted record."
    )
    child_ids = fields.One2many(
        'recycle.bin', 'parent_id',
        string='Related Records',
        readonly=True,
        help="References to records related to the parent record that were also deleted."
    )
    start_date = fields.Date(
        string="Start Date",
        help="The starting date for the record retention period."
    )
    end_date = fields.Date(
        string="End Date",
        help="The ending date for the record retention period."
    )



    @api.model_create_multi
    def create(self, values_list):
        """Override the create method to log creation of records.

        Support multi-record creation by accepting a list of value dicts.
        """
        # Ensure deleted_datetime is set for each values dict
        for vals in values_list:
            if isinstance(vals, dict):
                vals.setdefault('deleted_datetime', fields.Datetime.now())

        records = super(RecycleBin, self).create(values_list)

        # Log creation for each new record individually
        for rec in records:
            try:
                self.log_create_action(self.env, self.env.user, rec)
            except Exception as e:
                _logger.error(f"Failed to log creation of recycle bin record {rec.id}: {e}", exc_info=True)

        return records

    def apply_date_filter(self):
        filtered_records = self.search([
            ('deleted_datetime', '>=', self.start_date),
            ('deleted_datetime', '<=', self.end_date)
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Filtered Records',
            'view_mode': 'tree,form',
            'res_model': 'recycle.bin',
            'domain': [('id', 'in', filtered_records.ids)],
            'target': 'current',
        }

    def log_create_action(self, env, user, record):
        """Log create actions performed on recycle bin records."""
        try:
        
            env['recycle.bin.audit.log'].create({
                'action': 'create',
                'user_id': user.id,
                'recycle_bin_id': record.id,
                'timestamp': fields.Datetime.now(),
                'details': _("Record ID: %s, Model: %s was created in the recycle bin") % (record.record_id, record.model_id.name),
            })
        except Exception as e:
            _logger.error(_("Failed to log create action for record %(record_id)s: %(error)s") % {
                'record_id': record.id,
                'error': e,
            }, exc_info=True)

    def log_restore_action(self, env, user, record):
        """Log restore actions performed on recycle bin records."""
        try:
         
            env['recycle.bin.audit.log'].create({
                'action': 'restore',
                'user_id': user.id,
                'recycle_bin_id': record.id,
                'timestamp': fields.Datetime.now(),
                'details': _("Record ID: %s, Model: %s was restored from the recycle bin") % (record.record_id, record.model_id.name),
            })
        except Exception as e:
            _logger.error(_("Failed to log restore action for record %(record_id)s: %(error)s") % {
                'record_id': record.id,
                'error': e,
            }, exc_info=True)


    def log_delete_action(self, env, user, record):
        """Log delete actions performed on recycle bin records."""
        try:
                
            env['recycle.bin.audit.log'].create({
                'action': 'delete',
                'user_id': user.id,
                'recycle_bin_id': record.id,
                'timestamp': fields.Datetime.now(),
                'details': _("Record ID: %s, Model: %s was deleted from the recycle bin") % (record.record_id, record.model_id.name),
            })
        except Exception as e:
            _logger.error(_("Failed to log delete action for record %(record_id)s: %(error)s") % {
                'record_id': record.id,
                'error': e,
            }, exc_info=True)

    @api.model
    def get_excluded_models(self):
        """Retrieve the list of excluded models from configuration parameters."""
        excluded_models_param = self.env['ir.config_parameter'].sudo().get_param('recycle_bin.exclude_models', default='')
        return excluded_models_param.split(',') if excluded_models_param else []

    def restore_record(self):
        restored_record_count = 0

        for record in self:
            model_name = self.env['ir.model'].browse(record.model_id.id).model

            # ----- AccessError check for protected model -----
            if model_name == 'ir.model' and not self.env.user.has_group('base.group_system'):
                msg = _("You are not allowed to restore 'Models' (ir.model) records.\n\n"
                        "This operation is allowed for the following groups:\n"
                        "        - Administration/Access Rights\n\n"
                        "Contact your administrator to request access if necessary.")
                raise AccessError(msg)
            # ----- Security check END -----
            try:
                model_name = self.env['ir.model'].browse(record.model_id.id).model
                # Validate deleted_data
                if not record.deleted_data:
                    _logger.error(f"Missing deleted_data for record ID {record.id}")
                    continue

                data = json.loads(record.deleted_data)

                fields_info = self.env[model_name].fields_get()

                # Define fields to exclude from restoration
                non_restorable_fields = [
                    'id', 'create_date', 'write_date', '__last_update',
                     'commercial_partner_id'
                ]
                child_relationship_fields = [
                    field for field, info in fields_info.items() if info.get('type') in ('one2many', 'many2many')
                ]

                # Combine excluded fields
                excluded_fields = set(non_restorable_fields + child_relationship_fields)

                # Remove excluded fields from the data
                for field in excluded_fields:
                    data.pop(field, None)

                # Adjust Many2one fields and other data transformations
                for field_name, field_value in data.items():
                    field_info = fields_info.get(field_name, {})
                    if field_info.get('type') == 'datetime' and isinstance(field_value, str):
                        try:
                            parsed_datetime = datetime.strptime(field_value, "%Y-%m-%d %H:%M:%S.%f")
                            data[field_name] = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                parsed_datetime = datetime.strptime(field_value, "%Y-%m-%d %H:%M:%S")
                                data[field_name] = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                _logger.error(f"Error parsing datetime for field {field_name} with value {field_value}")
                    elif 'image_' in field_name or 'avatar_' in field_name:
                        if isinstance(field_value, str) and field_value.startswith("b'") and field_value.endswith("'"):
                            image_data = field_value[2:-1]
                            data[field_name] = image_data
                    elif isinstance(field_value, list) and len(field_value) == 2 and isinstance(field_value[0], int):
                        data[field_name] = field_value[0]

                _logger.info(f"Attempting to create {model_name} with cleaned data: {data}")

                # Create the new record
                # import pdb;pdb.set_trace()
                new_record = self.env[model_name].sudo().create(data)
                new_record_id = new_record.id

                # Log the restore action for the main record
                self.log_restore_action(self.env, self.env.user, record)

                # Restore related child records

                for child in record.child_ids:
                    _logger.info(f"Restoring child record: {child}")
                    self.restore_child_record(child, new_record_id, record.record_id)

                    # Log the restore action for the child record
                    self.log_restore_action(self.env, self.env.user, child)

                    restored_record_count += 1

                # Handle related records if any
                self.get_related_records_data(parent_record_id=record.record_id, new_parent_record_id=new_record_id)

                # Remove the record from the recycle bin
                self.env.cr.execute("DELETE FROM recycle_bin WHERE id = %s", (record.id,))
                # record.unlink()

                restored_record_count += 1

            except Exception as e:
                _logger.error(f"Error restoring record ID {record.id}: {e}", exc_info=True)

        # Notify the user about the result
        if restored_record_count > 0:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Restoration Successful"),
                    "message": _('%s record(s) restored successfully.') % restored_record_count,
                    "type": "info",
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Records Restored"),
                    "message": _("No records were restored. Please check the Recycle Bin for valid records."),
                    "type": "warning",
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }


    def restore_child_record(self, child, new_order_id, original_order_id):
        _logger.info(f"restore_child_record STARTING")

        child_model_name = self.env['ir.model'].browse(child.model_id.id).model
        child_data = json.loads(child.deleted_data)

        # Update references and format Many2one fields
        for field_name, field_value in list(child_data.items()):
            # Check and replace specific record_id references with new_record_id
            if isinstance(field_value, list) and len(field_value) == 2:
                if field_value[0] == original_order_id:
                    _logger.warning(f"Replacing {original_order_id} with {new_order_id} on {field_name} - {field_value}")
                    child_data[field_name] = new_order_id  # Update with just the ID
                else:
                    # This ensures proper formatting for Many2one fields not being directly replaced
                    child_data[field_name] = field_value[0]  # Keep only the ID, discard the name
            elif field_value == original_order_id:
                # Direct integer match, uncommon but handled if necessary
                _logger.warning(f"Replacing {original_order_id} with {new_order_id} on {field_name} - {field_value}")
                child_data[field_name] = new_order_id

        # Exclude non-restorable fields
        excluded_fields = ['id', 'create_date', 'write_date', '__last_update']
        for field in excluded_fields:
            child_data.pop(field, None)

        _logger.info(f"Restoring {child_model_name} with corrected data: {child_data}")

        # Attempt to create the child record
        try:
            self.env[child_model_name].create(child_data)
        except Exception as e:
            _logger.error(f"Error restoring {child_model_name}: {e}", exc_info=True)

        # Skip logging action for child record
        # Comment or remove the line below to skip logging for child records
        # self.log_restore_action(self.env, self.env.user, child)

        # Directly delete the recycle bin entry for the child
        self.log_restore_action(self.env, self.env.user, child)
        child.unlink()


    def get_related_records_data(self, parent_record_id, new_parent_record_id):
        _logger.info(f"get_related_records_data STARTING with {parent_record_id} - {new_parent_record_id}")
        related_records = self.env['recycle.bin'].search([('parent_record_id', '=', parent_record_id)], order='record_id desc')

        if not related_records:
            _logger.warning("There are no related records...")
            return
        _logger.warning(f"related_records: {related_records}")

        for recycle_record in related_records:
            try:
                data = json.loads(recycle_record.deleted_data)
                model_name = recycle_record.model_id.model
                model = self.env[model_name]

                prepared_data = {}
                for field_name, field_value in data.items():
                    _logger.warning(f"working on {field_name} with {field_value}")
                    field = model._fields.get(field_name)
                    _logger.warning(f"field: {field}")

                    if field and field.type == 'many2one' and isinstance(field_value, list) and len(field_value) == 2:
                        prepared_data[field_name] = field_value[0]
                    elif field and field.type in ['one2many', 'many2many']:
                        continue
                    else:
                        prepared_data[field_name] = field_value

                # Correctly set 'res_id' if that's the intended logic
                if 'res_id' in prepared_data and prepared_data['res_id'] == parent_record_id:
                    prepared_data['res_id'] = new_parent_record_id

                # Exclude non-restorable fields
                excluded_fields = ['id', 'create_date', 'write_date', '__last_update']
                for field in excluded_fields:
                    prepared_data.pop(field, None)

                _logger.info(f"Restoring {model_name} with corrected data: {prepared_data}")
                new_related_record_id = self.env[model_name].create(prepared_data)
                _logger.warning(f"new_related_record_id: {new_related_record_id} for {model_name}")

            except json.JSONDecodeError as e:
                _logger.error(f"Error decoding JSON for recycle.bin record {recycle_record.id}: {e}")
                continue
            except Exception as e:
                _logger.error(f"Error restoring {model_name}: {e}", exc_info=True)

            recycle_record.unlink()

    def ensure_base64_encoded(self, data):
        """
        Ensure that the provided data is base64 encoded.
        If the data is not base64 encoded, encode it.
        """
        try:
            # If this step succeeds without raising an exception, the data is likely base64 encoded
            base64.b64decode(data, validate=True)
            _logger.warning(f"Trying to see if image is base64")
            return data  # Return the original data if it's already base64 encoded
        except Exception:
            # If an exception is raised, it means the data might not be base64 encoded
            _logger.warning(f"Encode the data into base64")
            return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def unlink(self):
        """Override unlink to support manual and cron-based clearing."""
        excluded_models = self.get_excluded_models()
        if self.env.context.get('bypass_recycle_bin'):
            _logger.info(f"Permanently deleting {len(self)} records from recycle bin.")
            return super(RecycleBin, self).unlink()
        else:
            for record in self:
                self.log_delete_action(self.env, self.env.user, record)
            return super(RecycleBin, self).unlink()

    def clear_recycle_bin(self):
        lifecycle_days = int(self.env['ir.config_parameter'].sudo().get_param('recycle_bin.lifecycle_days', default=30))
        date_limit = fields.Datetime.now() - timedelta(days=lifecycle_days)
        old_records = self.search([('deleted_datetime', '<', date_limit)])

        # Log deletion action
        for record in old_records:
            self.log_delete_action(self.env, self.env.user, record)  # Log record deletion from recycle bin

        # Then perform the actual deletion
        old_records.with_context(bypass_recycle_bin=True).unlink()
