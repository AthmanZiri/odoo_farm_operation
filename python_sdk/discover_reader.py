import serial
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ControlDiscovery")

def calculate_checksum_twos(data):
    total = sum(data)
    return (0 - total) & 0xFF

def test_config(port, baud, addr, cmd_code, dtr, rts):
    try:
        ser = serial.Serial(port, baud, timeout=0.2)
        # Set flow control lines
        ser.dtr = dtr
        ser.rts = rts
        time.sleep(0.2) # Wait for hardware 
        
        # A0 | Len | Addr | Cmd | CS
        payload = [0x03, addr, cmd_code]
        cs = calculate_checksum_twos(payload)
        packet = bytes([0xA0] + payload + [cs])
        
        logger.debug(f"Baud:{baud} Addr:{hex(addr)} DTR:{dtr} RTS:{rts} -> {packet.hex()}")
        ser.write(packet)
        time.sleep(0.05)
        resp = ser.read(100)
        ser.close()
        
        if resp:
            logger.info(f"!!! SUCCESS !!!")
            logger.info(f"Params: Baud:{baud} Addr:{hex(addr)} DTR:{dtr} RTS:{rts}")
            logger.info(f"Recv: {resp.hex()}")
            return True
    except Exception as e:
        pass
    return False

if __name__ == "__main__":
    port = "/dev/ttyUSB0"
    baud = 57600 # User confirmed
    addr = 0xFF # Broadcast usually works
    cmd = 0x21 # Get Information
    
    print(f"Starting CONTROL LINE discovery on {port}...")
    found = False
    for dtr in [True, False]:
        for rts in [True, False]:
            if test_config(port, baud, addr, cmd, dtr, rts):
                found = True
                break
        if found: break
    
    # Try another address if FF fails
    if not found:
        for addr in [0x00, 0x01]:
             if test_config(port, baud, addr, cmd, True, True):
                 found = True
                 break

    if not found:
        print("\n[FAILED] Still no response with control line variation.")
