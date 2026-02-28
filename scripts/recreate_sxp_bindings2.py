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

# Step 1: Get SGT list to understand ID format
print("=== SGT List ===")
r = requests.get(f'{ISE}/ers/config/sgt', auth=AUTH, headers=HEADERS, verify=False)
sgts = r.json().get('SearchResult', {}).get('resources', [])
sgt_map = {}
for s in sgts:
    r2 = requests.get(f'{ISE}/ers/config/sgt/{s["id"]}', auth=AUTH, headers=HEADERS, verify=False)
    detail = r2.json().get('Sgt', {})
    print(f"  {detail.get('name'):25s}  value={detail.get('value')}  id={s['id']}")
    sgt_map[detail.get('value')] = s['id']
    sgt_map[detail.get('name')] = s['id']

print(f"\nSGT ID map: {json.dumps(sgt_map, indent=2)}")

# Step 2: Try different formats with SGT ID reference
print("\n=== Testing formats ===")

# The error said valid props: ipFirstAddress, bindingName, ipAddressOrHost, sxpVpn, link, id, description, sgt, name, vns
# Maybe sgt needs to be the SGT name or the full ID reference

test_sgt_id = sgt_map.get(4, sgt_map.get('Employees', ''))
formats = [
    # Format 1: sgt as SGT name string
    {
        "ERSSxpLocalBindings": {
            "bindingName": "test_binding",
            "ipFirstAddress": "172.16.100.10",
            "sgt": "Employees",
            "sxpVpn": "Corp_VN",
            "vns": "Corp_VN"
        }
    },
    # Format 2: sgt as numeric string, vns added
    {
        "ERSSxpLocalBindings": {
            "bindingName": "test_binding",
            "ipFirstAddress": "172.16.100.10",
            "sgt": "4",
            "sxpVpn": "Corp_VN",
            "vns": "Corp_VN"
        }
    },
    # Format 3: ipAddressOrHost instead of ipFirstAddress
    {
        "ERSSxpLocalBindings": {
            "bindingName": "test_binding",
            "ipAddressOrHost": "172.16.100.10",
            "sgt": "Employees",
            "sxpVpn": "Corp_VN",
            "vns": "Corp_VN"
        }
    },
    # Format 4: Minimal - just required fields
    {
        "ERSSxpLocalBindings": {
            "ipAddressOrHost": "172.16.100.10",
            "sgt": "Employees",
            "sxpVpn": "Corp_VN"
        }
    },
]

for i, payload in enumerate(formats):
    print(f"\n  Attempt {i+1}: {json.dumps(payload)}")
    r = requests.post(f'{ISE}/ers/config/sxplocalbindings',
                      auth=AUTH, headers=HEADERS, json=payload, verify=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 201:
        print(f"  SUCCESS! Location: {r.headers.get('Location')}")
        loc = r.headers.get('Location', '')
        if loc:
            bid = loc.split('/')[-1]
            r2 = requests.get(f'{ISE}/ers/config/sxplocalbindings/{bid}',
                              auth=AUTH, headers=HEADERS, verify=False)
            print(f"  Created binding detail: {json.dumps(r2.json(), indent=2)}")
            # Delete the test binding
            requests.delete(f'{ISE}/ers/config/sxplocalbindings/{bid}',
                            auth=AUTH, headers=HEADERS, verify=False)
            print(f"  (test binding deleted)")
        break
    else:
        try:
            err = r.json()
            print(f"  Error: {json.dumps(err)[:500]}")
        except:
            print(f"  Error: {r.text[:500]}")
