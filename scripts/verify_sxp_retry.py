import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
import time

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

print("Waiting 120 seconds for SXP retry timer...")
time.sleep(120)

e1 = connect('192.168.244.13')
e1.enable()

print("=== SDA-Edge1 ===")
print("\n--- SXP connection status ---")
print(e1.send_command("show cts sxp connections brief"))

print("\n--- SXP SGT map (default VRF) ---")
print(e1.send_command("show cts sxp sgt-map brief"))

print("\n--- SXP SGT map (Corp_VN VRF) ---")
print(e1.send_command("show cts sxp sgt-map vrf Corp_VN"))

print("\n--- Role-based SGT map (Corp_VN) ---")
print(e1.send_command("show cts role-based sgt-map vrf Corp_VN all"))

e1.disconnect()
print("\nDone.")
