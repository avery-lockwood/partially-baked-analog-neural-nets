# Current state (as of 2026-07-25, session v4→v12)

Full numbers live in `10_findings_v2.md`; this is the fast-scan status
table. When a new session lands (v13+), update this file — don't let it
drift from 00_CRITICAL.

## Finding status
| # | one-line | status |
|---|---|---|
| F1 | no 60-90% plateau; linear decline -1.03pp/10% frozen, knee at output-layer boundary | REVISED |
| F2 | variance-first (numpy vs AIHWKit sd) | RETRACTED-PENDING (AIHWKit signal = optimizer-divergence artifact, seed 2) |
| F3 | parallel adapter wins in extreme-frozen regime only; ≈0 effect once edges are programmable | REFINED |
| F4 | drift: only 0% vs 68.8% frozen contrast survives | THINNED |
| F5 | technology-conditional clean-acc inversion (baked > write-quantized) | CONFIRMED |
| F6 | conversion dominance → control-plane elimination | CONFIRMED & EXTENDED |
| F7 | placement > budget: baking order matters more than fraction | NEW |
| F8 | cliff is linear in tunable-output-neuron count; boundary tracks architecture | NEW |
| F9 | bigger models bake better (overparam caveat, needs matched-capacity control) | NEW |
| F10 | one-hot time-domain encoding kills 2^N latency (18x reduction, 768→43 slots) | NEW |
| F11 | per-chip head calibration absorbs fab lottery AND core IR distortion | NEW |
| F12 | PB-1 TTS chip works end to end, spectrogram corr 0.86 (ceiling 0.994) | NEW |
| F13 | power is periphery/control-bound; autonomous sequencer → 23µW system | NEW |
| F14 | multimodal law: baked shared core + programmable encoders/decoders wins on every axis, power flat in #modalities | NEW |
| F15 | exact nodal IR solve: static mask underestimated true distortion up to 5x; baked compensation ~10x better than write-quantized; printed high-R ⇒ IR-immune by construction | NEW |

v1/v4 IR nulls: SUPERSEDED — static mask underestimated true nodal
distortion, F15's exact solve replaces those claims.

## Session artifacts
PB-1 chip (sim v7): 80-line one-hot in → baked 80×64+64×32 → memristor
32×13 head → LPC-10 out. Deliverables (regenerable from the bundle
notebooks, not all present as standalone files in the repo root right now):
`chip_viewer.html` (interactive die + charge-flow viewer, 5 voices), 5 audio
files walking ceiling→chip A→chip B→drifted chip A, `v10_chip_RC_causal.wav`,
`pb1_hardware.png`, `die_preview.png`. Hardware spec: 140×180mm 4-layer
FR-4 board + 14×12mm sputtered daughterboard (compatible with Avery's
sputter coater).

## Repo state
Git repo initialized 2026-07-25 (was not previously version-controlled).
Root docs + 3 bundle notebooks committed as the initial snapshot. Standalone
media (wav/png/html) mentioned in README_INDEX.md were NOT present in the
directory at init time — they're regenerable from the notebooks; add them
to the repo if/when they're regenerated and worth keeping around.
