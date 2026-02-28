import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

csr = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.16',
    'username': 'admin',
    'password': 'Versa@123',
    'secret': 'Versa@123',
    'timeout': 45,
    'auth_timeout': 45,
}

conn = ConnectHandler(**csr)
conn.enable()

print("--- Current G3 config ---")
print(conn.send_command("show running-config interface GigabitEthernet3"))

# Configure G3 with IP and CTS inline tagging
cmds = [
    'interface GigabitEthernet3',
    'ip address 10.1.200.1 255.255.255.0',
    'no shutdown',
    'cts manual',
    'policy static sgt 2 trusted',
    'propagate sgt',
    'exit',
    'exit',
    # Enable CTS role-based enforcement globally
    'cts role-based enforcement',
]
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

print("\n--- New G3 config ---")
print(conn.send_command("show running-config interface GigabitEthernet3"))

print("\n--- show cts interface G3 ---")
print(conn.send_command("show cts interface GigabitEthernet3"))

print("\n--- show cts interface summary ---")
print(conn.send_command("show cts interface summary"))

conn.disconnect()
print("\nDone.")
