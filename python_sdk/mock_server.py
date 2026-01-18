
import socket
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockServer")

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

def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 6000))
    server.listen(1)
    logger.info("Mock Server listening on 6000...")
    
    tags_db = [
        "E20000195607022216503895", # Tyre A1
        "E20000195607022216503896", # Tyre A2
    ]

    while True:
        try:
            conn, addr = server.accept()
            logger.info(f"Connected by {addr}")
            
            while True:
                data = conn.recv(1024)
                if not data: break
                
                # Check for Inventory Command (0x01) at index 2
                # len check
                if len(data) > 2 and data[2] == 0x01:
                    # Send a random burst of tags (1-3 tags)
                    count = random.randint(1, 3)
                    for _ in range(count):
                        tag_hex = random.choice(tags_db)
                        tag_epc = bytes.fromhex(tag_hex)
                        epc_len = len(tag_epc)
                        rssi = 0x81
                        
                        payload = bytes([0x03, 0x01, 0x01, epc_len]) + tag_epc + bytes([rssi])
                        
                        addr_byte = 0x01
                        cmd_byte = 0x01 
                        
                        body_pre_crc = [addr_byte, cmd_byte] + list(payload)
                        length_byte = len(body_pre_crc) + 2
                        
                        packet = [length_byte] + body_pre_crc
                        crc = calc_crc(packet)
                        
                        final = bytes(packet) + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
                        
                        conn.sendall(final)
                        time.sleep(0.05)
                        
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    run_server()
