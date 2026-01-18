
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
    "E20000195607022216503896"
]

print("Checking Tyre Assignments...")
tyres = models.execute_kw(db, uid, password, 'fleet.vehicle.tyre', 'search_read', [[('rfid_tag', 'in', TAGS)]], {'fields': ['name', 'vehicle_id', 'rfid_tag']})

for tyre in tyres:
    print(f"Tag {tyre['rfid_tag']} -> Tyre {tyre['name']} -> Vehicle {tyre['vehicle_id']}")
