# demo_pb2 provenance

This folder holds the **PB-2 / demo v13** work: scaling the v7 talking-clock
demo from 36 phrases to the full 720-minute natural-time space. See
`../60_demo_and_paper_goals.md` for the goal.

## Files lifted verbatim from the bundle notebooks (do not diverge silently)
These are byte-for-byte copies of the validated originals, extracted from
the notebooks so the new demo can `import` them and so they're
version-controlled outside the notebook JSON. If you change them, note it
here and consider whether the change belongs back in the notebook too.

| file | source |
|---|---|
| tts_chip_sim_v7.py | bundle_02_timedomain_tts.ipynb, code cell 6 (`%%writefile tts_chip_sim_v7.py`) |
| rc_context_v10.py  | bundle_02_timedomain_tts.ipynb, code cell 7 (`%%writefile rc_context_v10.py`) |
| build_viewer.py    | bundle_02_timedomain_tts.ipynb, code cell 8 (`%%writefile build_viewer.py`) |

`rc_context_v10.py` does `import tts_chip_sim_v7 as v7`, so both must sit in
the same dir / importable path (they do here).

## New files (this workstream)
| file | what |
|---|---|
| time_phrases.py | natural-English phrasing for all 720 clock minutes (pure stdlib, tested on host: 720 utterances, 35-word vocab) |
| build_corpus_v13.py | (draft) espeak/MBROLA + LPC analysis over all 720 phrasings, cached to corpus_v13.npz — needs the container (espeak-ng, mbrola-us1, numpy, scipy) |

## Note on the "mystery file" in 20_methods_env_v2.md
That doc records an unexplained `tts_chip_sim_v7.py` appearing mid-session in
a past run. This folder now has an *intentional*, provenance-tracked copy —
not the same event. Keep the habit of reviewing any unexplained file before
running it.
