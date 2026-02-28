import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {
    'Edge1': {'host': '192.168.244.13', 'username': SWITCH_USER, 'password': SWITCH_PASS, 'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45},
    'Edge2': {'host': '192.168.244.14', 'username': SWITCH_USER, 'password': SWITCH_PASS, 'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45},
}

for name in ['Edge1', 'Edge2']:
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"{'='*60}")
    conn = ConnectHandler(**devices[name])
    conn.enable()

    print(f"\n--- {name}: NVE peers ---")
    print(conn.send_command("show nve peers"))

    print(f"\n--- {name}: NVE interface ---")
    print(conn.send_command("show nve interface nve1"))

    print(f"\n--- {name}: LISP map-cache for 10.10.22.x ---")
    print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache 10.10.22.0/24"))

    print(f"\n--- {name}: LISP map-cache specific entries ---")
    print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache"))

    print(f"\n--- {name}: Ping cross-edge from VRF Corp_VN ---")
    if name == 'Edge1':
        print(conn.send_command("ping vrf Corp_VN 10.10.22.128 repeat 2", read_timeout=15))
    else:
        print(conn.send_command("ping vrf Corp_VN 10.10.22.2 repeat 2", read_timeout=15))

    conn.disconnect()

print("\nDone.")
