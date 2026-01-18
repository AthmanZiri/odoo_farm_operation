
import xmlrpc.client
import time

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

TARGET_LOC_ID = 35 # From config output
TAGS = [
    "E20000195607022216503895",
    "E20000195607022216503896", 
    "E20000195607022216503897",
    "E20000195607022216503898",
    "E20000195607022216509999"
]

print("Verifying Stock Moves...")
# 1. properties
# Get tyres
tyres = models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'search_read', [
    [('rfid_tag', 'in', TAGS)], ['id', 'name', 'product_id', 'location_id']
])

print(f"Found {len(tyres)} tyres in Odoo matching tags.")
if not tyres:
    print("No tyres found! Backend logic won't process moves for unknown tags.")
    exit(0)

product_ids = [t['product_id'][0] for t in tyres if t['product_id']]

# Check Tyres Location
print(f"Checking {len(tyres)} tyres...")
for tyre in tyres:
    print(f"Tyre {tyre['name']} Location: {tyre['location_id']}")

# Check moves ANYWHERE
moves = models.execute_kw(db, uid, password, 'stock.move', 'search_read', [
    [
        ('product_id', 'in', product_ids)
    ],
    ['id', 'product_id', 'location_dest_id', 'state']
])

print(f"Found {len(moves)} total stock moves for these products.")

for move in moves:
    print(f"- Move {move['id']} [{move['state']}] -> {move['location_dest_id'][1]}")

if len(moves) > 0:
    print("SUCCESS: Inventory moves created.")
else:
    print("FAILURE: No moves found.")
