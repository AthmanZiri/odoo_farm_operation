
import xmlrpc.client

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

TAGS = [
    "E20000195607022216503895",
    "E20000195607022216503896", 
    "E20000195607022216503897",
    "E20000195607022216503898",
    "E20000195607022216509999"
]

# Ensure a generic tyre product exists
# Check valid types
res = models.execute_kw(db, uid, password, 'product.template', 'fields_get', [['type'], ['selection']])
type_selection = dict(res['type']['selection'])
print(f"Valid types: {type_selection.keys()}")

prod_type = 'product' if 'product' in type_selection else 'consu' # Fallback to consu if product/storable not found
if 'storable' in type_selection: prod_type = 'storable' # Odoo 17+ naming?

product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[('name', '=', 'Mock Tyre Product')]])
if not product_ids:
    print(f"Creating product with type={prod_type}")
    product_id = models.execute_kw(db, uid, password, 'product.product', 'create', [{
        'name': 'Mock Tyre Product',
        'type': prod_type
    }])
else:
    product_id = product_ids[0]

print(f"Using Product ID: {product_id}")

for i, tag in enumerate(TAGS):
    # Check if exists
    exists = models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'search', [[('rfid_tag', '=', tag)]])
    if not exists:
        print(f"Creating tyre for tag {tag}")
        models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'create', [{
            'name': f'MOCK-TYRE-{i+1}',
            'rfid_tag': tag,
            'product_id': product_id,
        }])
    else:
        print(f"Tyre for {tag} already exists.")

print("Tyres seeded.")

# Debug: Check Product UOM and Location
prod = models.execute_kw(db, uid, password, 'product.product', 'read', [[product_id], ['uom_id']])
print(f"Product UOM: {prod[0]['uom_id']}")

# Check default stock location
try:
    stock_loc = models.execute_kw(db, uid, password, 'ir.model.data', 'check_object_reference', ['stock', 'stock_location_stock'])
    print(f"Default Stock Location: {stock_loc}")
except Exception as e:
    print(f"Error finding stock location: {e}")
