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
