# 00_CRITICAL_v2 — Partial-Baking Analog NN Study
*Supersedes 00_CRITICAL (2026-07-24). Updated 2026-07-25 after the v4–v12 session. Read this first; details in numbered files.*

**Who:** Avery Lockwood (she/her) — industrial arts instructor, fabricator, engineering student (mech E + comp E); builds her own lab equipment incl. sputter/PVD deposition. Control plane: ESP32. Detail: 40_collaborator_avery.md (unchanged).

**Project:** Simulation DSE of hybrid fixed(baked)/programmable analog NNs. GAP CLAIMED (unchanged, extended): systematic frozen-ratio DSE absent from literature; NOW ALSO: encoding × ratio 2D DSE, multimodal baking topology, and the baked-IR-compensation chain are unclaimed.

**THE THESIS SHARPENED (this session's main output).** The paper's question has moved from "how much can you bake?" to a design law:
> **Bake what is shared and stable — it neither drifts, nor leaks, nor interferes, nor (at printed operating points) suffers IR drop; keep tunability private, small, and placed where change enters.**
Every finding below is an instance of this law.

**Status of prior findings (see 10_findings_v2.md for full numbers):**
- F1 REVISED: no 60–90% plateau — linear decline −1.03pp/10% frozen (p=2e-15, 30 seeds); knee at output-layer boundary, not a universal %.
- F2 RETRACTED-PENDING: variance-first does not survive; AIHWKit signal = one seed below no-adapt floor (optimizer-divergence suspect).
- F3 REFINED: adapter wins only in extreme-frozen regime; coverage not rank (r2≈r4); redundant when edges are programmable (v11).
- F4 THINNED: only 0% vs 68.8% drift contrast significant (p=0.039).
- F5 CONFIRMED as technology-conditional.
- F6 CONFIRMED & EXTENDED: conversion-dominance → control-plane elimination (v9).
- v1/v4 IR NULLS SUPERSEDED: static mask underestimates true nodal distortion ≤5×; prior nulls were mask-model statements. Replacement chain in F15 is stronger.

**New findings F7–F15 (one-liners):**
- F7 PLACEMENT>BUDGET: baking order matters more than fraction; tunable capacity belongs where the shift enters.
- F8 CLIFF=BOUNDARY: "cliff" is linear in tunable output neurons (3–4pp/neuron); %-location tracks architecture (scaling-test passed, 4 sizes).
- F9 BIGGER BAKES BETTER: ≥90%-recovery max-frozen 60→90%, cost 0.60→0.40× over 1.9k→32k weights (overparam caveat).
- F10 TIME-DOMAIN ENCODING: one-hot binary input kills 2^N latency; R=16–32 levels/window suffice; first-spike WTA; 768→43 slots (18×).
- F11 HEAD CALIBRATION: per-chip ridge write-verify absorbs the fab lottery AND core IR distortion (44% weight error → +8% RMSE).
- F12 TTS CHIP WORKS: LPC-10/MBROLA talking clock, spectrogram corr 0.86 (ceiling 0.994); drift audible; RC-causal variant streams with printed R+C context (corr 0.874).
- F13 POWER: PB-1 core 13µW@100Hz; periphery 69%, array 1.7%; control plane is the war → autonomous sequencer → 23µW system; 480× vs ESP32 SW; 28nm ASIC wins but is unprintable.
- F14 MULTIMODAL LAW: baked shared core is best on recovery, interference, forgetting AND power; power flat in #modalities (24µW @M=8 vs 192µW separate); frozen core learns a never-trained joint feature as well as programmable.
- F15 IR CHAIN: ohmic arrays are linear → exact input-independent W_eff; printed MΩ devices + mΩ copper → r≈2.4e-9, immune by construction; baked compensation 10× better than write-quantized; clipping is the hard wall; rail droop bounded 15× by one-hot sparsity; head-cal rescues the rest.

**Artifacts this session:** PB-1 chip (sim v7): 80-line one-hot in → baked 80×64+64×32 → memristor 32×13 head → LPC-10 out; audio (5 voices incl. drift), interactive die viewer (chip_viewer.html), hardware spec (140×180mm 4-layer + 14×12mm sputtered daughterboard), power/IR/scaling/multimodal studies. File map: README_INDEX.md.

**Next steps (top of queue):** 1) AIHWKit CRN port (last big cross-validation gap), 2) F2 loss-trace autopsy, 3) modality-dropout on the sum bus, 4) inverted-multimodal adapter test with partially-baked encoders, 5) OTS relaxation-neuron SPICE. Full queue: 50_investigation_queue.md.

**Env quirks (additions):** espeak-ng + mbrola + mbrola-us1 install from Ubuntu archive (allowlisted); espeak `--pho` needs mbrola voice; background processes die between tool calls — run long jobs foreground with timeout.
