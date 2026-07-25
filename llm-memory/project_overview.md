# Project overview

**What this is:** simulation-based design-space exploration (DSE) of hybrid
fixed(baked)/programmable analog neural networks — i.e., analog NN hardware
where most weights are permanently fabricated ("baked") and a small fraction
stay electrically tunable (memristor/programmable).

**The gap claimed:** a systematic frozen-ratio DSE (how much of a network to
bake vs. leave programmable, and where) is absent from the literature.
Extended this session to also cover: encoding × ratio 2D DSE, multimodal
baking topology, and a baked-IR-compensation chain.

**The thesis (the design law — this is the paper's spine):**
> Bake what is shared and stable — it neither drifts, nor leaks, nor
> interferes, nor (at printed operating points) suffers IR drop. Keep
> tunability private, small, and placed where change enters.

Every finding in 10_findings_v2.md is treated as an instance of this law;
30_design_rules_hardware.md distills it into 12 concrete engineering rules.

**One-paragraph version (from README_INDEX.md):** the frozen-ratio question
resolved into that design law. The "cliff" long assumed in this space is
actually the output-layer boundary in disguise (linear, 3-4pp per tunable
output neuron, tracks architecture). One-hot time-domain encoding kills
converter latency and IR sensitivity simultaneously. Per-chip head
calibration absorbs both fab variation and core IR distortion. Power is
periphery- and control-bound, not array-bound. A fully baked core needs
only a ring sequencer (23µW system), and a multimodal shared baked core is
flat in modality count. The PB-1 talking clock demonstrates the whole stack
end to end: real speech in, 0.86 spectrogram fidelity out, drift audible,
buildable as a 4-layer PCB plus a 14×12mm sputtered daughterboard.

**Doc map (project root, authoritative — this file is a summary, not a
replacement):**
- `00_CRITICAL_v2.md` — 2-minute-read superseding summary, status of every
  finding (confirmed/revised/retracted/refined), next steps.
- `10_findings_v2.md` — full results with statistics, F1-F15.
- `20_methods_env_v2.md` — CRN protocol, time-domain model, LPC pipeline,
  power model, nodal solver, sandbox notes.
- `30_design_rules_hardware.md` — the design law, 12 rules, PB-1 rev A
  hardware spec.
- `50_investigation_queue.md` — priority queue P0-P3.
- Notebooks `bundle_01/02/03_*.ipynb` — run-all regenerates every script,
  CSV, and figure; this is the project's transfer format.

See `current_state.md` in this folder for a condensed status table, and
`queue.md` for what's next.
