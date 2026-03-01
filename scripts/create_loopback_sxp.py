import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
import urllib3
urllib3.disable_warnings()
from creds import ISE_USER, ISE_PASS

ISE = "https://192.168.11.250:9060"
AUTH = (ISE_USER, ISE_PASS)
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# Bindings to create: IP → SGT value
BINDINGS = [
    ("10.1.1.1", 101),
    ("10.1.1.2", 102),
    ("10.1.1.3", 103),
]

# Step 1: Check existing SGTs
print("=" * 60)
print("Step 1: Check existing SGTs on ISE")
print("=" * 60)
r = requests.get(f"{ISE}/ers/config/sgt?size=100", auth=AUTH, headers=HEADERS, verify=False)
existing_sgts = {}
if r.status_code == 200:
    for sgt in r.json().get("SearchResult", {}).get("resources", []):
        # Get detail
        detail = requests.get(sgt["link"]["href"], auth=AUTH, headers=HEADERS, verify=False)
        if detail.status_code == 200:
            d = detail.json()["Sgt"]
            existing_sgts[d["value"]] = d["name"]
            print(f"  SGT {d['value']:>5} = {d['name']}")

# Step 2: Create SGTs if they don't exist
print(f"\n{'=' * 60}")
print("Step 2: Create missing SGTs")
print("=" * 60)
sgt_names = {}  # value -> name mapping for binding creation
for ip, sgt_val in BINDINGS:
    if sgt_val in existing_sgts:
        sgt_names[sgt_val] = existing_sgts[sgt_val]
        print(f"  SGT {sgt_val} already exists as '{existing_sgts[sgt_val]}'")
    else:
        name = f"SGT_{sgt_val}"
        payload = {
            "Sgt": {
                "name": name,
                "value": sgt_val,
                "description": f"Loopback SGT {sgt_val}"
            }
        }
        r = requests.post(f"{ISE}/ers/config/sgt", auth=AUTH, headers=HEADERS,
                          json=payload, verify=False)
        if r.status_code == 201:
            print(f"  Created SGT {sgt_val} = '{name}'")
            sgt_names[sgt_val] = name
        else:
            print(f"  FAILED to create SGT {sgt_val}: {r.status_code} {r.text}")
            sgt_names[sgt_val] = name  # try anyway

# Step 3: Create SXP static bindings with VPN=Corp_VN
print(f"\n{'=' * 60}")
print("Step 3: Create SXP static bindings (VPN=Corp_VN)")
print("=" * 60)
for ip, sgt_val in BINDINGS:
    sgt_name = sgt_names.get(sgt_val, f"SGT_{sgt_val}")
    payload = {
        "ERSSxpLocalBindings": {
            "ipAddressOrHost": ip,
            "sgt": sgt_name,
            "sxpVpn": "Corp_VN"
        }
    }
    r = requests.post(f"{ISE}/ers/config/sxplocalbindings", auth=AUTH, headers=HEADERS,
                      json=payload, verify=False)
    if r.status_code == 201:
        print(f"  {ip} -> {sgt_name} (SGT {sgt_val}): CREATED")
    else:
        print(f"  {ip} -> {sgt_name} (SGT {sgt_val}): FAILED {r.status_code} {r.text}")

# Step 4: Verify all SXP bindings
print(f"\n{'=' * 60}")
print("Step 4: Verify all SXP local bindings")
print("=" * 60)
r = requests.get(f"{ISE}/ers/config/sxplocalbindings?size=100", auth=AUTH, headers=HEADERS, verify=False)
if r.status_code == 200:
    for b in r.json().get("SearchResult", {}).get("resources", []):
        detail = requests.get(b["link"]["href"], auth=AUTH, headers=HEADERS, verify=False)
        if detail.status_code == 200:
            d = detail.json()["ERSSxpLocalBindings"]
            print(f"  {d.get('ipAddressOrHost', 'N/A'):>18} -> SGT: {d.get('sgt', 'N/A'):<20} VPN: {d.get('sxpVpn', 'N/A')}")

print("\nDone.")
