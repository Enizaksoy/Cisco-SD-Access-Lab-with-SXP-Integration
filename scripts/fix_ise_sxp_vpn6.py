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

# Fabric switch SXP connections to update
connections = {
    '464b0ad4-1a2b-4863-805b-9408b01e61a7': {'name': 'SDA-Edge1', 'ip': '10.1.0.3'},
    'e9a196c3-aea3-406a-8ad1-2e19de2a3323': {'name': 'SDA-Edge2', 'ip': '10.1.0.4'},
    'e8aa35a7-5179-4f34-890e-e4744875a9ea': {'name': 'SDA-Border', 'ip': '10.1.0.2'},
}

print("=== Updating SXP connections: sxpVpn default -> Corp_VN ===\n")

for conn_id, info in connections.items():
    print(f"--- {info['name']} ({info['ip']}) ---")

    payload = {
        "ERSSxpConnection": {
            "id": conn_id,
            "sxpPeer": info['name'],
            "sxpVpn": "Corp_VN",
            "sxpNode": "ISE",
            "ipAddress": info['ip'],
            "sxpMode": "LISTENER",
            "sxpVersion": "VERSION_4",
            "enabled": True
        }
    }

    r = requests.put(f'{ISE}/ers/config/sxpconnections/{conn_id}',
                     auth=AUTH, headers=HEADERS, json=payload, verify=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        print(f"  SUCCESS - sxpVpn = Corp_VN")
    else:
        print(f"  Error: {r.text[:300]}")

# Verify all connections
print("\n=== Verifying all SXP connections ===\n")
r = requests.get(f'{ISE}/ers/config/sxpconnections', auth=AUTH, headers=HEADERS, verify=False)
all_conns = r.json().get('SearchResult', {}).get('resources', [])

for conn in all_conns:
    r2 = requests.get(f'{ISE}/ers/config/sxpconnections/{conn["id"]}', auth=AUTH, headers=HEADERS, verify=False)
    d = r2.json().get('ERSSxpConnection', {})
    print(f"  {d.get('sxpPeer'):15s}  IP: {d.get('ipAddress'):18s}  VPN: {d.get('sxpVpn'):10s}  Enabled: {d.get('enabled')}")

print("\nDone. Wait ~30 seconds for SXP to reconverge, then verify on switches:")
print("  show cts sxp sgt-map vrf Corp_VN")
