
import xmlrpc.client

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# 1. Find the reader (or create)
reader_ip = "127.0.0.1"
reader_ids = models.execute_kw(db, uid, password, 'rfid.reader', 'search', [[
    '|', ('ip_address', '=', reader_ip), ('serial_port', '=', reader_ip)
]])

if not reader_ids:
    print("Creating new reader...")
    reader_id = models.execute_kw(db, uid, password, 'rfid.reader', 'create', [{
        'name': 'Mock Inventory Reader',
        'ip_address': reader_ip,
        'usage': 'inventory',
        # Need a location. Let's find Stock
        'location_id': 8 # Usually Stock? Let's search.
    }])
else:
    reader_id = reader_ids[0]
    print(f"Updating reader {reader_id}...")
    models.execute_kw(db, uid, password, 'rfid.reader', 'write', [[reader_id], {
        'usage': 'inventory',
        'location_id': 8 # Fallback, assumes demo data
    }])

# Verify Location
loc_ids = models.execute_kw(db, uid, password, 'stock.location', 'search', [[('usage', '=', 'internal')]])
if loc_ids:
    target_loc = loc_ids[0]
    print(f"Setting location to {target_loc}")
    models.execute_kw(db, uid, password, 'rfid.reader', 'write', [[reader_id], {
        'location_id': target_loc
    }])
else:
    print("No internal location found!")

print("Reader configured for INVENTORY.")
