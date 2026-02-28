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

# Remove static sgt policy on G2 so CSR does IP-based SXP lookup
print("--- Removing static sgt policy on G2 ---")
cmds = [
    'interface GigabitEthernet2',
    'cts manual',
    'no policy static sgt 2 trusted',
    'propagate sgt',
    'exit',
    'exit',
]
out = conn.send_config_set(cmds, cmd_verify=False)
print(out)

print("\n--- show run int G2 ---")
print(conn.send_command("show running-config interface GigabitEthernet2"))

print("\n--- show cts interface G2 ---")
print(conn.send_command("show cts interface GigabitEthernet2"))

# Remind which IPs have SGT 4
print("\n--- SXP bindings (CSR should resolve source IP from these) ---")
print(conn.send_command("show cts sxp sgt-map brief"))

print("\nTest: send traffic FROM an IP in the SXP table (e.g. 172.16.100.10=SGT4)")
print("The CSR should now tag outgoing frames on G3 with the correct SGT.")

conn.disconnect()
