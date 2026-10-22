"""Assembly proxy + Remote Menu Control Panel for Free Fire iOS 1.132.10

- Serves custom assembly-csharp-patch (71 official + 3 BASE IFix)
- Serves live web dashboard at http://<proxy-ip>:7777/
- Toggles: ESP, Aimbot, Arm, TeamESP, Crosshair, JumpAir, etc.
- /api/config  -> JSON state for future assembly poll
- /api/toggle  -> change flags live
- /api/state   -> full state
All original CDN interception kept. No red-list activity.
"""
from __future__ import annotations

import gzip
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import unquote, parse_qs

from mitmproxy import http

ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / "payload"
STATE_FILE = ROOT / "remote_state.json"
ENTRY = b"codepatch/assembly-csharp-patch"
LINE = re.compile(rb"(?m)^codepatch/assembly-csharp-patch,[^\r\n]*", re.IGNORECASE)
ASSET_ENDPOINT = re.compile(
    r"(?:^|/)codepatch/assembly-csharp-patch(?:[._-](?:[a-z0-9._-]|~[0-9a-f]{2}){1,95})?/?$",
    re.IGNORECASE,
)
LOGGER = logging.getLogger("assembly_proxy")

DEFAULT_STATE = {
    "esp": True,
    "aimbot": True,
    "arm": False,
    "team_esp": True,
    "crosshair": True,
    "jump_air": False,
    "jump_control": False,
    "jump_toggle": False,
    "carm": False,
    "ct1": False,
    "author": "@FAKHERDDIN5 + Layla remote",
    "last_update": None,
}


def load_state() -> dict:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_STATE)


def save_state(state: dict) -> None:
    state["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    # also sync a simple localConfig for compatibility
    cfg = {
        "testCodePatch": True,
        "esp": bool(state.get("esp")),
        "aim": bool(state.get("aimbot")),
        "arm": bool(state.get("arm")),
        "team_esp": bool(state.get("team_esp")),
        "crosshair": bool(state.get("crosshair")),
        "jump_air": bool(state.get("jump_air")),
        "m_esp": bool(state.get("esp")),
        "m_aim": bool(state.get("aimbot")),
        "m_arm": bool(state.get("arm")),
        "m_t1": bool(state.get("team_esp")),
        "m_cc": bool(state.get("crosshair")),
        "m_jair": bool(state.get("jump_air")),
        "m_jc": bool(state.get("jump_control")),
        "m_jt": bool(state.get("jump_toggle")),
        "m_carm": bool(state.get("carm")),
        "m_ct1": bool(state.get("ct1")),
    }
    (ROOT / "config" / "localConfig.json").write_text(json.dumps(cfg), encoding="utf-8")


def route_path(path: str) -> str:
    return unquote(path.split("?", 1)[0]).rstrip("/").lower()


def is_fileinfo(path: str) -> bool:
    value = route_path(path)
    return "/abhotupdates/" in value and value.endswith("/fileinfo")


def is_assembly(path: str) -> bool:
    return bool(ASSET_ENDPOINT.search(route_path(path)))


def replace_row(content: bytes, new_line: bytes) -> tuple[bytes, int]:
    if len(LINE.findall(content)) != 1:
        return content, 0
    return LINE.sub(lambda _: new_line, content, count=1), 1


def parse_range(header: str, size: int) -> tuple[int, int] | None:
    if not header.lower().startswith("bytes=") or "," in header:
        return None
    try:
        value = header[6:].strip()
        if "-" not in value:
            return None
        left, right = value.split("-", 1)
        if left and right:
            start, end = int(left), int(right)
        elif left:
            start, end = int(left), size - 1
        elif right:
            n = int(right)
            if n < 1:
                return None
            start, end = max(0, size - n), size - 1
        else:
            return None
        if start < 0 or end < start or start >= size:
            return None
        return start, min(end, size - 1)
    except ValueError:
        return None


# ─────────────────────────── WEB UI ───────────────────────────

DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Layla Remote Menu · Free Fire Assembly</title>
<style>
:root{--bg:#0b0f14;--card:#141a22;--accent:#00e5a0;--accent2:#00b4ff;--text:#e6edf3;--muted:#8b949e;--danger:#ff4d6d;--ok:#00e5a0}
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
.btn{background:var(--card);border:1px solid #2d3748;color:var(--text);padding:10px 18px;border-radius:10px;cursor:pointer;font-size:.85rem;font-weight:600;transition:.15s}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn.danger:hover{border-color:var(--danger);color:var(--danger)}
.btn.ok:hover{border-color:var(--ok);color:var(--ok)}
.footer{text-align:center;color:var(--muted);font-size:.75rem;margin-top:30px}
.live{display:inline-block;width:8px;height:8px;background:var(--ok);border-radius:50%;margin-right:6px;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style>
</head>
<body>
<div class="header">
  <h1>🔥 Layla Remote Menu</h1>
  <p>Free Fire Assembly Proxy · iOS 1.132.10 · Control remoto</p>
</div>

<div class="status" id="status">
  <span class="live"></span> <b>ONLINE</b> · Estado sincronizado com o assembly
</div>

<div class="grid" id="toggles"></div>

<div class="btn-row">
  <button class="btn ok" onclick="setAll(true)">Ativar Tudo</button>
  <button class="btn danger" onclick="setAll(false)">Desativar Tudo</button>
  <button class="btn" onclick="refresh()">Refresh</button>
</div>

<div class="status" style="font-family:monospace;font-size:.75rem" id="raw"></div>

<div class="footer">
  Assembly: 74 IFix (71 oficial + 3 BASE) · @FAKHERDDIN5 + Layla remote · made by @@prudenciodev
</div>

<script>
const OPTIONS = [
  {key:"esp",         label:"ESP"},
  {key:"aimbot",      label:"Aimbot"},
  {key:"arm",         label:"Arm"},
  {key:"team_esp",    label:"Team ESP"},
  {key:"crosshair",   label:"Crosshair"},
  {key:"jump_air",    label:"Jump Air"},
  {key:"jump_control",label:"Jump Control"},
  {key:"jump_toggle", label:"Jump Toggle"},
  {key:"carm",        label:"C-Arm"},
  {key:"ct1",         label:"C-T1"},
];

let state = {};

async function load() {
  const r = await fetch("/api/config");
  state = await r.json();
  render();
  document.getElementById("raw").textContent = JSON.stringify(state, null, 2);
}

function render() {
  const grid = document.getElementById("toggles");
  grid.innerHTML = "";
  OPTIONS.forEach(o => {
    const on = !!state[o.key];
    const card = document.createElement("div");
    card.className = "card" + (on ? " on" : "");
    card.innerHTML = `
      <div class="name">${o.label}</div>
      <label class="toggle">
        <input type="checkbox" ${on?"checked":""} onchange="toggle('${o.key}', this.checked)">
        <span class="slider"></span>
      </label>`;
    grid.appendChild(card);
  });
}

async function toggle(key, val) {
  const r = await fetch("/api/toggle", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({key, value: val})
  });
  state = await r.json();
  render();
  document.getElementById("raw").textContent = JSON.stringify(state, null, 2);
}

async function setAll(val) {
  for (const o of OPTIONS) {
    await fetch("/api/toggle", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify({key: o.key, value: val})
    });
  }
  await load();
}

function refresh(){ load(); }
load();
setInterval(load, 4000);
</script>
</body>
</html>
'''


class AssemblyOnlyProxy:
    def __init__(self) -> None:
        self.asset = (PAYLOAD / "assembly-csharp-patch.gz").read_bytes()
        self.uncompressed = (PAYLOAD / "assembly-csharp-patch.bytes").read_bytes()
        self.line = (PAYLOAD / "fileinfo-line.txt").read_bytes().strip()
        if gzip.decompress(self.asset) != self.uncompressed:
            raise ValueError("Payload GZIP fails integrity check")
        fields = self.line.split(b",")
        if len(fields) != 8 or fields[0] != ENTRY or fields[3] != b"3":
            raise ValueError("fileinfo line does not match codepatch syntax")
        import base64
        import hashlib
        if fields[1] != base64.b64encode(hashlib.sha1(self.uncompressed).digest()) or \
           fields[4] != base64.b64encode(hashlib.sha1(self.asset).digest()) or \
           int(fields[2]) != len(self.uncompressed) or int(fields[5]) != len(self.asset):
            raise ValueError("Payload fileinfo SHA-1 or byte length mismatch; rebuild first")
        self.state = load_state()
        save_state(self.state)
        LOGGER.warning("Assembly-only proxy + Remote Menu loaded: UnityFS %d bytes, GZIP %d bytes",
                       len(self.uncompressed), len(self.asset))
        LOGGER.warning("Dashboard: http://0.0.0.0:7777/  |  API: /api/config")

    def _serve_local(self, flow: http.HTTPFlow, path: str) -> bool:
        """Handle requests that hit the proxy itself (dashboard / api)."""
        host = (flow.request.pretty_host or "").lower()
        # treat any request that is not going to freefire CDN as local panel traffic
        if "freefiremobile.com" in host or "garena" in host:
            return False

        method = flow.request.method.upper()
        p = route_path(path)

        # Dashboard
        if p in ("", "/", "/menu", "/index.html", "/dashboard"):
            flow.response = http.Response.make(
                200, DASHBOARD_HTML.encode("utf-8"),
                {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}
            )
            return True

        # API: get config
        if p in ("/api/config", "/api/state", "/config.json"):
            self.state = load_state()
            body = json.dumps(self.state, ensure_ascii=False).encode("utf-8")
            flow.response = http.Response.make(
                200, body,
                {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"}
            )
            return True

        # API: toggle
        if p == "/api/toggle" and method in ("POST", "PUT", "GET"):
            try:
                if method == "GET":
                    qs = parse_qs(flow.request.query or "")
                    key = (qs.get("key") or [None])[0]
                    val = (qs.get("value") or ["true"])[0].lower() in ("1", "true", "yes", "on")
                else:
                    raw = flow.request.content or b"{}"
                    data = json.loads(raw.decode("utf-8", errors="ignore") or "{}")
                    key = data.get("key")
                    val = bool(data.get("value", True))
                if key and key in self.state:
                    self.state[key] = val
                    save_state(self.state)
                    LOGGER.warning("REMOTE TOGGLE: %s = %s", key, val)
            except Exception as exc:
                LOGGER.warning("toggle error: %s", exc)
            body = json.dumps(self.state, ensure_ascii=False).encode("utf-8")
            flow.response = http.Response.make(
                200, body,
                {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"}
            )
            return True

        # CORS preflight
        if method == "OPTIONS":
            flow.response = http.Response.make(204, b"", {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            })
            return True

        # localConfig.json if someone requests it
        if p.endswith("localconfig.json") or p == "/localconfig.json":
            cfg = (ROOT / "config" / "localConfig.json").read_bytes()
            flow.response = http.Response.make(200, cfg, {"Content-Type": "application/json", "Cache-Control": "no-store"})
            return True

        return False

    def request(self, flow: http.HTTPFlow) -> None:
        path = flow.request.path

        # 1) Local dashboard / API first
        if self._serve_local(flow, path):
            return

        normalized = route_path(path)
        if "/codepatch/" in normalized:
            LOGGER.warning("codepatch request: matched=%s path=%s", is_assembly(path), normalized)

        if is_fileinfo(path):
            for h in ("If-None-Match", "If-Modified-Since", "Range", "If-Range"):
                flow.request.headers.pop(h, None)
            flow.request.headers["cache-control"] = "no-cache"
            return

        if not is_assembly(path):
            return

        method = flow.request.method.upper()
        if method not in ("GET", "HEAD"):
            return

        headers = {
            "Content-Type": "application/octet-stream",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        }
        size = len(self.asset)
        requested_range = flow.request.headers.get("Range")
        if requested_range:
            match = parse_range(requested_range, size)
            if match is None:
                headers["Content-Range"] = f"bytes */{size}"
                flow.response = http.Response.make(416, b"", headers)
                return
            first, last = match
            chunk = self.asset[first:last + 1]
            headers["Content-Range"] = f"bytes {first}-{last}/{size}"
            flow.response = http.Response.make(206, b"" if method == "HEAD" else chunk, headers)
            flow.response.headers["Content-Length"] = str(len(chunk))
            LOGGER.warning("SERVED ASSEMBLY locally: gzip range %d-%d (HTTP 206)", first, last)
        else:
            flow.response = http.Response.make(200, b"" if method == "HEAD" else self.asset, headers)
            flow.response.headers["Content-Length"] = str(size)
            LOGGER.warning("SERVED ASSEMBLY locally: gzip %d bytes (HTTP 200)", size)

    def response(self, flow: http.HTTPFlow) -> None:
        if flow.response is None or not is_fileinfo(flow.request.path):
            return
        if flow.response.status_code != 200:
            LOGGER.warning("fileinfo passed through: upstream returned HTTP %d", flow.response.status_code)
            return
        try:
            body = flow.response.content
        except ValueError as exc:
            LOGGER.warning("fileinfo decoding failed, not modifying: %s", exc)
            return
        if body is None:
            return
        updated, n = replace_row(body, self.line)
        if n != 1:
            LOGGER.warning("fileinfo did not have exactly one codepatch line; left untouched")
            return
        flow.response.content = updated
        for h in ("ETag", "Last-Modified", "Content-MD5", "Content-Range"):
            flow.response.headers.pop(h, None)
        flow.response.headers["cache-control"] = "no-store, no-cache, must-revalidate, max-age=0"
        LOGGER.info("fileinfo codepatch row replaced (other entries kept)")


addons = [AssemblyOnlyProxy()]
