# 30_DESIGN_RULES & PB-1 HARDWARE — distilled engineering guidance
*Keywords: design law, placement, encoding, periphery, RC, OTS, PB-1, floorplan, sputter, process*

## The design law
**Bake what is shared and stable — it neither drifts, nor leaks, nor interferes, nor (at printed operating points) suffers IR drop. Keep tunability private, small, and placed where change enters.**

## Rules (each backed by a finding)
1. Size the tunable part by STRUCTURE, not percentage: full span of the layer where the shift enters + the complete output layer (F7, F8). The %-rule does not transfer across architectures; the boundary rule does.
2. Don't scatter tunable columns (random order worst at high frozen) (F7).
3. Input-space shift → tunable input layer; output/prosody-space → tunable head; one-hot text shift is a permutation and may still be output-recoverable if representations stay separable (F7 proviso).
4. Inputs: one-hot / binary lines wherever the domain allows — kills input DAC, input timing precision, 2^N latency, raises first-layer SNR, and buys ~15× rail-droop margin (F10, F15).
5. Interlayer: continuous time-domain chaining; budget R=16–32 levels/window; first-spike WTA for classification outputs (F10).
6. Per-chip head calibration is mandatory and free: absorbs fab lottery, write noise, AND core IR (F11). Calibrate through the real hardware, never from the design model.
7. Multimodal: baked shared core, per-modality programmable encoders, per-head programmable decoders; dormant parallel adapter (B=0) on the core as fab insurance iff edges will be baked (F14, F3).
8. Choose high device resistance (1–10MΩ printed): array power becomes negligible AND r_seg→1e-9 (IR immunity). The power choice and the IR choice are the same choice (F13, F15).
9. Leakage-aware ratio: every memristor moved to the baked side deletes its off-leak forever; head as small as F8 allows (F13).
10. Periphery ladder (est.): op-amp bank 9µW → shared S/H-muxed op-amp 0.9 → dynamic clocked comparators 0.06 → RC + OTS/NbO2 relaxation (zero-transistor integrate-and-fire) 0.01. Control plane: baked chips need only a ring sequencer (~10µW) (F13).
11. RC/CR printed passives are baked temporal computation: low-pass banks = causal context memory (replaces lookahead, enables streaming); high-pass = onset/delta features; τ carries ~5% fab tolerance — model it (F12b).
12. IR: don't mitigate, EXIT — high-R devices + fat copper. If stuck in the low-R regime: design-time pre-compensation (baked-only 10× advantage) until conductance clipping; then re-architect (F15).

## PB-1 rev A hardware spec (talking-clock chip, v7 net)
- Net: 80 one-hot in → 80×64 baked → 64×32 baked → 32×13 memristor head → 13 pulse-width outputs → LPC lattice/vocoder. 7,584 weights, 5.5% programmable (416; 832 devices differential).
- Board: 140×180mm 4-layer FR-4. Differential pairs map to the stackup: carbon G⁺ plane / prepreg / carbon G⁻ plane, joined per-bitline by plated vias; Cu wordlines top, bitline returns bottom.
- Areas @1.5mm screen-print pitch: L1 120×96mm (10,240 R), L2 96×48mm (4,096 R). Alternatives: thick-film 0.4mm → 23cm² total; inkjet 0.5mm → 36cm².
- Head: daughterboard 14×12mm — glass slide, sputtered Ti/Pt bottom stripes (32), TiO2−x ~50nm blanket, top Pt/Ag stripes (13×2), parylene/epoxy cap. Shadow-mask process compatible with Avery's Simple-Sputter-Coater.
- Periphery: 13× integrator+comparator strip; 10× 74HC595 input drivers; ESP32 for programming/drift-refresh ONLY; ring sequencer for inference.
- Power: 13µW core @100Hz (23µW with sequencer); 43-slot inference (43µs @1µs printed slot) vs 5ms frame.
- All-memristor comparison: same net would need ~24cm² of sputtered oxide + ~15k write-verify ops vs 832 — the split is what makes the board shop-buildable.
- Deliverables: chip_viewer.html (die + charge-flow + 5 voices), pb1_hardware.png (stackup + floorplan), audio wavs.
