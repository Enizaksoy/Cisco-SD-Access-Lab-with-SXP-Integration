import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
import urllib3
urllib3.disable_warnings()

from creds import ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# Step 1: Get all SXP connections
print("=== Current SXP Connections ===")
r = requests.get(f'{ISE}/ers/config/sxpconnections', auth=AUTH, headers=HEADERS, verify=False)
print(f"Status: {r.status_code}")
data = r.json()

connections = data.get('SearchResult', {}).get('resources', [])
print(f"Found {len(connections)} SXP connections\n")

# Step 2: Get details of each connection
for conn in connections:
    conn_id = conn['id']
    conn_name = conn.get('name', 'unknown')
    r2 = requests.get(f'{ISE}/ers/config/sxpconnections/{conn_id}', auth=AUTH, headers=HEADERS, verify=False)
    if r2.status_code == 200:
        detail = r2.json().get('SxpConnection', {})
        print(f"ID: {conn_id}")
        print(f"  Name: {detail.get('name')}")
        print(f"  Description: {detail.get('description')}")
        print(f"  Peer IP: {detail.get('sxpPeer')}")
        print(f"  SXP VPN: {detail.get('sxpVpn')}")
        print(f"  SXP Node: {detail.get('sxpNode')}")
        print(f"  SXP Mode: {detail.get('sxpMode')}")
        print(f"  IP Version: {detail.get('ipVersion')}")
        print(f"  Enabled: {detail.get('enabled')}")
        print()

print("\n=== Done ===")
