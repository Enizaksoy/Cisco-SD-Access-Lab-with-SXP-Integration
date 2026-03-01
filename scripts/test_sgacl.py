import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

print("=" * 60)
print("SGACL Test: Ping from CSR100v_Static loopbacks to Windows0")
print("=" * 60)

conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.17', username='admin',
                      password='Versa@123', secret='Versa@123', timeout=45, auth_timeout=45)
conn.enable()
prompt = conn.find_prompt()
print(f"  Prompt: {prompt}")

print("\n  Test 1: Ping 10.10.22.128 source 10.1.1.1 (SGT 101) - should FAIL")
print(conn.send_command("ping 10.10.22.128 source 10.1.1.1 repeat 5", read_timeout=30))

print("\n  Test 2: Ping 10.10.22.128 source 10.1.1.2 (SGT 102) - should PASS")
print(conn.send_command("ping 10.10.22.128 source 10.1.1.2 repeat 5", read_timeout=30))

print("\n  Test 3: Ping 10.10.22.128 source 10.1.1.3 (SGT 103) - no rule, should PASS")
print(conn.send_command("ping 10.10.22.128 source 10.1.1.3 repeat 5", read_timeout=30))

print("\n  Test 4: Ping 10.10.22.128 source 10.1.200.2 - baseline, should PASS")
print(conn.send_command("ping 10.10.22.128 source 10.1.200.2 repeat 3", read_timeout=30))

conn.disconnect()

# Check SGACL counters
print("\n" + "=" * 60)
print("CSR_SXP SGACL counters")
print("=" * 60)
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.16', username='admin',
                      password='Versa@123', secret='Versa@123', timeout=45, auth_timeout=45)
conn.enable()
print(conn.send_command("show cts role-based counters"))
conn.disconnect()

print("\nDone.")
