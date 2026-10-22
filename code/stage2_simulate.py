"""Stage 2, Part 1: pair silencing in the FlyVis models (STAGE2-PROTOCOL.md, Sections 1.1-1.2).

  python -B stage2_simulate.py replay          development models: AI-06's four stage-1 pairs, compared with its records
  python -B stage2_simulate.py development     development models: Serbe's six pairs, both strengths, both stimuli
  python -B stage2_simulate.py confirmation    the 46 confirmation models (needs a passing replay record)

Launch on the GPU only through the portfolio lock (AI-09's study/code/gpu_lock.py). AI-06 is imported read-only
(always run with python -B); the FlyVis and matplotlib caches are pointed at AI-11 before FlyVis is imported.
Writes raw records only (traces and per-trajectory metrics) under results/stage2/pairs/; no ratio, category or other
per-type summary is computed here. Existing valid records are kept, so a stopped run resumes.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np

CODE = Path(__file__).resolve().parent
STUDY = CODE.parent
AI06 = (STUDY / "reference/flyvis-first-order").resolve()  # release: the reference study's files
OUT = STUDY / "results/stage2"
# AI-06's core.py does `from common import *`, meaning its own stage1 common.py (which points FlyVis at AI-06's
# model folder). AI-11's code folder also has a common.py, so AI-06's folders go first on the import path, and this
# script never imports AI-11's common.
sys.path.insert(0, str(AI06 / "study/code"))
sys.path.insert(0, str(AI06 / "02-Code/stage1"))
import revision_common as ai06  # noqa: E402  (AI-06 paths, stimuli, model list, metrics; read only)
from core import Core, metrics, TARGETS  # noqa: E402  (AI-06 batched simulator; its stage1 common sets env vars)
assert Path(sys.modules["common"].__file__).resolve() == (AI06 / "02-Code/stage1/common.py").resolve()

os.environ["MPLCONFIGDIR"] = str(STUDY / ".cache/matplotlib")
os.environ["XDG_CACHE_HOME"] = str(STUDY / ".cache")

PAIRS = [("Tm1", "Tm2"), ("Tm1", "Tm4"), ("Tm1", "Tm9"), ("Tm2", "Tm4"), ("Tm2", "Tm9"), ("Tm4", "Tm9")]
STRENGTHS = [0.5, 1.0]
STIMULI = ["final_slow", "dev_fast"]
DEVELOPMENT = ai06.CONFIG["development_models"]
CONFIRMATION = [m for m in ai06.MODELS if m not in DEVELOPMENT]
STAGE1_PAIRS = {("Tm1", "Tm2"): 4, ("Tm1", "Tm9"): 5, ("Tm2", "Tm4"): 6, ("Tm4", "Tm9"): 7}   # core.PAIRS indices
STAGE1_STIMULUS = {"000": "dev_fast", "004": "dev_fast", "001": "final_slow", "005": "final_slow"}
TOLERANCE = 1e-4
BATCH = ai06.CONFIG["batch_size"]
assert TARGETS == ai06.READOUTS


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)) + "\n")
    tmp.replace(path)


def signature() -> str:
    files = [Path(__file__), AI06 / "02-Code/stage1/core.py", AI06 / "02-Code/stage1/common.py",
             AI06 / "study/code/revision_common.py", AI06 / "study/config.json"]
    return hashlib.sha256("\n".join(sha256(p) for p in files).encode()).hexdigest()


def release_original_signature() -> str:
    """release: the signature of the original files, from the digests that release-changes.json records for the
    files adapted for this release, so the recorded replay check still gates the confirmation run."""
    sys.path.append(str(STUDY / "tools"))
    import release_paths as rp
    files = [Path(__file__), AI06 / "02-Code/stage1/core.py", AI06 / "02-Code/stage1/common.py",
             AI06 / "study/code/revision_common.py", AI06 / "study/config.json"]
    changed = rp.changes().get("changed_files", {})
    digests = [changed.get(rp.release_relative(p), {}).get("original_sha256") or sha256(p) for p in files]
    return hashlib.sha256("\n".join(digests).encode()).hexdigest()


def code_of(names: tuple, strength: float) -> str:
    return f"s{round(100 * strength):03d}-{'+'.join(names)}"


def valid(path: Path, sig: str) -> bool:
    if not path.exists() or not path.with_suffix(".json").exists():
        return False
    meta = json.loads(path.with_suffix(".json").read_text())
    return meta.get("sha256") == sha256(path) and meta.get("simulation_signature") == sig


def write_record(path: Path, arrays: dict, meta: dict, sig: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".npz.tmp")
    with tmp.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    tmp.replace(path)
    save_json(path.with_suffix(".json"), {**meta, "sha256": sha256(path), "simulation_signature": sig, "utc": utc_now()})


def checked_arrays(trace: np.ndarray, stim: dict) -> dict:
    """The native metrics and AI-06's independent readout must agree, as in AI-06's runner."""
    import torch
    native = metrics(torch.as_tensor(trace), stim["angle"], stim["intensity"], float(stim["speed"]), time_start=0)
    arrays = {k: v.detach().cpu().numpy() for k, v in native.items() if k != "window"}
    independent = ai06.independent_metrics(trace, stim)
    for key in ("dsi", "denominator", "peaks", "raw_mean", "raw_integral"):
        if not np.allclose(arrays[key], independent[key], atol=2e-6, rtol=2e-5):
            raise RuntimeError(f"independent readout disagreement: {key}")
    arrays.update(trace=trace, max_abs_voltage=independent["max_abs_voltage"])
    return arrays


def normalised_gap(peaks: np.ndarray, reference: np.ndarray, scale: float) -> float:
    return float(np.max(np.abs(peaks.astype(np.float64) - reference.astype(np.float64))) / max(scale, 1e-8))


def run_model(model: str, device: str, sig: str, pairs: list, strengths: list, stimuli: list, folder: str) -> dict:
    import torch
    started = time.perf_counter()
    model_folder = AI06 / f"03-Data/flyvis-root/results/flow/0000/{model}"
    expected = next(item["checkpoint_sha256"] for item in ai06.SELECTION["models"] if item["model"] == model)
    if sha256(model_folder / "best_chkpt") != expected:
        raise RuntimeError(f"checkpoint changed: {model}")
    core = Core(model, device)
    gray = core.gray()
    report = {"model": model, "baseline_gap": {}, "conditions": 0}
    for key in stimuli:
        stim = ai06.stimulus(key)
        if sha256(AI06 / ai06.STIMULI[key]["path"]) != ai06.STIMULI[key]["sha256"]:
            raise RuntimeError(f"stimulus changed: {key}")
        frames = stim["stimulus"]
        if frames.ndim == 4:
            frames = frames[:, :, 0]
        n_frames = ai06.causal_frames(key)
        causal = frames[:, 200:200 + n_frames]
        _, state, _ = core.run(frames[:, :200], state=gray.expand(24, -1).clone())
        state = state.detach()
        # Baseline again, against AI-06's saved record (ratios later use AI-06's record).
        trace, _, _ = core.run(causal, state=state.clone(), start=0)
        mine = checked_arrays(trace.cpu().numpy(), stim)
        with np.load(AI06 / "study/results/runs" / model / key / "baseline.npz", allow_pickle=False) as saved:
            saved_peaks = saved["peaks"]
        gap = normalised_gap(mine["peaks"], saved_peaks, float(np.max(saved_peaks)))
        report["baseline_gap"][key] = gap
        if gap > TOLERANCE:
            raise RuntimeError(f"baseline differs from AI-06's record: {model} {key} gap {gap:.2e}")
        dest = OUT / folder / model / key
        pending = [(names, s) for s in strengths for names in pairs
                   if not valid(dest / (code_of(names, s) + ".npz"), sig)]
        queue = [(c, t) for c in range(len(pending)) for t in range(24)]
        partial = {}
        for begin in range(0, len(queue), BATCH):
            jobs = queue[begin:begin + BATCH]
            idx = [t for _, t in jobs]
            atten = torch.zeros((len(jobs), core.c), device=device)
            for row, (c, _) in enumerate(jobs):
                names, s = pending[c]
                for name in names:
                    atten[row, ai06.NAMES.index(name)] = s
            t0 = time.perf_counter()
            out, _, _ = core.run(causal[idx], atten, state=state[idx].clone(), start=0)
            if device == "cuda":
                torch.cuda.synchronize()
            wall = time.perf_counter() - t0
            bank = out.cpu().numpy()
            del out
            for row, (c, t) in enumerate(jobs):
                rec = partial.setdefault(c, [np.empty((24, n_frames, 8), np.float32), set(), 0.0])
                rec[0][t] = bank[row]
                rec[1].add(t)
                rec[2] += wall / len(jobs)
                if len(rec[1]) == 24:
                    names, s = pending[c]
                    arrays, _, seconds = partial.pop(c)
                    write_record(dest / (code_of(names, s) + ".npz"), checked_arrays(arrays, stim),
                                 {"model": model, "stimulus": key, "strength": s, "names": list(names), "kind": "pair",
                                  "wall_seconds": seconds}, sig)
                    report["conditions"] += 1
        if partial:
            raise RuntimeError("incomplete trajectory assembly")
        del state
    report["seconds"] = time.perf_counter() - started
    del core, gray
    if device == "cuda":
        torch.cuda.empty_cache()
    return report


def environment(device: str) -> dict:
    import torch
    import flyvis
    info = {"python": platform.python_version(), "torch": torch.__version__, "flyvis": getattr(flyvis, "__version__", "?"),
            "numpy": np.__version__, "platform": platform.platform(), "device": device}
    if device == "cuda":
        info.update(gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda,
                    gpu_memory_mib=int(torch.cuda.get_device_properties(0).total_memory / 2**20))
    return info


def configure(device: str):
    import torch
    torch.set_num_threads(ai06.CONFIG["cpu_threads"])
    torch.set_num_interop_threads(ai06.CONFIG["cpu_threads"])
    if device == "cuda":
        if not os.environ.get("AI09_GPU_LOCK_FD"):
            raise RuntimeError("launch through the portfolio GPU lock (AI-09 study/code/gpu_lock.py)")
        os.fstat(int(os.environ["AI09_GPU_LOCK_FD"]))
        torch.cuda.set_per_process_memory_fraction(ai06.CONFIG["max_gpu_memory_fraction"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False


def replay(device: str, sig: str) -> None:
    """AI-06's four stage-1 Serbe pairs in the development models, compared with its saved records."""
    results, worst = [], 0.0
    for model, key in STAGE1_STIMULUS.items():
        report = run_model(model, device, sig, list(STAGE1_PAIRS), STRENGTHS, [key], "replay")
        with np.load(AI06 / "study/results/runs" / model / key / "baseline.npz", allow_pickle=False) as saved:
            scale = float(np.max(saved["peaks"]))
        n_frames = ai06.causal_frames(key)
        stim = ai06.stimulus(key)
        stage1 = ai06.legacy_panel(model, key)
        for names, index in STAGE1_PAIRS.items():
            for s in STRENGTHS:
                with np.load(stage1 / f"s{round(100 * s):03d}-pair{index}.npz", allow_pickle=False) as old:
                    old_peaks = ai06.independent_metrics(old["trace"][:, :n_frames], stim)["peaks"]
                with np.load(OUT / "replay" / model / key / (code_of(names, s) + ".npz"), allow_pickle=False) as new:
                    new_peaks = new["peaks"]
                gap = normalised_gap(new_peaks, old_peaks, scale)
                worst = max(worst, gap)
                results.append({"model": model, "stimulus": key, "pair": "+".join(names), "strength": s,
                                "stage1_record": str((stage1 / f"s{round(100 * s):03d}-pair{index}.npz").relative_to(AI06)),
                                "normalised_peak_gap": gap, "pass": gap <= TOLERANCE})
        results.append({"model": model, "baseline_gap": report["baseline_gap"], "seconds": report["seconds"]})
    record = {"utc": utc_now(), "simulation_signature": sig, "environment": environment(device), "tolerance": TOLERANCE,
              "cases": results, "worst_normalised_gap": worst,
              "pass": all(r.get("pass", True) for r in results)}
    save_json(OUT / "replay-check.json", record)
    print(f"replay: {sum('pair' in r for r in results)} cases, worst normalised gap {worst:.2e}, pass {record['pass']}")


def batch_run(phase: str, device: str, sig: str) -> None:
    if phase == "confirmation":
        check = json.loads((OUT / "replay-check.json").read_text())
        if not check["pass"] or check["simulation_signature"] not in (sig, release_original_signature()):
            raise SystemExit("the replay check must pass with this code before the confirmation run")
    models = DEVELOPMENT if phase == "development" else CONFIRMATION
    log = {"phase": phase, "started_utc": utc_now(), "simulation_signature": sig, "environment": environment(device),
           "pairs": ["+".join(p) for p in PAIRS], "strengths": STRENGTHS, "stimuli": STIMULI, "models": {}}
    for model in models:
        report = run_model(model, device, sig, PAIRS, STRENGTHS, STIMULI, phase)
        log["models"][model] = report
        save_json(OUT / f"{phase}-run.json", log)
        print(f"{phase}: model {model} done in {report['seconds']:.1f} s; new conditions {report['conditions']}; "
              f"baseline gaps {', '.join(f'{k} {v:.1e}' for k, v in report['baseline_gap'].items())}", flush=True)
    log["finished_utc"] = utc_now()
    log["worst_baseline_gap"] = max(g for r in log["models"].values() for g in r["baseline_gap"].values())
    save_json(OUT / f"{phase}-run.json", log)
    print(f"{phase}: complete; worst baseline gap {log['worst_baseline_gap']:.2e}")


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    device = "cuda" if os.environ.get("AI09_GPU_LOCK_FD") else "cpu"
    if phase not in ("replay", "development", "confirmation"):
        sys.exit(__doc__)
    configure(device)
    sig = signature()
    if phase == "replay":
        replay(device, sig)
    else:
        batch_run(phase, device, sig)


if __name__ == "__main__":
    main()
