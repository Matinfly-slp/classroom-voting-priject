# Development history

This timeline is based on prior project discussions and files that could be recovered. It distinguishes actual source snapshots from milestones that are only documented. No missing source code is fabricated.

## Initial prototype — 4 October 2026
**Status: milestone discussed; complete matching source snapshot not recovered.**

The project began as a teacher/server and student/client classroom voting system over a local wired network.

## V2-era implementation — 4 October 2026
**Status: partial historical code recovered; not a complete runnable release.**

The recovered code document shows:
- Automatic student computer IDs derived from the last IPv4 octet (PC-01 to PC-16)
- English/Persian interface
- Anonymous and named voting modes
- Results shown after the teacher ends voting, rather than live totals
- Duplicate-vote prevention
- JSON messages over the LAN

Only a partial code document is available, not a verified complete matching set of teacher and student files.

## Later V4/V5 development
**Status: features discussed across later iterations; exact version-to-feature mapping needs original archives.**

Subsequent discussions covered multiple question types, four-option quizzes, 1–10 ratings with comments, revoting, teacher-side student controls, and interface troubleshooting. A reliable complete V4 archive was not recovered, so these features are not assigned to a specific release tag here.

## V5.1 — supplied package
**Status: original V5.1 ZIP inspected; source files not yet committed in this repository.**

The supplied archive contains `teacher_server.py`, `student_client.py`, `config.json`, and `README.txt`. Its README describes LAN discovery and fallback, reconnection, multilingual UI, voting and rating modes, teacher controls, and a timed exam mode.

The archive's configuration contains a classroom-specific teacher IP; that value should be replaced with a neutral blank/default before publishing the configuration publicly.

## Repository policy for future releases
- Keep each complete release in its own folder, e.g. `releases/V5.1/`.
- Add a Git tag for every verified source release.
- Include a changelog and test notes with each release.
- Do not label a reconstructed or partial snapshot as an original release.
