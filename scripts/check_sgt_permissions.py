import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {
    'Edge1': '192.168.244.13',
    'Edge2': '192.168.244.14',
    'Border': '192.168.244.11',
}

for name, ip in devices.items():
    print(f"\n{'='*60}")
    print(f"=== {name} ({ip}) ===")
    print(f"{'='*60}")
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()

    print(f"\n--- {name}: show cts role-based permissions ---")
    print(conn.send_command("show cts role-based permissions"))

    print(f"\n--- {name}: show cts role-based counters ---")
    print(conn.send_command("show cts role-based counters"))

    print(f"\n--- {name}: show run | include role-based ---")
    print(conn.send_command("show running-config | include role-based"))

    print(f"\n--- {name}: show cts rbacl ---")
    print(conn.send_command("show cts rbacl"))

    conn.disconnect()

print("\nDone.")
