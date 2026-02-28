import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
import time

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

print("="*70)
print("=== LISP Data Plane Definitive Test ===")
print("="*70)

# Connect to both edges
e1 = connect('192.168.244.13')
e1.enable()
e2 = connect('192.168.244.14')
e2.enable()

# Step 1: Clear interface counters on both edges
print("\n[Step 1] Clearing interface counters on both edges...")
e1.send_command("clear counters LISP0.4099", expect_string=r'\[confirm\]', read_timeout=10)
e1.send_command("", expect_string=r'#', read_timeout=5)  # confirm
e2.send_command("clear counters LISP0.4099", expect_string=r'\[confirm\]', read_timeout=10)
e2.send_command("", expect_string=r'#', read_timeout=5)  # confirm

# Also clear L2LISP0.8190 (VLAN 1023 L2 flooding)
e1.send_command("clear counters L2LISP0.8190", expect_string=r'\[confirm\]', read_timeout=10)
e1.send_command("", expect_string=r'#', read_timeout=5)
e2.send_command("clear counters L2LISP0.8190", expect_string=r'\[confirm\]', read_timeout=10)
e2.send_command("", expect_string=r'#', read_timeout=5)

print("Counters cleared. Waiting 3 seconds...")
time.sleep(3)

# Step 2: Check counters BEFORE ping
print("\n[Step 2] Interface counters BEFORE ping:")
print("\n  Edge1 LISP0.4099:")
out = e1.send_command("show interface LISP0.4099 | include packets")
print(f"    {out}")
print("\n  Edge2 LISP0.4099:")
out = e2.send_command("show interface LISP0.4099 | include packets")
print(f"    {out}")
print("\n  Edge1 L2LISP0.8190:")
out = e1.send_command("show interface L2LISP0.8190 | include packets")
print(f"    {out}")
print("\n  Edge2 L2LISP0.8190:")
out = e2.send_command("show interface L2LISP0.8190 | include packets")
print(f"    {out}")

# Step 3: Send ping from Edge1 to 10.10.22.128 (Windows0 on Edge2)
print("\n[Step 3] Sending 5 pings from Edge1 VRF Corp_VN to 10.10.22.128...")
ping_out = e1.send_command("ping vrf Corp_VN 10.10.22.128 repeat 5", read_timeout=20)
print(f"  Result: {ping_out}")

# Step 4: Send ping from Edge2 to 10.10.22.2 (Windows1 on Edge1)
print("\n[Step 4] Sending 5 pings from Edge2 VRF Corp_VN to 10.10.22.2...")
ping_out = e2.send_command("ping vrf Corp_VN 10.10.22.2 repeat 5", read_timeout=20)
print(f"  Result: {ping_out}")

time.sleep(2)

# Step 5: Check counters AFTER ping
print("\n[Step 5] Interface counters AFTER ping:")
print("\n  Edge1 LISP0.4099:")
out = e1.send_command("show interface LISP0.4099 | include packets")
print(f"    {out}")
print("\n  Edge2 LISP0.4099:")
out = e2.send_command("show interface LISP0.4099 | include packets")
print(f"    {out}")
print("\n  Edge1 L2LISP0.8190:")
out = e1.send_command("show interface L2LISP0.8190 | include packets")
print(f"    {out}")
print("\n  Edge2 L2LISP0.8190:")
out = e2.send_command("show interface L2LISP0.8190 | include packets")
print(f"    {out}")

# Step 6: Check platform drops
print("\n[Step 6] Platform drop counters:")
print("\n  Edge1 platform drops:")
try:
    out = e1.send_command("show platform software fed switch active drop | exclude ^$", read_timeout=15)
    # Only show lines with non-zero counts
    for line in out.split('\n'):
        if line.strip() and not line.startswith('---'):
            parts = line.split()
            if parts and any(p.isdigit() and int(p) > 0 for p in parts[-3:] if p.isdigit()):
                print(f"    {line}")
except:
    print("    (command not available)")

print("\n  Edge2 platform drops:")
try:
    out = e2.send_command("show platform software fed switch active drop | exclude ^$", read_timeout=15)
    for line in out.split('\n'):
        if line.strip() and not line.startswith('---'):
            parts = line.split()
            if parts and any(p.isdigit() and int(p) > 0 for p in parts[-3:] if p.isdigit()):
                print(f"    {line}")
except:
    print("    (command not available)")

# Step 7: Check LISP0.4099 and L2LISP full details
print("\n[Step 7] Full LISP0.4099 interface detail on Edge1:")
print(e1.send_command("show interface LISP0.4099"))

print("\n[Step 7b] Full L2LISP0.8190 interface detail on Edge1:")
print(e1.send_command("show interface L2LISP0.8190"))

# Step 8: Check if VXLAN port is being used - look at IP traffic stats
print("\n[Step 8] IP traffic UDP stats:")
print("\n  Edge1 UDP stats:")
print(e1.send_command("show ip traffic | section UDP"))
print("\n  Edge2 UDP stats:")
print(e2.send_command("show ip traffic | section UDP"))

# Step 9: Check multicast forwarding for L2
print("\n[Step 9] Multicast join for 239.0.17.1 on Edge1:")
print(e1.send_command("show ip igmp groups 239.0.17.1"))

e1.disconnect()
e2.disconnect()

print("\n\nTest complete.")
