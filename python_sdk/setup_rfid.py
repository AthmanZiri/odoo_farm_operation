import os
import sys
import subprocess
import time
import platform

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SetupWizard")

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def print_header(text):
    print("\n" + "=" * 50)
    print(f" {text}")
    print("=" * 50)

def setup_dependencies():
    print_header("Step 1: Installing Dependencies")
    print("Checking for 'pyserial'...")
    try:
        import serial
        print(" [OK] pyserial is already installed.")
    except ImportError:
        print(" Installing pyserial...")
        out = run_command(f"{sys.executable} -m pip install pyserial")
        if out is not None:
            print(" [OK] Successfully installed pyserial.")
        else:
            print(" [ERROR] Failed to install pyserial. Please run 'pip install pyserial' manually.")
            return False
    return True

def setup_permissions():
    if platform.system() != "Linux":
        return True
    
    print_header("Step 2: Checking Linux Permissions")
    # This is a bit tricky to automate fully without sudo, but we can try chmod 666 if it fails
    print("If you encounter connection errors, you may need to run:")
    print(" sudo usermod -a -G dialout $USER")
    print("And then RESTART your computer.")
    return True

def detect_serial_ports():
    print_header("Step 3: Detecting RFID Reader")
    ports = []
    if platform.system() == "Windows":
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
    else:
        # Check /dev/ttyUSB*
        stdout = run_command("ls /dev/ttyUSB* 2>/dev/null")
        if stdout:
            ports = stdout.split("\n")

    if not ports:
        print(" [!] No USB/Serial readers found.")
        return None
    
    print(" Found the following devices:")
    for i, port in enumerate(ports):
        print(f"  {i+1}. {port}")
    
    choice = input("\n Select your reader (or press Enter for 1): ")
    if not choice:
        return ports[0]
    try:
        idx = int(choice) - 1
        return ports[idx]
    except:
        return ports[0]

def test_connection(target, is_serial=True, diagnostic=False):
    if diagnostic:
        print_header("Diagnostic Mode: Intensive Hardware Test")
        logging.getLogger("UHFReader").setLevel(logging.DEBUG)
    else:
        print_header("Step 4: Testing Connection")
    
    mode_str = "Serial" if is_serial else "TCP/IP"
    print(f" Connecting to {target} ({mode_str})...")
    try:
        from rfid_driver import UHFReader
        reader = UHFReader(target=target, port=57600 if is_serial else 6000, is_serial=is_serial)
        reader.connect()
        print(" [OK] Connected successfully!")
        
        test_duration = 30 if diagnostic else 5
        print(f" Looking for tags for {test_duration} seconds...")
        print(" (Hold your tags near the reader and try different angles)")
        
        start = time.time()
        tags_found = 0
        while time.time() - start < test_duration:
            tags = reader.inventory_real_time()
            if tags:
                for tag in tags:
                    print(f"  [FOUND] Tag: {tag['epc']} (RSSI: {tag['rssi']})")
                    tags_found += 1
                if not diagnostic:
                    break
            time.sleep(0.5)
        
        if tags_found == 0:
            print(" [!] No tags identified. Check hardware connections or tag compatibility.")
        else:
            print(f" [OK] Successfully identified {tags_found} tags.")
            
        reader.disconnect()
    except Exception as e:
        print(f" [ERROR] Connection failed: {e}")
        if is_serial and platform.system() == "Linux":
            print("\n Try running this command to fix permission issues:")
            print(f" sudo chmod 666 {target}")

def start_middleware(target, is_serial, odoo_url):
    print_header("Step 5: Starting Middleware")
    cmd = [sys.executable, "middleware.py"]
    if is_serial:
        cmd += ["--serial", target, "--port", "57600"]
    else:
        cmd += ["--ip", target, "--port", "6000"]
    
    if odoo_url:
        cmd += ["--odoo-url", odoo_url]

    choice = input("\n Would you like to run the middleware in the background? [y/N]: ").lower()
    
    if choice == 'y':
        log_file = "middleware.log"
        print(f" Starting middleware in background. Logs will be saved to {log_file}")
        
        try:
            if platform.system() == "Windows":
                # On Windows, use start /B or just Popen with creation flags
                subprocess.Popen(cmd, stdout=open(log_file, "a"), stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                # On Linux, use Popen and redirect to log file
                with open(log_file, "a") as f:
                    subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, preexec_fn=os.setpgrp)
            
            print(" [OK] Middleware started in background.")
            print(f" To stop it, you'll need to kill the process or close the terminal.")
        except Exception as e:
            print(f" [ERROR] Failed to start background process: {e}")
    else:
        print(" To run manually, use:")
        print(f" {' '.join(cmd)}")

def main():
    print_header("RFID Reader Automated Setup Wizard")
    print("This script will help you set up your ST-8504 E710 reader.")
    
    if not setup_dependencies():
        return

    setup_permissions()
    
    mode = input("\n Is your reader connected via (1) USB/Serial or (2) Network/IP? [1/2]: ")
    
    target = ""
    is_serial = True
    
    if mode == "2":
        target = input(" Enter Reader IP Address: ")
        is_serial = False
    else:
        target = detect_serial_ports()
        is_serial = True
        
    if target:
        test_connection(target, is_serial)
        
        choice = input("\n [?] Still no tags? Would you like to run Diagnostic Mode (30s intensive test)? [y/N]: ").lower()
        if choice == 'y':
            test_connection(target, is_serial, diagnostic=True)

        print_header("Odoo Integration")
        odoo_url = input(" Enter your Odoo URL (e.g., http://localhost:8069) [Leave blank for mock]: ")
        
        start_middleware(target, is_serial, odoo_url)
    else:
        print("\n Please make sure the reader is plugged into your USB port and try again.")

    print_header("Setup Complete!")
    print("You can now run the middleware to sync with Odoo:")
    print(" python middleware.py")

if __name__ == "__main__":
    main()
