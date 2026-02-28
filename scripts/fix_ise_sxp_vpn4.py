import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests, json
import urllib3
urllib3.disable_warnings()

from creds import ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# Step 1: Check existing SXP VPNs
print("=== Existing SXP VPNs (Local Domains) ===")
r = requests.get(f'{ISE}/ers/config/sxplocalbindings', auth=AUTH, headers=HEADERS, verify=False)
print(f"  Local bindings status: {r.status_code}")

# Try SXP VPN Groups endpoint
r = requests.get(f'{ISE}/ers/config/sxpvpns', auth=AUTH, headers=HEADERS, verify=False)
print(f"  SXP VPNs status: {r.status_code}")
if r.status_code == 200:
    print(json.dumps(r.json(), indent=2))

# Step 2: Create Corp_VN VPN in ISE
print("\n=== Creating VPN 'Corp_VN' in ISE ===")
vpn_payload = {
    "SxpVpn": {
        "sxpVpnName": "Corp_VN"
    }
}
r = requests.post(f'{ISE}/ers/config/sxpvpns', auth=AUTH, headers=HEADERS, json=vpn_payload, verify=False)
print(f"  Status: {r.status_code}")
if r.status_code in [200, 201]:
    print(f"  SUCCESS - VPN Corp_VN created")
    print(f"  Location: {r.headers.get('Location', 'N/A')}")
else:
    print(f"  Response: {r.text[:500]}")

# Step 3: Verify VPNs again
print("\n=== Verify VPNs after creation ===")
r = requests.get(f'{ISE}/ers/config/sxpvpns', auth=AUTH, headers=HEADERS, verify=False)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    print(json.dumps(r.json(), indent=2))
