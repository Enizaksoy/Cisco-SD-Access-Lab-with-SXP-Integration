#!/usr/bin/env python3
from creds import CATCENTER_PASS
"""Catalyst Center Verification Script
Checks fabric site, VN, IP pools, anycast gateways, ISE integration via API.
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json, urllib.request, ssl, base64

CATCENTER_IP = '192.168.11.254'
USERNAME = 'admin'
PASSWORD = CATCENTER_PASS

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_token():
    req = urllib.request.Request(
        f'https://{CATCENTER_IP}/dna/system/api/v1/auth/token',
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Basic ' + base64.b64encode(f'{USERNAME}:{PASSWORD}'.encode()).decode()},
        method='POST')
    return json.loads(urllib.request.urlopen(req, context=ctx).read().decode())['Token']

def api_get(path, token):
    req = urllib.request.Request(
        f'https://{CATCENTER_IP}{path}',
        headers={'x-auth-token': token})
    try:
        return json.loads(urllib.request.urlopen(req, context=ctx).read().decode())
    except urllib.error.HTTPError as e:
        return {'error': f'{e.code}: {e.read().decode()[:200]}'}

def main():
    token = get_token()
    print('Token: OK\n')

    checks = [
        ('Network Devices',           '/dna/intent/api/v1/network-device?managementIpAddress=192.168.244.*'),
        ('Fabric Sites',              '/dna/intent/api/v1/sda/fabricSites'),
        ('Fabric Zones',              '/dna/intent/api/v1/sda/fabricZones'),
        ('Anycast Gateways',          '/dna/intent/api/v1/sda/anycastGateways'),
        ('Global IP Pools',           '/dna/intent/api/v1/global-pool'),
        ('Authentication Servers',    '/dna/intent/api/v1/authentication-policy-servers'),
        ('Virtual Network (Corp_VN)', '/dna/intent/api/v1/virtual-network?virtualNetworkName=Corp_VN'),
        ('SDA VN at Fabric Site',     '/dna/intent/api/v1/business/sda/virtual-network?virtualNetworkName=Corp_VN&siteNameHierarchy=Global/SDA-Lab'),
    ]

    for label, path in checks:
        print(f'--- {label} ---')
        resp = api_get(path, token)
        # Summarize response
        if 'response' in resp:
            items = resp['response']
            if isinstance(items, list):
                print(f'  Count: {len(items)}')
                for item in items:
                    if isinstance(item, dict):
                        # Print key fields
                        keys_to_show = ['hostname', 'managementIpAddress', 'reachabilityStatus',
                                        'ipAddress', 'state', 'isIseEnabled', 'pxgridEnabled',
                                        'id', 'siteId', 'fabricId', 'virtualNetworkName',
                                        'ipPoolName', 'vlanName', 'vlanId', 'trafficType',
                                        'ipPoolCidr', 'ipPoolName', 'authenticationProfileName',
                                        'trustState', 'role']
                        summary = {k: item[k] for k in keys_to_show if k in item}
                        print(f'  {json.dumps(summary)}')
            else:
                print(f'  {json.dumps(items, indent=2)[:500]}')
        elif 'error' in resp:
            print(f'  ERROR: {resp["error"]}')
        else:
            # Non-standard response (e.g., VN query)
            keys_to_show = ['virtualNetworkName', 'status', 'description',
                            'siteNameHierarchy', 'fabricType']
            summary = {k: resp[k] for k in keys_to_show if k in resp}
            if summary:
                print(f'  {json.dumps(summary)}')
            else:
                print(f'  {json.dumps(resp, indent=2)[:500]}')
        print()

if __name__ == '__main__':
    main()
