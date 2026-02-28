import sys, json, requests, urllib3
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
urllib3.disable_warnings()

from creds import ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
ISE_OPEN = 'https://192.168.11.250'
ISE_AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Content-Type': 'application/json', 'Accept': 'application/json'}

# 1. Static SXP Local Bindings (ERS API)
print("=== ISE Static SXP Local Bindings ===")
resp = requests.get(f"{ISE}/ers/config/sxplocalbindings",
                    auth=ISE_AUTH, headers=HEADERS, verify=False)
if resp.ok:
    resources = resp.json().get('SearchResult', {}).get('resources', [])
    print(f"Total static bindings: {len(resources)}")
    for r in resources:
        detail = requests.get(f"{ISE}/ers/config/sxplocalbindings/{r['id']}",
                              auth=ISE_AUTH, headers=HEADERS, verify=False)
        if detail.ok:
            d = detail.json()['ERSSxpLocalBindings']
            print(f"  {d.get('ipAddressOrHost','?')} -> SGT {d.get('sgt','?')} ({d.get('sgtNameOrValue','?')})")

# 2. Check ISE Open API for SXP mappings
print("\n=== ISE Dynamic Mappings (Open API) ===")
for endpoint in ['/api/v1/trustsec/sgtvnvlan', '/api/v1/certs/trusted-certificate']:
    pass

# 3. Check active RADIUS sessions (these generate dynamic SXP mappings)
print("\n=== ISE Active RADIUS Sessions (MNT API) ===")
MNT_HEADERS = {'Accept': 'application/xml'}
resp = requests.get(f"https://192.168.11.250/admin/API/mnt/Session/ActiveList",
                    auth=ISE_AUTH, headers=MNT_HEADERS, verify=False)
if resp.ok:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(resp.text)
    sessions = root.findall('.//activeSession')
    print(f"Total active sessions: {len(sessions)}")
    for s in sessions:
        user = s.findtext('user_name', '?')
        ip = s.findtext('framed_ip_address', 'no-ip')
        sgt = s.findtext('cts_security_group', '?')
        nas = s.findtext('nas_ip_address', '?')
        print(f"  User: {user}, IP: {ip}, SGT: {sgt}, NAS: {nas}")
else:
    print(f"MNT API error: {resp.status_code}")

# 4. Try TrustSec SXP mappings endpoint
print("\n=== ISE All SXP Mappings (Open API) ===")
for path in ['/api/v1/trustsec/sxp/local-bindings', '/api/v1/trustsec/sxp/mappings']:
    resp = requests.get(f"{ISE_OPEN}{path}",
                        auth=ISE_AUTH, headers=HEADERS, verify=False)
    print(f"  {path}: {resp.status_code}")
    if resp.ok:
        print(f"  {json.dumps(resp.json(), indent=2)[:1000]}")

print("\nDone.")
