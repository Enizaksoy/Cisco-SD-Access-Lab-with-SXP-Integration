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

# The 7 static SXP bindings to recreate with VPN=Corp_VN
# Correct format: ipAddressOrHost, sgt (by name), sxpVpn
BINDINGS = [
    {"ip": "172.16.100.10", "sgt": "Employees",        "desc": "Employees (SGT 4)"},
    {"ip": "172.16.100.20", "sgt": "Test_Servers",      "desc": "Test_Servers (SGT 13)"},
    {"ip": "172.16.100.30", "sgt": "Developers",        "desc": "Developers (SGT 8)"},
    {"ip": "172.16.100.40", "sgt": "Production_Users",  "desc": "Production_Users (SGT 7)"},
    {"ip": "172.16.100.50", "sgt": "Guests",            "desc": "Guests (SGT 6)"},
    {"ip": "8.8.8.8",       "sgt": "Network_Services",  "desc": "Network_Services (SGT 3)"},
    {"ip": "1.1.1.0/24",    "sgt": "Auditors",          "desc": "Auditors (SGT 9)"},
]

print("=== Recreating 7 ISE SXP Static Bindings (VPN=Corp_VN) ===\n")

success = 0
fail = 0
for b in BINDINGS:
    payload = {
        "ERSSxpLocalBindings": {
            "ipAddressOrHost": b["ip"],
            "sgt": b["sgt"],
            "sxpVpn": "Corp_VN"
        }
    }
    r = requests.post(f'{ISE}/ers/config/sxplocalbindings',
                      auth=AUTH, headers=HEADERS, json=payload, verify=False)
    if r.status_code == 201:
        print(f"  [OK]   {b['ip']:20s} -> {b['desc']}")
        success += 1
    else:
        err_msg = ""
        try:
            err_msg = r.json().get('ERSResponse', {}).get('messages', [{}])[0].get('title', '')
        except:
            err_msg = r.text[:200]
        print(f"  [FAIL] {b['ip']:20s} -> {b['desc']}  ({r.status_code}: {err_msg})")
        fail += 1

print(f"\nResults: {success} created, {fail} failed")

# Verify
print("\n=== Verifying all bindings ===\n")
time.sleep(2)
r = requests.get(f'{ISE}/ers/config/sxplocalbindings', auth=AUTH, headers=HEADERS, verify=False)
total = r.json().get('SearchResult', {}).get('total', 0)
resources = r.json().get('SearchResult', {}).get('resources', [])
print(f"Total bindings: {total}\n")

for res in resources:
    r2 = requests.get(f'{ISE}/ers/config/sxplocalbindings/{res["id"]}',
                      auth=AUTH, headers=HEADERS, verify=False)
    d = r2.json().get('ERSSxpLocalBindings', {})
    print(f"  {d.get('ipAddressOrHost', 'N/A'):20s}  SGT: {d.get('sgt', 'N/A'):30s}  VPN: {d.get('sxpVpn', 'N/A')}")

print("\nDone. Wait ~30s then verify on switches:")
print("  show cts sxp sgt-map vrf Corp_VN")
