import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {'Edge1': '192.168.244.13', 'CP': '192.168.244.12', 'Border': '192.168.244.11'}

for name, ip in devices.items():
    print(f"=== {name} ===")
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()

    print(conn.send_command("show running-config | include multicast-routing"))
    print(conn.send_command("show running-config | include ip pim"))
    print(conn.send_command("show ip pim rp mapping"))
    print()
    conn.disconnect()

print("Done.")
