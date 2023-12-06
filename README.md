# Synack DUO automation based on ruo
Approve Duo Push requests without a phone and save the token required for further automation.

# Requirements
1. Python
2. PyCryptoDome

`pip install pycryptodome`

3. Requests 

`pip install requests`

# Usage
1. Run main.py
2. Insert code from the qr code (using another qrcode scanner) or by clicking on the link in the email (on your desktop)
3. Wait
4. ....
5. Profit
6. Modify synaconnect.py with your credentials in lines 11,12.
7. Modify line 37 setting options.headless = True , if you don't want to see the browser.

# Known issue
The device order must have the automation of this script as primary.  If you don't have it as such request it to be made primary or make it primary by removing previous devices, and re-add them later
