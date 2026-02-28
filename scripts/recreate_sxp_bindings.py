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

# First, check current state and try to understand the correct JSON format
print("=== Current bindings ===")
r = requests.get(f'{ISE}/ers/config/sxplocalbindings', auth=AUTH, headers=HEADERS, verify=False)
print(f"  Count: {r.json().get('SearchResult', {}).get('total', 0)}")

# Try creating one test binding to find correct field names
print("\n=== Testing JSON format ===")

# Attempt 1: standard field names
formats = [
    {
        "ERSSxpLocalBindings": {
            "ipFirstAddress": "172.16.100.10",
            "sgt": "4",
            "sxpVpn": "Corp_VN",
            "bindingName": "test1"
        }
    },
    {
        "ERSSxpLocalBindings": {
            "ipFirstAddress": "172.16.100.10",
            "sgtValue": 4,
            "sxpVpn": "Corp_VN",
            "bindingName": "test1"
        }
    },
    {
        "ERSSxpLocalBindings": {
            "ipFirstAddress": "172.16.100.10",
            "sgt": "Employees",
            "sxpVpn": "Corp_VN",
            "bindingName": "test1"
        }
    },
]

for i, payload in enumerate(formats):
    print(f"\n  Attempt {i+1}: {json.dumps(payload, indent=2)}")
    r = requests.post(f'{ISE}/ers/config/sxplocalbindings',
                      auth=AUTH, headers=HEADERS, json=payload, verify=False)
    print(f"  Status: {r.status_code}")
    if r.status_code == 201:
        print(f"  SUCCESS! Location: {r.headers.get('Location')}")
        # Get the created binding to see the format
        loc = r.headers.get('Location', '')
        if loc:
            bid = loc.split('/')[-1]
            r2 = requests.get(f'{ISE}/ers/config/sxplocalbindings/{bid}',
                              auth=AUTH, headers=HEADERS, verify=False)
            print(f"  Created: {json.dumps(r2.json(), indent=2)}")
            # Clean up test
            requests.delete(f'{ISE}/ers/config/sxplocalbindings/{bid}',
                            auth=AUTH, headers=HEADERS, verify=False)
        break
    else:
        print(f"  Error: {r.text[:300]}")
