import base64
import io
import zipfile
import logging
from PIL import Image
from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProductBulkImageImport(models.TransientModel):
    _name = 'product.bulk.image.import'
    _description = 'Product Bulk Image Import Wizard'

    zip_file = fields.Binary(string='ZIP File', required=True, attachment=False)
    zip_filename = fields.Char(string='Filename')

    def _resize_image(self, image_data, target_size_kb=200):
        """
        Resizes and compresses image data to be under target_size_kb.
        """
        if not image_data or len(image_data) <= target_size_kb * 1024:
            return image_data

        try:
            img = Image.open(io.BytesIO(image_data))
            # Convert RGBA to RGB if saving as JPEG
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            img_format = 'JPEG' # Force JPEG for better compression/size control
            
            # Iterative quality reduction
            quality = 95
            output = io.BytesIO()
            img.save(output, format=img_format, quality=quality, optimize=True)
            
            while output.tell() > target_size_kb * 1024 and quality > 30:
                quality -= 10
                output = io.BytesIO()
                img.save(output, format=img_format, quality=quality, optimize=True)

            # If still too large, reduce dimensions
            while output.tell() > target_size_kb * 1024:
                width, height = img.size
                if width <= 400 or height <= 400: # Don't go too small
                    break
                new_width = int(width * 0.8)
                new_height = int(height * 0.8)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                img.save(output, format=img_format, quality=quality, optimize=True)

            return output.getvalue()
        except Exception as e:
            _logger.error("Error resizing image: %s", str(e))
            return image_data

    def action_import_images(self):
        self.ensure_one()
        if not self.zip_file:
            raise UserError(_("Please upload a ZIP file."))

        try:
            # Decode the ZIP file
            zip_data = base64.b64decode(self.zip_file)
            zip_buffer = io.BytesIO(zip_data)
        except Exception as e:
            raise UserError(_("Invalid ZIP file: %s") % str(e))

        if not zipfile.is_zipfile(zip_buffer):
            raise UserError(_("The uploaded file is not a valid ZIP file."))

        success_count = 0
        skipped_count = 0
        not_found_refs = []

        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            for file_name in zf.namelist():
                # Skip directories and non-image files
                if file_name.endswith('/') or not file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue

                # Read image data
                image_data = zf.read(file_name)
                
                # Resize image to 200KB
                image_data = self._resize_image(image_data, target_size_kb=200)
                
                # Extract filename without extension and path
                # e.g., 'folder/FURN001.jpg' -> 'FURN001'
                base_name = file_name.split('/')[-1]
                name_without_ext = base_name.rsplit('.', 1)[0]
                
                # Logic to find product
                # 1. Exact match
                product = self.env['product.product'].search([('default_code', '=', name_without_ext)], limit=1)
                
                # 2. Try stripping suffix (e.g., FURN001_1 -> FURN001)
                if not product and '_' in name_without_ext:
                    potential_ref = name_without_ext.rsplit('_', 1)[0]
                    product = self.env['product.product'].search([('default_code', '=', potential_ref)], limit=1)

                if not product:
                    not_found_refs.append(base_name)
                    skipped_count += 1
                    continue

                # Assign Image
                try:
                    image_b64 = base64.b64encode(image_data)
                    
                    if not product.image_1920:
                        # Set as main image
                        product.image_1920 = image_b64
                    else:
                        # Add as extra image
                        self.env['product.image'].create({
                            'product_tmpl_id': product.product_tmpl_id.id,
                            'name': base_name,
                            'image_1920': image_b64,
                        })
                    success_count += 1
                except Exception as e:
                    _logger.error("Failed to import image %s: %s", file_name, str(e))
                    skipped_count += 1

        # Summary message
        message = _("Import completed. %s images imported.") % success_count
        if not_found_refs:
            message += _("\n\n%s files skipped (product not found):\n%s") % (len(not_found_refs), ', '.join(not_found_refs[:20])) # Limit list
            if len(not_found_refs) > 20:
                message += "..."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Result'),
                'message': message,
                'type': 'success' if not not_found_refs else 'warning',
                'sticky': True,
            }
        }
