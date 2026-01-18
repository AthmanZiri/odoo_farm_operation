import serial
import time
import sys

def sniff(port, baud):
    print(f"\n[*] Sniffing {port} at {baud} bps for 10 seconds...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
        start_time = time.time()
        buffer = b''
        while time.time() - start_time < 10:
            data = ser.read(100)
            if data:
                print(f"[FOUND DATA] {data.hex()}")
                buffer += data
            if len(buffer) > 200: break
        ser.close()
        if buffer:
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    port = "/dev/ttyUSB0"
    bauds = [57600, 115200, 38400, 9600, 230400, 460800, 1000000]
    
    print(f"Starting PASSIVE SNIFFER on {port}...")
    print("If the reader is in 'Always On' mode, it will be spitting out tags.")
    
    for baud in bauds:
        if sniff(port, baud):
            print(f"\n[!!!] DATA DETECTED at {baud} bps!")
            break
    else:
        print("\n[SILENCE] No data received from reader in passive mode.")
