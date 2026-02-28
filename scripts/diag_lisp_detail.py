import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
edge1 = {
    'host': '192.168.244.13', 'username': SWITCH_USER, 'password': SWITCH_PASS,
    'secret': SWITCH_SECRET, 'device_type': 'cisco_ios', 'timeout': 45, 'auth_timeout': 45,
}

conn = ConnectHandler(**edge1)
conn.enable()

# Trigger a ping first to generate map-request
print("--- Ping to trigger map-request ---")
print(conn.send_command("ping vrf Corp_VN 10.10.22.128 repeat 3", read_timeout=15))

# Now check map-cache for /32 entry
print("\n--- LISP map-cache after ping ---")
print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache"))

# Check LISP map-request statistics
print("\n--- LISP statistics ---")
print(conn.send_command("show lisp instance-id 4099 ipv4 statistics"))

# Check LISP database (local registrations)
print("\n--- LISP database (what Edge1 registers) ---")
print(conn.send_command("show lisp instance-id 4099 ipv4 database"))

# Check LISP session to CP
print("\n--- LISP session ---")
print(conn.send_command("show lisp session"))

# Check specific map-cache for the destination
print("\n--- LISP map-cache 10.10.22.128/32 ---")
print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache 10.10.22.128/32"))

conn.disconnect()
print("\nDone.")
