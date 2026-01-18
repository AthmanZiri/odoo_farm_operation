
import xmlrpc.client

url = "http://localhost:8090"
db = "trye_management"
username = "admin"
password = "admin"

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Reset Reader to Gate Mode
reader_ip = "127.0.0.1"
reader_ids = models.execute_kw(db, uid, password, 'rfid.reader', 'search', [[
    '|', ('ip_address', '=', reader_ip), ('serial_port', '=', reader_ip)
]])

if reader_ids:
    print(f"Resetting User {reader_ids[0]} to GATE mode.")
    models.execute_kw(db, uid, password, 'rfid.reader', 'write', [[reader_ids[0]], {
        'usage': 'gate',
        # location_id doesn't matter for gate
    }])
else:
    print("Reader not found to reset.")
