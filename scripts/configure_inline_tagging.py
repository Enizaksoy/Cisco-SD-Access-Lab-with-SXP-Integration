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

# 1. Show current config on Gi1/0/7
print("\n--- Current Gi1/0/7 config ---")
out = conn.send_command("show running-config interface GigabitEthernet1/0/7")
print(out)

# 2. Remove dot1x and configure inline tagging
print("\n--- Removing dot1x and enabling CTS inline tagging on Gi1/0/7 ---")
cmds = [
    'interface GigabitEthernet1/0/7',
    'no service-policy type control subscriber PMAP_DefaultWiredDot1xClosedAuth_1X_MAB',
    'no dot1x pae authenticator',
    'no dot1x timeout supp-timeout 7',
    'no dot1x max-req 3',
    'no access-session closed',
    'no access-session port-control auto',
    'switchport mode trunk',
    'cts manual',
    'propagate sgt',
    'exit',
    'exit',
]
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

# 3. Verify new config
print("\n--- New Gi1/0/7 config ---")
out = conn.send_command("show running-config interface GigabitEthernet1/0/7")
print(out)

# 4. Check CTS interface status
print("\n--- CTS interface Gi1/0/7 ---")
out = conn.send_command("show cts interface GigabitEthernet1/0/7")
print(out)

conn.disconnect()
print("\nDone.")
