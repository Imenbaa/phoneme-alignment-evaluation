# Phoneme Alignment Evaluation Toolkit

A Python toolkit for evaluating phoneme alignment systems.
Based on a rewrite of the [ESTER `trackeval` Perl script](http://www.afcp-parole.org/ester/) (Gravier & Galliano, 2008), extended with boundary-based F1 metrics suited to forced alignment evaluation.

---

## Overview

Alignment systems produce a sequence of phoneme segments with associated timestamps. Evaluating these systems requires metrics that jointly assess:

- **Recognition quality** — are the right phonemes predicted?
- **Alignment quality** — are the boundaries placed at the right time?

This toolkit provides two complementary evaluation modes:

| Mode | What it measures | Key metric |
|------|------------------|------------|
| Overlap-based | Duration of correctly detected phoneme per event | F1 (recall/precision on duration) |
| Boundary-based | Precision of boundary placement | F1@20ms |

Both modes operate at the **phoneme level** (each phoneme = one event) across **all audio files** in the corpus simultaneously.

---

## Input Format

All input files follow the **ETF (Event Tracking File)** format, one segment per line:

```
<source> <channel> <start_time> <duration> <type> <subtype> <event> [<score> [<decision>]]
```

| Field | Description |
|---|---|
| `source` | Audio file basename (no extension) |
| `channel` | Channel number (typically `1`) |
| `start_time` | Segment start in seconds |
| `duration` | Segment duration in seconds |
| `type` | Segment type (e.g. `ph` for phoneme) |
| `subtype` | Speaking style or condition (e.g. `planned`, `spont`); use `-` if unused |
| `event` | Phoneme label (e.g. `a`, `p`, `t`, `sil`) |
| `score` | Confidence score from the system; use `-` if unavailable |
| `decision` | `true` if the event is present, `false` otherwise |

**Example ETF reference file or hyp file:**
```
Rhap-D0020.wav 1 0.000000 0.180000 sc - a - f
Rhap-D0020.wav 1 0.180000 0.040000 sc - a - f
Rhap-D0020.wav 1 0.220000 0.288020 sc - a - f
Rhap-D0020.wav 1 0.508020 0.030000 sc - a - f
Rhap-D0020.wav 1 0.538020 0.070000 sc - a - f
Rhap-D0020.wav 1 0.608020 0.030000 sc - a - t

```

These ETF files are built in such a way that for a phoneme /a/, we check its presence (t) or absence (f) in each segment in all files. 

The script create_etf_from_pkl.py contains a function "pkl_to_etf" that takes as input a dictionary of files and their corresponding ref and hyp phonemes sequences and intervals (example:**alignment_rhap.pkl**) and creates an etf file.

you can use it as follows:

```
pkl_to_etf("alignment_rhap.pkl", "hyp.etf", use_hyp=True)
pkl_to_etf("alignment_rhap.pkl", "ref.etf", use_hyp=False)
```
---

## Metrics

### Overlap-based F1 (trackeval original logic)

For each phoneme event, the script computes:

```
TP = duration correctly detected (overlap between ref and hyp, both positive)
FN = duration of ref not covered by hyp  (miss)
FP = duration of hyp over a negative ref region  (false alarm)

recall    = TP / (TP + FN)  =  (tar - miss) / tar
precision = TP / (TP + FP)  =  (tar - miss) / (tar - miss + ins)
F1        = 2 · recall · precision / (recall + precision)
```

This metric penalizes both **recognition errors** (wrong phoneme label) and **alignment errors** (correct label but shifted boundary), since both reduce the overlap duration.

### Boundary-based F1 (added by me)

For each phoneme, segment **start boundaries** are extracted from ref and hyp. A hypothesis boundary is a **True Positive** if and only if it falls within ±δ of a reference boundary:

```
|t_hyp_start - t_ref_start| ≤ δ
```

Each reference boundary can be matched at most once (greedy nearest-neighbor matching).

```
TP = matched boundaries within tolerance δ
FP = hyp boundaries with no close reference  →  hallucinated or shifted beyond δ
FN = ref boundaries with no close hypothesis →  missed or shifted beyond δ

F1@δ = 2 · precision · recall / (precision + recall)
```

Three tolerances are reported: **F1@0ms**, **F1@20ms**, **F1@50ms**.

> **Note on F1@0ms:** Since aligners work at frame resolution (typically 10ms for MFA, 20ms for CTC), exact boundary coincidence is driven by frame discretization, not true precision. F1@0ms should not be interpreted as a meaningful alignment quality measure. F1@20ms is the recommended primary boundary metric.

> **Note on phoneme identity:** Boundary F1 does not verify phoneme labels — it only checks whether a boundary exists near the reference position. This is a deliberate design choice: the metric evaluates **alignment** (boundary placement), while phoneme recognition quality is captured separately by PER.

### Summary of differences

| Property | Overlap F1 | Boundary F1@20ms |
|----------|------------|------------------|
| Unit | duration (seconds) | boundary position |
| Penalizes wrong label | yes | no |
| Penalizes shifted boundary | partially | yes, directly |
| Penalizes missing phoneme | yes | yes (2 boundaries lost) |
| Sensitive to uniform shift | yes | no (if within tolerance) |

---

## Aggregation

All metrics are aggregated at **corpus level** by summing raw counts (TP, FP, FN, miss, ins, tar) across files before computing ratios. This avoids the instability of averaging per-file F1 scores, especially for short files or rare phonemes.

---

## Installation

```bash
git clone https://github.com/Imenbaa/phoneme-alignment-evaluation
```
---

## Usage

### Command-line

```bash
# Overlap-based detection report
python trackeval.py --margin=0 --error=event ref.etf hyp.etf

# Segmentation (boundary recall/precision)
python trackeval.py --margin=0 --segmentation=event ref.etf hyp.etf

# Both + boundary F1
python trackeval.py --margin=0 --boundary_delta=0.02 --error=event --segmentation=event \
                    --boundary-f1 ref.etf hyp.etf

# Output to file
python trackeval.py --margin=0 --error=event -o results.txt ref.etf hyp.etf

# With speaking style subtypes
python trackeval.py --margin=0 --subtype --segmentation=event+subtype --error event+subtype ref.etf hyp.etf
```

### Python API

```python
from trackeval import run_trackeval

# Run evaluation
results = run_trackeval(
    reffn          = "ref.etf",
    hypfn          = "hyp.etf",
    margin         = 0.0,        # no erosion
    boundary_delta = 0.020,      # 20ms tolerance for boundary F1
    bnd_f1         = True        # compute boundary F1
)

# Global metrics
print(f"F1 (overlap)    = {results['global']['F1']:.4f}")
print(f"F1@20ms (bnd)   = {results['global']['bnd_F1']:.4f}")
print(f"Recall          = {results['global']['recall']:.4f}")
print(f"Precision       = {results['global']['precision']:.4f}")
print(f"Miss rate       = {results['global']['miss_rate']:.4f}")
print(f"False alarm rate= {results['global']['false_alarm_rate']:.4f}")

# Per-phoneme
for ph, m in results['by_event'].items():
    print(f"{ph:5s}  F1={m['F1']:.3f}  F1@20ms={m.get('bnd_F1', 0):.3f}")

# Per-file
for src, m in results['by_source'].items():
    print(f"{src}  recall={m['recall']:.3f}")

```

---

## Command-line options

| Option | Default | Description |
|---|---|---|
| `-m`, `--margin` | `0.25` | Margin applied to ref segment boundaries before scoring. Use `0` for phoneme alignment. |
| `-D`, `--delta_boundary` | `0.02` | Tolerance of boundaries for phoneme alignment |
| `-r`, `--error[=spec]` | — | Report detection errors. `spec` can be `sum`, `event`, `source`, or combinations with `+`. |
| `-b`, `--segmentation[=spec]` | — | Report segmentation statistics (boundary recall/precision). |
| `--boundary-f1` | off | Compute boundary-based F1 with tolerance = `--margin`. |
| `-t`, `--subtype` | off | Enable per-subtype reporting (e.g. per speaking style). |
| `-s`, `--uem=fn` | — | Restrict scoring to regions defined in a UEM file. |
| `-e`, `--event=str` | all | Score only specified phoneme(s). Repeatable. |
| `-l`, `--list=fn` | — | Load phoneme list from file. |
| `-n`, `--max-segments=n` | 0 | Limit hypothesis segments per source/event. |
| `-a`, `--align` | off | Print ref/hyp alignment to output. |
| `-o`, `--output=fn` | stdout | Write output to file. |
| `-d`, `--det[=fn]` | — | Output DET curve data. Requires confidence scores in hyp ETF. |
| `-v`, `--verbose` | off | Print progress to stdout. |

---

## The `margin` parameter

The `margin` parameter has **two effects** in the original ESTER script:

1. **Boundary tolerance** — used in `etfbcmp()` to decide whether a hypothesis boundary is close enough to a reference boundary.
2. **Segment erosion** — in `etfcmp()`, both edges of each reference segment are shrunk inward by `margin` seconds before scoring. This neutralizes ambiguous transition zones in diarization.

For phoneme alignment, erosion is **harmful**: phonemes typically last 50–150ms, and a 250ms erosion (the ESTER default) would destroy all segments. Use `--margin=0` to disable erosion. Boundary tolerance for F1 is controlled separately via `boundary_delta` in the Python API.

---

## Origin and relation to ESTER `trackeval`

This script is a Python rewrite of the Perl `trackeval` script used in the ESTER evaluation campaigns for French broadcast speech (Gravier et al., 2004; Galliano et al., 2009). The original script was designed for **speaker diarization** and **speech/music segmentation**, where segments last several seconds and the relevant metric is duration overlap.

The following extensions were added for phoneme alignment evaluation:

- `etfbcmp_f1()` — boundary F1 with TP/FP/FN decomposition (vs. the original `etfbcmp()` which only returns a match count)
- `run_trackeval()` — programmatic API returning structured Python dicts
- `boundary_delta` — decouples boundary tolerance from segment erosion

