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

# Check current SXP mappings first
print("--- Current SXP mappings ---")
print(conn.send_command("show cts sxp sgt-map brief"))

# Enable sgt-caching on G2 ingress so CSR resolves source IP to SGT
print("\n--- Enabling cts role-based sgt-map on G2 ---")
cmds = [
    'interface GigabitEthernet2',
    'cts role-based sgt-map sgt-caching',
    'exit',
]
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

# Verify
print("\n--- show cts interface G2 ---")
print(conn.send_command("show cts interface GigabitEthernet2"))

print("\n--- show cts interface G3 ---")
print(conn.send_command("show cts interface GigabitEthernet3"))

print("\n--- show cts role-based sgt-map all ---")
print(conn.send_command("show cts role-based sgt-map all"))

conn.disconnect()
print("\nDone.")
