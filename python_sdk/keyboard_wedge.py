import argparse
import time
import logging
from pynput.keyboard import Controller, Key
from rfid_driver import UHFReader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("KeyboardWedge")

def main():
    parser = argparse.ArgumentParser(description="RFID Keyboard Wedge")
    parser.add_argument("--ip", help="Reader IP Address")
    parser.add_argument("--port", type=int, default=None, help="Reader Port (TCP) or Baud Rate")
    parser.add_argument("--serial", help="Serial Port (e.g. /dev/ttyUSB0)")
    args = parser.parse_args()

    # Connection Logic
    if args.serial:
        target = args.serial
        # Default baud rate for these readers is typically 57600
        port = args.port if args.port else 57600
        is_serial = True
        logger.info(f"Connecting to Serial: {target} @ {port}")
    elif args.ip:
        target = args.ip
        # Default TCP port is 6000
        port = args.port if args.port else 6000
        is_serial = False
        logger.info(f"Connecting to TCP: {target}:{port}")
    else:
        logger.error("Please provide --ip or --serial")
        return

    reader = UHFReader(target, port=port, is_serial=is_serial)
    keyboard = Controller()

    try:
        reader.connect()
        logger.info("Ready to scan. Place cursor in your document!")
        
        seen_tags = {}
        
        while True:
            tags = reader.inventory_real_time()
            current_time = time.time()
            
            for tag in tags:
                epc = tag['epc']
                
                # Debounce to prevent rapid-fire typing of the same tag
                last_seen = seen_tags.get(epc, 0)
                if current_time - last_seen > 2.0: # Wait 2 seconds before re-typing same tag
                    logger.info(f"Typing: {epc}")
                    
                    # Type the EPC followed by Enter
                    keyboard.type(epc)
                    keyboard.press(Key.enter)
                    keyboard.release(Key.enter)
                    
                    seen_tags[epc] = current_time
            
            # Clean cache
            seen_tags = {k:v for k,v in seen_tags.items() if current_time - v < 60}
            
            time.sleep(0.05) 
            
    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
