# Development history

This timeline is based on prior project discussions and the files that could be recovered. It distinguishes committed source snapshots from milestones documented from earlier work. Missing source code is not reconstructed or presented as an original release.

## Initial prototype — 4 October 2026

**Status: milestone documented; complete matching source snapshot not recovered.**

The project began as a teacher/server and student/client classroom voting system operating over a local wired network.

## V2-era implementation — 4 October 2026

**Status: partial historical code recovered; not a complete runnable release.**

The recovered code document describes:

- Automatic student computer IDs derived from the last IPv4 octet (PC-01 to PC-16)
- English/Persian interface
- Anonymous and named voting modes
- Results displayed after the teacher ends voting rather than live totals
- Duplicate-vote prevention
- JSON messages over the LAN

Only a partial code document is available, not a verified complete matching set of teacher and student files.

## Later V4/V5 development

**Status: features discussed across later iterations; exact version-to-feature mapping is not fully established.**

Subsequent development discussions covered multiple question types, four-option quizzes, 1–10 ratings with comments, revoting, teacher-side student controls, and interface troubleshooting. A reliable complete V4 archive was not recovered, so these features are not assigned to a specific release tag.

## V5.1 — supplied package

**Status: source snapshot committed in this repository.**

The supplied V5.1 package contains:

- `teacher_server.py`
- `student_client.py`
- `config.json`
- `README.txt`

The package documentation describes LAN discovery and configured-IP fallback, reconnection, multilingual UI, voting and rating modes, teacher controls, and a timed exam mode.

The classroom-specific teacher IP was cleared from the committed `config.json`; the setting is intentionally blank so the repository does not expose a private LAN address.

## Repository and release policy

- Keep each complete source snapshot in its own folder, such as `releases/V5.1/`.
- Add a Git tag only for a clearly identified source release.
- Include a changelog and honest test notes with each release.
- Do not label reconstructed or partial code as an original release.
- Keep local network addresses, credentials, and other private configuration out of public commits.
