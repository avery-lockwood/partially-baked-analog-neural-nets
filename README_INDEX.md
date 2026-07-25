# Partial-Baking Analog NN — Session Package (2026-07-25, v4–v12)

One day of work, packaged. Start with **00_CRITICAL_v2.md** (2-minute read),
then **10_findings_v2.md** (everything, with numbers).

## Documents
| file | what |
|---|---|
| 00_CRITICAL_v2.md | Superseding summary: revised F1–F6, new F7–F15, the design law, top of queue |
| 10_findings_v2.md | Comprehensive findings with statistics, per experiment v4→v12, + limitations ledger v2 |
| 20_methods_env_v2.md | CRN protocol, time-domain model, LPC pipeline, power model, nodal solver, sandbox notes |
| 30_design_rules_hardware.md | The design law, 12 engineering rules, full PB-1 rev A hardware spec |
| 50_investigation_queue.md | Consolidated priority queue P0–P3 + paper skeleton note |

## Notebooks (project transfer format: run-all regenerates every script & CSV; figures embedded)
| notebook | covers | findings |
|---|---|---|
| bundle_01_validation_scaling.ipynb | v4 CRN validation + baking order; v8 4-size scaling | F1rev, F2, F7, F8, F9 |
| bundle_02_timedomain_tts.ipynb | v5 encoding/latency; v6 legacy; **v7 PB-1 chip**; v10 RC-causal; viewer builder | F10, F11, F12, F12b |
| bundle_03_system_power_ir.ipynb | v8/v10/v11 multimodal; v9 power; v8 hardware render; **v12 nodal IR** | F13, F14, F15 |

## Standalone media (not embedded in notebooks — regenerable, but listen/open directly)
- chip_viewer.html — interactive die + charge flow synced to audio, 5 voices
- v7_mbrola_original.wav → v7_vocoder_ceiling.wav → v7_chip_A.wav → v7_chip_B.wav → v7_chip_A_drifted.wav (listen in that order)
- v10_chip_RC_causal.wav — the printed-RC streaming variant
- pb1_hardware.png, die_preview.png, and all study figures (also embedded in bundles)

## Environment to reproduce
Python 3.12 + numpy/scipy/sklearn/matplotlib; `pip --break-system-packages`;
`apt-get install espeak-ng mbrola mbrola-us1` for bundle 02. No network
datasets needed. Long jobs: run foreground with `timeout` (background procs
are killed between tool calls in the sandbox).

## The one-paragraph version
The frozen-ratio question resolved into a design law: **bake what is shared
and stable; keep tunability private, small, and placed where change enters.**
The "cliff" is the output-layer boundary in disguise (linear, 3–4pp per
tunable output neuron, tracks architecture). One-hot time-domain encoding
kills converter latency and IR sensitivity simultaneously. Per-chip head
calibration absorbs fab variation AND core IR distortion. Power is
periphery- and control-bound, not array-bound — a fully baked core needs
only a ring sequencer (23µW system) and a multimodal shared baked core is
flat in modality count. The PB-1 talking clock demonstrates the whole stack
end to end: real speech in, 0.86 spectrogram fidelity out, drift audible,
buildable as a 4-layer PCB plus a 14×12mm sputtered daughterboard.
