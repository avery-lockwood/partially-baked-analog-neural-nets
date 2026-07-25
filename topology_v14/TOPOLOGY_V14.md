# topology_v14 — is a grid the best arrangement for the baked sections?

*2026-07-25. Question posed by Avery: can clustering the fixed-resistor
section into a different topology shrink it, or beat the grid? And since IR
drop is exactly predictable (F15), can we build the model using the
prediction? Script: `topology_v14.py`; raw numbers:
`results_topology_v14.csv`; log: `run.log`. Runs in the container in ~40 s.*

## Setup

Real trained PB-2 baked weights (L1 92×64, L2 64×32 from
`demo_pb2/demo_v13_data.json`), driven by the real showcase-utterance frames
(2,628 one-hot input frames / stored a1 activations). Exact nodal solver
(verbatim nodal_ir_v12, differential planes share wordlines), r_seg swept
1e-4 / 1e-3 / 3e-3. Metrics: exact W_eff distortion, **activation-current
error on real drive patterns** (the physically meaningful one — biases and
ReLU live in the periphery, so array IR only touches currents), device
count, footprint area, wire length (with join-bus + 1.15× inter-tile routing
overhead charged).

Interventions:
- **perm** — free row/col permutation: heavy columns near drivers, heavy ×
  frequently-driven rows near the sense edge. Function unchanged.
- **tiled k∈{2,4}, θ** — k-means co-clustering of output columns on their
  pruned row-usage masks; cells |W|<θ·max not printed; rows a tile doesn't
  use dropped (row compaction); tile outputs join a short bus into the
  shared integrator (series R modeled). Assumes per-tile wordline feeds
  (fat traces from the same driver), stated as a model assumption.
- **IR-aware baking** — F15 fixed-point pre-compensation run per layout
  (continuous baked values), i.e. predict this geometry's W_eff, bake the
  inverse.

## Results (L1, representative rows; full CSV has 42)

| layout | r_seg | W_eff err | act err raw | act err + IR-baked | clip | wire rel |
|---|--:|--:|--:|--:|--:|--:|
| grid            | 1e-4 | 0.084 | 0.103 | — | — | 1.00 |
| grid+perm       | 1e-4 | 0.076 | 0.096 | — | — | 1.00 |
| tiled k4 θ0.05  | 1e-4 | 0.089 | **0.080** | — | — | 1.43 |
| grid            | 1e-3 | 0.484 | 0.556 | 0.540 | 2.3% | 1.00 |
| grid+perm       | 1e-3 | 0.455 | 0.535 | 0.498 | **1.0%** | 1.00 |
| tiled k4 θ0.05  | 1e-3 | 0.428 | 0.373 | **0.270** | 11.4% | 1.43 |
| grid            | 3e-3 | 0.751 | 0.822 | 0.919 (!) | 22.2% | 1.00 |
| grid+perm       | 3e-3 | 0.727 | 0.808 | 0.889 (!) | 23.3% | 1.00 |
| tiled k4 θ0.05  | 3e-3 | 0.674 | 0.597 | 0.588 | 30.6% | 1.40 |

L2 (64×32) shows the same ordering, milder (grid 0.350 → perm 0.319 raw at
1e-3; comp 0.16, clip <1%). Printed PB-1 operating point r=2.4e-9: W_eff
err 2.2e-3 — immune regardless of topology, as F15 said.

## Findings

1. **Placement is free and always helps.** Pure permutation (zero hardware
   cost, zero function change) buys ~5–10% relative distortion reduction
   and — more importantly — **halves conductance clipping** in the
   compensation regime (2.3%→1.0% at r=1e-3), extending the feasible range
   of IR-aware baking. There is no reason ever to place weights in
   arbitrary order.
2. **Clustered tiling is an electrical win, not an area win (for this
   network).** k=4 tiles cut activation-current error ~1.5× raw and ~2×
   with IR-aware baking at r=1e-3 (0.540→0.270 vs grid+comp) by shortening
   wordline runs. Cost: ~40% wire-length overhead (join buses + routing)
   and per-tile wordline feeds.
3. **Area did NOT shrink — and that's the honest headline.** Even pruning
   60% of devices (θ=0.2, prune-only err 0.355 — already unacceptable),
   nearly every input row remains used in every tile, so row compaction
   never triggers: the trained W is dense/unstructured. **A grid is
   area-optimal for a dense weight matrix; topology only shrinks the array
   if the model is trained to be clusterable** (group/structured sparsity
   at train time → tiles that genuinely own disjoint row subsets). That
   co-design experiment is the queued follow-up, and it closes the loop
   with "build the model using the predicted IR": train with the layout in
   the loss, not just bake against the layout afterward.
4. **IR-aware baking works until the clipping wall, then backfires.** At
   r=1e-3 pre-compensation improves every layout (best: tiled k4, act err
   0.270). At r=3e-3 the demanded conductances clip (22–31% of cells) and
   compensation makes the grid *worse* than raw (0.822→0.919) — matching
   F15's conductance-clipping hard wall and its "re-architect, don't
   compensate" rule. The fixed point is also known to under-converge in
   this regime (residuals are upper bounds).
5. **At the printed operating point none of this matters** (design rule 8/12
   already exited the IR regime). Topology is the tool for the *dense/low-R*
   regimes: sputtered thin-film cores, finer pitches, research arrays — or
   the eventual scaling of the baked core past what one high-R monolith can
   host (F15 clipping grows with array width).

## Model assumptions / caveats

Per-tile wordline re-drive assumed (not a continued thin wordline);
inter-tile wordline routing charged to the wire metric (1.15×), not the
electrical model; join bus as series R on the sense; ohmic-only solver;
single weight-draw (chip A), no seed sweep; drive statistics from the 16
showcase utterances, not the full corpus.

## Follow-ups (queued)

- Group-sparsity / clustered training so tiles own disjoint row subsets →
  real row compaction → genuine area shrink; then re-run this harness.
- Greedy/simulated-annealing placement against the exact solver (current
  perm is a one-shot heuristic; the solver is fast enough at this scale to
  iterate).
- Layout-in-the-loss training (train against predicted W_eff of the chosen
  topology — the full "build the model using the IR" version).
