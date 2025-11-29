# -*- coding: utf-8 -*-
from odoo import api, models

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    @api.model
    def _preload_maintenance_templates(self, template_xml_id, checklist_data):
        """
        Preloads checklist fields for a given worksheet template.
        :param template_xml_id: The XML ID of the worksheet template.
        :param checklist_data: A list of dictionaries, each defining a field.
                               Example: [{'name': 'x_check_oil', 'string': 'Check Oil', 'type': 'boolean', 'group': 'Inspect'}]
        """
        template = self.env.ref(template_xml_id)
        model_id = template.model_id.id
        
        fields_to_create = []
        for item in checklist_data:
            field_name = item['name']
            # Check if field already exists to avoid duplication errors on update
            existing_field = self.env['ir.model.fields'].search([
                ('name', '=', field_name),
                ('model_id', '=', model_id)
            ], limit=1)
            
            if not existing_field:
                fields_to_create.append({
                    'name': field_name,
                    'field_description': item['string'],
                    'ttype': item.get('type', 'boolean'), # Default to boolean for checklist
                    'model_id': model_id,
                })
        
        if fields_to_create:
            self.env['ir.model.fields'].create(fields_to_create)
