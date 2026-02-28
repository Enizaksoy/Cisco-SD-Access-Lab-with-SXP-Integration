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

# Try global sgt-caching
print("--- Trying global cts sgt-caching ---")
cmds = ['cts sgt-caching']
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

# Check available cts commands
print("\n--- Available cts commands ---")
out = conn.send_command("show cts ?", expect_string=r'#', read_timeout=10)
print(out)

# Check if there's a way to enable IP-SGT resolution
print("\n--- show cts role-based counters ---")
print(conn.send_command("show cts role-based counters"))

# Check what SXP IPs match SGT 4 (Employees)
print("\n--- SXP entries with SGT 4 ---")
out = conn.send_command("show cts sxp sgt-map brief")
for line in out.splitlines():
    if 'SGT' in line or ', 4>' in line:
        print(line)

print("\n--- show cts interface G2 after sgt-caching ---")
print(conn.send_command("show cts interface GigabitEthernet2"))

conn.disconnect()
print("\nDone.")
