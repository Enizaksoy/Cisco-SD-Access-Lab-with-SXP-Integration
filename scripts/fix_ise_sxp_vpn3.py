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

# SXP connections to update (fabric switches only, not CSR)
connections_to_fix = {
    '464b0ad4-1a2b-4863-805b-9408b01e61a7': {'name': 'SDA-Edge1', 'ip': '10.1.0.3'},
    'e9a196c3-aea3-406a-8ad1-2e19de2a3323': {'name': 'SDA-Edge2', 'ip': '10.1.0.4'},
    'e8aa35a7-5179-4f34-890e-e4744875a9ea': {'name': 'SDA-Border', 'ip': '10.1.0.2'},
}

for conn_id, info in connections_to_fix.items():
    print(f"\n=== Updating {info['name']} ({info['ip']}) sxpVpn: default -> Corp_VN ===")

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
        print(f"  SUCCESS - sxpVpn updated to Corp_VN")
    else:
        print(f"  Response: {r.text[:500]}")

# Verify
print("\n\n=== Verifying updated connections ===")
for conn_id, info in connections_to_fix.items():
    r = requests.get(f'{ISE}/ers/config/sxpconnections/{conn_id}', auth=AUTH, headers=HEADERS, verify=False)
    detail = r.json().get('ERSSxpConnection', {})
    print(f"  {detail.get('sxpPeer')}: sxpVpn = {detail.get('sxpVpn')}")

print("\nDone. SXP bindings should now be installed in Corp_VN VRF on the switches.")
print("Wait ~30 seconds and verify with: show cts sxp sgt-map vrf Corp_VN")
