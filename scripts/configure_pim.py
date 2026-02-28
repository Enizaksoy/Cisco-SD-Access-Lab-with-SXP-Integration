import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
switches = {
    'SDA-Border': {'host': '192.168.244.11', 'lo0': '10.1.0.2'},
    'SDA-CP':     {'host': '192.168.244.12', 'lo0': '10.1.0.1'},
    'SDA-Edge1':  {'host': '192.168.244.13', 'lo0': '10.1.0.3'},
    'SDA-Edge2':  {'host': '192.168.244.14', 'lo0': '10.1.0.4'},
}

RP = '10.1.0.2'  # Border Loopback0

for name, info in switches.items():
    print(f"\n{'='*60}")
    print(f"=== {name} ({info['host']}) ===")
    print(f"{'='*60}")
    
    conn = ConnectHandler(device_type='cisco_ios', host=info['host'], username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()

    cmds = [
        'ip multicast-routing',
        f'ip pim rp-address {RP}',
        'interface Loopback0',
        'ip pim sparse-mode',
        'exit',
        'interface GigabitEthernet1/0/1',
        'ip pim sparse-mode',
        'exit',
    ]
    out = conn.send_config_set(cmds, cmd_verify=False)
    print(out)

    # Verify
    print(f"\n--- {name}: PIM neighbors ---")
    print(conn.send_command("show ip pim neighbor"))

    print(f"\n--- {name}: PIM RP ---")
    print(conn.send_command("show ip pim rp mapping"))

    conn.disconnect()

# Wait and re-check PIM neighbors
import time
print("\nWaiting 15 seconds for PIM to establish...")
time.sleep(15)

print(f"\n{'='*60}")
print("=== Re-checking PIM neighbors on Edge1 ===")
conn = ConnectHandler(device_type='cisco_ios', host='192.168.244.13', username=SWITCH_USER,
                      password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
conn.enable()
print(conn.send_command("show ip pim neighbor"))
print("\n--- Multicast route for 239.0.17.1 ---")
print(conn.send_command("show ip mroute 239.0.17.1"))
print("\n--- Test cross-edge ping ---")
print(conn.send_command("ping vrf Corp_VN 10.10.22.128 repeat 3", read_timeout=15))
conn.disconnect()

print("\nDone.")
