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

    print(f"\n--- {name}: show run | section nve ---")
    print(conn.send_command("show running-config | section ^interface nve", read_timeout=10))

    print(f"\n--- {name}: show nve interface ---")
    print(conn.send_command("show nve interface"))

    print(f"\n--- {name}: show ip interface brief | include nve ---")
    print(conn.send_command("show ip interface brief | include nve"))

    print(f"\n--- {name}: show tunnel interface ---")
    print(conn.send_command("show ip interface brief | include Tunnel|LISP|Loopback"))

    # Check underlay reachability
    other_lo = '10.1.0.4' if name == 'Edge1' else '10.1.0.3'
    print(f"\n--- {name}: ping other edge Loopback0 ({other_lo}) ---")
    print(conn.send_command(f"ping {other_lo} source Loopback0 repeat 2", read_timeout=15))

    print(f"\n--- {name}: IS-IS neighbors ---")
    print(conn.send_command("show isis neighbors"))

    conn.disconnect()

print("\nDone.")
