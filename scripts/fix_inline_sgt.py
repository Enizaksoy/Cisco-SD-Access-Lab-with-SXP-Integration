import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
edge1 = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.13',
    'username': SWITCH_USER,
    'password': SWITCH_PASS,
    'secret': SWITCH_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

print("=== Connecting to SDA-Edge1 ===")
conn = ConnectHandler(**edge1)
conn.enable()

# 1. Set the port as trusted + propagate sgt
print("\n--- Setting trusted + propagate sgt on Gi1/0/7 ---")
cmds = [
    'interface GigabitEthernet1/0/7',
    'cts manual',
    'policy static sgt 4 trusted',
    'propagate sgt',
    'exit',
    'exit',
]
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

# 2. Check CTS interface again
print("\n--- show cts interface Gi1/0/7 ---")
print(conn.send_command("show cts interface GigabitEthernet1/0/7"))

# 3. Check platform CTS for Gi1/0/7
print("\n--- Platform CTS Gi1/0/7 ---")
out = conn.send_command("show platform software cts forwarding-manager switch active F0 port")
for line in out.splitlines():
    if 'Gi' in line and '1/0/7' in line or 'Name' in line or '---' in line:
        print(line)

# 4. Check inline tagging capability
print("\n--- show cts interface summary ---")
out = conn.send_command("show cts interface summary")
print(out[:2000])

# 5. Check running config
print("\n--- show run int Gi1/0/7 ---")
print(conn.send_command("show running-config interface GigabitEthernet1/0/7"))

# 6. Check if Cat9Kv supports CMD
print("\n--- show platform hardware fed switch active fwd-asic resource tcam utilization ---")
out = conn.send_command("show platform hardware fed switch active sgacl resource usage", read_timeout=15)
print(out[:1000] if out else "(no output)")

print("\n--- show platform software fed switch active sgacl detail ---")
out = conn.send_command("show platform software fed switch active sgacl detail", read_timeout=15)
print(out[:1000] if out else "(no output)")

conn.disconnect()
print("\nDone.")
