#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from creds import CATCENTER_PASS
"""
Create SD-Access Fabric Topology in CML
- 4x Cat9Kv UADP (Border, CP, Edge-1, Edge-2)
- 1x External Connector (vlan244 - management)
- 1x Unmanaged Switch (fabric interconnect)
- Management + fabric links

CML Bare Metal: 192.168.48.156
"""

import sys
import json
import urllib.request
import urllib.error
import ssl

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# CML Server
CML_HOST = "192.168.48.156"
USERNAME = "admin"
PASSWORD = CATCENTER_PASS

# SSL context (ignore self-signed cert)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api_call(method, path, data=None, token=None):
    url = f"https://{CML_HOST}/api/v0{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    resp = urllib.request.urlopen(req, context=ctx)
    return json.loads(resp.read().decode())

# Authenticate
print("[1] Authenticating to CML...")
token = api_call("POST", "/authenticate", {"username": USERNAME, "password": PASSWORD})
print(f"    Token obtained")

# Create lab
print("[2] Creating lab: SD-Access-Fabric...")
lab = api_call("POST", "/labs", {"title": "SD-Access-Fabric"}, token)
lab_id = lab["id"] if isinstance(lab, dict) else lab
print(f"    Lab ID: {lab_id}")

# Node definitions
nodes_config = [
    {
        "label": "SDA-Border",
        "node_definition": "cat9000v-uadp",
        "x": -300, "y": 0,
        "config": f"""hostname SDA-Border
!
interface GigabitEthernet1
 ip address 192.168.244.11 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 192.168.244.4
!
enable secret {CML_PASS}
username admin privilege 15 secret {CML_PASS}
!
line vty 0 15
 login local
 transport input ssh
!
crypto key generate rsa modulus 2048
ip ssh version 2
!
end"""
    },
    {
        "label": "SDA-CP",
        "node_definition": "cat9000v-uadp",
        "x": -100, "y": 0,
        "config": f"""hostname SDA-CP
!
interface GigabitEthernet1
 ip address 192.168.244.12 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 192.168.244.4
!
enable secret {CML_PASS}
username admin privilege 15 secret {CML_PASS}
!
line vty 0 15
 login local
 transport input ssh
!
crypto key generate rsa modulus 2048
ip ssh version 2
!
end"""
    },
    {
        "label": "SDA-Edge1",
        "node_definition": "cat9000v-uadp",
        "x": 100, "y": 0,
        "config": f"""hostname SDA-Edge1
!
interface GigabitEthernet1
 ip address 192.168.244.13 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 192.168.244.4
!
enable secret {CML_PASS}
username admin privilege 15 secret {CML_PASS}
!
line vty 0 15
 login local
 transport input ssh
!
crypto key generate rsa modulus 2048
ip ssh version 2
!
end"""
    },
    {
        "label": "SDA-Edge2",
        "node_definition": "cat9000v-uadp",
        "x": 300, "y": 0,
        "config": f"""hostname SDA-Edge2
!
interface GigabitEthernet1
 ip address 192.168.244.14 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 192.168.244.4
!
enable secret {CML_PASS}
username admin privilege 15 secret {CML_PASS}
!
line vty 0 15
 login local
 transport input ssh
!
crypto key generate rsa modulus 2048
ip ssh version 2
!
end"""
    },
]

# External connector for management
ext_connector = {
    "label": "Mgmt-VLAN244",
    "node_definition": "external_connector",
    "x": 0, "y": -200,
    "config": "bridge0"  # will be updated
}

# Unmanaged switch for fabric interconnect
fabric_switch = {
    "label": "Fabric-Switch",
    "node_definition": "unmanaged_switch",
    "x": 0, "y": 200,
}

# Create nodes
print("[3] Creating nodes...")
node_ids = {}

# External connector
print(f"    Creating: {ext_connector['label']}...")
ext_node = api_call("POST", f"/labs/{lab_id}/nodes", {
    "label": ext_connector["label"],
    "node_definition": ext_connector["node_definition"],
    "x": ext_connector["x"],
    "y": ext_connector["y"],
    "configuration": "bridge0",
}, token)
ext_node_id = ext_node["id"] if isinstance(ext_node, dict) else ext_node
node_ids["ext_connector"] = ext_node_id
print(f"    -> ID: {ext_node_id}")

# Update external connector to use vlan244
print(f"    Setting connector to vlan244...")
api_call("PATCH", f"/labs/{lab_id}/nodes/{ext_node_id}", {
    "configuration": "vlan244"
}, token)

# Fabric interconnect switch
print(f"    Creating: {fabric_switch['label']}...")
fab_node = api_call("POST", f"/labs/{lab_id}/nodes", {
    "label": fabric_switch["label"],
    "node_definition": fabric_switch["node_definition"],
    "x": fabric_switch["x"],
    "y": fabric_switch["y"],
}, token)
fab_node_id = fab_node["id"] if isinstance(fab_node, dict) else fab_node
node_ids["fabric_switch"] = fab_node_id
print(f"    -> ID: {fab_node_id}")

# Cat9Kv nodes
serial_num = 1
for node_cfg in nodes_config:
    label = node_cfg["label"]
    serial = f"CMLUADP{serial_num:03d}"
    print(f"    Creating: {label} (SN: {serial})...")

    # Add serial number to config
    config_with_serial = node_cfg["config"]

    node = api_call("POST", f"/labs/{lab_id}/nodes", {
        "label": label,
        "node_definition": node_cfg["node_definition"],
        "x": node_cfg["x"],
        "y": node_cfg["y"],
        "configuration": config_with_serial,
        "tags": [f"serial:{serial}"],
    }, token)
    node_id = node["id"] if isinstance(node, dict) else node
    node_ids[label] = node_id
    print(f"    -> ID: {node_id}")
    serial_num += 1

# Get interfaces for each node
print("\n[4] Getting node interfaces...")
all_interfaces = {}
for label, nid in node_ids.items():
    ifaces = api_call("GET", f"/labs/{lab_id}/nodes/{nid}/interfaces", token=token)
    all_interfaces[label] = ifaces
    iface_details = []
    for iface_id in ifaces:
        detail = api_call("GET", f"/labs/{lab_id}/interfaces/{iface_id}", token=token)
        iface_details.append(detail)
    all_interfaces[label] = iface_details
    print(f"    {label}: {len(iface_details)} interfaces")
    for d in iface_details:
        print(f"      - {d.get('label', 'N/A')} (slot: {d.get('slot', 'N/A')})")

# Create links
# Management: each Cat9Kv GigabitEthernet1 (typically slot 0) -> ext connector via fabric switch?
# Actually, connect management interfaces directly to external connector
# Fabric: remaining interfaces interconnected

print("\n[5] Creating management links (GigabitEthernet1 -> Mgmt VLAN244)...")

# For external connector, we need enough interfaces
# External connector has ports - we'll create links from each Cat9Kv's first interface

# Get external connector interfaces
ext_ifaces = all_interfaces.get("ext_connector", [])
print(f"    External connector has {len(ext_ifaces)} interface(s)")

# We need to use an unmanaged switch between the external connector and the Cat9Kv nodes
# because external connector typically has limited ports

# First, connect ext connector to a management unmanaged switch
print("    Creating management switch...")
mgmt_switch = api_call("POST", f"/labs/{lab_id}/nodes", {
    "label": "Mgmt-Switch",
    "node_definition": "unmanaged_switch",
    "x": 0, "y": -100,
}, token)
mgmt_switch_id = mgmt_switch["id"] if isinstance(mgmt_switch, dict) else mgmt_switch
node_ids["mgmt_switch"] = mgmt_switch_id

# Get mgmt switch interfaces
mgmt_sw_ifaces = api_call("GET", f"/labs/{lab_id}/nodes/{mgmt_switch_id}/interfaces", token=token)
mgmt_sw_details = []
for iface_id in mgmt_sw_ifaces:
    detail = api_call("GET", f"/labs/{lab_id}/interfaces/{iface_id}", token=token)
    mgmt_sw_details.append(detail)
print(f"    Mgmt switch has {len(mgmt_sw_details)} ports")

# Refresh ext connector interfaces
ext_ifaces_raw = api_call("GET", f"/labs/{lab_id}/nodes/{ext_node_id}/interfaces", token=token)
ext_iface_details = []
for iface_id in ext_ifaces_raw:
    detail = api_call("GET", f"/labs/{lab_id}/interfaces/{iface_id}", token=token)
    ext_iface_details.append(detail)

# Link: ext_connector port0 <-> mgmt_switch port0
if ext_iface_details and mgmt_sw_details:
    ext_port = ext_iface_details[0]["id"]
    mgmt_port0 = mgmt_sw_details[0]["id"]
    print(f"    Linking: Ext Connector <-> Mgmt Switch...")
    try:
        link = api_call("POST", f"/labs/{lab_id}/links", {
            "src_int": ext_port,
            "dst_int": mgmt_port0,
        }, token)
        print(f"    -> Link created")
    except Exception as e:
        print(f"    -> Link error: {e}")

# Link each Cat9Kv GigabitEthernet1 (slot 0 usually) to mgmt switch
mgmt_port_idx = 1  # port0 is used by ext connector
for label in ["SDA-Border", "SDA-CP", "SDA-Edge1", "SDA-Edge2"]:
    node_ifaces = all_interfaces.get(label, [])
    # Find GigabitEthernet1 (management interface, typically slot 0)
    mgmt_iface = None
    for iface in node_ifaces:
        if iface.get("label") == "GigabitEthernet1" or iface.get("slot") == 0:
            mgmt_iface = iface
            break

    if mgmt_iface and mgmt_port_idx < len(mgmt_sw_details):
        src = mgmt_iface["id"]
        dst = mgmt_sw_details[mgmt_port_idx]["id"]
        print(f"    Linking: {label} GigabitEthernet1 <-> Mgmt Switch port{mgmt_port_idx}...")
        try:
            link = api_call("POST", f"/labs/{lab_id}/links", {
                "src_int": src,
                "dst_int": dst,
            }, token)
            print(f"    -> Link created")
        except Exception as e:
            print(f"    -> Link error: {e}")
        mgmt_port_idx += 1
    else:
        print(f"    WARNING: Could not find mgmt interface for {label}")

# Fabric links: connect Cat9Kv nodes via fabric switch (full mesh through switch)
print("\n[6] Creating fabric links (inter-switch via Fabric-Switch)...")
fab_sw_ifaces_raw = api_call("GET", f"/labs/{lab_id}/nodes/{fab_node_id}/interfaces", token=token)
fab_sw_details = []
for iface_id in fab_sw_ifaces_raw:
    detail = api_call("GET", f"/labs/{lab_id}/interfaces/{iface_id}", token=token)
    fab_sw_details.append(detail)
print(f"    Fabric switch has {len(fab_sw_details)} ports")

fab_port_idx = 0
for label in ["SDA-Border", "SDA-CP", "SDA-Edge1", "SDA-Edge2"]:
    node_ifaces = all_interfaces.get(label, [])
    # Find GigabitEthernet2 (first fabric interface, typically slot 1)
    fabric_iface = None
    for iface in node_ifaces:
        if iface.get("label") == "GigabitEthernet2" or iface.get("slot") == 1:
            fabric_iface = iface
            break

    if fabric_iface and fab_port_idx < len(fab_sw_details):
        src = fabric_iface["id"]
        dst = fab_sw_details[fab_port_idx]["id"]
        print(f"    Linking: {label} GigabitEthernet2 <-> Fabric-Switch port{fab_port_idx}...")
        try:
            link = api_call("POST", f"/labs/{lab_id}/links", {
                "src_int": src,
                "dst_int": dst,
            }, token)
            print(f"    -> Link created")
        except Exception as e:
            print(f"    -> Link error: {e}")
        fab_port_idx += 1
    else:
        print(f"    WARNING: Could not find fabric interface for {label}")

# Summary
print("\n" + "=" * 70)
print("SD-Access Fabric Topology Created!")
print("=" * 70)
print(f"Lab ID:  {lab_id}")
print(f"Lab URL: https://{CML_HOST}/lab/{lab_id}")
print()
print("Nodes:")
print(f"  {'Name':<20} {'Role':<15} {'Mgmt IP':<18} {'Serial'}")
print(f"  {'-'*20} {'-'*15} {'-'*18} {'-'*12}")
print(f"  {'SDA-Border':<20} {'Border':<15} {'192.168.244.11':<18} CMLUADP001")
print(f"  {'SDA-CP':<20} {'Control Plane':<15} {'192.168.244.12':<18} CMLUADP002")
print(f"  {'SDA-Edge1':<20} {'Edge':<15} {'192.168.244.13':<18} CMLUADP003")
print(f"  {'SDA-Edge2':<20} {'Edge':<15} {'192.168.244.14':<18} CMLUADP004")
print()
print("Management: VLAN 244 (192.168.244.0/24, GW: 192.168.244.4)")
print()
print("NOTE: Serial numbers must be set MANUALLY via node definition XML")
print("      in CML UI: Edit node -> Advanced -> prod_serial_number")
print()
print("Next steps:")
print("  1. Set unique serial numbers for each Cat9Kv node")
print("  2. Start the lab")
print("  3. Verify management connectivity (ping 192.168.244.4)")
print("  4. Verify Catalyst Center can reach switches")
print("  5. Run discovery on Catalyst Center")
