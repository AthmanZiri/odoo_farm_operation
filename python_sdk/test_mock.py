import socket
import threading
import time
from rfid_driver import UHFReader

def mock_reader_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 6000))
    server.listen(1)
    print("Mock Server listening...")
    
    conn, addr = server.accept()
    print(f"Mock Server connected by {addr}")
    
    while True:
        try:
            data = conn.recv(1024)
            if not data: break
            
            # Check for Inventory Command (0x01)
            # cmd is at index 2 (Len, Addr, Cmd) -> 04 01 01 ...
            if len(data) > 2 and data[2] == 0x01:
                print("Mock Server received Inventory Command")
                # Send back a fake tag response
                # Data structure expected by rfid_driver.py inventory_real_time:
                # Byte 0-2: Info/Padding
                # Byte 3: EPC Length
                # Byte 4..N: EPC
                # Byte N+1: RSSI
                
                # Mock a list of tags (Vehicle A has 4 tyres, plus 1 alien)
                # We will cycle through them or send them sequentially
                
                tags_db = [
                    "E20000195607022216503895", # Tyre 1 (Vehicle A)
                    "E20000195607022216503896", # Tyre 2 (Vehicle A)
                    "E20000195607022216503897", # Tyre 3 (Vehicle A)
                    "E20000195607022216503898", # Tyre 4 (Vehicle A)
                    "E20000195607022216509999", # Alien Tyre
                ]
                
                import random
                tag_hex = random.choice(tags_db)
                
                tag_epc = bytes.fromhex(tag_hex)
                epc_len = len(tag_epc)
                rssi = 0x81
                
                # Payload construction
                payload = bytes([0x03, 0x01, 0x01, epc_len]) + tag_epc + bytes([rssi])
                
                # Frame: Length | Addr | Cmd | Payload | CRC_LSB | CRC_MSB
                # Length = 1(Addr) + 1(Cmd) + len(payload) + 2(CRC)
                # Packet sent over wire: [Length] [Body...] [CRC]
                
                # Unlike A0 protocol, Ex10 Raw starts with Length (for the body+crc)
                
                addr = 0x01
                cmd = 0x01 # Response to Inventory
                
                body_pre_crc = [addr, cmd] + list(payload)
                length_byte = len(body_pre_crc) + 2 # +2 for CRC
                
                packet_for_crc = [length_byte] + body_pre_crc
                
                # Calculate CRC16 (Reflected 0x8408)
                def calc_crc(data):
                    polynomial = 0x8408
                    crc = 0xFFFF
                    for byte in data:
                        crc ^= byte
                        for _ in range(8):
                            if crc & 0x0001:
                                crc = (crc >> 1) ^ polynomial
                            else:
                                crc >>= 1
                    return crc

                crc_val = calc_crc(packet_for_crc)
                
                final_packet = bytes(packet_for_crc) + bytes([crc_val & 0xFF, (crc_val >> 8) & 0xFF])
                
                time.sleep(0.05) # Faster capability for batch sim
                conn.sendall(final_packet)
                
        except Exception as e:
            print(f"Mock Server Error: {e}")
            break
            
    conn.close()
    server.close()

if __name__ == "__main__":
    t = threading.Thread(target=mock_reader_server)
    t.daemon = True
    t.start()
    
    time.sleep(1)
    
    reader = UHFReader("127.0.0.1", 6000)
    reader.connect()
    print("Sending Inventory...")
    tags = reader.inventory_real_time()
    print(f"Tags found: {tags}")
    reader.disconnect()
