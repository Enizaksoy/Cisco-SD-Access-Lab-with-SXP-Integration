import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
edge1 = ConnectHandler(device_type='cisco_ios', host='192.168.244.13', username=SWITCH_USER,
                       password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
edge1.enable()

print("--- NVE peers ---")
print(edge1.send_command("show nve peers"))

print("\n--- NVE summary ---")
print(edge1.send_command("show nve summary"))

print("\n--- VXLAN interface ---")
print(edge1.send_command("show ip interface brief | include nve|NVE|VXLAN|Tunnel"))

# Check L2LISP interfaces
print("\n--- L2LISP0.8190 (VLAN 1023) detail ---")
print(edge1.send_command("show lisp instance-id 8190 ethernet server summary"))

print("\n--- LISP ethernet map-cache ---")
print(edge1.send_command("show lisp instance-id 8190 ethernet map-cache"))

# Clear LISP map-cache and retry
print("\n--- Clearing LISP map-cache ---")
edge1.send_command("clear lisp instance-id 4099 ipv4 map-cache", expect_string=r'#', read_timeout=10)

import time
time.sleep(5)

print("\n--- Retry ping ---")
print(edge1.send_command("ping vrf Corp_VN 10.10.22.128 repeat 5", read_timeout=20))

print("\n--- Map-cache after ping ---")
print(edge1.send_command("show lisp instance-id 4099 ipv4 map-cache 10.10.22.128/32"))

edge1.disconnect()
