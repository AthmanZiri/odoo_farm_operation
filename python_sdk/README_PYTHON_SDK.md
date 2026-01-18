# ST-8504 E710 UHF Reader Python SDK Manual

This manual provides instructions on how to use the Python SDK for the ST-8504 E710 UHF RFID Reader. The SDK allows for both network (TCP/IP) and serial (USB/RS232) communication with the reader.

## Installation

### Prerequisites
- Python 3.8 or higher.
- `pyserial` library (required for Serial/USB connections).

### Quick Start (Recommended)
We have provided an **Automated Setup Wizard** that handles installation and connection tests for you.

1. Open your terminal in this folder.
2. Run:
   ```bash
   python setup_rfid.py
   ```
3. Follow the on-screen instructions to automatically detect your reader and test your first scan.
4. **New**: Choose to start the middleware in the **background**. The script will handle the launch and save all logs to `middleware.log`.

---

### Manual Setup (Advanced)
If you prefer to set things up yourself, follow these steps:

1. Install dependencies:
   ```bash
   pip install pyserial
   ```

## Files in the SDK
- `rfid_driver.py`: Core driver containing the `UHFReader` class and low-level protocol implementation.
- `middleware.py`: High-level wrapper for integrating the reader with external systems like Odoo.
- `keyboard_wedge.py`: Utility to simulate keyboard input from scanned RFID tags.

## Connection Modes

### 1. TCP/IP Mode (Ethernet)
Used for connecting to the reader over a network. Follow these steps for a successful setup:

**Step 1: Check Network Connectivity**
- Ensure your computer is on the same subnet as the reader (e.g., `192.168.1.x`).
- Ping the reader's IP to verify connectivity: `ping 192.168.1.190`.

**Step 2: Verify Port Availability**
- The default port is usually `6000`. Ensure this port is not blocked by a firewall on your network.

**Step 3: Hardware Initialization**
```python
from rfid_driver import UHFReader

# Initialize reader with IP and Port
reader = UHFReader(target="192.168.1.190", port=6000, is_serial=False)
reader.connect()
```

### 2. Plug & Play: USB / Serial Mode
Use this if you are plugging the reader directly into your computer using a USB cable.

#### **Step 1: Find where the reader is "plugged in"**
Your computer gives the reader a special name when you plug it in.
- **On Windows**:
  1. Right-click the **Start button** and pick **Device Manager**.
  2. Look for **Ports (COM & LPT)**.
  3. You will see something like `USB Serial Port (COM3)`. Remember that name: **COM3**.
- **On Linux**:
  1. Open a "Terminal" window.
  2. Type this command and press Enter: `ls /dev/ttyUSB*`
  3. It will show something like `/dev/ttyUSB0`. That is your reader's name.

#### **Step 2: Give your computer permission (Linux Only)**
If you are on Linux, you need to tell the computer it's okay for you to talk to the reader. Run this simple command:
```bash
sudo chmod 666 /dev/ttyUSB0
```
*(Replace `/dev/ttyUSB0` with the name you found in Step 1)*

#### **Step 3: Tell the code to use the reader**
Now, just put that name into your code like this:

```python
from rfid_driver import UHFReader

# 1. Put the name you found in Step 1 here (e.g., "COM3" or "/dev/ttyUSB0")
my_reader_name = "/dev/ttyUSB0" 

# 2. Connect to the reader
reader = UHFReader(target=my_reader_name, port=57600, is_serial=True)
reader.connect()

print("Successfully connected to the reader!")
```

## API Reference: `UHFReader` Class

### `connect()`
Establishes a connection to the reader based on the initialization parameters.

### `disconnect()`
Closes the active connection.

### `inventory_real_time()`
Performs a real-time inventory scan.
- **Returns**: A list of dictionaries, one for each tag found.
  - `epc`: The Electronic Product Code (hex string).
  - `rssi`: Received Signal Strength Indicator.
  - `ant`: The antenna number that detected the tag.

**Example:**
```python
tags = reader.inventory_real_time()
for tag in tags:
    print(f"Detected EPC: {tag['epc']} (RSSI: {tag['rssi']})")
```

### `get_reader_information()`
Retrieves hardware information from the reader.

## Protocol Details (Advanced)
This driver implements the **Reader Protocol for Ex10 Series (E710)**.
- **Protocol Type**: Raw Frame (No `0xA0` header used in older Chafon models).
- **Checksum**: CRC-16 (Polynomial `0x8408`).
- **Inventory Command**: `0x01` (Standard Inventory).
- **Default Address**: `0x00`.

## Advanced Usage: Middleware & Odoo Integration

The `middleware.py` script demonstrates how to:
- Connect to a reader using command-line arguments.
- Implement a **debounce** mechanism to avoid duplicate scans within a short period.
- Push scanned tags to an external API (e.g., Odoo's XML-RPC).

### Running the Middleware
**Important:** You must specify your Odoo database name using `--db` if it is not "odoo".

```bash
python middleware.py --ip 192.168.1.200 --odoo-url http://your-odoo-server:8069 --db your_database_name
```
For Serial connection:
```bash
python middleware.py --serial /dev/ttyUSB0 --odoo-url http://localhost:8069 --db your_database_name
```

### Debouncing Logic
The middleware maintains a `seen_tags` dictionary to prevent hammering the backend with the same tag multiple times per second:
```python
if current_time - last_seen > 5: # 5-second debounce
    odoo.push_tag(epc, args.ip)
    seen_tags[epc] = current_time
```

## Common Mistakes & Tips

### 1. "NameError: name '...' is not defined"
Ensure you call methods on the **reader instance**. 
- **Incorrect**: `get_reader_information()`
- **Correct**: `reader.get_reader_information()`

### 2. Using the wrong "Reader Name"
If you unplug and replug the reader, the name might change (e.g., from `COM3` to `COM4` or `/dev/ttyUSB0` to `/dev/ttyUSB1`). Always double-check Step 1 if you can't connect.

### 3. No tags found (`[]`)
If `inventory_real_time()` returns an empty list `[]`:
- The tags might be too far away (try holding them within 1 foot of the antenna).
- The tag might be oriented incorrectly (try rotating the tag).
- Ensure the antenna cable is screwed in tightly.

## Troubleshooting 

| Issue | Possible Cause | Solution |
| :--- | :--- | :--- |
| **Connection Failed** | Wrong Port/IP or Permissions | Re-run Step 1 & 2. Check cables. |
| **No Tags Found** | Range or Orientation | Move tag closer; rotate 90 degrees. |
| **Empty Info Response** | Reader is busy or Timeout | Try calling the function again after a second. |
| **Permission Denied** | Linux security | Run the `sudo chmod` command from Step 2. |

### Still having trouble?
Try running the mock test to verify your Python environment is set up correctly:
```bash
python test_mock.py
```
This simulates a reader and should always show "tags" being found, helping you confirm if the issue is with the **code** or the **hardware**.
