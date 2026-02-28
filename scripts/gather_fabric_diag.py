import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
switches = {
    'SDA-Border': {'host': '192.168.244.11'},
    'SDA-CP':     {'host': '192.168.244.12'},
    'SDA-Edge1':  {'host': '192.168.244.13'},
    'SDA-Edge2':  {'host': '192.168.244.14'},
}

# Commands to gather from all switches
common_cmds = [
    'show ip multicast-routing',
    'show ip pim neighbor',
    'show ip pim rp mapping',
    'show ip mroute 239.0.17.1',
    'show ip igmp membership 239.0.17.1',
    'show nve peers',
    'show nve summary',
    'show nve vni',
]

# Edge-specific commands
edge_cmds = [
    'show lisp instance-id 4099 ipv4 map-cache',
    'show lisp instance-id 4099 ipv4 database',
    'show lisp instance-id 8190 ethernet map-cache',
    'show lisp instance-id 8190 ethernet database',
    'show lisp instance-id 8190 ethernet server summary',
    'show lisp session',
    'show vlan brief',
    'show ip interface brief | include Vlan|Loopback|LISP',
    'show ip arp vrf Corp_VN',
    'show mac address-table vlan 1023',
    'show ip cef vrf Corp_VN 10.10.22.128',
    'show ip cef vrf Corp_VN 10.10.22.2',
    'show run | section router lisp',
    'show run | section ^interface LISP',
    'show run interface nve1',
    'show platform software fed switch active ifm interfaces nve',
    'show lisp instance-id 4099 ipv4 map-cache 10.10.22.2/32',
    'show lisp instance-id 4099 ipv4 map-cache 10.10.22.128/32',
]

# CP-specific commands
cp_cmds = [
    'show lisp instance-id 4099 ipv4 server summary',
    'show lisp instance-id 4099 ipv4 server 10.10.22.2/32',
    'show lisp instance-id 4099 ipv4 server 10.10.22.128/32',
    'show lisp instance-id 8190 ethernet server summary',
    'show lisp session',
    'show run | section router lisp',
]

# Border-specific commands
border_cmds = [
    'show lisp instance-id 4099 ipv4 map-cache',
    'show lisp instance-id 4099 ipv4 database',
    'show lisp session',
    'show run | section router lisp',
    'show run interface nve1',
]

for name, info in switches.items():
    print(f"\n{'#'*70}")
    print(f"### {name} ({info['host']})")
    print(f"{'#'*70}")

    try:
        conn = ConnectHandler(device_type='cisco_ios', host=info['host'], username=SWITCH_USER,
                              password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
        conn.enable()

        # Common commands
        for cmd in common_cmds:
            print(f"\n--- {cmd} ---")
            try:
                print(conn.send_command(cmd, read_timeout=15))
            except Exception as e:
                print(f"  Error: {e}")

        # Role-specific commands
        if 'Edge' in name:
            for cmd in edge_cmds:
                print(f"\n--- {cmd} ---")
                try:
                    print(conn.send_command(cmd, read_timeout=15))
                except Exception as e:
                    print(f"  Error: {e}")
        elif name == 'SDA-CP':
            for cmd in cp_cmds:
                print(f"\n--- {cmd} ---")
                try:
                    print(conn.send_command(cmd, read_timeout=15))
                except Exception as e:
                    print(f"  Error: {e}")
        elif name == 'SDA-Border':
            for cmd in border_cmds:
                print(f"\n--- {cmd} ---")
                try:
                    print(conn.send_command(cmd, read_timeout=15))
                except Exception as e:
                    print(f"  Error: {e}")

        conn.disconnect()
    except Exception as e:
        print(f"  CONNECTION FAILED: {e}")

print("\n\nDiagnostic collection complete.")
