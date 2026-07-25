# What's next

## ACTIVE WORKSTREAM (2026-07-25): scaled demo + paper
See `60_demo_and_paper_goals.md` (spec) and `current_state.md` (status).
DONE this session (all in `demo_pb2/`, committed; numbers in
`demo_pb2/RESULTS_v13.md`): Docker container up; 720-utt corpus; scaling
sweep (baked core doesn't saturate); interactive clock viewer with
current-heatmap die + 4 voices + memristor-aging week slider (published as
an Artifact); physical t^-nu drift experiment; `70_literature_validation.md`.

DONE (session 2, 2026-07-25): **paper draft v1 = `80_paper_draft.md`**;
**topology_v14/** (grid vs perm vs clustered tiles, IR-aware baking — see
TOPOLOGY_V14.md); viewer input-channel phone labels + Artifact republish.

**NEXT, in order:**
1. **Error bars over multiple seeds** for the drift + scaling curves (both are
   single-seed right now; the drift table's gain-comp wiggle is from
   per-week independent draws — see RESULTS_v13 caveats). This is the main
   thing standing between the current results and paper-grade figures.
2. Verify the citations in `70_literature_validation.md` / the paper's
   reference list (subagent-gathered; need a human/careful pass before
   publishing).
3. Iterate `80_paper_draft.md` with Avery (structure is in place; drop in
   multi-seed figures when #1 lands).
4. Group-sparsity / clusterable training follow-up from topology_v14 (make
   tiles own disjoint row subsets → real area shrink; then layout-in-the-
   loss training). New, from Avery's topology question.
5. RC-causal streaming front end (speced in 60_, NOT built yet) on the large
   corpus — parity-at-fewer-lines streaming variant for the demo.
6. Optional demo polish: widen the showcase-time set; matched-capacity
   control for the scaling claim (F9 caveat).

The v4-v12 investigation queue below is still valid but secondary to the
demo/paper push unless Avery redirects.

---

Condensed from `50_investigation_queue.md` — check that file for full detail
before starting anything; this is a priority-ordered pointer, not the full
spec.

## P0 — validity & cross-checks (do these first)
1. AIHWKit CRN port — last big cross-validation gap (all v4-v12 work is
   numpy-side only).
2. F2 autopsy — loss traces on the AIHWKit 94.6% config; decide keep/delete
   on variance-first.
3. Modality dropout on the sum bus — prerequisite for trusting F14's
   flat-power claim end to end.
4. Vary train/test split per seed for honest absolute CIs.

## P1 — the paper's load-bearing extensions
5. Inverted-multimodal test (partially-baked encoders).
6. Overparameterization control for F9 before claiming "bigger bakes
   better" generally.
7. Encoding × frozen-ratio 2D DSE.
8. Leakage-aware cost function in the Pareto.
9. Per-layer independent R sweep.
10. Vocabulary-size knob on the F7 output-only-recovery proviso.
11. F6 energy per baking order.

## P2 — hardware realism
12-17. Better IR compensation solver, memristor I-V nonlinearity, SPICE
validation, RC temporal-basis follow-ups, write-limited fine-tune realism,
drift-over-weeks with real AIHWKit PCM model.

## P3 — queued by Avery, do NOT start unprompted
18. Memristor transformer (baked W_Q/K/V/O + FFN). Explicitly deferred —
    respect this, don't pick it up without her asking.

## Paper skeleton (from 50_investigation_queue.md)
Frozen-ratio DSE (F1/F7/F8/F9) → encoding & system (F10/F13) →
calibration & robustness (F11/F15/F5) → multimodal topology (F14) → PB-1
demonstrator (F12) → honest limitations ledger.
