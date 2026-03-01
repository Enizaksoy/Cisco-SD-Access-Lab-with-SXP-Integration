import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from netmiko import ConnectHandler
from creds import SWITCH_USER, SWITCH_PASS, SWITCH_SECRET

DEVICES = [
    ('SDA-Border', '192.168.244.11'),
    ('SDA-CP', '192.168.244.12'),
    ('SDA-Edge1', '192.168.244.13'),
    ('SDA-Edge2', '192.168.244.14'),
]

for name, ip in DEVICES:
    print(f"\n{'=' * 50}")
    print(f"  {name} ({ip})")
    print('=' * 50)
    try:
        conn = ConnectHandler(device_type='cisco_ios', host=ip, username=SWITCH_USER,
                              password=SWITCH_PASS, secret=SWITCH_SECRET, timeout=45, auth_timeout=45)
        conn.enable()

        # Show current console config
        print("\n  Before:")
        print(conn.send_command("show run | section line con"))
        print(conn.send_command("show run | include username cisco"))

        # Configure local user and console authentication
        config = [
            "username cisco privilege 15 secret cisco",
            "aaa authentication login CONSOLE local",
            "line con 0",
            "login authentication CONSOLE",
        ]
        output = conn.send_config_set(config)
        print(f"\n  Config applied:\n{output}")

        # Verify
        print("\n  After:")
        print(conn.send_command("show run | section line con"))
        print(conn.send_command("show run | include username cisco"))

        conn.disconnect()
        print(f"\n  {name}: OK")
    except Exception as e:
        print(f"\n  {name}: FAILED - {e}")

print("\n\nDone. Console login: cisco / cisco (privilege 15)")
