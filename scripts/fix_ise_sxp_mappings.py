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

# Step 1: Get all SXP local bindings (static mappings)
print("=== Current SXP Local Bindings ===\n")
r = requests.get(f'{ISE}/ers/config/sxplocalbindings', auth=AUTH, headers=HEADERS, verify=False)
bindings = r.json().get('SearchResult', {}).get('resources', [])
print(f"Found {len(bindings)} bindings\n")

binding_details = []
for b in bindings:
    r2 = requests.get(f'{ISE}/ers/config/sxplocalbindings/{b["id"]}', auth=AUTH, headers=HEADERS, verify=False)
    detail = r2.json()
    top_key = list(detail.keys())[0]
    d = detail[top_key]
    binding_details.append({'id': b['id'], 'detail': d, 'top_key': top_key})
    print(f"  ID: {b['id']}")
    print(f"    IP: {d.get('ipFirstAddress', 'N/A')}")
    print(f"    SGT: {d.get('sgt', 'N/A')}")
    print(f"    VPN: {d.get('sxpVpn', 'N/A')}")
    print(f"    Name: {d.get('bindingName', 'N/A')}")
    print()

# Step 2: Delete old bindings and recreate with Corp_VN
print("=== Recreating bindings with VPN=Corp_VN ===\n")
for bd in binding_details:
    d = bd['detail']
    bid = bd['id']
    top_key = bd['top_key']

    ip = d.get('ipFirstAddress', '')
    sgt = d.get('sgt', '')
    name = d.get('bindingName', '')

    print(f"  Updating {ip} (SGT={sgt})...")

    # Delete old
    r_del = requests.delete(f'{ISE}/ers/config/sxplocalbindings/{bid}',
                            auth=AUTH, headers=HEADERS, verify=False)
    print(f"    Delete: {r_del.status_code}")

    # Recreate with Corp_VN
    new_payload = {
        top_key: {
            "bindingName": name,
            "ipFirstAddress": ip,
            "sgt": sgt,
            "sxpVpn": "Corp_VN"
        }
    }
    # Include subnet if present
    if d.get('ipSecondAddress'):
        new_payload[top_key]['ipSecondAddress'] = d['ipSecondAddress']

    r_create = requests.post(f'{ISE}/ers/config/sxplocalbindings',
                             auth=AUTH, headers=HEADERS, json=new_payload, verify=False)
    print(f"    Create: {r_create.status_code} {'OK' if r_create.status_code == 201 else r_create.text[:200]}")

# Step 3: Verify
print("\n=== Verify updated bindings ===\n")
time.sleep(2)
r = requests.get(f'{ISE}/ers/config/sxplocalbindings', auth=AUTH, headers=HEADERS, verify=False)
bindings = r.json().get('SearchResult', {}).get('resources', [])
for b in bindings:
    r2 = requests.get(f'{ISE}/ers/config/sxplocalbindings/{b["id"]}', auth=AUTH, headers=HEADERS, verify=False)
    d = r2.json().get(list(r2.json().keys())[0], {})
    print(f"  {d.get('ipFirstAddress', 'N/A'):20s}  SGT: {d.get('sgt', 'N/A'):20s}  VPN: {d.get('sxpVpn', 'N/A')}")

print("\nDone. Wait ~30 seconds then check: show cts sxp sgt-map vrf Corp_VN")
