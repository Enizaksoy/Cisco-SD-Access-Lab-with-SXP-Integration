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

# Step 1: Get the existing VPN details to see the format
print("=== Existing VPN detail ===")
r = requests.get(f'{ISE}/ers/config/sxpvpns/ff539573-b748-4008-8200-a20573427619',
                 auth=AUTH, headers=HEADERS, verify=False)
print(json.dumps(r.json(), indent=2))

# Step 2: Try creating Corp_VN with the correct format
print("\n=== Creating Corp_VN VPN ===")
# Try matching the existing VPN's JSON structure
existing = r.json()
# Get the key name from the existing response
top_key = list(existing.keys())[0]
print(f"  Top-level key: {top_key}")
existing_detail = existing[top_key]
print(f"  Fields: {list(existing_detail.keys())}")

# Now create with matching format
payload = {
    top_key: {
        "sxpVpnName": "Corp_VN"
    }
}
print(f"\n  Payload: {json.dumps(payload, indent=2)}")
r2 = requests.post(f'{ISE}/ers/config/sxpvpns', auth=AUTH, headers=HEADERS, json=payload, verify=False)
print(f"  Status: {r2.status_code}")
print(f"  Response: {r2.text[:500]}")

# If that fails, try other field names
if r2.status_code != 201:
    for field_name in ['sxpVpnName', 'name', 'vpnName']:
        payload2 = {top_key: {field_name: "Corp_VN"}}
        print(f"\n  Trying field '{field_name}': {json.dumps(payload2)}")
        r3 = requests.post(f'{ISE}/ers/config/sxpvpns', auth=AUTH, headers=HEADERS, json=payload2, verify=False)
        print(f"  Status: {r3.status_code}")
        if r3.status_code == 201:
            print(f"  SUCCESS with field '{field_name}'!")
            break
        print(f"  Response: {r3.text[:300]}")
