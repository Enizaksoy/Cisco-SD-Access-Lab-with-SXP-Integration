import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
import time

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

print("Waiting 30 seconds for SXP to reconverge...")
time.sleep(30)

for name, ip in [('SDA-Edge1', '192.168.244.13'), ('SDA-Edge2', '192.168.244.14'), ('SDA-Border', '192.168.244.11')]:
    print(f"\n{'='*60}")
    print(f"=== {name} ({ip}) ===")
    print(f"{'='*60}")
    conn = connect(ip)
    conn.enable()

    print(f"\n--- show cts sxp connections brief ---")
    print(conn.send_command("show cts sxp connections brief"))

    print(f"\n--- show cts sxp sgt-map vrf Corp_VN ---")
    print(conn.send_command("show cts sxp sgt-map vrf Corp_VN"))

    print(f"\n--- show cts role-based sgt-map vrf Corp_VN all ---")
    print(conn.send_command("show cts role-based sgt-map vrf Corp_VN all"))

    conn.disconnect()

print("\nDone.")
