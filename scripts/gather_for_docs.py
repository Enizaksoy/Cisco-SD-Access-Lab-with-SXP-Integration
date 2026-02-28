import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from netmiko import ConnectHandler

from creds import SWITCH_PASS, SWITCH_SECRET, SWITCH_USER
SWITCHES = [
    {
        'name': 'SDA-Edge1',
        'device_type': 'cisco_ios',
        'host': '192.168.244.13',
        'username': SWITCH_USER,
        'password': SWITCH_PASS,
        'secret': SWITCH_SECRET,
        'timeout': 45,
        'auth_timeout': 45,
    },
    {
        'name': 'SDA-Edge2',
        'device_type': 'cisco_ios',
        'host': '192.168.244.14',
        'username': SWITCH_USER,
        'password': SWITCH_PASS,
        'secret': SWITCH_SECRET,
        'timeout': 45,
        'auth_timeout': 45,
    },
]

COMMANDS = [
    'show lisp instance-id 4099 ipv4 map-cache',
    'show lisp instance-id 4099 ipv4 database',
    'show lisp instance-id 8190 ethernet map-cache',
    'show lisp instance-id 8190 ethernet database',
    'show ip cef vrf Corp_VN 10.10.22.128',
    'show ip cef vrf Corp_VN 10.10.22.2',
    'show ip route vrf Corp_VN',
    'show cts role-based sgt-map vrf Corp_VN all',
    'show cts role-based permissions',
    'show ip pim neighbor',
    'show ip mroute 239.0.17.1',
    'show mac address-table vlan 1023',
    'show ip arp vrf Corp_VN',
    'show vlan brief',
    'show lisp session',
]

SEPARATOR = '=' * 80

for sw in SWITCHES:
    name = sw.pop('name')
    print(f'\n{SEPARATOR}')
    print(f'  SWITCH: {name} ({sw["host"]})')
    print(SEPARATOR)

    try:
        conn = ConnectHandler(**sw)
        conn.enable()
        print(f'[+] Connected and enabled on {name}')

        for cmd in COMMANDS:
            print(f'\n{"─" * 80}')
            print(f'>>> {cmd}')
            print('─' * 80)
            try:
                output = conn.send_command(cmd, read_timeout=30)
                print(output)
            except Exception as e:
                print(f'[ERROR running command] {e}')

        conn.disconnect()
        print(f'\n[+] Disconnected from {name}')

    except Exception as e:
        print(f'[ERROR connecting to {name}] {e}')

print(f'\n{SEPARATOR}')
print('  DONE - All switches processed')
print(SEPARATOR)
