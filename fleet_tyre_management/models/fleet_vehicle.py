from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    axle_config_id = fields.Many2one('fleet.tyre.axle.config', string='Axle Configuration')
    
    tyre_ids = fields.One2many('fleet.vehicle.tyre', 'vehicle_id', string='tyres', domain=[('state', '=', 'mounted')])
    tyre_count = fields.Integer(compute='_compute_tyre_count', string='tyre Count')
    
    tyre_layout_html = fields.Html(compute='_compute_tyre_layout_html', string='Tyre Layout')

    def _compute_tyre_count(self):
        for record in self:
            record.tyre_count = len(record.tyre_ids)

    trailer_id = fields.Many2one('fleet.vehicle', string='Attached Trailer', domain=[('axle_config_id', '!=', False)])

    @api.depends('axle_config_id', 'tyre_ids', 'tyre_ids.position_id', 'trailer_id.axle_config_id', 'trailer_id.tyre_ids')
    def _compute_tyre_layout_html(self):
        for main_vehicle in self:
            if not main_vehicle.axle_config_id:
                main_vehicle.tyre_layout_html = '<p class="text-muted text-center">No Axle Configuration selected</p>'
                continue
            
            # Prepare list of units to render: (vehicle, config, title)
            units = [(main_vehicle, main_vehicle.axle_config_id, main_vehicle.name)]
            if main_vehicle.trailer_id and main_vehicle.trailer_id.axle_config_id:
                units.append((main_vehicle.trailer_id, main_vehicle.trailer_id.axle_config_id, "Trailer: " + main_vehicle.trailer_id.name))

            whole_html = '<div class="tyre-chassis" style="display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 20px; background: #f8f9fa; border-radius: 8px;">'

            for i, (vehicle, config, label) in enumerate(units):
                if i > 0:
                     # Connector
                     whole_html += '<div style="width: 10px; height: 30px; background: #333;"></div>'

                # Unit Label
                whole_html += f'<div class="text-muted small mb-1">{label}</div>'

                # Chassis
                whole_html += '<div class="chassis-frame" style="width: 200px; display: flex; flex-direction: column; gap: 40px; border-left: 5px solid #333; border-right: 5px solid #333; padding: 10px 0; min-height: 100px;">'
                
                # Group positions by axle
                positions = config.position_ids.sorted(lambda r: (r.axle_number, r.sequence))
                axles = {}
                for pos in positions:
                    if pos.axle_number not in axles: axles[pos.axle_number] = []
                    axles[pos.axle_number].append(pos)

                for axle_num in sorted(axles.keys()):
                    # Axle Line
                    whole_html += f'<div class="axle-row" style="display: flex; justify-content: space-between; align-items: center; position: relative;">'
                    whole_html += f'<div style="width: 100%; height: 4px; background: #555; position: absolute; top: 50%; z-index: 0;"></div>'
                    
                    # Left Wheels
                    left_wheels = [p for p in axles[axle_num] if p.side == 'left']
                    whole_html += '<div class="wheels-left" style="display: flex; gap: 5px; z-index: 1;">'
                    for pos in left_wheels:
                        tyre = vehicle.tyre_ids.filtered(lambda t: t.position_id == pos)
                        color = "#ccc" # default gray
                        title = "Empty"
                        if tyre:
                            title = f"{tyre.name} ({tyre.current_tread_depth}mm)"
                            if tyre.current_tread_depth > 5: color = "#28a745"
                            elif tyre.current_tread_depth > 2: color = "#ffc107"
                            else: color = "#dc3545"
                            
                        whole_html += f'<div title="{title}" style="width: 30px; height: 50px; background: {color}; border: 2px solid #333; border-radius: 4px;"></div>'
                    whole_html += '</div>'
                    
                    # Center Wheels (Motorcycles/Trikes)
                    center_wheels = [p for p in axles[axle_num] if p.side == 'center']
                    if center_wheels:
                         whole_html += '<div class="wheels-center" style="display: flex; gap: 5px; z-index: 1; background: #fff;">' # White bg to hide axle line
                         for pos in center_wheels:
                             tyre = vehicle.tyre_ids.filtered(lambda t: t.position_id == pos)
                             color = "#ccc"
                             title = "Empty"
                             if tyre:
                                title = f"{tyre.name} ({tyre.current_tread_depth}mm)"
                                if tyre.current_tread_depth > 5: color = "#28a745"
                                elif tyre.current_tread_depth > 2: color = "#ffc107"
                                else: color = "#dc3545"
                             whole_html += f'<div title="{title}" style="width: 30px; height: 50px; background: {color}; border: 2px solid #333; border-radius: 4px;"></div>'
                         whole_html += '</div>'

                    # Right Wheels
                    right_wheels = [p for p in axles[axle_num] if p.side == 'right']
                    whole_html += '<div class="wheels-right" style="display: flex; gap: 5px; z-index: 1;">'
                    for pos in reversed(right_wheels): 
                         tyre = vehicle.tyre_ids.filtered(lambda t: t.position_id == pos)
                         color = "#ccc"
                         title = "Empty"
                         if tyre:
                            title = f"{tyre.name} ({tyre.current_tread_depth}mm)"
                            if tyre.current_tread_depth > 5: color = "#28a745"
                            elif tyre.current_tread_depth > 2: color = "#ffc107"
                            else: color = "#dc3545"
                         whole_html += f'<div title="{title}" style="width: 30px; height: 50px; background: {color}; border: 2px solid #333; border-radius: 4px;"></div>'
                    whole_html += '</div>'
                    
                    whole_html += '</div>' # End Axle Row
                
                whole_html += '</div>' # End Vehicle Chassis
            
            whole_html += '</div>' # End Main Container
            main_vehicle.tyre_layout_html = whole_html

    tyre_layout_json = fields.Text(compute='_compute_tyre_layout_json')

    @api.depends('axle_config_id', 'tyre_ids', 'tyre_ids.position_id', 'trailer_id.axle_config_id', 'trailer_id.tyre_ids', 'trailer_id.tyre_ids.position_id')
    def _compute_tyre_layout_json(self):
        import json
        for main_vehicle in self:
            data = {
                'units': [],
                'editable': True
            }

            units = [(main_vehicle, main_vehicle.axle_config_id, main_vehicle.name, 'main')]
            if main_vehicle.trailer_id and main_vehicle.trailer_id.axle_config_id:
                units.append((main_vehicle.trailer_id, main_vehicle.trailer_id.axle_config_id, main_vehicle.trailer_id.name, 'trailer'))
            
            for vehicle, config, label, unit_type in units:
                if not config: continue
                
                unit_data = {
                    'label': label,
                    'type': unit_type,
                    'vehicle_id': vehicle.id,
                    'axles': {}
                }

                # Get positions
                positions = config.position_ids.sorted(lambda r: (r.axle_number, r.sequence))
                for pos in positions:
                    axle_num = str(pos.axle_number)
                    if axle_num not in unit_data['axles']:
                        unit_data['axles'][axle_num] = {
                            'left': [],
                            'right': [],
                            'center': []
                        }
                    
                    tyre = vehicle.tyre_ids.filtered(lambda t: t.position_id == pos)
                    
                    slot = {
                        'position_id': pos.id,
                        'position_code': pos.code,
                        'position_name': pos.name,
                        'side': pos.side,
                        'tyre_id': tyre.id if tyre else False,
                        'tyre_name': tyre.name if tyre else False,
                        'tread': tyre.current_tread_depth if tyre else 0,
                        'status': tyre.state if tyre else 'empty',
                        # Add simple color helper
                        'color_class': 'success' 
                    }
                    if tyre:
                        if tyre.current_tread_depth < 2: slot['color_class'] = 'danger'
                        elif tyre.current_tread_depth < 5: slot['color_class'] = 'warning'
                    else:
                        slot['color_class'] = 'empty'

                    unit_data['axles'][axle_num][pos.side].append(slot)
                
                data['units'].append(unit_data)
            
            
            # Use a custom handler to stringify NewId or other non-JSON types
            def json_serial(obj):
                return str(obj)

            main_vehicle.tyre_layout_json = json.dumps(data, default=json_serial)

    def action_view_tyres(self):
        self.ensure_one()
        return {
            'name': 'tyres',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.tyre',
            'view_mode': 'kanban,list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }
