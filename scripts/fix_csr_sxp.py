import sys, json, requests, urllib3
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
urllib3.disable_warnings()
from netmiko import ConnectHandler

from creds import CSR_PASS, CSR_SECRET, CSR_USER, ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
ISE_AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# Create SXP connection with correct sxpNode
print("=== Creating ISE SXP connection → CSR ===")
sxp_data = {
    "ERSSxpConnection": {
        "ipAddress": "192.168.244.16",
        "sxpPeer": "CSR_SXP",
        "sxpVpn": "default",
        "sxpNode": "ISE",
        "sxpMode": "LISTENER",
        "sxpVersion": "VERSION_4",
        "enabled": True
    }
}

resp = requests.post(
    f"{ISE}/ers/config/sxpconnections",
    auth=ISE_AUTH, headers=HEADERS, json=sxp_data, verify=False
)
print(f"Status: {resp.status_code}")
if resp.status_code == 201:
    print(f"Created: {resp.headers.get('Location', '')}")
else:
    print(resp.text[:500])

# Wait and verify
import time
print("\nWaiting 20 seconds for SXP to establish...")
time.sleep(20)

# Check CSR SXP status
print("\n=== Checking CSR SXP ===")
csr = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.16',
    'username': CSR_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}
conn = ConnectHandler(**csr)
conn.enable()

print("\n--- show cts sxp connections brief ---")
print(conn.send_command("show cts sxp connections brief"))

print("\n--- show cts sxp sgt-map brief ---")
print(conn.send_command("show cts sxp sgt-map brief"))

print("\n--- show cts role-based sgt-map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

conn.disconnect()
print("\nDone.")
