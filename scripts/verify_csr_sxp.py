import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import CSR_PASS, CSR_SECRET, CSR_USER
csr = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.16',
    'username': CSR_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

conn = ConnectHandler(**csr)
conn.enable()

print("--- show cts sxp connections brief ---")
print(conn.send_command("show cts sxp connections brief"))

print("\n--- show cts sxp sgt-map brief ---")
print(conn.send_command("show cts sxp sgt-map brief"))

print("\n--- show cts role-based sgt-map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

print("\n--- show cts interface G2 ---")
print(conn.send_command("show cts interface GigabitEthernet2"))

conn.disconnect()
