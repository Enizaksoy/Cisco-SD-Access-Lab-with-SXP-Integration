import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {
    'Edge1': {'host': '192.168.244.13', 'username': SWITCH_USER, 'password': SWITCH_PASS, 'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45},
    'Edge2': {'host': '192.168.244.14', 'username': SWITCH_USER, 'password': SWITCH_PASS, 'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45},
    'CP':    {'host': '192.168.244.12', 'username': SWITCH_USER, 'password': SWITCH_PASS, 'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45},
}

for name in ['Edge1', 'Edge2']:
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"{'='*60}")
    conn = ConnectHandler(**devices[name])
    conn.enable()

    print(f"\n--- {name}: VLAN 1023 status ---")
    print(conn.send_command("show vlan id 1023"))

    print(f"\n--- {name}: SVI Vlan1023 ---")
    print(conn.send_command("show ip interface brief | include Vlan1023"))

    print(f"\n--- {name}: MAC table Vlan 1023 ---")
    print(conn.send_command("show mac address-table vlan 1023"))

    print(f"\n--- {name}: LISP EID table for 10.10.22.x ---")
    print(conn.send_command("show lisp instance-id * ethernet eid-table"))

    print(f"\n--- {name}: ARP for 10.10.22.x ---")
    print(conn.send_command("show ip arp vrf Corp_VN | include 10.10.22"))

    print(f"\n--- {name}: CTS role-based counters ---")
    print(conn.send_command("show cts role-based counters"))

    print(f"\n--- {name}: Access sessions ---")
    print(conn.send_command("show access-session"))

    conn.disconnect()

# Check CP for LISP registrations
print(f"\n{'='*60}")
print("=== CP (Map Server) ===")
print(f"{'='*60}")
conn = ConnectHandler(**devices['CP'])
conn.enable()

print("\n--- CP: LISP site registrations ---")
print(conn.send_command("show lisp instance-id 4099 ipv4 server", read_timeout=15))

print("\n--- CP: LISP ethernet registrations ---")
print(conn.send_command("show lisp instance-id 8191 ethernet server", read_timeout=15))

conn.disconnect()
print("\nDone.")
