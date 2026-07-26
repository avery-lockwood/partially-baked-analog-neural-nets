# Current state (as of 2026-07-25, session v4→v12)

Full numbers live in `10_findings_v2.md`; this is the fast-scan status
table. When a new session lands (v13+), update this file — don't let it
drift from 00_CRITICAL.

## WORKSTREAM: PB-2 / demo v13 — largely DONE (2026-07-25)
Built a bigger TTS-chip demo (feeding the paper) — all in `demo_pb2/`,
committed. Numbers + honest caveats: `demo_pb2/RESULTS_v13.md`. Pipeline
runs in the Docker container `analog-nn-dev`.
Shipped:
- 720-utterance natural-time corpus (36→720). **Scaling result: the fixed
  baked core does NOT saturate** — chip k-RMSE flat ~0.084 while the float
  ceiling improves 23% across a 17× vocabulary jump (the headline figure).
- Interactive clock-face web viewer (`demo_pb2/clock_viewer.html`), published
  live as an Artifact: current-heatmap die (charge where it physically flows)
  + filling bitline caps, 4 voices, and a **memristor-aging week slider**
  (physical t^-nu drift, head-only; browser recomputes only the head live so
  the baked core visibly stays frozen).
- Drift result: uncompensated fidelity 0.90→0.79 over 12 weeks; a global
  gain-rescale recovers most; head recalibration resets it (extends F4 with
  the physical model).
- `70_literature_validation.md` (project root): sim assumptions vs published
  data, honest verdicts. Citations still need a human check before publishing.

**Session 2 (2026-07-25, later):**
- **Paper draft v1 assembled: `80_paper_draft.md`** (project root) — all of it
  in one place: power (§6), passives/RC (§7), converter-free encoding (§5),
  topology (§8), multimodal + recommended architecture for Avery's trimodal
  scene-describing chip (§9), methods, lit-validation refs, limitations,
  pre-submission checklist.
- **NEW investigation `topology_v14/`** (script + CSV + TOPOLOGY_V14.md):
  grid vs permuted vs clustered-tiled baked arrays, exact nodal solve on the
  real PB-2 weights. Findings: placement is free and always helps (halves
  comp clipping); k=4 tiling is a ~2× electrical win at r=1e-3 under
  IR-aware baking; **area does NOT shrink** — trained W is dense, row
  compaction never triggers → grid is area-optimal unless the model is
  trained clusterable (group sparsity queued); comp backfires past the
  clipping wall (r=3e-3); printed op point immune regardless.
- Clock viewer: input channels now labeled with phone letters (L1 gutter:
  per-row letters, active ones light up; prev/now/next/pos block labels);
  Artifact republished at same URL.

- Multi-seed error bars DONE (2026-07-25, `demo_pb2/seeds_v13.py`, 8 seeds,
  per-seed splits): scaling no-saturation claim holds with 95% CIs (chip A
  0.093→0.084, never up); **drift correction** — the 0.90→0.79 single-seed
  drop was a per-week-redraw artifact; honest 12-week uncompensated
  Δmelcorr −0.021±0.015, worst seed −0.048, monotone in all 8 seeds
  (RESULTS_v13.md multi-seed section; paper §11 + abstract updated).
- Paper figures pipeline DONE: `paper_figures/make_figures.py` → 7 figures
  (power, latency, topology, IR, multimodal, scaling+CI, drift+CI), all
  referenced from `80_paper_draft.md`; v12 nodal CSV copied to
  `paper_figures/data/` for reproducible builds.

**NOT yet done / next:** citation hand-check;
group-sparsity clusterable-training follow-up (topology_v14). RC-causal
streaming front end speced (`60_demo_and_paper_goals.md`) but not built.
Full ordered list in `queue.md`. The v4-v12 investigation queue is secondary
unless Avery redirects.

**Git note:** Avery is archiving the v2 numbered docs into `oldmdfiles/` and
an `old claude chats/` folder — intentional but left uncommitted. The v2 docs
(00–50 + 40) now live in `oldmdfiles/`, not root; don't "restore" them. Avoid
`git add -A` (would sweep in `old claude chats/`).

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
