"""
Web Dashboard — Network Naming Compliance Monitor
Run:  python src/dashboard.py
Open: http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify
import sqlite3, json, datetime
from monitor import (
    init_db, check_compliance, save_device, save_alert,
    _demo_devices, CONFIG, get_all_devices, get_all_alerts
)

app = Flask(__name__)
init_db(CONFIG["db_path"])

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Network Naming Compliance Monitor</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
  header{background:#161b27;border-bottom:1px solid #2d3748;padding:16px 32px;display:flex;align-items:center;justify-content:space-between}
  header h1{font-size:18px;font-weight:600;color:#fff}header span{font-size:12px;color:#718096}
  .live{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#48bb78}
  .live::before{content:'';width:8px;height:8px;border-radius:50%;background:#48bb78;animation:pulse 1.5s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
  main{padding:24px 32px;max-width:1200px;margin:0 auto}
  .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
  .metric{background:#161b27;border:1px solid #2d3748;border-radius:10px;padding:16px 20px}
  .metric-label{font-size:12px;color:#718096;margin-bottom:6px}
  .metric-val{font-size:28px;font-weight:700}
  .green{color:#48bb78}.red{color:#fc8181}.amber{color:#f6ad55}.blue{color:#63b3ed}
  .panels{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px}
  .card{background:#161b27;border:1px solid #2d3748;border-radius:10px;padding:16px 20px}
  .card h2{font-size:13px;color:#a0aec0;margin-bottom:12px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
  .alert-box{background:#2d1a1a;border:1px solid #9b2c2c;border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:13px;animation:fadein .4s}
  @keyframes fadein{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
  .alert-title{color:#fc8181;font-weight:600;margin-bottom:3px}
  .alert-sub{color:#a0aec0;font-size:11px}
  .ok-box{background:#1a2d1e;border:1px solid #276749;border-radius:8px;padding:8px 14px;margin-bottom:6px;font-size:12px;color:#9ae6b4;animation:fadein .4s}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{color:#718096;font-weight:500;text-align:left;padding:8px 12px;border-bottom:1px solid #2d3748;font-size:11px;text-transform:uppercase}
  td{padding:8px 12px;border-bottom:1px solid #1a202c;color:#e2e8f0}
  tr:hover td{background:#1a202c}
  .pill{display:inline-flex;align-items:center;gap:4px;font-size:11px;padding:2px 10px;border-radius:20px;font-weight:600}
  .pill-ok{background:#1a2d1e;color:#9ae6b4}.pill-bad{background:#2d1a1a;color:#fc8181}
  .btn{padding:6px 14px;border-radius:6px;font-size:12px;cursor:pointer;border:1px solid #4a5568;background:#2d3748;color:#e2e8f0;margin-right:8px}
  .btn:hover{background:#4a5568}
  .controls{display:flex;align-items:center;gap:10px;margin-bottom:20px;flex-wrap:wrap}
  input[type=text]{background:#2d3748;border:1px solid #4a5568;color:#e2e8f0;padding:6px 12px;border-radius:6px;font-size:13px;width:200px}
  input[type=text]::placeholder{color:#718096}
  .empty{text-align:center;padding:24px;color:#4a5568;font-size:13px}
  footer{text-align:center;padding:20px;color:#4a5568;font-size:12px;border-top:1px solid #2d3748;margin-top:24px}
</style>
</head>
<body>
<header>
  <h1>🛡 Network Naming Compliance Monitor</h1>
  <div style="display:flex;align-items:center;gap:16px">
    <span class="live">Live Monitoring</span>
    <span id="last-scan" style="font-size:12px;color:#718096"></span>
  </div>
</header>
<main>
  <div class="metrics">
    <div class="metric"><div class="metric-label">Total Devices</div><div class="metric-val blue" id="m-total">0</div></div>
    <div class="metric"><div class="metric-label">Compliant</div><div class="metric-val green" id="m-ok">0</div></div>
    <div class="metric"><div class="metric-label">Violations</div><div class="metric-val red" id="m-bad">0</div></div>
    <div class="metric"><div class="metric-label">Alerts Sent</div><div class="metric-val amber" id="m-alerts">0</div></div>
  </div>
  <div class="controls">
    <input type="text" id="dev-input" placeholder="Enter device hostname…">
    <button class="btn" onclick="addDevice()">+ Add Device</button>
    <button class="btn" onclick="runScan()">⟳ Simulate Scan</button>
    <button class="btn" onclick="clearAlerts()">🗑 Clear Alerts</button>
  </div>
  <div class="panels">
    <div class="card">
      <h2>⚠ Admin Alerts</h2>
      <div id="alert-list"><div class="empty">No alerts — all clear!</div></div>
    </div>
    <div class="card">
      <h2>📡 Live Event Feed</h2>
      <div id="feed-list"><div class="empty">Waiting for devices…</div></div>
    </div>
  </div>
  <div class="card">
    <h2>💻 Connected Devices</h2>
    <table>
      <thead><tr><th>Hostname</th><th>IP Address</th><th>MAC</th><th>First Seen</th><th>Status</th></tr></thead>
      <tbody id="device-table"></tbody>
    </table>
  </div>
</main>
<footer>Network Naming Compliance Monitor v1.0 &mdash; Internship Project</footer>
<script>
async function refresh(){
  const res = await fetch('/api/status');
  const d   = await res.json();
  document.getElementById('m-total').textContent   = d.total;
  document.getElementById('m-ok').textContent      = d.compliant;
  document.getElementById('m-bad').textContent     = d.violations;
  document.getElementById('m-alerts').textContent  = d.alerts;
  document.getElementById('last-scan').textContent = 'Last scan: ' + new Date().toLocaleTimeString();

  const at = document.getElementById('alert-list');
  if(d.alert_items.length){
    at.innerHTML = d.alert_items.map(a=>`
      <div class="alert-box">
        <div class="alert-title">⚠ ${a.hostname} (${a.ip})</div>
        <div class="alert-sub">${a.reason} &bull; ${a.sent_at}</div>
      </div>`).join('');
  } else { at.innerHTML = '<div class="empty">No alerts — all clear!</div>'; }

  const fl = document.getElementById('feed-list');
  fl.innerHTML = d.devices.slice(0,10).map(dv=>`
    <div class="${dv.compliant?'ok-box':'alert-box'}">
      <b>${dv.hostname}</b> &mdash; ${dv.ip} &bull; ${dv.compliant?'✓ Compliant':'✗ Violation'} &bull; ${dv.first_seen}
    </div>`).join('') || '<div class="empty">Waiting for devices…</div>';

  const tb = document.getElementById('device-table');
  tb.innerHTML = d.devices.map(dv=>`
    <tr><td style="font-family:monospace">${dv.hostname}</td><td style="font-family:monospace">${dv.ip}</td>
    <td style="font-family:monospace;font-size:11px;color:#718096">${dv.mac||'—'}</td>
    <td style="color:#718096;font-size:12px">${dv.first_seen}</td>
    <td><span class="pill ${dv.compliant?'pill-ok':'pill-bad'}">${dv.compliant?'✓ Compliant':'✗ Violation'}</span></td></tr>`
  ).join('') || '<tr><td colspan="5" class="empty">No devices yet</td></tr>';
}

async function addDevice(){
  const name = document.getElementById('dev-input').value.trim();
  if(!name) return;
  await fetch('/api/add_device', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({hostname:name})});
  document.getElementById('dev-input').value = '';
  refresh();
}
async function runScan(){
  await fetch('/api/scan', {method:'POST'});
  refresh();
}
function clearAlerts(){
  document.getElementById('alert-list').innerHTML = '<div class="empty">Cleared!</div>';
}
document.getElementById('dev-input').addEventListener('keydown', e=>{ if(e.key==='Enter') addDevice(); });
refresh();
setInterval(refresh, 5000);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route("/api/status")
def status():
    devices = get_all_devices()
    alerts  = get_all_alerts()
    device_list = [
        {"hostname": r[0], "ip": r[1], "mac": r[2],
         "compliant": bool(r[3]), "first_seen": r[4]} for r in devices
    ]
    alert_list = [
        {"hostname": r[0], "ip": r[1], "reason": r[2], "sent_at": r[3]} for r in alerts
    ]
    total     = len(device_list)
    compliant = sum(1 for d in device_list if d["compliant"])
    return jsonify({
        "total": total, "compliant": compliant,
        "violations": total - compliant, "alerts": len(alert_list),
        "devices": device_list, "alert_items": alert_list
    })

@app.route("/api/add_device", methods=["POST"])
def api_add_device():
    from flask import request
    data     = request.get_json()
    hostname = data.get("hostname", "").strip().upper()
    ip       = "192.168.1." + str(hash(hostname) % 200 + 10)
    mac      = ":".join(f"{(hash(hostname+str(i)))%256:02X}" for i in range(6))
    compliant, failures = check_compliance(hostname)
    save_device(hostname, ip, mac, compliant)
    if not compliant:
        save_alert(hostname, ip, "; ".join(failures))
    return jsonify({"compliant": compliant, "failures": failures})

@app.route("/api/scan", methods=["POST"])
def api_scan():
    devices = _demo_devices()
    results = []
    for dev in devices:
        compliant, failures = check_compliance(dev["hostname"])
        save_device(dev["hostname"], dev["ip"], dev["mac"], compliant)
        if not compliant:
            save_alert(dev["hostname"], dev["ip"], "; ".join(failures))
        results.append({"hostname": dev["hostname"], "compliant": compliant})
    return jsonify({"scanned": len(results), "results": results})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
