import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests, json, time
import urllib3
urllib3.disable_warnings()

from creds import ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# Fabric switch connections to recreate with Corp_VN
connections = [
    {'id': '464b0ad4-1a2b-4863-805b-9408b01e61a7', 'name': 'SDA-Edge1', 'ip': '10.1.0.3'},
    {'id': 'e9a196c3-aea3-406a-8ad1-2e19de2a3323', 'name': 'SDA-Edge2', 'ip': '10.1.0.4'},
    {'id': 'e8aa35a7-5179-4f34-890e-e4744875a9ea', 'name': 'SDA-Border', 'ip': '10.1.0.2'},
]

# Step 1: Delete existing connections
print("=== Step 1: Delete existing SXP connections ===\n")
for conn in connections:
    print(f"  Deleting {conn['name']} ({conn['ip']})...")
    r = requests.delete(f'{ISE}/ers/config/sxpconnections/{conn["id"]}',
                        auth=AUTH, headers=HEADERS, verify=False)
    print(f"    Status: {r.status_code} {'OK' if r.status_code == 204 else r.text[:200]}")

print("\n  Waiting 5 seconds for ISE to process deletes...")
time.sleep(5)

# Step 2: Recreate with Corp_VN VPN
print("\n=== Step 2: Recreate with sxpVpn = Corp_VN ===\n")
for conn in connections:
    print(f"  Creating {conn['name']} ({conn['ip']}) with VPN=Corp_VN...")
    payload = {
        "ERSSxpConnection": {
            "sxpPeer": conn['name'],
            "sxpVpn": "Corp_VN",
            "sxpNode": "ISE",
            "ipAddress": conn['ip'],
            "sxpMode": "LISTENER",
            "sxpVersion": "VERSION_4",
            "enabled": True
        }
    }
    r = requests.post(f'{ISE}/ers/config/sxpconnections',
                      auth=AUTH, headers=HEADERS, json=payload, verify=False)
    print(f"    Status: {r.status_code}")
    if r.status_code == 201:
        print(f"    SUCCESS - Location: {r.headers.get('Location', 'N/A')}")
    else:
        print(f"    Error: {r.text[:300]}")

# Step 3: Verify
print("\n=== Step 3: Verify all SXP connections ===\n")
time.sleep(2)
r = requests.get(f'{ISE}/ers/config/sxpconnections', auth=AUTH, headers=HEADERS, verify=False)
all_conns = r.json().get('SearchResult', {}).get('resources', [])
print(f"  Total connections: {len(all_conns)}\n")

for c in all_conns:
    r2 = requests.get(f'{ISE}/ers/config/sxpconnections/{c["id"]}', auth=AUTH, headers=HEADERS, verify=False)
    d = r2.json().get('ERSSxpConnection', {})
    print(f"  {d.get('sxpPeer'):15s}  IP: {d.get('ipAddress'):18s}  VPN: {d.get('sxpVpn'):10s}  Mode: {d.get('sxpMode'):10s}  Enabled: {d.get('enabled')}")

print("\nDone. Wait ~30 seconds for SXP to reconverge.")
print("Then verify on switches: show cts sxp sgt-map vrf Corp_VN")
