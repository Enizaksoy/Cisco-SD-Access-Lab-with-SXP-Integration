import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
from creds import SWITCH_USER, SWITCH_PASS, SWITCH_SECRET

# Check CSR_SXP
print("=" * 60)
print("CSR_SXP - SXP state")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.16', username='admin',
                      password='Versa@123', secret='Versa@123', timeout=45, auth_timeout=45)
conn.enable()

print("\n--- SXP connections ---")
print(conn.send_command("show cts sxp connections"))

print("\n--- SXP SGT map ---")
print(conn.send_command("show cts sxp sgt-map"))

print("\n--- CTS role-based SGT map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

print("\n--- SXP config ---")
print(conn.send_command("show run | section cts"))

conn.disconnect()

# Check Border for comparison
print("\n" + "=" * 60)
print("SDA-Border - SXP state")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.11', username=SWITCH_USER,
                      password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
conn.enable()

print("\n--- SXP SGT map ---")
print(conn.send_command("show cts sxp sgt-map"))

print("\n--- CTS role-based SGT map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

conn.disconnect()
print("\nDone.")
