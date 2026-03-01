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

# Check SXP connections
print("=" * 60)
print("ISE SXP Connections")
print("=" * 60)
r = requests.get(f"{ISE}/ers/config/sxpconnections?size=100", auth=AUTH, headers=HEADERS, verify=False)
if r.status_code == 200:
    for conn in r.json().get("SearchResult", {}).get("resources", []):
        detail = requests.get(conn["link"]["href"], auth=AUTH, headers=HEADERS, verify=False)
        if detail.status_code == 200:
            d = detail.json()["ERSSxpConnection"]
            print(f"\n  Peer: {d.get('sxpPeer', 'N/A')}")
            print(f"  Mode: {d.get('sxpMode', 'N/A')}")
            print(f"  VPN:  {d.get('sxpVpn', 'N/A')}")
            print(f"  Node: {d.get('sxpNode', 'N/A')}")
            print(f"  Status: {d.get('status', 'N/A')}")
            print(f"  Version: {d.get('sxpVersion', 'N/A')}")
            # Print all fields
            for k, v in d.items():
                if k not in ('sxpPeer', 'sxpMode', 'sxpVpn', 'sxpNode', 'status', 'sxpVersion', 'link', 'id'):
                    print(f"  {k}: {v}")
else:
    print(f"  Failed: {r.status_code}")

# Check SXP VPNs
print(f"\n{'=' * 60}")
print("ISE SXP VPNs")
print("=" * 60)
r = requests.get(f"{ISE}/ers/config/sxpvpns?size=100", auth=AUTH, headers=HEADERS, verify=False)
if r.status_code == 200:
    for vpn in r.json().get("SearchResult", {}).get("resources", []):
        detail = requests.get(vpn["link"]["href"], auth=AUTH, headers=HEADERS, verify=False)
        if detail.status_code == 200:
            d = detail.json()
            print(f"  {d}")
else:
    print(f"  Failed: {r.status_code} {r.text}")

# Check local bindings detail
print(f"\n{'=' * 60}")
print("ISE SXP Local Bindings (detail)")
print("=" * 60)
r = requests.get(f"{ISE}/ers/config/sxplocalbindings?size=100", auth=AUTH, headers=HEADERS, verify=False)
if r.status_code == 200:
    for b in r.json().get("SearchResult", {}).get("resources", []):
        detail = requests.get(b["link"]["href"], auth=AUTH, headers=HEADERS, verify=False)
        if detail.status_code == 200:
            d = detail.json()["ERSSxpLocalBindings"]
            print(f"  {d.get('ipAddressOrHost','?'):>18} -> SGT: {d.get('sgt','?'):<25} VPN: {d.get('sxpVpn','?')}")

print("\nDone.")
