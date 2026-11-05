# Development history

This timeline records the project evolution based on the available conversation records and source files. It deliberately distinguishes original source snapshots from milestones that are documented but whose complete files are not currently available.

## Initial prototype — 4 October 2026
**Status: milestone documented; no complete source snapshot recovered.**

The first prototype established the teacher/server and student/client structure for classroom voting over a local network. The initial design used TCP communication and planned support for a teacher PC plus up to 16 student PCs.

## V2 — 4 October 2026
**Status: historical code snapshot partially recovered.**

The V2 design included:
- Automatic student computer IDs derived from the last IPv4 octet (PC-01 to PC-16)
- English/Persian interface
- Anonymous and named voting modes
- No live result totals; show final results after the teacher ends voting
- Duplicate-vote prevention
- JSON messages over the LAN

A historical code document was found, but the complete matching set of teacher and student files could not be verified. It is therefore not represented as a complete runnable release.

## V4 — 17 October 2026
**Status: release package reported in conversation; original ZIP not currently available in this upload.**

The V4 package was described as including:
- Teacher and student applications plus configuration and README
- Revoting
- Aggregate student final results
- Four-option quiz
- 1–10 rating with comments
- Average rating and per-PC enable/disable controls

The original V4 ZIP was not available in the current upload, so this repository does not fabricate a V4 source archive.

## V5 and V5.1 — late October 2026
**Status: V5.1 source package available; V5 intermediate source package not recovered.**

The V5/V5.1 development added a timed exam workflow and further interface/network refinements. The current V5.1 package contains:
- `teacher_server.py`
- `student_client.py`
- `config.json`
- `README.txt`

The V5.1 archive is preserved under `releases/V5.1/`. The configured teacher IP has been cleared from the archived copy so a classroom-specific private LAN address is not accidentally treated as a universal default.

## How to read this history
- A milestone entry is not proof that its original source files are present.
- Only an explicitly labelled source snapshot should be treated as a recoverable historical code version.
- Future releases should be added as separate versioned folders and Git tags, with a short changelog and test notes.
