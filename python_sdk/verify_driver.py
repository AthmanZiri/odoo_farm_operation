import sys
import os
import time
import logging

# Add the script directory to the path so we can import our modified rfid_driver
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_driver import UHFReader

# Enable debug logging to see packets
logging.getLogger("UHFReader").setLevel(logging.DEBUG)

def test_inventory():
    # Use the parameters confirmed to work: 57600 baud, /dev/ttyUSB0
    # Use reader address 0x00 as identified in diagnostics
    reader = UHFReader("/dev/ttyUSB0", port=57600, address=0x00, is_serial=True)
    
    try:
        reader.connect()
        print("Connected to reader.")
        
        print("\n--- Testing Get Reader Information (0x21) ---")
        info = reader.get_reader_information()
        if info:
            print(f"Reader Info Response: {info}")
        else:
            print("Failed to get reader information.")

        print("\n--- Testing Inventory (0x89) ---")
        for i in range(2):
            tags = reader.inventory_real_time()
            print(f"0x89 Attempt {i+1}: {tags}")

        print("\n--- Testing Standard Inventory (0x01) ---")
        reader.send_command(0x01)
        resp = reader.receive_response()
        print(f"0x01 Response: {resp}")

        print("\n--- Testing Fast Inventory (0x51) ---")
        reader.send_command(0x51, [0x00]) # Target A
        resp = reader.receive_response()
        print(f"0x51 Response: {resp}")

        print("\n--- Testing Another Fast Inventory (0xEE) ---")
        reader.send_command(0xEE)
        resp = reader.receive_response()
        print(f"0xEE Response: {resp}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        reader.disconnect()

if __name__ == "__main__":
    test_inventory()
