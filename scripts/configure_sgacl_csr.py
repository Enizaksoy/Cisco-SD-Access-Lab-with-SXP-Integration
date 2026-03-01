import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.16', username='admin',
                      password='Versa@123', secret='Versa@123', timeout=45, auth_timeout=45)
conn.enable()

# Step 1: Check current CTS enforcement state
print("=== Before: CTS config ===")
print(conn.send_command("show run | include cts"))
print()
print(conn.send_command("show cts role-based permissions"))

# Step 2: Configure role-based ACLs and permissions
print("\n=== Configuring SGACL ===")
config = [
    # Role-based ACL: deny ICMP, permit everything else
    "ip access-list role-based BLOCK_ICMP",
    "deny icmp",
    "permit ip",
    # Role-based ACL: permit all
    "ip access-list role-based PERMIT_ALL",
    "permit ip",
    # Apply: SGT 5 (Contractors/10.10.22.128) -> SGT 101 (10.1.1.1) = block ICMP
    "cts role-based permissions from 5 to 101 BLOCK_ICMP",
    # Apply: SGT 5 (Contractors/10.10.22.128) -> SGT 102 (10.1.1.2) = permit all
    "cts role-based permissions from 5 to 102 PERMIT_ALL",
]
output = conn.send_config_set(config)
print(output)

# Step 3: Verify
print("\n=== After: CTS role-based permissions ===")
print(conn.send_command("show cts role-based permissions"))
print()
print("=== Role-based ACLs ===")
print(conn.send_command("show ip access-lists role-based"))

conn.disconnect()
print("\nDone. Now test: ping 10.1.1.1 from 10.10.22.128 should FAIL, ping 10.1.1.2 should PASS.")
