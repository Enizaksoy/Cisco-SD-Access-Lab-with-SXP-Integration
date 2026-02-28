import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests, json
import urllib3
urllib3.disable_warnings()

from creds import ISE_PASS, ISE_USER
ISE = 'https://192.168.11.250:9060'
AUTH = (ISE_USER, ISE_PASS)
HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# Get all SXP connections
r = requests.get(f'{ISE}/ers/config/sxpconnections', auth=AUTH, headers=HEADERS, verify=False)
data = r.json()
connections = data.get('SearchResult', {}).get('resources', [])
print(f"Found {len(connections)} SXP connections\n")

# Get full details with raw JSON
for conn in connections:
    conn_id = conn['id']
    r2 = requests.get(f'{ISE}/ers/config/sxpconnections/{conn_id}', auth=AUTH, headers=HEADERS, verify=False)
    print(f"--- Connection {conn_id} ---")
    print(json.dumps(r2.json(), indent=2))
    print()
