import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {
    'Edge1': '192.168.244.13',
    'Edge2': '192.168.244.14',
    'Border': '192.168.244.11',
    'CP': '192.168.244.12',
}

for name, ip in devices.items():
    print(f"\n{'='*50}")
    print(f"=== {name} ===")
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()

    print(f"\n--- {name}: PIM config ---")
    print(conn.send_command("show running-config | include pim|multicast"))

    print(f"\n--- {name}: PIM neighbors ---")
    print(conn.send_command("show ip pim neighbor"))

    if name == 'Edge2':
        print(f"\n--- Edge2: CEF for 10.10.22.2 ---")
        print(conn.send_command("show ip cef vrf Corp_VN 10.10.22.2 detail"))

    conn.disconnect()

print("\nDone.")
