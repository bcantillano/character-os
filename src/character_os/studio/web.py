"""Optional stdlib web UI for Character Studio."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from character_os.studio.service import StudioService

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Character Studio</title>
  <style>
    :root { color-scheme: light; --bg:#f6f1e8; --ink:#1c1917; --accent:#0f766e; --card:#fffdf8; --line:#d6d3d1; }
    body { margin:0; font-family: "Iowan Old Style", "Palatino Linotype", Palatino, serif; background: radial-gradient(circle at top left, #efe6d6, var(--bg)); color: var(--ink); }
    main { max-width: 960px; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
    h1 { font-size: 2.4rem; margin: 0 0 .25rem; letter-spacing: -.02em; }
    .sub { opacity: .75; margin-bottom: 1.5rem; }
    section { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 1rem 1.1rem; margin-bottom: 1rem; box-shadow: 0 10px 30px rgba(28,25,23,.04); }
    h2 { margin: 0 0 .75rem; font-size: 1.15rem; }
    label { display:block; font-size: .85rem; margin: .5rem 0 .2rem; opacity: .8; }
    input, select, textarea, button { font: inherit; }
    input, select, textarea { width: 100%; box-sizing: border-box; padding: .55rem .7rem; border: 1px solid var(--line); border-radius: 10px; background: #fff; }
    textarea { min-height: 4.5rem; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap: .75rem; }
    button { margin-top: .75rem; background: var(--accent); color: white; border: 0; border-radius: 999px; padding: .55rem 1rem; cursor: pointer; }
    button.secondary { background: #44403c; }
    pre { white-space: pre-wrap; background: #1c1917; color: #f5f5f4; border-radius: 12px; padding: .9rem; overflow:auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .82rem; }
    .stages { display:grid; gap: .4rem; }
    .stage { border-left: 3px solid var(--accent); padding: .35rem .6rem; background: #fafaf9; border-radius: 0 8px 8px 0; }
    @media (max-width: 700px) { .row { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>Character Studio</h1>
  <p class="sub">Phase 2 inspect / validate / stage-debug UI (stdlib). Chat still runs through the event-bus CLI.</p>

  <section>
    <h2>Packs</h2>
    <div class="row">
      <div>
        <label>Characters</label>
        <select id="characters"></select>
      </div>
      <div>
        <label>Worlds</label>
        <select id="worlds"></select>
      </div>
    </div>
    <button onclick="showCharacter()">Show character</button>
    <button class="secondary" onclick="validateCharacter()">Validate character</button>
    <button class="secondary" onclick="showMemories()">Memories</button>
    <button class="secondary" onclick="showWorld()">Show world</button>
    <button class="secondary" onclick="validateWorld()">Validate world</button>
  </section>

  <section>
    <h2>Stage debug</h2>
    <label>Message</label>
    <textarea id="message">Ahoy there.</textarea>
    <label>Provider</label>
    <select id="provider"><option value="stub">stub</option><option value="openai">openai</option></select>
    <button onclick="runTrace()">Run stage trace</button>
  </section>

  <section>
    <h2>Output</h2>
    <div id="stages" class="stages"></div>
    <pre id="out">(ready)</pre>
  </section>
</main>
<script>
async function api(path, opts) {
  const res = await fetch(path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) throw Object.assign(new Error(data.error || res.statusText), { data });
  return data;
}
function show(data) {
  document.getElementById('out').textContent = JSON.stringify(data, null, 2);
}
function showStages(stages) {
  const el = document.getElementById('stages');
  el.innerHTML = (stages || []).map(s => `<div class="stage"><strong>${s.stage}</strong> ${s.detail || ''}</div>`).join('');
}
async function refresh() {
  const chars = await api('/api/characters');
  const worlds = await api('/api/worlds');
  const csel = document.getElementById('characters');
  const wsel = document.getElementById('worlds');
  csel.innerHTML = chars.map(c => `<option value="${c.id}">${c.name} (${c.id})</option>`).join('');
  wsel.innerHTML = worlds.map(w => `<option value="${w.id}">${w.name} (${w.id})</option>`).join('');
}
async function showCharacter() {
  showStages([]);
  show(await api('/api/character/' + document.getElementById('characters').value));
}
async function validateCharacter() {
  showStages([]);
  show(await api('/api/validate/character/' + document.getElementById('characters').value));
}
async function showMemories() {
  showStages([]);
  show(await api('/api/memories/' + document.getElementById('characters').value));
}
async function showWorld() {
  showStages([]);
  show(await api('/api/world/' + document.getElementById('worlds').value));
}
async function validateWorld() {
  showStages([]);
  show(await api('/api/validate/world/' + document.getElementById('worlds').value));
}
async function runTrace() {
  const body = {
    character_id: document.getElementById('characters').value,
    message: document.getElementById('message').value,
    provider: document.getElementById('provider').value,
  };
  const data = await api('/api/debug/trace', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  showStages(data.stages);
  show(data);
}
refresh().catch(err => show({ error: String(err) }));
</script>
</body>
</html>
"""


def make_handler(studio: StudioService):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # quieter default
            pass

        def _send(self, code: int, payload: object, content_type: str = "application/json") -> None:
            raw = payload if isinstance(payload, (bytes, bytearray)) else (
                payload.encode("utf-8") if content_type.startswith("text/") else json.dumps(payload, default=str).encode("utf-8")
            )
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _error(self, code: int, message: str) -> None:
            self._send(code, {"error": message})

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            try:
                if path in {"/", "/index.html"}:
                    self._send(200, _HTML, "text/html; charset=utf-8")
                    return
                if path == "/api/characters":
                    self._send(200, [c.__dict__ for c in studio.list_characters()])
                    return
                if path == "/api/worlds":
                    self._send(200, [w.__dict__ for w in studio.list_worlds()])
                    return
                if path.startswith("/api/character/"):
                    cid = path.rsplit("/", 1)[-1]
                    self._send(200, studio.show_character(cid).__dict__)
                    return
                if path.startswith("/api/world/"):
                    wid = path.rsplit("/", 1)[-1]
                    self._send(200, studio.show_world(wid))
                    return
                if path.startswith("/api/validate/character/"):
                    cid = path.rsplit("/", 1)[-1]
                    self._send(200, studio.validate_character(cid).as_dict())
                    return
                if path.startswith("/api/validate/world/"):
                    wid = path.rsplit("/", 1)[-1]
                    self._send(200, studio.validate_world(wid).as_dict())
                    return
                if path.startswith("/api/memories/"):
                    cid = path.rsplit("/", 1)[-1]
                    qs = parse_qs(parsed.query)
                    include_archived = qs.get("archived", ["1"])[0] != "0"
                    self._send(
                        200,
                        studio.inspect_runtime(cid, include_archived=include_archived).__dict__,
                    )
                    return
                self._error(404, "not found")
            except Exception as exc:  # noqa: BLE001 — surface to UI
                self._error(400, str(exc))

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._error(400, "invalid JSON")
                return
            try:
                if parsed.path == "/api/debug/trace":
                    result = studio.stage_trace(
                        str(payload.get("character_id") or ""),
                        str(payload.get("message") or ""),
                        provider_name=str(payload.get("provider") or "stub"),
                        persist=bool(payload.get("persist") or False),
                    )
                    self._send(200, result.as_dict())
                    return
                self._error(404, "not found")
            except Exception as exc:  # noqa: BLE001
                self._error(400, str(exc))

    return Handler


def serve_studio(
    studio: StudioService,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    handler = make_handler(studio)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Character Studio web UI: http://{host}:{port}")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
