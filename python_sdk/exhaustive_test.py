import sys
import os
import time
import logging

# Add the script directory to the path so we can import our modified rfid_driver
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_driver import UHFReader

# Enable debug logging
logging.getLogger("UHFReader").setLevel(logging.DEBUG)

def main():
    reader = UHFReader("/dev/ttyUSB0", port=57600, address=0x00, is_serial=True)
    try:
        reader.connect()
        print("Connected.")

        # Test various commands with various data
        tests = [
            ("0x01 (No Data)", 0x01, []),
            ("0x01 (Q=4, S=0)", 0x01, [0x04, 0x00]),
            ("0x01 (Q=4, S=0, Mask=0, AdrT=0, LenT=0)", 0x01, [0x04, 0x00, 0x00, 0x00, 0x00]),
            ("0x80 (No Data)", 0x80, []),
            ("0x80 (Q=4, S=0)", 0x80, [0x04, 0x00]),
            ("0x51 (Target A)", 0x51, [0x00]),
            ("0x51 (No Data)", 0x51, []),
        ]

        for name, cmd, data in tests:
            print(f"\n--- Testing {name} ---")
            reader.send_command(cmd, data)
            resp = reader.receive_response()
            if resp:
                print(f"RESPONSE: {resp}")
            else:
                print("No response.")
            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
