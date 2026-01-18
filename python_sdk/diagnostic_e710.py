import serial
import time

def calculate_checksum(data):
    """Simple sum checksum (two's complement of sum)."""
    total = sum(data)
    return (0 - total) & 0xFF

def calculate_crc16(data):
    """CRC-16 as described in the E710 manual (Reflected, Poly 0x8408)."""
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

def test_protocol(ser, name, header, cmd_byte, data, checksum_type):
    print(f"\n--- Testing Protocol: {name} ---")
    
    # Construct packet
    if header is not None:
        # Standard A0 protocol: A0, Len, Adr, Cmd, Data..., Checksum
        adr = 0xFF
        body = [adr, cmd_byte] + data
        length = len(body)
        packet = [header, length] + body
        
        if checksum_type == "twos":
            cs = calculate_checksum(packet[1:])
            full_packet = packet + [cs]
        elif checksum_type == "crc16":
            crc = calculate_crc16(packet[1:])
            full_packet = packet + [crc & 0xFF, (crc >> 8) & 0xFF]
    else:
        # Ex10 Raw protocol: Len, Adr, Cmd, Data..., CRC16
        adr = 0xFF
        body = [adr, cmd_byte] + data
        length = len(body) + 2 # Adr + Cmd + Data + CRC16 (2 bytes)
        packet = [length] + body
        crc = calculate_crc16(packet)
        full_packet = packet + [crc & 0xFF, (crc >> 8) & 0xFF]

    print(f"Sending: {bytes(full_packet).hex().upper()}")
    ser.write(bytes(full_packet))
    time.sleep(0.5)
    
    if ser.in_waiting:
        resp = ser.read(ser.in_waiting)
        print(f"RESPONSE: {resp.hex().upper()}")
        return True
    else:
        print("No response.")
        return False

def main():
    port = "/dev/ttyUSB0"
    baud = 57600
    
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Opened {port} at {baud} baud.")
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    # Test Commands
    # 0x21: Get Reader Information
    # 0x51: Start Fast Inventory (E710 specific)
    
    commands = [
        ("Get Info", 0x21, []),
        ("Fast Inventory", 0x51, [0x00]), # Target A
    ]
    
    for cmd_name, cmd_byte, cmd_data in commands:
        print(f"\n===== Testing {cmd_name} (0x{cmd_byte:02X}) =====")
        
        # 1. Standard A0 + Two's Comp (Most likely for general Chafon)
        test_protocol(ser, "Standard A0 + Two's Comp", 0xA0, cmd_byte, cmd_data, "twos")
        
        # 2. Standard A0 + CRC16
        test_protocol(ser, "Standard A0 + CRC16", 0xA0, cmd_byte, cmd_data, "crc16")
        
        # 3. Ex10 Raw + CRC16 (As described in manual for Ex10)
        test_protocol(ser, "Ex10 Raw + CRC16", None, cmd_byte, cmd_data, "crc16")

    ser.close()

if __name__ == "__main__":
    main()
