import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
def connect(host):
    return ConnectHandler(device_type='cisco_ios', host=host, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)

print("="*70)
print("=== Cross-Edge Ping Verification ===")
print("="*70)

# Edge1 test
e1 = connect('192.168.244.13')
e1.enable()

print("\n--- Edge1: Ping 10.10.22.128 (Windows0 on Edge2) ---")
print(e1.send_command("ping vrf Corp_VN 10.10.22.128 repeat 5", read_timeout=20))

print("\n--- Edge1: LISP0.4099 counters ---")
print(e1.send_command("show interface LISP0.4099 | include packets"))

print("\n--- Edge1: NVE peers ---")
print(e1.send_command("show nve peers"))

e1.disconnect()

# Edge2 test
e2 = connect('192.168.244.14')
e2.enable()

print("\n--- Edge2: Ping 10.10.22.2 (Windows1 on Edge1) ---")
print(e2.send_command("ping vrf Corp_VN 10.10.22.2 repeat 5", read_timeout=20))

print("\n--- Edge2: LISP0.4099 counters ---")
print(e2.send_command("show interface LISP0.4099 | include packets"))

print("\n--- Edge2: NVE peers ---")
print(e2.send_command("show nve peers"))

e2.disconnect()

print("\n\nVerification complete.")
