import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
import time

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

# Edge1
print("="*70)
print("=== Edge1 (10.1.0.3) - Deep Data Plane Check ===")
print("="*70)
e1 = connect('192.168.244.13')
e1.enable()

# LISP0.4099 interface details
print("\n--- show interface LISP0.4099 ---")
print(e1.send_command("show interface LISP0.4099"))

print("\n--- show interface LISP0 ---")
print(e1.send_command("show interface LISP0"))

# Check if there are any ACLs blocking
print("\n--- show access-lists ---")
print(e1.send_command("show access-lists"))

# Check for CTS SGACL that might block
print("\n--- show cts role-based permissions ---")
print(e1.send_command("show cts role-based permissions"))

# Check VRF routing table
print("\n--- show ip route vrf Corp_VN ---")
print(e1.send_command("show ip route vrf Corp_VN"))

# Ping from switch itself (SVI) to remote host
print("\n--- Ping from Edge1 SVI to 10.10.22.128 (on Edge2) ---")
print(e1.send_command("ping vrf Corp_VN 10.10.22.128 source 10.10.22.1 repeat 3", read_timeout=20))

# Ping to Edge2 loopback (underlay)
print("\n--- Ping Edge2 Lo0 (underlay) ---")
print(e1.send_command("ping 10.1.0.4 repeat 3", read_timeout=15))

# Check LISP data plane stats
print("\n--- show lisp instance-id 4099 ipv4 statistics ---")
print(e1.send_command("show lisp instance-id 4099 ipv4 statistics"))

# Check platform LISP forwarding
print("\n--- show platform software fed switch active ip route vrf Corp_VN 10.10.22.128 ---")
try:
    print(e1.send_command("show platform software fed switch active ip route vrf Corp_VN 10.10.22.128", read_timeout=15))
except:
    print("  (command not available)")

# Check adjacency
print("\n--- show adjacency vlan 1023 detail ---")
print(e1.send_command("show adjacency vlan 1023 detail", read_timeout=15))

# Check LISP decap
print("\n--- show lisp instance-id 4099 ipv4 away-eids ---")
try:
    print(e1.send_command("show lisp instance-id 4099 ipv4 away-eids", read_timeout=10))
except:
    print("  (not available)")

# Check if there is a LISP decap filter
print("\n--- show lisp decap-filter ---")
try:
    print(e1.send_command("show lisp decap-filter", read_timeout=10))
except:
    print("  (not available)")

e1.disconnect()

# Edge2
print("\n" + "="*70)
print("=== Edge2 (10.1.0.4) - Deep Data Plane Check ===")
print("="*70)
e2 = connect('192.168.244.14')
e2.enable()

print("\n--- show interface LISP0.4099 ---")
print(e2.send_command("show interface LISP0.4099"))

# ACLs
print("\n--- show access-lists ---")
print(e2.send_command("show access-lists"))

# CTS
print("\n--- show cts role-based permissions ---")
print(e2.send_command("show cts role-based permissions"))

# VRF routes
print("\n--- show ip route vrf Corp_VN ---")
print(e2.send_command("show ip route vrf Corp_VN"))

# Ping from Edge2 to remote host on Edge1
print("\n--- Ping from Edge2 SVI to 10.10.22.2 (on Edge1) ---")
print(e2.send_command("ping vrf Corp_VN 10.10.22.2 source 10.10.22.1 repeat 3", read_timeout=20))

# Ping underlay
print("\n--- Ping Edge1 Lo0 (underlay) ---")
print(e2.send_command("ping 10.1.0.3 repeat 3", read_timeout=15))

# LISP stats
print("\n--- show lisp instance-id 4099 ipv4 statistics ---")
print(e2.send_command("show lisp instance-id 4099 ipv4 statistics"))

# Try to see if VXLAN UDP packets are arriving
print("\n--- show ip traffic | include UDP ---")
print(e2.send_command("show ip traffic | include UDP"))

e2.disconnect()

print("\n\nDeep data plane diagnostics complete.")
