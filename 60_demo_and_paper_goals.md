# 60_DEMO_AND_PAPER_GOALS — the end-state we're building toward
*Created 2026-07-25. Direction set by Avery: a bigger, more complex TTS-chip
demo for her website, feeding a paper. This file is the north star for the
demo/paper workstream; the numbered findings docs (00–50) remain the record
of what's already been shown.*

## The three deliverables (Avery's stated end goal)
1. **A paper** with: (a) simulation methods, (b) validation of results that
   cites data from other published papers, (c) a working demo of the
   concept.
2. **A working demo Avery can show off on her website** (averyazalea.com) —
   larger and more complex than the v7 36-phrase talking clock.
3. The physical build path stays real (PB-1 rev A hardware spec, buildable
   with her sputter coater) so the demo is not vaporware.

## Demo scope decision — PB-2 "full talking clock" (demo v13)
Chosen direction (scale the existing, proven talking-clock demo rather than
switch domains — keeps the LPC-10 / TMS5100 Speak&Spell heritage and the
whole validated pipeline, just larger and harder):

- **Corpus 36 → full time space.** Speak *any* time of day in natural
  English: hours 1–12 × minutes 00–59 with natural phrasings ("quarter past
  three", "twenty to nine", "three oh five", "half past ten", "noon",
  "midnight"). ~720 unique utterances vs. 36. Optionally + day-of-week and a
  few canned announcements. This is a genuinely larger, phonetically richer
  corpus.
- **Why this tests the thesis harder (not just bigger):** the design law is
  "bake what is *shared*." A single baked phonetic core now has to hold a
  much larger shared representation while only the tiny per-chip head stays
  programmable. The load-bearing question: does spectrogram fidelity hold as
  the corpus grows 20×, or does the fixed baked core saturate? Either answer
  is a real paper result (generalization of the baked core, or a measured
  capacity limit + the scaling curve).
- **Streaming front end:** use the RC-causal encoder (v10, `rc_context_v10`)
  so synthesis is strictly causal / real-time-able, not batch lookahead —
  more impressive live on a website and a distinct contribution (printed RC
  = baked temporal computation).
- **Interactive web viewer:** extend the existing `chip_viewer.html` /
  `build_viewer.py` path — a clock face; pick or land on a time → hear the
  chip say it while watching charge flow through baked L1/L2 → memristor
  head. Self-contained HTML (works as a website embed / Artifact).

Open sub-decisions to confirm with Avery when convenient (do NOT block on
these — pick sensible defaults and note them):
- Head width: v7 head is 32×13. A 20× corpus may want a slightly wider
  hidden/head; measure first, widen only if fidelity demands it (respect the
  design law — keep the programmable part as small as the data allows, F8).
- Whether to add non-clock content (weather/date) in this pass or keep it
  pure-time for a clean scaling story. Default: pure time this pass.

## Paper — validation-against-literature workstream
The paper must *cite published data* to justify the sim's device/noise
assumptions and to benchmark results. Concrete citation targets to gather
(literature task, queued):
- Analog in-memory-compute / memristor-crossbar accuracy + variability
  numbers (to justify SIGMA_FAB≈5%, SIGMA_PROG≈4%, 16 write levels, drift):
  e.g. IBM AIHWKit / analog-AI papers, HfOx/TiOx RRAM device studies.
- Printed / thin-film resistor tolerance & stability (to justify the baked
  core's 5% and the "immune-by-construction" IR argument): printed
  electronics literature.
- LPC-10 / TMS5100 vocoder intelligibility (heritage + the "precision
  tolerance" claim): the Speak & Spell / TI codec literature.
- Time-domain / pulse-width analog NN encoding prior art (position the F10
  latency claim): spiking / time-domain analog compute papers.
- Crossbar IR-drop analyses (position F15's exact nodal solve vs. the
  static-mask literature).
Deliverable: a `70_literature_validation.md` mapping each sim assumption and
each headline result to at least one citable external number, with the gap
(where our numbers are optimistic/pessimistic vs. published) stated
honestly. This is the "validation that cites data from other papers" the
paper needs.

## Build/run substrate
All heavy runs go through the Docker dev container `analog-nn-dev`
(`.docker/README.md`). Corpus generation calls espeak-ng + MBROLA us1 (in
the image). The full-time corpus (~720 utterances) is much heavier than 36
— budget for it, cache the analyzed LPC frames to disk so re-runs are cheap,
and mind the weak Ryzen 3 (4 cores). Consider generating the corpus once
into a cached .npz and iterating the network on the cache.

## Status / next actions (living)
- [ ] Container reachable (blocked on `usermod -aG docker avery` + shell
      group refresh — see environment.md).
- [ ] Scale corpus generator to full natural-time phrasings; cache LPC
      frames.
- [ ] Retrain baked core on the large corpus; measure fidelity vs. corpus
      size (the scaling curve = the paper figure).
- [ ] RC-causal streaming path on the large corpus.
- [ ] New interactive viewer (clock face + charge flow + audio).
- [ ] Literature-validation doc (70_).
