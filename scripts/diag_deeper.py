import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
devices = {
    'Edge1': '192.168.244.13',
    'Edge2': '192.168.244.14',
}

for name, ip in devices.items():
    print(f"\n{'='*60}")
    print(f"=== {name} ===")
    print(f"{'='*60}")
    conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                          password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
    conn.enable()

    # VRF routing table
    print(f"\n--- {name}: VRF Corp_VN routing table ---")
    print(conn.send_command("show ip route vrf Corp_VN"))

    # LISP instance config
    print(f"\n--- {name}: show run | section router lisp ---")
    out = conn.send_command("show running-config | section ^router lisp", read_timeout=15)
    # Just print first 80 lines
    lines = out.splitlines()
    print('\n'.join(lines[:80]))
    if len(lines) > 80:
        print(f"... ({len(lines)-80} more lines)")

    # Check LISP decapsulation stats
    print(f"\n--- {name}: show lisp instance-id 4099 ipv4 statistics (decap) ---")
    out = conn.send_command("show lisp instance-id 4099 ipv4 statistics")
    for line in out.splitlines():
        if any(x in line.lower() for x in ['decap', 'encap', 'forward', 'drop', 'error', 'packet']):
            print(line)

    # Check if LISP is using the right locator
    print(f"\n--- {name}: show lisp instance-id 4099 ipv4 server rloc members ---")
    print(conn.send_command("show lisp instance-id 4099 ipv4 database"))

    conn.disconnect()

print("\nDone.")
