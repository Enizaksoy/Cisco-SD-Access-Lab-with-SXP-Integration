import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
import urllib3
import time
urllib3.disable_warnings()
from creds import ISE_USER, ISE_PASS

ISE = "https://192.168.11.250:9060"
AUTH = (ISE_USER, ISE_PASS)
H = {"Content-Type": "application/json", "Accept": "application/json"}

BINDINGS = [
    ("10.1.1.1", "SGT_101"),
    ("10.1.1.2", "SGT_102"),
    ("10.1.1.3", "SGT_103"),
    ("172.16.100.10", "Employees"),
    ("172.16.100.20", "Test_Servers"),
    ("172.16.100.30", "Developers"),
    ("172.16.100.40", "Production_Users"),
    ("172.16.100.50", "Guests"),
    ("8.8.8.8", "Network_Services"),
    ("1.1.1.0/24", "Auditors"),
]

# Step 1: Delete all existing bindings
print("Step 1: Deleting all existing bindings...")
r = requests.get(f"{ISE}/ers/config/sxplocalbindings?size=100", auth=AUTH, headers=H, verify=False)
for b in r.json().get("SearchResult", {}).get("resources", []):
    detail = requests.get(b["link"]["href"], auth=AUTH, headers=H, verify=False)
    d = detail.json()["ERSSxpLocalBindings"]
    requests.delete(f"{ISE}/ers/config/sxplocalbindings/{d['id']}", auth=AUTH, headers=H, verify=False)
    print(f"  Deleted {d.get('ipAddressOrHost','?')} (VPN={d.get('sxpVpn','?')})")

# Step 2: Create bindings in BOTH VPNs
print("\nStep 2: Creating bindings in both default and Corp_VN...")
for vpn in ["default", "Corp_VN"]:
    print(f"\n  --- VPN: {vpn} ---")
    for ip, sgt in BINDINGS:
        payload = {"ERSSxpLocalBindings": {"ipAddressOrHost": ip, "sgt": sgt, "sxpVpn": vpn}}
        r = requests.post(f"{ISE}/ers/config/sxplocalbindings", auth=AUTH, headers=H, json=payload, verify=False)
        print(f"  {ip} -> {sgt}: {'OK' if r.status_code == 201 else r.status_code}")

# Step 3: Move CSR_SXP to default VPN
print("\nStep 3: Moving CSR_SXP to default VPN...")
r = requests.get(f"{ISE}/ers/config/sxpconnections?size=100", auth=AUTH, headers=H, verify=False)
for conn in r.json().get("SearchResult", {}).get("resources", []):
    detail = requests.get(conn["link"]["href"], auth=AUTH, headers=H, verify=False)
    d = detail.json()["ERSSxpConnection"]
    if d.get("ipAddress") == "192.168.244.16":
        if d.get("sxpVpn") == "default":
            print("  Already in default VPN")
        else:
            requests.delete(f"{ISE}/ers/config/sxpconnections/{d['id']}", auth=AUTH, headers=H, verify=False)
            time.sleep(2)
            payload = {
                "ERSSxpConnection": {
                    "sxpPeer": "CSR_SXP", "sxpVpn": "default", "sxpNode": "ISE",
                    "sxpMode": "LISTENER", "sxpVersion": "VERSION_4",
                    "ipAddress": "192.168.244.16", "enabled": True
                }
            }
            r2 = requests.post(f"{ISE}/ers/config/sxpconnections", auth=AUTH, headers=H, json=payload, verify=False)
            print(f"  CSR_SXP -> default: {'OK' if r2.status_code == 201 else r2.status_code}")
        break

# Step 4: Summary
print("\nStep 4: Final ISE state")
print("\n  Connections:")
r = requests.get(f"{ISE}/ers/config/sxpconnections?size=100", auth=AUTH, headers=H, verify=False)
for conn in r.json().get("SearchResult", {}).get("resources", []):
    detail = requests.get(conn["link"]["href"], auth=AUTH, headers=H, verify=False)
    d = detail.json()["ERSSxpConnection"]
    print(f"    {d.get('sxpPeer','?'):>15}  VPN: {d.get('sxpVpn','?')}")

print(f"\n  Bindings: (should be {len(BINDINGS)} x 2 = {len(BINDINGS)*2})")
r = requests.get(f"{ISE}/ers/config/sxplocalbindings?size=100", auth=AUTH, headers=H, verify=False)
count = {"default": 0, "Corp_VN": 0}
for b in r.json().get("SearchResult", {}).get("resources", []):
    detail = requests.get(b["link"]["href"], auth=AUTH, headers=H, verify=False)
    d = detail.json()["ERSSxpLocalBindings"]
    vpn = d.get("sxpVpn", "?")
    count[vpn] = count.get(vpn, 0) + 1
print(f"    default: {count.get('default',0)}, Corp_VN: {count.get('Corp_VN',0)}")

print("\nWaiting 120s for SXP reconnect + propagation...")
time.sleep(120)

# Step 5: Verify all devices
from netmiko import ConnectHandler
from creds import SWITCH_USER, SWITCH_PASS, SWITCH_SECRET

for name, ip, user, pw, sec in [
    ('CSR_SXP', '192.168.244.16', 'admin', 'Versa@123', 'Versa@123'),
    ('SDA-Border', '192.168.244.11', SWITCH_USER, SWITCH_PASS, SWITCH_SECRET),
    ('SDA-Edge1', '192.168.244.13', SWITCH_USER, SWITCH_PASS, SWITCH_SECRET),
]:
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=user,
                          password=pw, secret=sec, timeout=45, auth_timeout=45)
    conn.enable()
    print(f"\n=== {name} ===")
    print(conn.send_command("show cts role-based sgt-map all"))
    conn.disconnect()

print("\nDone.")
