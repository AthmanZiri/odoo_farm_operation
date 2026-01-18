import time
import logging
import argparse
from rfid_driver import UHFReader

import xmlrpc.client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Middleware")

class OdooConnector:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        
    def connect(self):
        """Connect to Odoo."""
        if not self.url:
            logger.warning("No Odoo URL provided, running in Mock mode.")
            return
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                logger.info(f"Connected to Odoo: {self.db} as {self.username}")
            else:
                logger.error("Failed to authenticate with Odoo. Check credentials.")
        except Exception as e:
            logger.error(f"Odoo connection error: {e}")

    def push_tag(self, tag_epc, reader_ip):
        """Send tag to Odoo using the rfid_reader_integration module."""
        logger.info(f"Pushing Tag {tag_epc} from {reader_ip} to Odoo...")
        if self.models and self.uid:
            try:
                self.models.execute_kw(self.db, self.uid, self.password,
                    'rfid.tag.scan', 'rfid_scan_action', [tag_epc, reader_ip])
                logger.debug("Successfully pushed to Odoo.")
            except Exception as e:
                logger.error(f"Failed to push to Odoo: {e}")

    def push_batch(self, tag_epcs, reader_ip):
        """Send a batch of tags to Odoo using rfid.tag.scan batch_rfid_scan_action."""
        if not tag_epcs:
            return
        logger.info(f"Pushing Batch of {len(tag_epcs)} tags from {reader_ip} to Odoo...")
        if self.models and self.uid:
            try:
                self.models.execute_kw(self.db, self.uid, self.password,
                    'rfid.tag.scan', 'batch_rfid_scan_action', [list(tag_epcs), reader_ip])
                logger.info("Successfully pushed batch to Odoo.")
            except Exception as e:
                logger.error(f"Failed to push batch to Odoo: {e}")

def main():
    parser = argparse.ArgumentParser(description="RFID Middleware")
    parser.add_argument("--ip", help="Reader IP Address (e.g., 192.168.1.200)")
    parser.add_argument("--port", type=int, default=None, help="Reader Port (TCP) or Baud Rate (Serial)")
    parser.add_argument("--serial", help="Serial Port (e.g., /dev/ttyUSB0 or COM3)")
    parser.add_argument("--odoo-url", help="Odoo URL (e.g. http://localhost:8069)")
    parser.add_argument("--db", default="odoo", help="Odoo Database name")
    parser.add_argument("--user", default="admin", help="Odoo Username")
    parser.add_argument("--pwd", default="admin", help="Odoo Password")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger("UHFReader").setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    # Determine connection type
    if args.serial:
        # Serial Mode
        target = args.serial
        port_or_baud = args.port if args.port else 57600 # Default baud
        is_serial = True
        logger.info(f"Mode: Serial ({target} @ {port_or_baud})")
    elif args.ip:
        # TCP Mode
        target = args.ip
        port_or_baud = args.port if args.port else 6000
        is_serial = False
        logger.info(f"Mode: TCP/IP ({target}:{port_or_baud})")
    else:
        logger.error("Must specify either --ip or --serial")
        return

    reader = UHFReader(target, port=port_or_baud, is_serial=is_serial)
    odoo = OdooConnector(args.odoo_url, args.db, args.user, args.pwd)
    
    try:
        odoo.connect()
        reader.connect()
        
        # Keep track of recently seen tags to avoid spamming Odoo
        seen_tags = {} 
        
        # Buffer logic
        tag_buffer = set()
        last_tag_time = 0
        
        logger.info("Starting Inventory Loop...")
        while True:
            tags = reader.inventory_real_time()
            current_time = time.time()
            
            if tags:
                for tag in tags:
                    epc = tag['epc']
                    tag_buffer.add(epc)
                    last_tag_time = current_time
                    logger.debug(f"Buffered Tag: {epc}")
            
            # Flush Buffer Logic
            # If we have tags AND (it's been > 1.0s since last tag OR buffer is huge)
            if tag_buffer and (current_time - last_tag_time > 1.0):
                odoo.push_batch(tag_buffer, target)
                tag_buffer.clear()
            
            time.sleep(0.1) # Prevent CPU hogging
            
    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.exception("Error in main loop")
        # Attempt to flush buffer if valid tags were stuck
        if 'tag_buffer' in locals() and tag_buffer:
             logger.info("Flushing buffer before exit...")
             odoo.push_batch(tag_buffer, target)
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
