# llm-memory

Orientation folder for any LLM/assistant picking up this project cold. Read
these files at the start of a session before touching the numbered docs or
notebooks in the project root — they're the fast path to "what is this
project, who am I working with, and what's the current state."

| file | read for |
|---|---|
| avery.md | who Avery is, how she works, equipment she has |
| project_overview.md | what this project is, the thesis, why it's novel |
| current_state.md | status of findings as of the last session — confirmed/retracted/open |
| environment.md | how to reproduce, sandbox quirks, install gotchas |
| queue.md | what's next, in priority order |

These files summarize and point into the authoritative numbered docs in the
project root (00_CRITICAL_v2.md, 10_findings_v2.md, 20_methods_env_v2.md,
30_design_rules_hardware.md, 50_investigation_queue.md) and README_INDEX.md.
When the numbered docs get superseded (new version suffix, e.g. v2 → v3),
update this folder to match — these files should never contradict the
current numbered docs. Git history (`git log`) is authoritative for *when*
things changed; these files describe *current* state only.

Maintenance note: this folder was first created 2026-07-25, after the v4-v12
session, alongside setting up git for this project.
