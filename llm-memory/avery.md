# Avery Lockwood

- Pronouns: she/her.
- Industrial arts instructor, fabricator, and engineering student (mechanical
  E + computer E).
- Builds her own lab equipment, including a sputter/PVD deposition rig
  ("Simple-Sputter-Coater" — used for the PB-1 memristor head daughterboard
  process, see 30_design_rules_hardware.md).
- Hardware control plane of choice: ESP32.
- Works solo on this project; sessions are long single-day pushes (v4→v12
  happened in one day, 2026-07-25).

## Note on a missing file
00_CRITICAL_v2.md (line 4) references `40_collaborator_avery.md` as an
existing, unchanged file with more detail on Avery — but that file is not
present in the project directory as of 2026-07-25. Either it exists
elsewhere (a different session/machine) or it was lost. Worth asking Avery
directly rather than assuming; don't fabricate its contents. If she provides
it, add it here or restore it as its own numbered file and update this note.

## Working style (inferred from the docs, confirm with her over time)
- Runs long simulation sessions and packages results into a numbered-doc
  bundle (00_CRITICAL, 10_findings, 20_methods, 30_design_rules,
  50_queue) plus notebooks — treat that structure as the project's own
  convention, keep using it rather than inventing a new one.
- Cares a lot about statistical rigor (CRN, paired tests, retracting
  findings that don't survive scrutiny — see F2 in 10_findings_v2.md).
  Don't round off "retracted" or "thinned" findings back up to confident
  claims.
- Has a queued item explicitly marked "do not start" (P3, memristor
  transformer) — respect priority ordering in 50_investigation_queue.md,
  don't jump ahead to P3 work unassigned.
