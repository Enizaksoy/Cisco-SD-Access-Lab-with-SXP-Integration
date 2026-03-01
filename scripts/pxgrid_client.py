"""
pxGrid 2.0 Client - Queries ISE for Sessions, SXP Bindings, and SGTs
Uses REST API (pxGrid Control on port 8910)

pxGrid account: pxgrid_lab_client (created via AccountCreate API)
Credentials stored in: ../certs/pxgrid_creds.json
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
import urllib3
import json
urllib3.disable_warnings()

ISE = '192.168.11.250'
PXGRID_USER = 'pxgrid_lab_client'
PXGRID_PASS = 'MhVnd1nOBD7WwOXb'
H = {'Content-Type': 'application/json', 'Accept': 'application/json'}
AUTH = (PXGRID_USER, PXGRID_PASS)


def get_access_secret(peer_node):
    """Get the shared secret for accessing a pxGrid service node."""
    r = requests.post(f'https://{ISE}:8910/pxgrid/control/AccessSecret',
                      json={'peerNodeName': peer_node},
                      headers=H, auth=AUTH, verify=False, timeout=15)
    return r.json().get('secret', '') if r.status_code == 200 else ''


def pxgrid_post(url, payload=None, svc_auth=None):
    """Make a pxGrid REST API call."""
    r = requests.post(url, json=payload or {},
                      headers=H, auth=svc_auth, verify=False, timeout=15)
    return r.json() if r.status_code == 200 else {'error': r.status_code, 'body': r.text[:300]}


# Build SGT lookup table
def get_sgt_map():
    secret = get_access_secret('~ise-admin-ise')
    svc_auth = (PXGRID_USER, secret)
    data = pxgrid_post(f'https://{ISE}:8910/pxgrid/ise/config/trustsec/getSecurityGroups',
                       svc_auth=svc_auth)
    return {sg['tag']: sg['name'] for sg in data.get('securityGroups', [])}


def main():
    print("=" * 70)
    print("  pxGrid 2.0 Client — ISE Session/SGT/SXP Query")
    print("=" * 70)

    # Verify account is active
    r = requests.post(f'https://{ISE}:8910/pxgrid/control/AccountActivate',
                      json={}, headers=H, auth=AUTH, verify=False, timeout=15)
    state = r.json().get('accountState', '?') if r.status_code == 200 else f'HTTP {r.status_code}'
    print(f"\n  Account: {PXGRID_USER}  State: {state}")
    if state != 'ENABLED':
        print("  ERROR: Account not enabled. Approve in ISE pxGrid Client Management.")
        return

    # Get SGT name map
    sgt_map = get_sgt_map()

    # Get session service secret
    mnt_secret = get_access_secret('~ise-mnt-ise')
    mnt_auth = (PXGRID_USER, mnt_secret)

    # --- Active Sessions ---
    print(f"\n{'=' * 70}")
    print("  ACTIVE SESSIONS")
    print(f"{'=' * 70}")
    data = pxgrid_post(f'https://{ISE}:8910/pxgrid/mnt/sd/getSessions', svc_auth=mnt_auth)
    sessions = data.get('sessions', [])
    print(f"  Total: {len(sessions)}\n")
    print(f"  {'User':<20} {'IP':<18} {'SGT':<20} {'NAS Port':<25} {'State':<12} {'Profile':<25}")
    print(f"  {'-'*20} {'-'*18} {'-'*20} {'-'*25} {'-'*12} {'-'*25}")
    for s in sessions:
        ips = [ip for ip in s.get('ipAddresses', []) if ip and not ip.startswith('fe80')]
        ip_str = ips[0] if ips else '-'
        sgt = s.get('ctsSecurityGroup', '-')
        user = s.get('userName', '-')
        nas_port = s.get('nasPortId', '-')
        state = s.get('state', '-')
        profiles = s.get('selectedAuthzProfiles', [])
        profile = profiles[0] if profiles else '-'
        print(f"  {user:<20} {ip_str:<18} {sgt:<20} {nas_port:<25} {state:<12} {profile:<25}")

    # --- SXP Bindings ---
    print(f"\n{'=' * 70}")
    print("  SXP BINDINGS")
    print(f"{'=' * 70}")
    data = pxgrid_post(f'https://{ISE}:8910/pxgrid/ise/sxp/getBindings', svc_auth=mnt_auth)
    bindings = data.get('bindings', [])
    print(f"  Total: {len(bindings)}\n")
    print(f"  {'IP/Prefix':<22} {'SGT#':<6} {'SGT Name':<20} {'Type':<10} {'Source':<18} {'VPN':<10}")
    print(f"  {'-'*22} {'-'*6} {'-'*20} {'-'*10} {'-'*18} {'-'*10}")
    for b in bindings:
        ip = b.get('ipPrefix', '-')
        tag = b.get('tag', 0)
        name = sgt_map.get(tag, '?')
        btype = b.get('type', '-')
        source = b.get('source', '-')
        vpn = b.get('vpn', '-')
        print(f"  {ip:<22} {tag:<6} {name:<20} {btype:<10} {source:<18} {vpn:<10}")

    # --- Security Groups ---
    print(f"\n{'=' * 70}")
    print("  SECURITY GROUPS (SGTs)")
    print(f"{'=' * 70}")
    print(f"  Total: {len(sgt_map)}\n")
    print(f"  {'Tag':<8} {'Name':<25}")
    print(f"  {'-'*8} {'-'*25}")
    for tag in sorted(sgt_map.keys()):
        print(f"  {tag:<8} {sgt_map[tag]:<25}")

    print(f"\n{'=' * 70}")
    print("  pxGrid 2.0 query complete.")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
