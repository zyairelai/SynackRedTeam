# Synack DUO Automation Guide

Automate Synack DUO Push requests without needing a physical device and save the required token for further automation processes.

## Prerequisites
- Python3
- Libraries: pycryptodome, requests, beautifulsoup4

Install the necessary libraries:
```bash
pip install -r requirements.txt
```

## Setting up ruo
1. Execute `main.py`.
2. Enter the code from the QR code (use an alternative QR code scanner) or via the link provided in the email (accessible on a desktop).

## Using synconnect (Selenium-based token generation)
### Preparation
1. Complete the ruo setup.
2. In `synconnect.py`, update your credentials at lines 11 and 12.
3. To run in headless mode (without opening a browser window), set `options.headless = True` on line 37.
4. (Optional) Customize Token Storage Location
   - To save the token in a different location, modify the `file_path` on line 15.
   - By default, the token is stored in `/tmp/synacktoken`.

### Running the Script
Execute the script using Python:
```bash
python3 synconnect.py
```

## Using synconnect_cli (Requests-based token generation)
### Initial Setup
1. After setting up ruo, capture the login process with Burp Suite.
2. Locate the `/frame/v4/auth/prompt/data` request and note down the index and key from its response.
3. Update `synconnect_cli.py` with your credentials on lines 11 and 12.
4. Set the `index` (e.g., `phone2`) on line 16 and `key` (e.g., `DPXXXXXXXXXX`) on line 17.
5. (Optional) Customize Token Storage Location
   - To save the token in a different location, modify the `file_path` on line 18.
   - By default, the token is stored in `/tmp/synacktoken`.

### Running the Script
Execute using Python:
```bash
python3 synconnect_cli.py
```

## Known Issue and Solution
For the automation to work correctly, the device set up for this script must be the primary device. If it's not, request to make it primary or do so manually by removing previous devices and re-adding them later.

Alternatively, use `synconnect_cli.py` with the correct configuration to circumvent this issue.