"""Paths, immutable input checks, and independent numerical readouts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "study"
RESULTS = STUDY / "results"
CONFIG = json.loads((STUDY / "config.json").read_text())
READOUTS = CONFIG["readouts"]
NAMES = json.loads((ROOT / "03-Data/stage1/network-structure.json").read_text())["model_types"]
SELECTION = json.loads((ROOT / "03-Data/stage1/model-selection.json").read_text())
MODELS = [item["model"] for item in SELECTION["models"]]
CLUSTERS = {item["model"]: item["T4c_cluster"] for item in SELECTION["models"]}
STIMULI = {item["key"]: item for item in json.loads((ROOT / "03-Data/stage1/stimulus-manifest.json").read_text())}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False, default=lambda x: x.item()) + "\n")
    temporary.replace(path)


def load_npz(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def stimulus(key: str) -> dict[str, np.ndarray]:
    return load_npz(ROOT / STIMULI[key]["path"])


def window(length: int, speed: float) -> np.ndarray:
    times = (np.arange(length, dtype=np.float64) + 200) * 0.005 - 1
    end = ((10 * 2.25 / 5.8 + 2.25 / 5.8) - (-10 * 2.25 / 5.8)) / speed
    return (times >= 0) & (times <= end)


def causal_frames(key: str) -> int:
    mask = window(STIMULI[key]["frames"] - 200, STIMULI[key]["native_speed"])
    return int(np.flatnonzero(mask)[-1]) + 1


def independent_metrics(trace: np.ndarray, stim: dict) -> dict[str, np.ndarray]:
    values = trace[:, window(trace.shape[1], float(stim["speed"]))].astype(np.float64)
    peaks = np.maximum(values, 0).max(axis=1)
    sums, vectors = [], []
    for polarity in (0, 1):
        select = stim["intensity"] == polarity
        response = peaks[select]
        angles = np.deg2rad(stim["angle"][select].astype(np.float64))
        sums.append(response.sum(axis=0))
        vectors.append(np.abs((response * np.exp(1j * angles)[:, None]).sum(axis=0)))
    denominator = np.maximum(*sums)
    both = np.array(vectors) / (denominator + 1e-15)
    chosen = np.array([both[1 if r < 4 else 0, r] for r in range(8)])
    return {
        "dsi": chosen, "all_dsi": both, "denominator": denominator,
        "peaks": peaks, "raw_mean": values.mean(axis=1),
        "raw_integral": values.sum(axis=1) * 0.005,
        "max_abs_voltage": np.array(np.max(np.abs(values))),
    }


def legacy_panel(model: str, key: str) -> Path | None:
    for split in ("development", "final"):
        candidate = ROOT / "04-Results/stage1" / split / model / key
        if (candidate / "baseline.npz").exists():
            return candidate
    return None


def legacy_check(path: Path) -> dict:
    metadata = json.loads(path.with_suffix(".json").read_text())
    if sha256(path) != metadata["sha256"]:
        raise RuntimeError(f"Original result checksum mismatch: {path}")
    return metadata


def original_freeze_check() -> dict:
    freeze = json.loads((ROOT / "06-Study-History/stage1/freeze-manifest.json").read_text())
    failures = [rel for rel, digest in freeze["files"].items() if sha256(ROOT / rel) != digest]
    if failures:
        raise RuntimeError(f"Original frozen files changed: {failures}")
    return {"status": "pass", "files": len(freeze["files"])}


def freeze_check() -> str:
    path = STUDY / "freeze.json"
    record = json.loads(path.read_text())
    for rel, digest in record["files"].items():
        if sha256(ROOT / rel) != digest:
            raise RuntimeError(f"Revision frozen source changed: {rel}")
    return sha256(path)


def health() -> None:
    available = int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))) / 1024**2
    if available < CONFIG["minimum_ram_gib"]:
        raise RuntimeError(f"Available RAM below guard: {available:.2f} GiB")
    free = shutil.disk_usage(ROOT).free / 1024**3
    if free < CONFIG["minimum_disk_gib"]:
        raise RuntimeError(f"Free disk below guard: {free:.2f} GiB")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
