"""HTTP lane for chiptune generation, following the FlexInfer lane conventions.

POST /v1/music/generations mirrors the diffusers lanes' contract: JSON in,
``{"data": [{"b64_json": ..., "mime_type": "audio/wav", ...}]}`` out, so
pipelines can consume music exactly like images and video.

Run: uvicorn chiptune.server:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import base64
import random
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from chiptune.cli import EFFECT_PRESET_METHODS, GENRE_PRESET_METHODS

app = FastAPI(title="chiptune-api", version="0.1.0")


class MusicGenerationRequest(BaseModel):
    preset: str = "overworld"
    effects: str | None = None
    root: str | None = None
    bpm: int | None = Field(default=None, ge=40, le=300)
    bars: int = Field(default=8, ge=1, le=256)
    drums: bool = True
    bass: bool = True
    countermelody: bool = True
    seed: int | None = None
    response_format: str = "b64_json"


JUKEBOX_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Chiptune Jukebox</title>
<style>
:root { --bg:#0d0f0d; --panel:#151a15; --line:#243024; --ink:#d8e6d4; --dim:#8aa184; --hot:#7ee081; }
* { box-sizing:border-box; margin:0; }
body { background:var(--bg); color:var(--ink); font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
       min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
.deck { width:min(560px,100%); background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:28px; }
h1 { font-size:15px; letter-spacing:.3em; text-transform:uppercase; color:var(--hot); }
h1 small { display:block; color:var(--dim); letter-spacing:.05em; text-transform:none; margin-top:6px; font-weight:400; }
.presets { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:22px 0 16px; }
.presets button { background:var(--bg); color:var(--dim); border:1px solid var(--line); border-radius:8px;
  padding:10px 4px; font:inherit; font-size:12.5px; cursor:pointer; }
.presets button.on { color:var(--hot); border-color:var(--hot); }
.row { display:flex; gap:14px; align-items:center; margin:14px 0; font-size:12.5px; color:var(--dim); }
.row label { width:52px; }
.row input[type=range] { flex:1; accent-color:var(--hot); }
.row output { width:46px; text-align:right; color:var(--ink); }
.row select { background:var(--bg); color:var(--ink); border:1px solid var(--line); border-radius:6px; padding:6px 8px; font:inherit; }
.go { width:100%; margin-top:14px; background:var(--hot); color:#06230a; border:0; border-radius:8px;
  padding:13px; font:inherit; font-size:14px; font-weight:700; letter-spacing:.12em; cursor:pointer; }
.go:disabled { opacity:.45; cursor:default; }
audio { width:100%; margin-top:18px; display:none; }
audio.ready { display:block; }
.status { margin-top:12px; font-size:12px; color:var(--dim); min-height:16px; }
a.dl { color:var(--hot); font-size:12px; }
</style></head><body><div class="deck">
<h1>Chiptune Jukebox<small>flexinfer-chiptune, live from the cluster</small></h1>
<div class="presets" id="presets"></div>
<div class="row"><label>tempo</label><input type="range" id="bpm" min="60" max="200" value="120"
  oninput="bpmv.value=this.value"><output id="bpmv">120</output></div>
<div class="row"><label>bars</label><select id="bars"><option>4</option><option selected>8</option>
  <option>16</option><option>32</option></select>
  <label>fx</label><select id="fx"><option value="">clean</option><option>retro</option><option>space</option>
  <option>lofi</option><option>arcade</option><option>dreamy</option><option>dungeon</option><option>boss</option><option>toon</option></select></div>
<button class="go" id="go">▶ GENERATE</button>
<audio id="player" controls></audio>
<div class="status" id="status"></div>
</div><script>
let preset = "overworld";
fetch("/v1/music/presets").then(r => r.json()).then(d => {
  const box = document.getElementById("presets");
  d.presets.forEach(name => {
    const b = document.createElement("button");
    b.textContent = name; if (name === preset) b.classList.add("on");
    b.onclick = () => { preset = name;
      box.querySelectorAll("button").forEach(x => x.classList.remove("on")); b.classList.add("on"); };
    box.appendChild(b);
  });
});
document.getElementById("go").onclick = async () => {
  const go = document.getElementById("go"), st = document.getElementById("status");
  go.disabled = true; st.textContent = "composing\u2026";
  try {
    const body = { preset, bpm: +document.getElementById("bpm").value,
                   bars: +document.getElementById("bars").value };
    const fx = document.getElementById("fx").value; if (fx) body.effects = fx;
    const r = await fetch("/v1/music/generations", { method: "POST",
      headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (!r.ok) throw new Error((await r.json()).detail || r.status);
    const d = (await r.json()).data[0];
    const bytes = Uint8Array.from(atob(d.b64_json), c => c.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
    const player = document.getElementById("player");
    player.src = url; player.classList.add("ready"); player.play();
    st.innerHTML = `${d.duration}s of ${d.preset} at ${d.bpm} bpm (seed ${d.seed}) \u00b7 <a class="dl" href="${url}" download="${d.preset}-${d.seed}.wav">download .wav</a>`;
  } catch (e) { st.textContent = "failed: " + e.message; }
  go.disabled = false;
};
</script></body></html>"""


@app.get("/")
def jukebox() -> HTMLResponse:
    from fastapi.responses import HTMLResponse

    return HTMLResponse(JUKEBOX_HTML)


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {"ok": True}


@app.get("/v1/music/presets")
def presets() -> dict[str, object]:
    return {
        "presets": sorted(GENRE_PRESET_METHODS),
        "effects": sorted(EFFECT_PRESET_METHODS),
    }


@app.post("/v1/music/generations")
def generate(req: MusicGenerationRequest) -> dict[str, object]:
    if req.response_format != "b64_json":
        raise HTTPException(status_code=400, detail="Only response_format=b64_json is supported")
    if req.preset not in GENRE_PRESET_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset {req.preset!r}; see /v1/music/presets",
        )
    if req.effects and req.effects not in EFFECT_PRESET_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown effects {req.effects!r}; see /v1/music/presets",
        )

    from chiptune.output.audio import AudioExporter
    from chiptune.presets import EffectPresets, GenrePresets

    seed = req.seed if req.seed is not None else random.randrange(2**32)
    random.seed(seed)

    preset_factory = getattr(GenrePresets, GENRE_PRESET_METHODS[req.preset])
    composer = preset_factory(root=req.root) if req.root else preset_factory()
    if req.bpm:
        composer.bpm = req.bpm
    composer.add_melody(length_bars=req.bars)
    if req.countermelody:
        composer.add_countermelody()
    if req.bass:
        composer.add_bass()
    # Matches the CLI: these presets are drumless by design.
    if req.drums and req.preset not in ("sad", "victory"):
        composer.add_drums()
    track = composer.build()

    effects = None
    if req.effects:
        effects = getattr(EffectPresets, EFFECT_PRESET_METHODS[req.effects])()

    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "track.wav"
        AudioExporter().export_wav(track, str(wav_path), effects=effects)
        wav_bytes = wav_path.read_bytes()

    beats_per_bar = track.time_signature[0] if getattr(track, "time_signature", None) else 4
    duration = req.bars * beats_per_bar * 60.0 / composer.bpm
    return {
        "data": [
            {
                "b64_json": base64.b64encode(wav_bytes).decode(),
                "mime_type": "audio/wav",
                "preset": req.preset,
                "effects": req.effects,
                "bpm": composer.bpm,
                "bars": req.bars,
                "seed": seed,
                "duration": round(duration, 2),
            }
        ]
    }
