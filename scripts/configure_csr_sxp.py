import sys, json, requests, urllib3
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
urllib3.disable_warnings()
from netmiko import ConnectHandler

from creds import CSR_PASS, CSR_SECRET, CSR_USER, ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
ISE_AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# ============ Step 1: CSR needs a Loopback for SXP source ============
print("=" * 60)
print("=== Step 1: Configure CSR Loopback0 + SXP listener ===")
print("=" * 60)

csr = {
    'device_type': 'cisco_ios',
    'host': '192.168.244.16',
    'username': CSR_USER,
    'password': CSR_PASS,
    'secret': CSR_SECRET,
    'timeout': 45,
    'auth_timeout': 45,
}

conn_csr = ConnectHandler(**csr)
conn_csr.enable()

# CSR needs to reach ISE. Check if it can reach 192.168.11.250
# CSR G1 is on 192.168.244.0/24. ISE is on 192.168.11.250.
# Need a route to ISE via the management network or via Border.
print("\n--- Check if CSR can reach ISE ---")
out = conn_csr.send_command("ping 192.168.11.250 repeat 2", read_timeout=15)
print(out)

if 'Success rate is 0' in out or 'success rate is 0' in out.lower():
    print("\n--- CSR cannot reach ISE. Adding route via G1 gateway ---")
    # The management network gateway is 192.168.244.4 (3750X)
    cmds = [
        'ip route 192.168.11.0 255.255.255.0 192.168.244.4',
    ]
    conn_csr.send_config_set(cmds, cmd_verify=False)
    print("Added route to 192.168.11.0/24 via 192.168.244.4")
    out = conn_csr.send_command("ping 192.168.11.250 repeat 3", read_timeout=15)
    print(out)

# Configure SXP on CSR - listener to ISE
csr_cmds = [
    'cts sxp enable',
    'cts sxp default source-ip 192.168.244.16',
    'cts sxp default password none',
    'cts sxp connection peer 192.168.11.250 source 192.168.244.16 password none mode local listener',
]
out = conn_csr.send_config_set(csr_cmds, cmd_verify=False)
print(out)

print("\n--- CSR SXP connections ---")
print(conn_csr.send_command("show cts sxp connections brief"))

conn_csr.disconnect()

# ============ Step 2: Create SXP connection on ISE (Speaker → CSR) ============
print("\n" + "=" * 60)
print("=== Step 2: Create SXP connection on ISE → CSR ===")
print("=" * 60)

sxp_data = {
    "ERSSxpConnection": {
        "ipAddress": "192.168.244.16",
        "sxpPeer": "192.168.244.16",
        "sxpVpn": "default",
        "sxpNode": "ise35",
        "sxpMode": "LISTENER",
        "description": "CSR1000V SXP Listener"
    }
}

resp = requests.post(
    f"{ISE}/ers/config/sxpconnections",
    auth=ISE_AUTH, headers=HEADERS, json=sxp_data, verify=False
)
print(f"ISE SXP create: {resp.status_code}")
if resp.status_code == 201:
    print(f"Created: {resp.headers.get('Location', '')}")
elif resp.status_code == 200:
    print(resp.json())
else:
    print(resp.text[:500])

# Verify ISE SXP connections
print("\n--- ISE SXP connections ---")
resp = requests.get(
    f"{ISE}/ers/config/sxpconnections",
    auth=ISE_AUTH, headers=HEADERS, verify=False
)
if resp.ok:
    data = resp.json()
    for c in data.get('SearchResult', {}).get('resources', []):
        detail = requests.get(f"{ISE}/ers/config/sxpconnections/{c['id']}",
                              auth=ISE_AUTH, headers=HEADERS, verify=False)
        if detail.ok:
            d = detail.json()['ERSSxpConnection']
            print(f"  Peer: {d['ipAddress']}, Mode: {d['sxpMode']}, Description: {d.get('description','')}")

print("\nDone. Wait ~30 seconds for SXP to establish, then check CSR.")
