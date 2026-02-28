import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
edge1 = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.13',
    'username': SWITCH_USER,
    'password': SWITCH_PASS,
    'secret': SWITCH_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

print("=== Connecting to SDA-Edge1 ===")
conn = ConnectHandler(**edge1)
conn.enable()

# 1. CTS interface details
print("\n--- show cts interface Gi1/0/7 ---")
print(conn.send_command("show cts interface GigabitEthernet1/0/7"))

# 2. Check platform SGT inline capability
print("\n--- show cts role-based sgt-map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

# 3. Check CTS role-based enforcement
print("\n--- show cts role-based permissions ---")
print(conn.send_command("show cts role-based permissions"))

# 4. Check if inline tagging is globally enabled
print("\n--- show running | include cts ---")
print(conn.send_command("show running-config | include cts"))

# 5. Check interface status
print("\n--- show interface Gi1/0/7 status ---")
print(conn.send_command("show interfaces GigabitEthernet1/0/7 status"))

# 6. Check interface switchport
print("\n--- show interfaces Gi1/0/7 switchport ---")
print(conn.send_command("show interfaces GigabitEthernet1/0/7 switchport"))

# 7. Check platform inline tagging support
print("\n--- show platform software cts ---")
out = conn.send_command("show platform software cts forwarding-manager switch active F0 port", read_timeout=15)
print(out[:2000] if out else "(no output)")

# 8. Check cts environment
print("\n--- show cts environment-data ---")
print(conn.send_command("show cts environment-data"))

conn.disconnect()
print("\nDone.")
