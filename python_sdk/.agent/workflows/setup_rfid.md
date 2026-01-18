---
description: Automated setup for the ST-8504 E710 UHF RFID Reader
---

This workflow automates the process of installing dependencies, detecting your reader, and testing the connection.

1. **Navigate to the SDK directory**
   Open your terminal in the `rfid_reader_integration/scripts/python_sdk/` folder.

2. **Run the Setup Wizard**
   Execute the automated setup script and follow the on-screen instructions:
   ```bash
   python setup_rfid.py
   ```

3. **Follow the Prompts**
   - The script will automatically install `pyserial`.
   - It will help you find your reader if it's plugged in via USB.
   - It will guide you through fixing permission issues on Linux.
   - Finally, it will run a 5-second scan test to verify everything is working.

4. **Start the Middleware**
   Once the setup is successful, you can start pushing tags to Odoo:
   ```bash
   python middleware.py --ip [READER_IP_OR_PORT] --odoo-url [ODOO_URL]
   ```
