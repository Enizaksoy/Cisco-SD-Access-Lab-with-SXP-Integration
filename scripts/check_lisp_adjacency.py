import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

e1 = connect('192.168.244.13')
e1.enable()

print("="*70)
print("=== Edge1 LISP Adjacency & Forwarding Check ===")
print("="*70)

# Check CEF with detail for LISP nexthop
print("\n--- show ip cef vrf Corp_VN 10.10.22.128 detail ---")
print(e1.send_command("show ip cef vrf Corp_VN 10.10.22.128 detail"))

print("\n--- show ip cef vrf Corp_VN 10.10.22.128 internal ---")
print(e1.send_command("show ip cef vrf Corp_VN 10.10.22.128 internal"))

# Check adjacency for LISP0.4099
print("\n--- show adjacency LISP0.4099 detail ---")
print(e1.send_command("show adjacency LISP0.4099 detail"))

# Check LISP0 adjacency
print("\n--- show adjacency LISP0 detail ---")
print(e1.send_command("show adjacency LISP0 detail"))

# Check if there's an LISP encapsulation adjacency
print("\n--- show ip cef vrf Corp_VN adjacency LISP0.4099 ---")
print(e1.send_command("show ip cef vrf Corp_VN adjacency LISP0.4099"))

# Check platform forwarding entry
print("\n--- show platform software fed switch active ip cef vrf Corp_VN 10.10.22.128/32 ---")
try:
    out = e1.send_command("show platform software fed switch active ip cef vrf Corp_VN 10.10.22.128/32", read_timeout=15)
    print(out[:3000] if len(out) > 3000 else out)
except Exception as ex:
    print(f"  Error: {ex}")

# Check the LISP RLOC adjacency in the underlay
print("\n--- show ip cef 10.1.0.4 detail ---")
print(e1.send_command("show ip cef 10.1.0.4 detail"))

# Check LISP reliability
print("\n--- show interface LISP0 | include reliability ---")
print(e1.send_command("show interface LISP0 | include reliability"))

print("\n--- show interface LISP0.4099 | include reliability ---")
print(e1.send_command("show interface LISP0.4099 | include reliability"))

# Try to find where packets are being dropped
print("\n--- show platform software fed switch active drop summary ---")
try:
    print(e1.send_command("show platform software fed switch active drop summary", read_timeout=15))
except:
    print("  (not available)")

# Check for punt/inject issues
print("\n--- show platform software punt-policer ---")
try:
    out = e1.send_command("show platform software punt-policer", read_timeout=15)
    # Only show LISP related lines
    for line in out.split('\n'):
        if 'LISP' in line.upper() or 'lisp' in line or 'Header' in line or 'Gilligan' in line.upper():
            print(f"  {line}")
    if not any('LISP' in line.upper() or 'lisp' in line for line in out.split('\n')):
        print("  (no LISP-related punt entries)")
except:
    print("  (not available)")

# Check LISP reliable transport
print("\n--- show lisp instance-id 4099 ipv4 map-cache 10.10.22.128/32 detail ---")
try:
    print(e1.send_command("show lisp instance-id 4099 ipv4 map-cache 10.10.22.128/32", read_timeout=15))
except:
    pass

# Check if there's an NVE tunnel that should exist
print("\n--- show run | include nve|NVE|vxlan ---")
print(e1.send_command("show run | include nve|NVE|vxlan"))

# Check hardware forwarding
print("\n--- show platform software fed switch active fwd-asic resource utilization ---")
try:
    out = e1.send_command("show platform software fed switch active fwd-asic resource utilization", read_timeout=15)
    print(out[:2000] if len(out) > 2000 else out)
except:
    print("  (not available)")

# Check LISP encap type
print("\n--- show lisp instance-id 4099 ipv4 map-cache ---")
print(e1.send_command("show lisp instance-id 4099 ipv4 map-cache"))

# Critical check - is there a glean adjacency or incomplete forwarding?
print("\n--- show ip cef vrf Corp_VN unresolved ---")
print(e1.send_command("show ip cef vrf Corp_VN unresolved"))

# Check for any IP input errors or drops on Gi1/0/1 (underlay)
print("\n--- show interface GigabitEthernet1/0/1 | include packets|drops|errors ---")
print(e1.send_command("show interface GigabitEthernet1/0/1 | include packets|drops|errors"))

e1.disconnect()
print("\n\nDone.")
