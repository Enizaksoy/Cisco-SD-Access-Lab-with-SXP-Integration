"""
pxGrid 2.0 Web Dashboard - Real-time ISE Session/SGT/SXP/Policy viewer
Supports both REST pull (polling) and WebSocket push (STOMP real-time events)

Run: python pxgrid_web.py
Open: http://localhost:5050
"""
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, jsonify, Response, request
import requests
import urllib3
import time
import json
import ssl
import base64
import threading
import queue
import websocket
urllib3.disable_warnings()

app = Flask(__name__)

ISE = '192.168.11.250'
PXGRID_USER = 'pxgrid_lab_client'
PXGRID_PASS = 'MhVnd1nOBD7WwOXb'
H = {'Content-Type': 'application/json', 'Accept': 'application/json'}
AUTH = (PXGRID_USER, PXGRID_PASS)

# Real-time event list (WebSocket events polled by browser)
recent_events = []
recent_events_lock = threading.Lock()
ws_connected = False
ws_events_count = 0


def get_access_secret(peer_node):
    r = requests.post(f'https://{ISE}:8910/pxgrid/control/AccessSecret',
                      json={'peerNodeName': peer_node},
                      headers=H, auth=AUTH, verify=False, timeout=15)
    return r.json().get('secret', '') if r.status_code == 200 else ''


def pxgrid_post(url, svc_auth):
    r = requests.post(url, json={}, headers=H, auth=svc_auth, verify=False, timeout=15)
    return r.json() if r.status_code == 200 else {}


# ──────────────────────────────────────────────
# WebSocket STOMP subscriber (background thread)
# ──────────────────────────────────────────────
def parse_stomp_message(raw):
    """Parse a STOMP MESSAGE frame into headers + body."""
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    raw = raw.rstrip('\x00')
    parts = raw.split('\n\n', 1)
    header_lines = parts[0].split('\n')
    command = header_lines[0] if header_lines else ''
    headers = {}
    for line in header_lines[1:]:
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k] = v
    body = parts[1] if len(parts) > 1 else ''
    return command, headers, body


def stomp_subscriber():
    """Background thread: connect to pxGrid WebSocket and subscribe to topics."""
    global ws_connected, ws_events_count

    topics = [
        ('/topic/com.cisco.ise.session', 'sub-session'),
        ('/topic/com.cisco.ise.session.group', 'sub-session-group'),
        ('/topic/com.cisco.ise.sxp.binding', 'sub-sxp'),
        ('/topic/com.cisco.ise.config.trustsec.security.group', 'sub-sgt'),
        ('/topic/com.cisco.ise.config.trustsec.egress.policy', 'sub-policy'),
    ]

    while True:
        try:
            print("[WS] Getting pubsub access secret...")
            secret = get_access_secret('~ise-pubsub-ise')
            if not secret:
                print("[WS] Failed to get secret, retrying in 30s...")
                time.sleep(30)
                continue

            ws_url = f'wss://{ISE}:8910/pxgrid/ise/pubsub'
            auth_header = base64.b64encode(f'{PXGRID_USER}:{secret}'.encode()).decode()

            print(f"[WS] Connecting to {ws_url}...")
            ws = websocket.create_connection(ws_url,
                sslopt={'cert_reqs': ssl.CERT_NONE},
                header={'Authorization': f'Basic {auth_header}'},
                timeout=300)

            # STOMP CONNECT (binary frame)
            connect_frame = f'CONNECT\naccept-version:1.2\nhost:{ISE}\n\n\x00'
            ws.send_binary(connect_frame.encode('utf-8'))
            resp = ws.recv()
            if isinstance(resp, bytes):
                resp = resp.decode('utf-8', errors='replace')

            if 'CONNECTED' not in resp:
                print(f"[WS] STOMP connect failed: {resp[:200]}")
                ws.close()
                time.sleep(10)
                continue

            print("[WS] STOMP connected!")
            ws_connected = True

            # Subscribe to all topics
            for topic, sub_id in topics:
                sub_frame = f'SUBSCRIBE\ndestination:{topic}\nid:{sub_id}\n\n\x00'
                ws.send_binary(sub_frame.encode('utf-8'))
                print(f"[WS] Subscribed: {topic}")

            # Listen for events
            while True:
                raw = ws.recv()
                command, headers, body = parse_stomp_message(raw)

                if command == 'MESSAGE':
                    ws_events_count += 1
                    topic = headers.get('destination', 'unknown')
                    ts = time.strftime('%H:%M:%S')

                    # Parse JSON body
                    try:
                        data = json.loads(body) if body else {}
                    except json.JSONDecodeError:
                        data = {'raw': body[:500]}

                    event = {
                        'type': 'pxgrid_event',
                        'topic': topic,
                        'timestamp': ts,
                        'data': data,
                        'count': ws_events_count,
                    }

                    # Add to recent events list
                    with recent_events_lock:
                        recent_events.insert(0, event)
                        if len(recent_events) > 100:
                            recent_events[:] = recent_events[:100]

                    # Log
                    short_topic = topic.split('.')[-1]
                    print(f"[WS] [{ts}] Event #{ws_events_count} on {short_topic}: {json.dumps(data)[:150]}")

                elif command == 'HEARTBEAT' or command == '':
                    pass  # keepalive
                else:
                    print(f"[WS] Frame: {command}")

        except Exception as e:
            ws_connected = False
            print(f"[WS] Error: {e}. Reconnecting in 10s...")
            time.sleep(10)


# ──────────────────────────────────────────────
# REST API endpoints
# ──────────────────────────────────────────────
@app.route('/api/data')
def api_data():
    try:
        mnt_secret = get_access_secret('~ise-mnt-ise')
        admin_secret = get_access_secret('~ise-admin-ise')
        mnt_auth = (PXGRID_USER, mnt_secret)
        admin_auth = (PXGRID_USER, admin_secret)

        # SGTs
        sgt_data = pxgrid_post(f'https://{ISE}:8910/pxgrid/ise/config/trustsec/getSecurityGroups',
                               svc_auth=admin_auth)
        sgt_map = {sg['tag']: sg['name'] for sg in sgt_data.get('securityGroups', [])}
        sgt_id_map = {sg.get('id', ''): sg for sg in sgt_data.get('securityGroups', [])}

        # Sessions
        sess_data = pxgrid_post(f'https://{ISE}:8910/pxgrid/mnt/sd/getSessions', svc_auth=mnt_auth)
        sessions = []
        for s in sess_data.get('sessions', []):
            ips = [ip for ip in s.get('ipAddresses', []) if ip and not ip.startswith('fe80')]
            profiles = s.get('selectedAuthzProfiles', [])
            sessions.append({
                'user': s.get('userName', '-'),
                'ip': ips[0] if ips else '-',
                'mac': s.get('callingStationId', '-'),
                'sgt': s.get('ctsSecurityGroup', '-'),
                'nasPort': s.get('nasPortId', '-'),
                'nasIp': s.get('nasIpAddress', '-'),
                'state': s.get('state', '-'),
                'profile': profiles[0] if profiles else '-',
                'endpoint': s.get('endpointProfile', '-'),
                'vrf': s.get('vrf', '-') or '-',
                'authMethod': s.get('authMethod', '-'),
                'hostname': s.get('adHostResolvedIdentities', '-'),
            })

        # SXP Bindings
        bind_data = pxgrid_post(f'https://{ISE}:8910/pxgrid/ise/sxp/getBindings', svc_auth=mnt_auth)
        bindings = []
        for b in bind_data.get('bindings', []):
            tag = b.get('tag', 0)
            bindings.append({
                'ip': b.get('ipPrefix', '-'),
                'tag': tag,
                'sgtName': sgt_map.get(tag, '?'),
                'type': b.get('type', '-'),
                'source': b.get('source', '-'),
                'vpn': b.get('vpn', '-'),
                'peerSequence': b.get('peerSequence', '-'),
                'timestamp': b.get('timestamp', '-'),
            })

        # SGT list
        sgts = [{'tag': t, 'name': n} for t, n in sorted(sgt_map.items())]

        # Egress Policies
        policy_data = pxgrid_post(f'https://{ISE}:8910/pxgrid/ise/config/trustsec/getEgressPolicies',
                                  svc_auth=admin_auth)
        policies = []
        for p in policy_data.get('egressPolicies', []):
            src_id = p.get('sourceSecurityGroupId', '')
            dst_id = p.get('destinationSecurityGroupId', '')
            src_sg = sgt_id_map.get(src_id, {})
            dst_sg = sgt_id_map.get(dst_id, {})
            policies.append({
                'name': p.get('name', '-'),
                'status': p.get('status', '-'),
                'srcSgt': src_sg.get('name', src_id[:12]),
                'srcTag': src_sg.get('tag', '-'),
                'dstSgt': dst_sg.get('name', dst_id[:12]),
                'dstTag': dst_sg.get('tag', '-'),
                'description': p.get('description', '-'),
            })

        return jsonify({
            'sessions': sessions,
            'bindings': bindings,
            'sgts': sgts,
            'policies': policies,
            'wsConnected': ws_connected,
            'wsEvents': ws_events_count,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'ok'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/events')
def api_events():
    """Return recent WebSocket events (polled by browser every 3s)."""
    since = int(request.args.get('since', 0))
    with recent_events_lock:
        new_events = [e for e in recent_events if e.get('count', 0) > since]
    return jsonify({
        'events': new_events[:20],
        'wsConnected': ws_connected,
        'wsEvents': ws_events_count,
    })


@app.route('/')
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>pxGrid 2.0 Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }

  .header { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-bottom: 1px solid #334155; padding: 20px 32px; display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 22px; font-weight: 600; color: #f8fafc; }
  .header h1 span { color: #38bdf8; }
  .header-right { display: flex; align-items: center; gap: 16px; }
  .status-badge { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; }
  .status-ok { background: #065f46; color: #6ee7b7; }
  .status-err { background: #7f1d1d; color: #fca5a5; }
  .status-ws { background: #1e3a5f; color: #7dd3fc; }
  .timestamp { color: #94a3b8; font-size: 13px; }
  .refresh-btn { background: #1e40af; color: #fff; border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 500; transition: background 0.2s; }
  .refresh-btn:hover { background: #2563eb; }
  .refresh-btn:disabled { opacity: 0.5; cursor: wait; }
  .ise-info { color: #64748b; font-size: 12px; }

  .container { padding: 24px 32px; display: flex; flex-direction: column; gap: 24px; }

  .stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
  .stat-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }
  .stat-card .label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .stat-card .value { font-size: 28px; font-weight: 700; color: #f8fafc; }
  .stat-card .sub { font-size: 12px; color: #64748b; margin-top: 4px; }
  .stat-card:nth-child(1) .value { color: #38bdf8; }
  .stat-card:nth-child(2) .value { color: #a78bfa; }
  .stat-card:nth-child(3) .value { color: #34d399; }
  .stat-card:nth-child(4) .value { color: #fb923c; }
  .stat-card:nth-child(5) .value { color: #f472b6; }

  .section { background: #1e293b; border: 1px solid #334155; border-radius: 12px; overflow: hidden; }
  .section-header { padding: 16px 20px; border-bottom: 1px solid #334155; display: flex; align-items: center; gap: 10px; }
  .section-header h2 { font-size: 15px; font-weight: 600; }
  .dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot-blue { background: #38bdf8; }
  .dot-purple { background: #a78bfa; }
  .dot-green { background: #34d399; }
  .dot-orange { background: #fb923c; }
  .dot-pink { background: #f472b6; }
  .dot-red { background: #ef4444; }
  .pulse { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; padding: 10px 16px; font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; background: #0f172a; font-weight: 600; position: sticky; top: 0; }
  td { padding: 10px 16px; font-size: 13px; border-top: 1px solid #1e293b; }
  tr:hover td { background: #1e293b80; }
  .table-scroll { max-height: 400px; overflow-y: auto; }

  .badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; }
  .badge-started { background: #065f46; color: #6ee7b7; }
  .badge-disconnected { background: #78350f; color: #fcd34d; }
  .badge-local { background: #1e3a5f; color: #7dd3fc; }
  .badge-session { background: #3b0764; color: #d8b4fe; }
  .badge-sgt { background: #1e293b; color: #94a3b8; border: 1px solid #475569; }
  .badge-enabled { background: #065f46; color: #6ee7b7; }
  .badge-vpn { background: #1e3a5f; color: #93c5fd; border: 1px solid #1e40af; }
  .badge-vrf { background: #312e81; color: #a5b4fc; border: 1px solid #4338ca; }
  .badge-method { background: #1c1917; color: #a8a29e; border: 1px solid #44403c; }
  .badge-push { background: #831843; color: #f9a8d4; }
  .badge-pull { background: #1e3a5f; color: #7dd3fc; }

  .loading { text-align: center; padding: 60px; color: #64748b; }
  .spinner { display: inline-block; width: 32px; height: 32px; border: 3px solid #334155; border-top-color: #38bdf8; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 12px; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .protocol-info { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; margin: 0 20px 16px; font-size: 12px; color: #64748b; }
  .protocol-info code { color: #38bdf8; background: #1e293b; padding: 2px 6px; border-radius: 4px; }

  .event-log { max-height: 300px; overflow-y: auto; padding: 12px 20px; font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 12px; }
  .event-entry { padding: 6px 0; border-bottom: 1px solid #1e293b; display: flex; gap: 12px; }
  .event-entry .time { color: #64748b; min-width: 70px; }
  .event-entry .topic { color: #38bdf8; min-width: 100px; }
  .event-entry .detail { color: #e2e8f0; word-break: break-all; }
  .event-new { animation: fadeIn 0.5s ease; background: #1e293b40; }
  @keyframes fadeIn { from { background: #38bdf820; } to { background: transparent; } }

  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 1400px) { .two-col { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(3, 1fr); } }
</style>
</head>
<body>
<div class="header">
  <div>
    <h1><span>pxGrid 2.0</span> Dashboard</h1>
    <div class="ise-info">ISE: 192.168.11.250 &bull; Protocol: REST + WebSocket (STOMP) &bull; Port: 8910</div>
  </div>
  <div class="header-right">
    <span class="timestamp" id="ts">Loading...</span>
    <span class="status-badge status-ws" id="wsStatus">WS: connecting...</span>
    <span class="status-badge" id="status">...</span>
    <button class="refresh-btn" id="refreshBtn" onclick="loadData()">Refresh</button>
  </div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="label">Active Sessions</div><div class="value" id="sessCount">-</div><div class="sub">802.1X / MAB authenticated</div></div>
    <div class="stat-card"><div class="label">SXP Bindings</div><div class="value" id="bindCount">-</div><div class="sub">IP-to-SGT mappings</div></div>
    <div class="stat-card"><div class="label">Security Groups</div><div class="value" id="sgtCount">-</div><div class="sub">TrustSec SGTs defined</div></div>
    <div class="stat-card"><div class="label">Egress Policies</div><div class="value" id="polCount">-</div><div class="sub">SGACL matrix rules</div></div>
    <div class="stat-card"><div class="label">Push Events</div><div class="value" id="evtCount">0</div><div class="sub">Real-time via WebSocket</div></div>
  </div>

  <!-- Real-time Event Log -->
  <div class="section">
    <div class="section-header"><div class="dot dot-red pulse" id="wsDot"></div><h2>Real-Time Event Stream <span class="badge badge-push">PUSH via WebSocket/STOMP</span></h2></div>
    <div class="protocol-info">
      Subscribed topics: <code>/topic/com.cisco.ise.session</code> &bull; <code>/topic/com.cisco.ise.sxp.binding</code> &bull; <code>/topic/com.cisco.ise.config.trustsec.security.group</code> &bull; <code>/topic/com.cisco.ise.config.trustsec.egress.policy</code>
    </div>
    <div class="event-log" id="eventLog">
      <div style="color: #64748b; text-align: center; padding: 20px;">Waiting for real-time events... (authenticate a new user to see events appear here instantly)</div>
    </div>
  </div>

  <!-- Sessions -->
  <div class="section">
    <div class="section-header"><div class="dot dot-blue"></div><h2>Active Sessions <span class="badge badge-pull">REST Pull</span></h2></div>
    <div class="protocol-info">Service: <code>com.cisco.ise.session</code> &bull; REST: <code>getSessions</code></div>
    <div id="sessTable"><div class="loading"><div class="spinner"></div><br>Loading sessions...</div></div>
  </div>

  <!-- SXP Bindings -->
  <div class="section">
    <div class="section-header"><div class="dot dot-purple"></div><h2>SXP Bindings <span class="badge badge-pull">REST Pull</span></h2></div>
    <div class="protocol-info">Service: <code>com.cisco.ise.sxp</code> &bull; REST: <code>getBindings</code></div>
    <div id="bindTable"><div class="loading"><div class="spinner"></div><br>Loading bindings...</div></div>
  </div>

  <div class="two-col">
    <div class="section">
      <div class="section-header"><div class="dot dot-green"></div><h2>Security Groups (SGTs)</h2></div>
      <div class="table-scroll" id="sgtTable"><div class="loading"><div class="spinner"></div><br>Loading SGTs...</div></div>
    </div>
    <div class="section">
      <div class="section-header"><div class="dot dot-orange"></div><h2>TrustSec Egress Policies</h2></div>
      <div class="table-scroll" id="polTable"><div class="loading"><div class="spinner"></div><br>Loading policies...</div></div>
    </div>
  </div>

  <!-- pxGrid Services reference -->
  <div class="section">
    <div class="section-header"><div class="dot dot-pink"></div><h2>pxGrid 2.0 Architecture</h2></div>
    <div style="padding: 16px 20px;">
      <table>
        <tr><th>Service</th><th>Data</th><th>REST (Pull)</th><th>WebSocket Topic (Push)</th></tr>
        <tr><td><code>com.cisco.ise.session</code></td><td>RADIUS Sessions</td><td>getSessions, getSessionByIp/Mac</td><td>/topic/com.cisco.ise.session</td></tr>
        <tr><td><code>com.cisco.ise.sxp</code></td><td>SXP Bindings</td><td>getBindings</td><td>/topic/com.cisco.ise.sxp.binding</td></tr>
        <tr><td><code>com.cisco.ise.config.trustsec</code></td><td>SGTs, SGACLs, VNs</td><td>getSecurityGroups, getEgressPolicies</td><td>/topic/com.cisco.ise.config.trustsec.*</td></tr>
        <tr><td><code>com.cisco.ise.config.profiler</code></td><td>Endpoint Profiles</td><td>getProfiles</td><td>/topic/com.cisco.ise.config.profiler</td></tr>
        <tr><td><code>com.cisco.ise.radius</code></td><td>Auth Failures</td><td>getFailures</td><td>/topic/com.cisco.ise.radius.failure</td></tr>
        <tr><td><code>com.cisco.ise.pubsub</code></td><td>WebSocket Endpoint</td><td colspan="2">wss://ISE:8910/pxgrid/ise/pubsub (STOMP 1.2)</td></tr>
      </table>
    </div>
  </div>
</div>

<script>
let lastEventCount = 0;
let firstEvent = true;
let needsRefresh = false;

// Poll for new WebSocket events every 3 seconds
async function pollEvents() {
  try {
    const r = await fetch('/api/events?since=' + lastEventCount);
    const d = await r.json();

    document.getElementById('wsStatus').textContent = d.wsConnected ? 'WS: LIVE' : 'WS: reconnecting...';
    document.getElementById('wsStatus').className = 'status-badge ' + (d.wsConnected ? 'status-ok' : 'status-err');
    document.getElementById('evtCount').textContent = d.wsEvents;

    if (d.events && d.events.length > 0) {
      // Clear placeholder on first event
      if (firstEvent) {
        document.getElementById('eventLog').innerHTML = '';
        firstEvent = false;
      }

      // Process events (newest first from API, but we reverse to add in order)
      const sorted = d.events.sort((a, b) => a.count - b.count);
      sorted.forEach(evt => {
        if (evt.count <= lastEventCount) return;
        lastEventCount = evt.count;

        const topicShort = evt.topic.split('.').slice(-2).join('.');
        let detail = '';
        const ed = evt.data;

        if (evt.topic.includes('session')) {
          const ips = (ed.ipAddresses || []).filter(ip => ip && !ip.startsWith('fe80'));
          detail = (ed.state || '') + ' | User: ' + (ed.userName || '?') + ' | IP: ' + (ips[0] || '-') + ' | SGT: ' + (ed.ctsSecurityGroup || '-') + ' | MAC: ' + (ed.callingStationId || '-') + ' | Profile: ' + ((ed.selectedAuthzProfiles || [])[0] || '-');
          needsRefresh = true;
        } else if (evt.topic.includes('sxp')) {
          detail = 'IP: ' + (ed.ipPrefix || ed.ip || '?') + ' | SGT: ' + (ed.tag || '?') + ' | Type: ' + (ed.type || '?') + ' | VPN: ' + (ed.vpn || '?');
          needsRefresh = true;
        } else if (evt.topic.includes('security.group')) {
          detail = 'SGT: ' + (ed.name || '?') + ' (tag ' + (ed.tag || '?') + ')';
        } else {
          detail = JSON.stringify(ed).substring(0, 200);
        }

        const entry = document.createElement('div');
        entry.className = 'event-entry event-new';
        entry.innerHTML = '<span class="time">' + evt.timestamp + '</span><span class="topic">' + topicShort + '</span><span class="detail">' + detail + '</span>';

        const log = document.getElementById('eventLog');
        log.insertBefore(entry, log.firstChild);
        while (log.children.length > 50) log.removeChild(log.lastChild);
      });

      document.getElementById('wsDot').className = 'dot dot-green pulse';

      // Auto-refresh tables when session/sxp events arrive
      if (needsRefresh) {
        needsRefresh = false;
        loadData();
      }
    }
  } catch(e) {
    console.error('Event poll error:', e);
  }
  setTimeout(pollEvents, 3000);
}

async function loadData() {
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true; btn.textContent = 'Loading...';
  try {
    const r = await fetch('/api/data');
    const d = await r.json();
    if (d.status === 'error') throw new Error(d.message);

    document.getElementById('ts').textContent = 'Updated: ' + d.timestamp;
    document.getElementById('status').className = 'status-badge status-ok';
    document.getElementById('status').textContent = 'REST: OK';
    document.getElementById('wsStatus').textContent = d.wsConnected ? 'WS: LIVE' : 'WS: connecting...';
    document.getElementById('wsStatus').className = 'status-badge ' + (d.wsConnected ? 'status-ok' : 'status-ws');
    document.getElementById('evtCount').textContent = d.wsEvents;

    const activeSess = d.sessions.filter(s => s.state === 'STARTED').length;
    document.getElementById('sessCount').textContent = activeSess + ' / ' + d.sessions.length;
    document.getElementById('bindCount').textContent = d.bindings.length;
    document.getElementById('sgtCount').textContent = d.sgts.length;
    document.getElementById('polCount').textContent = d.policies.length;

    // Sessions
    let sh = '<table><tr><th>User</th><th>IP Address</th><th>MAC</th><th>SGT</th><th>NAS Port</th><th>State</th><th>Auth Profile</th><th>Auth</th><th>VRF</th><th>Endpoint</th><th>Hostname</th></tr>';
    d.sessions.forEach(s => {
      const sc = s.state === 'STARTED' ? 'badge-started' : 'badge-disconnected';
      sh += '<tr><td><strong>' + s.user + '</strong></td><td>' + s.ip + '</td><td style="font-family:monospace;font-size:12px">' + s.mac + '</td><td>' + (s.sgt !== '-' ? '<span class="badge badge-sgt">' + s.sgt + '</span>' : '-') + '</td><td style="font-size:12px">' + s.nasPort + '</td><td><span class="badge ' + sc + '">' + s.state + '</span></td><td>' + s.profile + '</td><td><span class="badge badge-method">' + s.authMethod + '</span></td><td>' + (s.vrf !== '-' ? '<span class="badge badge-vrf">' + s.vrf + '</span>' : '-') + '</td><td>' + s.endpoint + '</td><td style="font-size:12px;color:#94a3b8">' + s.hostname + '</td></tr>';
    });
    sh += '</table>';
    document.getElementById('sessTable').innerHTML = sh;

    // Bindings
    let bh = '<table><tr><th>IP / Prefix</th><th>SGT Tag</th><th>SGT Name</th><th>Type</th><th>Source</th><th>VPN / Domain</th><th>Peer Sequence</th><th>Timestamp</th></tr>';
    d.bindings.forEach(b => {
      const tc = b.type === 'Local' ? 'badge-local' : 'badge-session';
      const ts = b.timestamp ? b.timestamp.replace('T', ' ').replace(/\\.\\d+Z/, '') : '-';
      bh += '<tr><td style="font-family:monospace">' + b.ip + '</td><td><strong>' + b.tag + '</strong></td><td><span class="badge badge-sgt">' + b.sgtName + '</span></td><td><span class="badge ' + tc + '">' + b.type + '</span></td><td>' + b.source + '</td><td><span class="badge badge-vpn">' + b.vpn + '</span></td><td style="font-size:11px;color:#64748b">' + b.peerSequence + '</td><td style="font-size:11px;color:#64748b">' + ts + '</td></tr>';
    });
    bh += '</table>';
    document.getElementById('bindTable').innerHTML = bh;

    // SGTs
    let gh = '<table><tr><th>Tag</th><th>Name</th></tr>';
    d.sgts.forEach(s => { gh += '<tr><td><strong>' + s.tag + '</strong></td><td>' + s.name + '</td></tr>'; });
    gh += '</table>';
    document.getElementById('sgtTable').innerHTML = gh;

    // Policies
    let ph = '<table><tr><th>Name</th><th>Source SGT</th><th>Dest SGT</th><th>Status</th></tr>';
    d.policies.forEach(p => {
      ph += '<tr><td><strong>' + p.name + '</strong></td><td>' + p.srcSgt + ' (' + p.srcTag + ')</td><td>' + p.dstSgt + ' (' + p.dstTag + ')</td><td><span class="badge badge-enabled">' + p.status + '</span></td></tr>';
    });
    if (d.policies.length === 0) ph += '<tr><td colspan="4" style="text-align:center;color:#64748b;padding:20px">No policies</td></tr>';
    ph += '</table>';
    document.getElementById('polTable').innerHTML = ph;

  } catch(e) {
    document.getElementById('status').className = 'status-badge status-err';
    document.getElementById('status').textContent = 'ERROR';
    console.error(e);
  }
  btn.disabled = false; btn.textContent = 'Refresh';
}

// Initialize
loadData();
pollEvents();
// Background REST refresh every 60s as fallback
setInterval(loadData, 60000);
</script>
</body>
</html>"""


if __name__ == '__main__':
    # Start WebSocket subscriber in background thread
    ws_thread = threading.Thread(target=stomp_subscriber, daemon=True)
    ws_thread.start()

    print("\n  pxGrid 2.0 Web Dashboard (Real-Time)")
    print("  REST Pull  : http://localhost:5050/api/data")
    print("  WS Push SSE: http://localhost:5050/api/events")
    print("  Dashboard  : http://localhost:5050\n")
    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)
