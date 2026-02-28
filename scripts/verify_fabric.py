#!/usr/bin/env python3
from creds import SWITCH_PASS
"""SD-Access Fabric Verification Script
Checks IS-IS, LISP, VXLAN, VRF, and anycast gateway status on all fabric nodes.
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler

SWITCHES = [
    {'name': 'SDA-CP',     'host': '192.168.244.12', 'role': 'Control Plane'},
    {'name': 'SDA-Border', 'host': '192.168.244.11', 'role': 'Border'},
    {'name': 'SDA-Edge1',  'host': '192.168.244.13', 'role': 'Edge'},
    {'name': 'SDA-Edge2',  'host': '192.168.244.14', 'role': 'Edge'},
]

COMMANDS = [
    ('IS-IS Neighbors',         'show isis neighbors'),
    ('IS-IS Routes',            'show ip route isis'),
    ('LISP Sessions',           'show lisp session'),
    ('LISP Instance 4099',      'show lisp instance-id 4099 ipv4 server summary'),
    ('NVE Peers',               'show nve peers'),
    ('NVE VNI',                 'show nve vni'),
    ('VRF Summary',             'show vrf'),
    ('Vlan1021 (Anycast GW)',   'show ip interface brief | include Vlan1021|Loopback1021'),
    ('CTS Environment',         'show cts environment-data'),
    ('CTS RBACL',               'show cts rbacl'),
    ('SXP Connections',         'show cts sxp connections'),
]

def main():
    for sw in SWITCHES:
        print(f'\n{"="*60}')
        print(f' {sw["name"]} ({sw["host"]}) - {sw["role"]}')
        print(f'{"="*60}')
        try:
            conn = ConnectHandler(
                device_type='cisco_ios',
                host=sw['host'],
                username='admin',
                password=SWITCH_PASS,
                timeout=20,
            )
            for label, cmd in COMMANDS:
                print(f'\n--- {label} ---')
                output = conn.send_command(cmd, read_timeout=10)
                if output.strip():
                    print(output)
                else:
                    print('(empty)')
            conn.disconnect()
        except Exception as e:
            print(f'ERROR connecting: {e}')

if __name__ == '__main__':
    main()
