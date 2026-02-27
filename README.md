# Cisco SD-Access Lab with SXP Integration

A comprehensive Cisco SD-Access (SDA) fabric lab built on Cisco CML, featuring full fabric deployment via Catalyst Center, ISE integration for 802.1X/SGT, and SXP propagation testing.

## Live Documentation

**[View Full Lab Documentation](https://enizaksoy.github.io/SDA-Lab-CML/SDA_Lab_Documentation.html)**

## Lab Overview

### Architecture
- **Catalyst Center**: 2.3.7.x managing SD-Access fabric
- **ISE 3.5**: AAA, 802.1X, SGT assignment, SXP
- **4x Cat9Kv** switches (CML UADP images):
  - **SDA-Border** (192.168.244.11) - Border Node + OSPF external routing
  - **SDA-CP** (192.168.244.12) - Control Plane (Map Server/Map Resolver)
  - **SDA-Edge1** (192.168.244.13) - Edge Node
  - **SDA-Edge2** (192.168.244.14) - Edge Node

### Fabric Technologies
- **Underlay**: IS-IS (pushed by Catalyst Center)
- **Overlay**: LISP (Control Plane) + VXLAN (Data Plane)
- **Segmentation**: VRF-based (Corp_VN) + SGT micro-segmentation via CTS/TrustSec
- **AAA**: RADIUS (802.1X) with ISE, Open Authentication template
- **External Routing**: OSPF Area 0 on Border Gi1/0/2 for ISE reachability from Loopback0

### What's Implemented
1. Full SD-Access fabric deployment via Catalyst Center
2. IS-IS underlay, LISP overlay, VXLAN data plane
3. Virtual Network (Corp_VN) with IP pools and Anycast Gateways
4. ISE integration - CTS environment, 16 SGTs downloaded
5. 802.1X Open Authentication on all edge ports
6. OSPF external routing (Border to management network)
7. AAA/RADIUS pushed by Catalyst Center
8. ISE internal users (netadmin + User_1 through User_10)

### Goal
Test **IP-SGT propagation via SXP** from SD-Access fabric to external devices (Versa FlexVNF + Cisco router), demonstrating TrustSec SGT propagation beyond the fabric boundary.

## Repository Contents

| File/Directory | Description |
|---|---|
| `SDA_Lab_Documentation.html` | Full lab documentation with configs and verification outputs |
| `configs/` | Running configs and verification outputs from all 4 switches |
| `scripts/` | Python verification scripts (Catalyst Center API + fabric CLI) |
| `sda_topology.yaml` | CML topology definition |
| `create_sda_topology.py` | CML topology creation script |

## Lab Topology

```
                    Catalyst Center (192.168.11.254)
                              |
                    ISE 3.5 (192.168.11.250)
                              |
                    3750X Mgmt Switch (192.168.244.4)
                              |
            +-----------------+-----------------+
            |                 |                 |
     SDA-Border (.11)   SDA-CP (.12)      Edge Switches
     [Border Node]      [Control Plane]    [Edge Nodes]
     OSPF ↔ IS-IS       MS/MR              802.1X ports
            |                               |         |
            |                          SDA-Edge1    SDA-Edge2
            |                          (.13)        (.14)
     Gi1/0/2 → OSPF Area 0
     (ISE reachability)
```

## Technologies Verified

- IS-IS adjacencies between all fabric nodes
- LISP sessions (TCP/4342) - CP ↔ Border, CP ↔ Edge1, CP ↔ Edge2
- VXLAN NVE peers with VNI mappings
- CTS environment data (16 SGTs from ISE)
- RADIUS authentication (ISE as AAA server)
- Anycast Gateway (Vlan1021 - 172.16.100.1/24)

## Tools Used
- **Cisco CML 2.9.1** (Bare Metal - Lenovo P920)
- **Catalyst Center 2.3.7.x**
- **ISE 3.5**
- **Python + Netmiko** for automation scripts
- **Cat Center REST API** for verification
