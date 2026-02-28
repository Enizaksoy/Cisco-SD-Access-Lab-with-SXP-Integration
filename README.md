# Cisco SD-Access Lab with SXP Integration

A comprehensive Cisco SD-Access (SDA) fabric lab built on Cisco CML, featuring full fabric deployment via Catalyst Center, ISE integration for 802.1X/SGT, and SXP propagation testing.

## Live Documentation

**[View Full Lab Documentation](https://enizaksoy.github.io/Cisco-SD-Access-Lab-with-SXP-Integration/SDA_Lab_Documentation.html)**

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
- **AAA**: RADIUS (802.1X) with ISE, Closed Authentication template
- **External Routing**: OSPF Area 0 on Border Gi1/0/2 for ISE reachability from Loopback0

### What's Implemented
1. Full SD-Access fabric deployment via Catalyst Center
2. IS-IS underlay, LISP overlay, VXLAN data plane
3. Virtual Network (Corp_VN) with 4 IP pools and Anycast Gateways
4. ISE integration - CTS environment, 16 SGTs downloaded
5. 802.1X Closed Authentication on Edge ports (Gi1/0/5-10)
6. OSPF external routing (Border to management network)
7. AAA/RADIUS pushed by Catalyst Center
8. ISE internal users (netadmin + User_1 through User_10)
9. **ISE Identity Groups** (Employees, Contractors, Guests)
10. **ISE Authorization Profiles** with dynamic VLAN + SGT per group
11. **ISE Authorization Policies** (SDA_Employees, SDA_Contractors, SDA_Guests)
12. **DHCP pools** on Edge switches with split ranges to prevent duplicate IPs
13. **SXP** - ISE as Speaker, all fabric switches as Listeners (7 static + dynamic bindings)
14. **Dynamic SXP propagation** - RADIUS accounting IP-SGT bindings to all listeners
15. **CTS role-based enforcement** on overlay VLANs 1021-1024

### IP Pools & VLANs

| Pool | VLAN | Subnet | Gateway | Group | SGT |
|---|---|---|---|---|---|
| Corp_Pool | 1021 | 10.10.20.0/24 | 10.10.20.1 | Default | - |
| Employees_Pool | 1022 | 10.10.21.0/24 | 10.10.21.1 | Employees | 4 |
| Contractors_Pool | 1023 | 10.10.22.0/24 | 10.10.22.1 | Contractors | 5 |
| Guests_Pool | 1024 | 10.10.23.0/24 | 10.10.23.1 | Guests | 6 |

### Goal
Test **IP-SGT propagation via SXP** from SD-Access fabric to external devices (Cisco CSR router + Versa FlexVNF), demonstrating TrustSec SGT propagation beyond the fabric boundary with SGT-based ACLs.

## Lab Topology

```
                    Catalyst Center (192.168.11.254)
                              |
                    ISE 3.5 (192.168.11.250)
                    [SXP Speaker + RADIUS AAA]
                              |
                    3750X Mgmt Switch (192.168.244.4)
                              |
            +-----------------+-----------------+
            |                 |                 |
     SDA-Border (.11)   SDA-CP (.12)      Edge Switches
     [Border Node]      [Control Plane]    [Edge Nodes]
     SXP Listener       SXP Listener       SXP Listeners
     OSPF ↔ IS-IS       MS/MR              802.1X ports
            |                               |         |
            |                          SDA-Edge1    SDA-Edge2
            |                          (.13)        (.14)
            |                          Gi1/0/5-10   Gi1/0/5-10
     Gi1/0/2 → OSPF Area 0            dot1x+MAB    dot1x+MAB
     (ISE reachability)                DHCP .2-127  DHCP .128-254
            |
     [Future: SXP Speaker]
            |
     +------+------+
     |             |
  Cisco CSR     Versa FlexVNF
  SXP Listener  SXP Listener
  SGACL         SGT Policy
```

## Repository Contents

| File/Directory | Description |
|---|---|
| `SDA_Lab_Documentation.html` | Full lab documentation with configs and verification outputs |
| `configs/` | Running configs and verification outputs from all 4 switches |
| `scripts/` | Python verification scripts (Catalyst Center API + fabric CLI) |
| `sda_topology.yaml` | CML topology definition |
| `create_sda_topology.py` | CML topology creation script |

## Progress: 93% (53/57 tasks)

### Completed
- Full fabric deployment (IS-IS, LISP, VXLAN, VRF)
- ISE integration with CTS/TrustSec (16 SGTs)
- SXP with static + dynamic IP-SGT mappings
- 802.1X Closed Authentication with dynamic VLAN + SGT assignment
- DHCP pools with split ranges across Edge switches
- ISE authorization profiles and policies per user group
- PIM multicast underlay (required for LISP L2 broadcast-underlay 239.0.17.1)
- Cross-edge VXLAN data plane verified (host-to-host ping working)
- CSR1000V added with ISE SXP (10 IP-SGT mappings) + inline SGT tagging

### Remaining
- SGT-based ACLs (SGACL) on CSR
- CSR per-flow SGT resolution (needs cts sgt-caching or newer IOS-XE)
- Versa FlexVNF integration for end-to-end SGT propagation
- End-to-end test: Fabric → CSR → Versa

## Tools Used
- **Cisco CML 2.9.1** (Bare Metal - Lenovo P920)
- **Catalyst Center 2.3.7.x**
- **ISE 3.5**
- **Python + Netmiko** for automation scripts
- **Cat Center REST API** & **ISE ERS/Open API** for configuration
