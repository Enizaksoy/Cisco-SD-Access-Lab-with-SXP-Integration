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

# Check CEF for remote endpoint
print("--- CEF entry for 10.10.22.128 ---")
print(conn.send_command("show ip cef vrf Corp_VN 10.10.22.128 detail"))

# Check CEF for local endpoint (for comparison)
print("\n--- CEF entry for 10.10.22.2 (local) ---")
print(conn.send_command("show ip cef vrf Corp_VN 10.10.22.2 detail"))

# Check multicast routing for LISP flood
print("\n--- Multicast routing for 239.0.17.1 ---")
print(conn.send_command("show ip mroute 239.0.17.1"))

# Check if VXLAN port is open
print("\n--- show udp (VXLAN/LISP ports) ---")
out = conn.send_command("show ip sockets")
for line in out.splitlines():
    if '4789' in line or '4341' in line or '4342' in line or 'Proto' in line:
        print(line)

# Platform forwarding
print("\n--- Platform FED LISP ---")
print(conn.send_command("show platform software fed switch active ip route vrf Corp_VN 10.10.22.128 255.255.255.255", read_timeout=15))

conn.disconnect()
print("\nDone.")
