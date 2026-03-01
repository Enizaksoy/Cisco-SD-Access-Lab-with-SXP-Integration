import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
from creds import SWITCH_USER, SWITCH_PASS, SWITCH_SECRET

# Step 1: Trigger traffic from CSR100v_Static to Windows hosts
print("=" * 60)
print("STEP 1: Trigger pings from CSR100v_Static to Windows hosts")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.17', username='admin',
                      password='Versa@123', secret='Versa@123', timeout=45, auth_timeout=45)
conn.enable()

print("\n  Ping 10.10.22.128 (Windows0) source 10.1.200.2:")
print(conn.send_command("ping 10.10.22.128 source 10.1.200.2 repeat 5"))

print("\n  Ping 10.10.22.2 (Windows1) source 10.1.200.2:")
print(conn.send_command("ping 10.10.22.2 source 10.1.200.2 repeat 5"))

print("\n  Ping 10.10.22.1 (Border anycast) source 10.1.200.2:")
print(conn.send_command("ping 10.10.22.1 source 10.1.200.2 repeat 3"))
conn.disconnect()

# Step 2: Check Edge LISP map-cache (should now have 10.1.200.0/24)
print("\n" + "=" * 60)
print("STEP 2: Check Edge LISP map-cache for 10.1.200.0/24")
print("=" * 60)
for name, ip in [('SDA-Edge1', '192.168.244.13'), ('SDA-Edge2', '192.168.244.14')]:
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()
    print(f"\n--- {name} ---")
    print("  LISP map-cache (full):")
    print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache"))
    print(f"\n  Specific lookup 10.1.200.0:")
    print(conn.send_command("show lisp instance-id 4099 ipv4 map-cache 10.1.200.0/24"))
    print(f"\n  Corp_VN route to 10.1.200.0:")
    print(conn.send_command("show ip route vrf Corp_VN 10.1.200.0"))
    conn.disconnect()

# Step 3: Verify Border state
print("\n" + "=" * 60)
print("STEP 3: Border LISP + routing state")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.11', username=SWITCH_USER,
                      password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
conn.enable()
print("\n  LISP database (10.1.200.0/24):")
print(conn.send_command("show lisp instance-id 4099 ipv4 database"))
print("\n  Corp_VN route to 10.1.200.0:")
print(conn.send_command("show ip route vrf Corp_VN 10.1.200.0"))
print("\n  Corp_VN route to 10.10.22.0:")
print(conn.send_command("show ip route vrf Corp_VN 10.10.22.0"))
conn.disconnect()

# Step 4: Check map-server registration
print("\n" + "=" * 60)
print("STEP 4: Map-server (SDA-CP) registration")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.12', username=SWITCH_USER,
                      password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
conn.enable()
print("\n  10.1.200.0/24 registration:")
print(conn.send_command("show lisp instance-id 4099 ipv4 server 10.1.200.0/24"))
conn.disconnect()

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
