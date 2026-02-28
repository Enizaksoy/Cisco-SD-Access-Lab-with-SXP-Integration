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

border = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.11',
    'username': SWITCH_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

# ============ BORDER - Configure Gi1/0/3 ============
print("=" * 60)
print("=== Configuring SDA-Border Gi1/0/3 ===")
print("=" * 60)
conn_bdr = ConnectHandler(**border)
conn_bdr.enable()

# Check current Gi1/0/3 config
print("\n--- Current Border Gi1/0/3 config ---")
print(conn_bdr.send_command("show running-config interface GigabitEthernet1/0/3"))

# Configure Border Gi1/0/3 as routed port with CTS inline tagging
border_cmds = [
    'interface GigabitEthernet1/0/3',
    'no switchport',
    'ip address 10.1.100.1 255.255.255.252',
    'no shutdown',
    'cts manual',
    'policy static sgt 2 trusted',
    'propagate sgt',
    'exit',
    'exit',
]
out = conn_bdr.send_config_set(border_cmds, cmd_verify=False)
print(out)

# Add static routes for CSR to reach overlay subnets (if needed later)
# For now, CSR can reach Border via directly connected link

print("\n--- New Border Gi1/0/3 config ---")
print(conn_bdr.send_command("show running-config interface GigabitEthernet1/0/3"))

print("\n--- Border CTS interface Gi1/0/3 ---")
print(conn_bdr.send_command("show cts interface GigabitEthernet1/0/3"))

conn_bdr.disconnect()

# ============ CSR1000V - Configure G2 + CTS ============
print("\n" + "=" * 60)
print("=== Configuring CSR1000V G2 + CTS ===")
print("=" * 60)
conn_csr = ConnectHandler(**csr)
conn_csr.enable()

csr_cmds = [
    # G2 - data link to Border
    'interface GigabitEthernet2',
    'ip address 10.1.100.2 255.255.255.252',
    'no shutdown',
    'cts manual',
    'policy static sgt 2 trusted',
    'propagate sgt',
    'exit',
    'exit',
    # Enable CTS
    'cts sxp enable',
    'cts sxp default source-ip 10.1.100.2',
    'cts sxp default password none',
    # Static routes to overlay subnets via Border
    'ip route 10.10.20.0 255.255.255.0 10.1.100.1',
    'ip route 10.10.21.0 255.255.255.0 10.1.100.1',
    'ip route 10.10.22.0 255.255.255.0 10.1.100.1',
    'ip route 10.10.23.0 255.255.255.0 10.1.100.1',
]
out = conn_csr.send_config_set(csr_cmds, cmd_verify=False)
print(out)

print("\n--- CSR show ip interface brief ---")
print(conn_csr.send_command("show ip interface brief"))

print("\n--- CSR show run int G2 ---")
print(conn_csr.send_command("show running-config interface GigabitEthernet2"))

print("\n--- CSR show cts interface G2 ---")
print(conn_csr.send_command("show cts interface GigabitEthernet2"))

# Test connectivity
print("\n--- Ping Border from CSR ---")
print(conn_csr.send_command("ping 10.1.100.1", read_timeout=15))

conn_csr.disconnect()
print("\nDone.")
