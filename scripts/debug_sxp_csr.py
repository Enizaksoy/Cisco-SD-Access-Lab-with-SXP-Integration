import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import CSR_PASS, CSR_SECRET, CSR_USER
border = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.11',
    'username': SWITCH_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

csr = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.16',
    'username': CSR_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

# Check from Border: can ISE reach 192.168.244.16?
print("=== Border routing check ===")
conn = ConnectHandler(**border)
conn.enable()

print("\n--- Border: route to 192.168.244.16 ---")
print(conn.send_command("show ip route 192.168.244.16"))

print("\n--- Border: ping CSR from Border ---")
print(conn.send_command("ping 192.168.244.16 repeat 2", read_timeout=15))

print("\n--- Border: route to ISE 192.168.11.250 ---")
print(conn.send_command("show ip route 192.168.11.250"))

# Check if ISE knows about 192.168.244.0/24 via OSPF
print("\n--- Border: OSPF neighbors ---")
print(conn.send_command("show ip ospf neighbor"))

print("\n--- Border: OSPF routes ---")
print(conn.send_command("show ip route ospf"))

conn.disconnect()

# Check CSR routing
print("\n=== CSR routing check ===")
conn2 = ConnectHandler(**csr)
conn2.enable()

print("\n--- CSR: ip route ---")
print(conn2.send_command("show ip route"))

print("\n--- CSR: ping ISE ---")
print(conn2.send_command("ping 192.168.11.250 repeat 2", read_timeout=15))

# Check if CSR is listening on SXP port
print("\n--- CSR: show tcp brief ---")
out = conn2.send_command("show tcp brief")
for line in out.splitlines():
    if '64999' in line or 'Local' in line or '---' in line:
        print(line)

print("\n--- CSR: show cts sxp connections ---")
print(conn2.send_command("show cts sxp connections"))

conn2.disconnect()
print("\nDone.")
