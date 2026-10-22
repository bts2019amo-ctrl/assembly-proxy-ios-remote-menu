"""Launcher: mitmdump (assembly) + lightweight Remote Menu HTTP server."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "remote_state.json"
ASSET_CDN_RE = r'(?i)^(?:core|dl)[.-][a-z0-9-]+\.freefiremobile\.com(?::443)?$'

DEFAULT_STATE = {
    "esp": True, "aimbot": True, "arm": False, "team_esp": True,
    "crosshair": True, "jump_air": False, "jump_control": False,
    "jump_toggle": False, "carm": False, "ct1": False,
    "author": "@FAKHERDDIN5 + Layla remote", "last_update": None,
}

def load_state():
    if STATE_FILE.is_file():
        try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except: pass
    return dict(DEFAULT_STATE)

def save_state(state):
    state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    cfg = {
        "testCodePatch": True,
        "esp": bool(state.get("esp")), "aim": bool(state.get("aimbot")),
        "arm": bool(state.get("arm")), "team_esp": bool(state.get("team_esp")),
        "crosshair": bool(state.get("crosshair")), "jump_air": bool(state.get("jump_air")),
        "m_esp": bool(state.get("esp")), "m_aim": bool(state.get("aimbot")),
        "m_arm": bool(state.get("arm")), "m_t1": bool(state.get("team_esp")),
        "m_cc": bool(state.get("crosshair")), "m_jair": bool(state.get("jump_air")),
        "m_jc": bool(state.get("jump_control")), "m_jt": bool(state.get("jump_toggle")),
        "m_carm": bool(state.get("carm")), "m_ct1": bool(state.get("ct1")),
    }
    (ROOT / "config" / "localConfig.json").write_text(json.dumps(cfg), encoding="utf-8")

# ─── Dashboard HTML (same as in assembly_proxy) ───
DASHBOARD_HTML = open(ROOT / "assembly_proxy.py", encoding="utf-8").read()  # will extract later if needed
# re-embed clean HTML
DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Layla Remote Menu · Free Fire</title>
<style>
:root{--bg:#0b0f14;--card:#141a22;--accent:#00e5a0;--accent2:#00b4ff;--text:#e6edf3;--muted:#8b949e;--danger:#ff4d6d}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:20px}
.header{text-align:center;margin-bottom:28px}
.header h1{font-size:1.6rem;background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800}
.header p{color:var(--muted);font-size:.85rem;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;max-width:720px;margin:0 auto 24px}
.card{background:var(--card);border-radius:14px;padding:18px 14px;text-align:center;border:1px solid #1f2a36;transition:.2s}
.card.on{border-color:var(--accent);box-shadow:0 0 18px rgba(0,229,160,.15)}
.card .name{font-size:.95rem;font-weight:600;margin-bottom:10px}
.toggle{position:relative;width:56px;height:30px;margin:0 auto;cursor:pointer}
.toggle input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;background:#2d3748;border-radius:30px;transition:.25s}
.slider:before{content:"";position:absolute;height:24px;width:24px;left:3px;bottom:3px;background:white;border-radius:50%;transition:.25s}
input:checked+.slider{background:var(--accent)}
input:checked+.slider:before{transform:translateX(26px)}
.status{max-width:720px;margin:0 auto 20px;background:var(--card);border-radius:12px;padding:14px 18px;font-size:.8rem;color:var(--muted);border:1px solid #1f2a36}
.status b{color:var(--accent)}
.btn-row{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}
.btn{background:var(--card);border:1px solid #2d3748;color:var(--text);padding:10px 18px;border-radius:10px;cursor:pointer;font-size:.85rem;font-weight:600}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.footer{text-align:center;color:var(--muted);font-size:.75rem;margin-top:30px}
.live{display:inline-block;width:8px;height:8px;background:var(--accent);border-radius:50%;margin-right:6px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style></head><body>
<div class="header"><h1>🔥 Layla Remote Menu</h1>
<p>Free Fire Assembly · iOS 1.132.10 · Controle remoto das opções</p></div>
<div class="status" id="status"><span class="live"></span> <b>ONLINE</b> · Estado sincronizado</div>
<div class="grid" id="toggles"></div>
<div class="btn-row">
<button class="btn" onclick="setAll(true)">Ativar Tudo</button>
<button class="btn" onclick="setAll(false)">Desativar Tudo</button>
<button class="btn" onclick="refresh()">Refresh</button>
</div>
<div class="status" style="font-family:monospace;font-size:.75rem" id="raw"></div>
<div class="footer">Assembly 74 IFix · @FAKHERDDIN5 + Layla · made by @@prudenciodev</div>
<script>
const OPTIONS=[{key:"esp",label:"ESP"},{key:"aimbot",label:"Aimbot"},{key:"arm",label:"Arm"},{key:"team_esp",label:"Team ESP"},{key:"crosshair",label:"Crosshair"},{key:"jump_air",label:"Jump Air"},{key:"jump_control",label:"Jump Control"},{key:"jump_toggle",label:"Jump Toggle"},{key:"carm",label:"C-Arm"},{key:"ct1",label:"C-T1"}];
let state={};
async function load(){const r=await fetch("/api/config");state=await r.json();render();document.getElementById("raw").textContent=JSON.stringify(state,null,2)}
function render(){const g=document.getElementById("toggles");g.innerHTML="";OPTIONS.forEach(o=>{const on=!!state[o.key];const c=document.createElement("div");c.className="card"+(on?" on":"");c.innerHTML=`<div class="name">${o.label}</div><label class="toggle"><input type="checkbox" ${on?"checked":""} onchange="toggle('${o.key}',this.checked)"><span class="slider"></span></label>`;g.appendChild(c)})}
async function toggle(k,v){const r=await fetch("/api/toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:k,value:v})});state=await r.json();render();document.getElementById("raw").textContent=JSON.stringify(state,null,2)}
async function setAll(v){for(const o of OPTIONS)await fetch("/api/toggle",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:o.key,value:v})});await load()}
function refresh(){load()}
load();setInterval(load,4000);
</script></body></html>'''

class MenuHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # quiet

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: str):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in ("/", "/menu", "/index.html", "/dashboard"):
            self._html(DASHBOARD_HTML)
            return
        if path in ("/api/config", "/api/state", "/config.json"):
            self._json(200, load_state())
            return
        if path == "/api/toggle":
            qs = parse_qs(urlparse(self.path).query)
            key = (qs.get("key") or [None])[0]
            val = (qs.get("value") or ["true"])[0].lower() in ("1", "true", "yes", "on")
            state = load_state()
            if key and key in state:
                state[key] = val
                save_state(state)
            self._json(200, state)
            return
        if path.endswith("localconfig.json") or path == "/localconfig.json":
            cfg = (ROOT / "config" / "localConfig.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cfg)))
            self.end_headers()
            self.wfile.write(cfg)
            return
        self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/api/toggle":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8", errors="ignore") or "{}")
            except:
                data = {}
            key = data.get("key")
            val = bool(data.get("value", True))
            state = load_state()
            if key and key in state:
                state[key] = val
                save_state(state)
                print(f"[REMOTE] {key} = {val}", flush=True)
            self._json(200, state)
            return
        self.send_error(404)

def start_menu_server(host: str, port: int):
    save_state(load_state())
    httpd = ThreadingHTTPServer((host, port), MenuHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

def main():
    parser = argparse.ArgumentParser(description="Assembly Proxy + Remote Menu")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7777, help="mitmproxy port (assembly)")
    parser.add_argument("--menu-port", type=int, default=8080, help="Remote Menu web UI port")
    args = parser.parse_args()

    # start remote menu first
    start_menu_server(args.host, args.menu_port)

    exe = shutil.which("mitmdump")
    if not exe:
        folder = Path(sys.executable).parent
        for c in [folder / ("mitmdump.exe" if os.name == "nt" else "mitmdump"),
                  folder / "Scripts" / "mitmdump.exe", folder / "bin" / "mitmdump"]:
            if c.is_file():
                exe = str(c)
                break
    if not exe:
        sys.exit("mitmdump missing: py -m pip install -r requirements.txt")

    display_ip = args.host if args.host != "0.0.0.0" else "SEU-IP"
    print("=" * 58, flush=True)
    print("  🔥 Layla Assembly Proxy + Remote Menu", flush=True)
    print(f"  Assembly (mitm)  →  {args.host}:{args.port}", flush=True)
    print(f"  Remote Menu UI   →  http://{display_ip}:{args.menu_port}/", flush=True)
    print(f"  API config       →  http://{display_ip}:{args.menu_port}/api/config", flush=True)
    print("  Options: ESP · Aimbot · Arm · TeamESP · Crosshair · Jump...", flush=True)
    print("=" * 58, flush=True)

    cmd = [
        exe, "--mode", "regular",
        "--listen-host", args.host,
        "--listen-port", str(args.port),
        "--allow-hosts", ASSET_CDN_RE,
        "-s", str(ROOT / "assembly_proxy.py"),
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
