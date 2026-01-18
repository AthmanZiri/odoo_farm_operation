
import xmlrpc.client

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Check fields
fields = models.execute_kw(db, uid, password, 'stock.move', 'fields_get', [], {'attributes': ['string', 'type', 'required']})
print(f"stock.move fields: {sorted(fields.keys())}")  # Sorted for readability

move_vals = {
    # 'name': 'RFID Inventory Scan: Test', # Commented out to test dependency
    'product_id': 58,
    'product_uom_qty': 1,
    'product_uom': 1,
    'location_id': 5,
    'location_dest_id': 35,
}

print(f"Creating move with: {move_vals}")

try:
    move_id = models.execute_kw(db, uid, password, 'stock.move', 'create', [move_vals])
    print(f"Success! Move ID: {move_id}")
except Exception as e:
    print(f"FAILURE: {e}")
