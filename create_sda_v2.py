#!/usr/bin/env python3
"""Create SD-Access topology with unique serial numbers via vswitch.xml"""
import sys, json, urllib.request, ssl

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CML_HOST = "192.168.48.156"
USERNAME = "admin"
PASSWORD = "Elma12743??"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

VSWITCH_TEMPLATE = '''<?xml version="1.0"?>
<switch>
  <board_id>20612</board_id>
  <prod_serial_number>{serial}</prod_serial_number>
  <port_count>24</port_count>
{ports}
</switch>'''

PORTS = '\n'.join([f'  <port lpn="{i}"><asic_id>0</asic_id><asic_ifg>0</asic_ifg><asic_slice>0</asic_slice></port>' for i in range(1,25)])

nodes = [
    {"label": "SDA-Border", "ip": "192.168.244.11", "serial": "CMLUADP001"},
    {"label": "SDA-CP",     "ip": "192.168.244.12", "serial": "CMLUADP002"},
    {"label": "SDA-Edge1",  "ip": "192.168.244.13", "serial": "CMLUADP003"},
    {"label": "SDA-Edge2",  "ip": "192.168.244.14", "serial": "CMLUADP004"},
]

# Build config for each node
def make_iosxe(hostname, ip):
    return f"""hostname {hostname}
!
interface GigabitEthernet0/0
 ip address {ip} 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 192.168.244.4
!
enable secret Elma12743??
username admin privilege 15 secret Elma12743??
!
line vty 0 15
 login local
 transport input ssh
!
ip ssh version 2
!
end"""

def make_vswitch(serial):
    return VSWITCH_TEMPLATE.format(serial=serial, ports=PORTS)

# Build YAML with proper escaping
yaml_nodes = []

# External connector
yaml_nodes.append("""  - id: n0
    label: Mgmt-VLAN244
    node_definition: external_connector
    x: 0
    y: -300
    configuration: "vlan244"
    interfaces:
      - id: i0
        label: port
        slot: 0
        type: physical""")

# Mgmt switch
yaml_nodes.append("""  - id: n1
    label: Mgmt-Switch
    node_definition: unmanaged_switch
    x: 0
    y: -150
    interfaces:
      - id: i0
        label: port0
        slot: 0
        type: physical
      - id: i1
        label: port1
        slot: 1
        type: physical
      - id: i2
        label: port2
        slot: 2
        type: physical
      - id: i3
        label: port3
        slot: 3
        type: physical
      - id: i4
        label: port4
        slot: 4
        type: physical""")

# Fabric switch
yaml_nodes.append("""  - id: n2
    label: Fabric-Switch
    node_definition: unmanaged_switch
    x: 0
    y: 200
    interfaces:
      - id: i0
        label: port0
        slot: 0
        type: physical
      - id: i1
        label: port1
        slot: 1
        type: physical
      - id: i2
        label: port2
        slot: 2
        type: physical
      - id: i3
        label: port3
        slot: 3
        type: physical""")

# Cat9Kv nodes
positions = [(-300,0), (-100,0), (100,0), (300,0)]
for idx, node in enumerate(nodes):
    iosxe = make_iosxe(node["label"], node["ip"])
    vswitch = make_vswitch(node["serial"])
    x, y = positions[idx]
    n_id = idx + 3

    # Indent config lines for YAML block scalar
    iosxe_indented = '\n'.join(['        ' + line for line in iosxe.split('\n')])
    vswitch_indented = '\n'.join(['        ' + line for line in vswitch.split('\n')])

    yaml_nodes.append(f"""  - id: n{n_id}
    label: {node["label"]}
    node_definition: cat9000v-uadp
    x: {x}
    y: {y}
    configuration:
      - name: iosxe_config.txt
        content: |-
{iosxe_indented}
      - name: conf/vswitch.xml
        content: |-
{vswitch_indented}
    interfaces:
      - id: i0
        label: Loopback0
        type: loopback
      - id: i1
        label: GigabitEthernet0/0
        slot: 0
        type: physical
      - id: i2
        label: GigabitEthernet1/0/1
        slot: 1
        type: physical
      - id: i3
        label: GigabitEthernet1/0/2
        slot: 2
        type: physical""")

links = """links:
  - id: l0
    n1: n0
    i1: i0
    n2: n1
    i2: i0
    label: ext-to-mgmt-sw
  - id: l1
    n1: n3
    i1: i1
    n2: n1
    i2: i1
    label: border-mgmt
  - id: l2
    n1: n4
    i1: i1
    n2: n1
    i2: i2
    label: cp-mgmt
  - id: l3
    n1: n5
    i1: i1
    n2: n1
    i2: i3
    label: edge1-mgmt
  - id: l4
    n1: n6
    i1: i1
    n2: n1
    i2: i4
    label: edge2-mgmt
  - id: l5
    n1: n3
    i1: i2
    n2: n2
    i2: i0
    label: border-fabric
  - id: l6
    n1: n4
    i1: i2
    n2: n2
    i2: i1
    label: cp-fabric
  - id: l7
    n1: n5
    i1: i2
    n2: n2
    i2: i2
    label: edge1-fabric
  - id: l8
    n1: n6
    i1: i2
    n2: n2
    i2: i3
    label: edge2-fabric"""

yaml_content = f"""lab:
  description: SD-Access Fabric with Catalyst Center
  notes: 4x Cat9Kv UADP - unique serial numbers
  title: SD-Access-Fabric
  version: 0.2.0
nodes:
{chr(10).join(yaml_nodes)}
{links}
"""

# Write YAML
yaml_path = "sda_topology_v2.yaml"
with open(yaml_path, 'w') as f:
    f.write(yaml_content)
print(f"[1] YAML written to {yaml_path}")

# Authenticate
print("[2] Authenticating...")
req = urllib.request.Request(
    f"https://{CML_HOST}/api/v0/authenticate",
    data=json.dumps({"username": USERNAME, "password": PASSWORD}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, context=ctx)
token = json.loads(resp.read().decode())
print(f"    Token obtained")

# Import
print("[3] Importing topology...")
req = urllib.request.Request(
    f"https://{CML_HOST}/api/v0/import",
    data=yaml_content.encode(),
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/yaml"
    },
    method="POST"
)
resp = urllib.request.urlopen(req, context=ctx)
result = json.loads(resp.read().decode())

if isinstance(result, dict) and "id" in result:
    lab_id = result["id"]
    warnings = result.get("warnings", [])
    print(f"    Lab created: {lab_id}")
    if warnings:
        print(f"    Warnings: {warnings}")
    print(f"\n    URL: https://{CML_HOST}/lab/{lab_id}")
else:
    print(f"    Result: {result}")

print("\n=== Summary ===")
print(f"{'Node':<15} {'IP':<18} {'Serial'}")
print(f"{'-'*15} {'-'*18} {'-'*12}")
for n in nodes:
    print(f"{n['label']:<15} {n['ip']:<18} {n['serial']}")
