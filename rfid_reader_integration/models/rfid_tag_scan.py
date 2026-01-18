from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class RfidTagScan(models.Model):
    _name = 'rfid.tag.scan'
    _description = 'RFID Tag Scan Log'
    _order = 'scan_time desc'

    epc_code = fields.Char(string='EPC Code', required=True, index=True)
    scan_time = fields.Datetime(string='Scan Time', default=fields.Datetime.now)
    reader_id = fields.Many2one('rfid.reader', string='Reader')
    reader_ip = fields.Char(string='Source IP')
    location_id = fields.Many2one('stock.location', string='Location', related='reader_id.location_id', store=True)
    product_id = fields.Many2one('product.product', string='Identified Product', compute='_compute_product', store=True)

    @api.depends('epc_code')
    def _compute_product(self):
        for record in self:
            # Simple EPC to Product mapping - in a real scenario, you'd store EPC on product.product
            # For now, we search for products with this EPC in a custom field if it exists
            # Or just leave it for manual association/extension
            product = self.env['product.product'].search([('barcode', '=', record.epc_code)], limit=1)
            record.product_id = product

    @api.model
    def rfid_scan_action(self, tag_epc, reader_ip):
        """
        External API point called by Python Middleware via XML-RPC.
        """
        _logger.info(f"RFID Scan Received: EPC {tag_epc} from {reader_ip}")
        
        # Find reader by IP or Serial Port fallback
        reader = self.env['rfid.reader'].search([
            '|', 
            ('ip_address', '=', reader_ip),
            ('serial_port', '=', reader_ip)
        ], limit=1)
        
        scan_vals = {
            'epc_code': tag_epc,
            'reader_ip': reader_ip,
            'reader_id': reader.id if reader else False,
        }
        
        scan_record = self.create(scan_vals)
        
        # Hook for further processing (e.g. updating stock, move logic)
        return scan_record.id

    @api.model
    def batch_rfid_scan_action(self, tag_epcs, reader_ip):
        """
        Process a batch of tags for Smart Gate Check.
        1. Find products/tyres associated with these EPCs.
        2. Infer which vehicle is being scanned.
        3. Create/Update a Gate Check record.
        """
        _logger.info(f"Batch RFID Scan from {reader_ip}: {tag_epcs}")
        if not tag_epcs:
            return False

        # 1.3 Identify Tyres from RFID Tags
        tyres = self.env['fleet.vehicle.tyre'].search([('rfid_tag', 'in', tag_epcs)])
        if not tyres:
            _logger.info("No known tyres found in batch.")
            return False

        # 1.4 Check Reader Usage
        # We need to find the reader object to check its usage context
        reader = self.env['rfid.reader'].search([
            '|', 
            ('ip_address', '=', reader_ip),
            ('serial_port', '=', reader_ip)
        ], limit=1)

        if reader and reader.usage == 'inventory':
            _logger.info(f"Reader {reader.name} is in INVENTORY mode. Processing stock moves.")
            return self._process_mass_inventory(tyres, reader.location_id)

        # 2. Vehicle Inference (Voting System) - GATE CHECK LOGIC
        vehicle_counts = {}
        for tyre in tyres:
            if tyre.vehicle_id:
                vehicle_counts[tyre.vehicle_id.id] = vehicle_counts.get(tyre.vehicle_id.id, 0) + 1
        
        if not vehicle_counts:
             _logger.info("Tyres found but none are mounted on a vehicle.")
             return False

        # Get the vehicle with the most votes
        best_vehicle_id = max(vehicle_counts, key=vehicle_counts.get)
        vehicle = self.env['fleet.vehicle'].browse(best_vehicle_id)
        
        # Threshold: Optional, ensure a certain % of tyres match?
        # For now, just take the winner.
        
        _logger.info(f"Inferred Vehicle: {vehicle.name} (matches {vehicle_counts[best_vehicle_id]} tyres)")

        # 3. Handle Gate Check
        # Find an open gate check or create a new one
        # Use existing logic from fleet.tyre.gate.check
        
        # Check if there is already a DRAFT gate check for this vehicle today
        gate_check = self.env['fleet.tyre.gate.check'].search([
            ('vehicle_id', '=', vehicle.id),
            ('state', '=', 'draft'),
            ('date', '=', fields.Date.context_today(self))
        ], limit=1)
        
        if not gate_check:
            # Create new
            gate_check = self.env['fleet.tyre.gate.check'].create({
                'vehicle_id': vehicle.id,
                'gate_scan_type': 'check_in', # Default for backend creation, onchange will correct if needed
                # onchange logic typically runs in UI, here we might need to manually trigger or set scan type
                # For simplicity, let's look for last DONE check to determine direction
                # This logic duplicates _onchange_vehicle_id slightly, safe to copy for backend logic
            })
            gate_check._onchange_vehicle_id() # Populate expected lines
            gate_check.write({'date': fields.Date.context_today(self)}) # Ensure date is set


        # 4. Mark Scanned Tyres
        found_tyre_ids = tyres.ids
        
        # Mark matched lines as scanned
        for line in gate_check.line_ids:
            if line.tyre_id.id in found_tyre_ids:
                line.is_scanned = True
        
        # Log the batch scan event
        for epc in tag_epcs:
            self.create({
                'epc_code': epc,
                'reader_ip': reader_ip,
                # 'reader_id': ... 
            })

        # Broadcast event to Web Client (Channel: 'rfid_scans')
        # Payload: { 'epc': '...', 'vehicle_id': ... }
        
        notification_payload = {
            'type': 'batch_scan',
            'scans': tag_epcs,
            'tyre_ids': tyres.ids,
            'inferred_vehicle_id': vehicle.id if vehicle else False,
            'gate_check_id': gate_check.id if gate_check else False
        }
        
        self.env['bus.bus']._sendone('rfid_scans', 'rfid_notification', notification_payload)

        return gate_check.id

    def _process_mass_inventory(self, tyres, location_dest_id):
        """
        Move tyres to the reader's location using stock.move.
        """
        if not location_dest_id:
            _logger.warning("Inventory Reader has no location configured.")
            return False
            
        moves_to_create = []
        for tyre in tyres:
            # Only move if not already there
            if tyre.location_id == location_dest_id:
                continue
                
            # If tyre is mounted on vehicle, should we move it?
            # Usually Inventory Mode implies it's in the warehouse.
            # Let's assume physical reality wins: If scanned in Warehouse, it IS in Warehouse.
            # Potentially unmount from vehicle?
            # For MVP: Just update location.
            
            # Find a product and source location
            product = tyre.product_id
            location_src_id = tyre.location_id.id if tyre.location_id else self.env.ref('stock.stock_location_stock').id
            
            # Create Stock Move
            moves_to_create.append({
                'reference': f'RFID Inventory Scan: {tyre.name}',
                'product_id': product.id,
                'product_uom_qty': 1,
                'product_uom': product.uom_id.id,
                'location_id': location_src_id,
                'location_dest_id': location_dest_id.id,
                # Use lot_id if possible? fleet.vehicle.tyre doesn't always have lot_id depending on config.
                # Assuming serial tracking might be managed differently.
                # If tyre has no stock.lot, we just move product count? 
                # Fleet tyre usually tracks individual item.
            })
            
            # Direct Update as well for immediate visibility
            tyre.location_id = location_dest_id

        if moves_to_create:
            # Batch create moves (simplified)
            # In real system, we should create a Picking or use internal transfer wizard logic.
            # Here we just create done moves.
            Move = self.env['stock.move']
            for move_vals in moves_to_create:
                move = Move.create(move_vals)
                move._action_confirm()
                move._action_assign()
                move.move_line_ids.write({'quantity': 1}) # Set done qty
                move._action_done()
                
        return True
