# -*- coding: utf-8 -*-
from odoo import api, models

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    @api.model
    def _preload_maintenance_templates(self, template_xml_id, checklist_data):
        """
        Legacy method to preload checklist fields for a given worksheet template.
        Kept for backward compatibility with older data files (e.g., JD S660, Isuzu).
        """
        template = self.env.ref(template_xml_id)
        model_id = template.model_id.id
        
        fields_to_create = []
        for item in checklist_data:
            field_name = item['name']
            existing_field = self.env['ir.model.fields'].search([
                ('name', '=', field_name),
                ('model_id', '=', model_id)
            ], limit=1)
            
            if not existing_field:
                fields_to_create.append({
                    'name': field_name,
                    'field_description': item['string'],
                    'ttype': item.get('type', 'boolean'),
                    'model_id': model_id,
                })
        
        if fields_to_create:
            self.env['ir.model.fields'].create(fields_to_create)

    @api.model
    def _generate_accumulated_template(self, template_xml_id, series_name, interval, specific_fields, interval_unit='Hour'):
        """
        Generates a worksheet template by accumulating fields from lower service intervals.
        Dynamic View Generation: Creates/Updates the Form View based on accumulated fields.

        :param template_xml_id: The XML ID of the worksheet template.
        :param series_name: Name of the equipment series (e.g., 'JD 8230').
        :param interval: The service interval number (e.g., 4500).
        :param specific_fields: Fields specific to this interval.
        :param interval_unit: Unit of the interval (default 'Hour').
        """
        template = self.env.ref(template_xml_id)
        model_id = template.model_id.id
        
        # Helper to parse group from string (e.g., "CLEAN: Fuel Tank")
        def parse_field_string(field_string):
            if ':' in field_string:
                parts = field_string.split(':', 1)
                return parts[0].strip().upper(), parts[1].strip()
            return 'OTHER', field_string

        # 1. Identify Lower Templates
        domain = [('name', 'like', f'{series_name} - % {interval_unit} Service')]
        all_series_templates = self.search(domain)
        
        lower_templates = []
        for t in all_series_templates:
            try:
                # Name format: "JD 8230 - 250 Hour Service" or "Isuzu - 5,000 km Service"
                name_parts = t.name.rsplit(' - ', 1)[1].split(' ')
                # Remove commas and convert to int
                t_interval = int(name_parts[0].replace(',', ''))
                
                # Check if it is a lower interval and a factor
                if t_interval < interval and interval % t_interval == 0:
                    lower_templates.append((t_interval, t))
            except (IndexError, ValueError):
                continue
                
        lower_templates.sort(key=lambda x: x[0])
        
        items_map = {} # Key: field_name, Value: dict config
        fields_to_create = []

        # 2. Process Specific Fields
        for item in specific_fields:
            field_name = item['name']
            group, string = parse_field_string(item['string'])
            # Create/Check field existence
            existing = self.env['ir.model.fields'].search([
                ('name', '=', field_name),
                ('model_id', '=', model_id)
            ], limit=1)
            
            if not existing:
                fields_to_create.append({
                    'name': field_name,
                    'field_description': item['string'],
                    'ttype': item.get('type', 'boolean'), 
                    'model_id': model_id,
                })
            
            items_map[field_name] = {'group': group, 'string': item['string'], 'name': field_name}

        # 3. Process Lower Templates (Harvest Fields from their Views)
        for t_interval, t_record in lower_templates:
            ext_ids = t_record.get_external_id()
            if not ext_ids: 
                continue
            
            full_xml_id = ext_ids.get(t_record.id)
            if not full_xml_id:
                continue
                
            module, name = full_xml_id.split('.')
            if name.startswith('template_'):
                view_name = name.replace('template_', 'view_')
                view_xml_id = f"{module}.{view_name}"
                view = self.env.ref(view_xml_id, raise_if_not_found=False)
                
                if view:
                    # Parse Arch to find fields
                    from lxml import etree
                    doc = etree.fromstring(view.arch)
                    for node in doc.xpath('//field'):
                        f_name = node.get('name')
                        # Ensure it's a checklist field (x_) and not already added (higher priority overrides?)
                        # Logic: Lower intervals are base. Specific fields (already added) override? 
                        # Or if we want to include ALL, we just skip duplicates.
                        if f_name and f_name.startswith('x_') and f_name not in items_map:
                            # Fetch field def to get String/Group
                            f_record = self.env['ir.model.fields'].search([('name', '=', f_name), ('model_id', '=', model_id)], limit=1)
                            if f_record:
                                group, _ = parse_field_string(f_record.field_description)
                                items_map[f_name] = {
                                    'name': f_name,
                                    'string': f_record.field_description,
                                    'group': group
                                }

        if fields_to_create:
            self.env['ir.model.fields'].create(fields_to_create)

        # 4. Generate/Update the Form View for *this* template
        from collections import defaultdict
        grouped_fields = defaultdict(list)
        for fname, info in items_map.items():
            grouped_fields[info['group']].append(fname)
            
        # Build Arch
        arch = """<form><sheet><group>"""
        sorted_groups = sorted(grouped_fields.keys())
        
        for g in sorted_groups:
            arch += f"""<group string="{g}">"""
            for fname in grouped_fields[g]:
                arch += f"""<field name="{fname}"/>"""
            arch += """</group>"""
            
        arch += """</group><group><field name="x_comments"/></group></sheet></form>"""
        
        # Find or Create view for THIS template
        # XML ID convention: template_xxx -> view_xxx
        module, name = template_xml_id.split('.')
        current_view_name = name.replace('template_', 'view_')
        current_view_xml_id = f"{module}.{current_view_name}"
        
        view = self.env.ref(current_view_xml_id, raise_if_not_found=False)
        if view:
            view.write({'arch': arch})
        else:
            # Create new view
            new_view = self.env['ir.ui.view'].create({
                'name': f"{current_view_name}",
                'model': template.model_id.model,
                'arch': arch,
                'type': 'form',
            })
            
            # Create XML ID for persistence
            self.env['ir.model.data'].create({
                'module': module,
                'name': current_view_name,
                'model': 'ir.ui.view',
                'res_id': new_view.id,
                'noupdate': True
            })


