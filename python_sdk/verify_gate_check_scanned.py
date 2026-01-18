
import xmlrpc.client

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

print("Verifying Gate Check...")

# 1. Find latest gate check for Test Vehicle
print("Searching for Gate Check for TEST-RFID-GATE...")
veh_ids = models.execute_kw(db, uid, password, 'fleet.vehicle', 'search', [[('license_plate', '=', 'TEST-RFID-GATE')]])
if not veh_ids:
    print("Vehicle not found!")
    exit(1)

check_ids = models.execute_kw(db, uid, password, 'fleet.tyre.gate.check', 'search', [[('vehicle_id', '=', veh_ids[0])]], {'limit': 1, 'order': 'id desc'})

if not check_ids:
    print("FAILURE: No Gate Check created.")
    exit(1)

check = models.execute_kw(db, uid, password, 'fleet.tyre.gate.check', 'read', [check_ids], {'fields': ['name', 'vehicle_id', 'line_ids']})[0]
print(f"Latest Check: {check['name']} for Vehicle {check['vehicle_id'][1]}")

if check['vehicle_id'][1] != 'Nissan/Micra/TEST-RFID-GATE':
    print(f"WARNING: Vehicle mismatch. Expected TEST-RFID-GATE, got {check['vehicle_id'][1]}")

# 2. Check Lines
lines = models.execute_kw(db, uid, password, 'fleet.tyre.gate.check.line', 'read', [check['line_ids']], {'fields': ['tyre_id', 'is_scanned']})

print(f"Found {len(lines)} lines.")
scanned_count = 0
for line in lines:
    status = "SCANNED (GREEN)" if line['is_scanned'] else "MISSING (RED)"
    if line['is_scanned']: scanned_count += 1
    print(f"- Tyre {line['tyre_id'][1]}: {status}")

if scanned_count > 0:
    print(f"SUCCESS: {scanned_count} tyres marked as scanned.")
else:
    print("FAILURE: No tyres marked as scanned.")
