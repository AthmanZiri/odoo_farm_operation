
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
]

# 1. Create Vehicle
veh_id = models.execute_kw(db, uid, password, 'fleet.vehicle', 'create', [{
    'model_id': 1, # Assumes demo data model exists 
    'license_plate': 'TEST-RFID-GATE',
}])
print(f"Created Vehicle: {veh_id}")

# 2. Update Tyres to Mounted on this Vehicle
tyre_ids = models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'search', [[('rfid_tag', 'in', TAGS)]])
print(f"Found {len(tyre_ids)} tyres to mount.")

models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'write', [tyre_ids, {
    'vehicle_id': veh_id,
    'state': 'mounted'
}])

print("Tyres mounted on vehicle.")
