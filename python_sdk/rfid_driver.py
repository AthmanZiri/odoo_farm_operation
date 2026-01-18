import socket
import struct
import time
import logging
import serial # Requires pyserial

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UHFReader")

class UHFReader:
    def __init__(self, target, port=6000, address=0x00, is_serial=False):
        """
        Initialize the UHF Reader client.
        :param target: IP address (if network) or Serial Port (e.g. /dev/ttyUSB0, COM3).
        :param port: TCP port (default 6000) OR BaudRate (if serial, typically 57600 or 115200).
        :param address: Reader address (default 0x01).
        :param is_serial: Set to True for USB/Serial connection.
        """
        self.target = target
        self.port_or_baud = port
        self.address = address
        self.is_serial = is_serial
        self.connection = None
        self.connected = False
        
    def connect(self):
        """Establish connection (TCP or Serial)."""
        try:
            if self.is_serial:
                logger.info(f"Connecting to Serial: {self.target} @ {self.port_or_baud}")
                self.connection = serial.Serial(
                    port=self.target,
                    baudrate=self.port_or_baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5
                )
                if self.connection.is_open:
                    self.connected = True
            else:
                logger.info(f"Connecting to TCP: {self.target}:{self.port_or_baud}")
                self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.connection.settimeout(5)
                self.connection.connect((self.target, self.port_or_baud))
                self.connected = True
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False
            raise

    def disconnect(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("Disconnected")

    def _calculate_checksum(self, data):
        """
        Calculate CRC-16 as specified in the E710 manual.
        Reflected, Polynomial 0x8408.
        """
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

    def send_command(self, cmd, data=None):
        """
        Send a command to the reader using Ex10 Raw protocol.
        frame: Len | Addr | Cmd | Data | CRC16_LSB | CRC16_MSB
        Len = len(Addr + Cmd + Data + CRC)
        """
        if not self.connected:
            raise Exception("Not connected")

        if data is None:
            data = []
            
        # Frame construction
        addr = self.address
        
        # Length = 1(Addr) + 1(Cmd) + len(Data) + 2(CRC)
        length = 1 + 1 + len(data) + 2
        
        packet_pre_crc = [length, addr, cmd] + list(data)
        crc = self._calculate_checksum(packet_pre_crc)
        
        packet = packet_pre_crc + [crc & 0xFF, (crc >> 8) & 0xFF]
        
        packet_bytes = bytearray(packet)
        logger.debug(f"Sending: {packet_bytes.hex().upper()}")
        
        if self.is_serial:
            # Flush input buffer to remove any old garbage/noise
            try:
                self.connection.reset_input_buffer()
            except Exception:
                pass # Ignore if not supported or failed
            self.connection.write(packet_bytes)
        else:
            self.connection.sendall(packet_bytes)

    def receive_response(self):
        """
        Receive response from reader in Ex10 Raw format.
        """
        try:
            # Helper to read N bytes
            def read_n(n):
                if self.is_serial:
                    return self.connection.read(n)
                else:
                    return self.connection.recv(n)

            # First byte is Length
            len_byte = read_n(1)
            if not len_byte:
                return None
            
            length = len_byte[0]
            
            # SANITY CHECK: Packet length
            # Standard responses are usually < 60 bytes. 
            # If we see something huge (like 200+), it's likely noise or we lost sync.
            if length < 3 or length > 64:
                logger.warning(f"Invalid packet length: {length} (Likely Sync Error). Flushing buffer.")
                if self.is_serial:
                    try:
                        self.connection.reset_input_buffer()
                    except:
                        pass
                return None
                
            # Read the rest of the packet (length bytes)
            # length includes: Addr(1) + Cmd(1) + Data(N) + CRC(2)
            # So payload to read is length bytes.
            
            payload = read_n(length)
            if not payload or len(payload) < length:
                logger.warning(f"Incomplete packet: expected {length} bytes, got {len(payload) if payload else 0}")
                return None
            
            # Full data for CRC check: [Length] + [Payload]
            full_data = list(len_byte) + list(payload)
            # logger.debug(f"RAW RECV: {bytearray(full_data).hex().upper()}")
            
            # Verify CRC
            calculated_crc = self._calculate_checksum(full_data[:-2])
            received_crc = payload[-2] | (payload[-1] << 8)
            
            if calculated_crc != received_crc:
                logger.warning(f"CRC mismatch: Calculated {calculated_crc:04X}, Received {received_crc:04X}")
                return None
            
            addr = payload[0]
            cmd = payload[1]
            data = payload[2:-2]
            
            return {
                'addr': addr,
                'cmd': cmd,
                'data': data
            }
            
        except (socket.timeout, serial.SerialTimeoutException):
            return None
        except Exception as e:
            logger.error(f"Receive error: {e}")
            # If serial error, maybe try to reconnect or just wait?
            if self.is_serial:
                time.sleep(0.1)
            return None

    def inventory_real_time(self):
        """
        Send Inventory Command (0x01) for E710.
        Returns list of dicts: [{'epc': '...', 'rssi': -10, 'ant': 1}]
        Protocol: Ex10 Raw + CRC16
        Cmd: 0x01 | 04 | 00
        Resp: Len | Adr | 01 | Ant(1) | ?(2) | EPCLen(1) | EPC(N) | RSSI(1) | CRC
        """
        cmd = 0x01
        # Q=4, Session=0
        data = [0x04, 0x00] 
        self.send_command(cmd, data)
        
        tags = []
        start_time = time.time()
        
        # Read loop for multiple tag responses
        # The reader sends one packet per tag found.
        while (time.time() - start_time) < 0.5: # 500ms listen window
            response = self.receive_response()
            if not response:
                continue
            
            if response['cmd'] == 0x01:
                # Parse Tag Data
                # Data structure found in diagnostics:
                # Byte 0: ? (03) - Likely Antenna or Info
                # Byte 1: ? (01)
                # Byte 2: ? (01)
                # Byte 3: EPC Length (0C = 12)
                # Byte 4..N: EPC
                # Byte N+1: RSSI
                
                payload = response['data']
                if len(payload) > 4:
                    # ant = payload[0] # Assuming first byte is Ant
                    # For now, let's just grab the EPC based on length byte
                    
                    try:
                        epc_len = payload[3]
                        if len(payload) >= 4 + epc_len + 1:
                            epc_bytes = payload[4 : 4 + epc_len]
                            rssi = payload[4 + epc_len]
                            ant = payload[0]
                            
                            epc_hex = epc_bytes.hex().upper()
                            
                            tag = {'epc': epc_hex, 'rssi': rssi, 'ant': ant}
                            tags.append(tag)
                            logger.debug(f"Tag Found: {tag}")
                    except Exception as e:
                        logger.error(f"Error parsing tag packet: {e}")
            else:
                 logger.debug(f"Unknown response cmd: {response['cmd']:02x}")
                 
        return tags

    def get_reader_information(self):
        """Command 0x70 ? or 0x21 ?"""
        # 0x21 is usually Get Hardware Version
        # 0x70 is Get baseband?
        cmd = 0x21
        self.send_command(cmd)
        return self.receive_response()

if __name__ == "__main__":
    # Example Usage
    reader = UHFReader("192.168.1.190", 6000)
    try:
        reader.connect()
        while True:
            reader.inventory_real_time()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(e)
    finally:
        reader.disconnect()
