# Classroom Voting

A Python/Tkinter classroom voting and assessment system designed for a local wired LAN.

## Project status

This repository currently contains the project overview and a documented development timeline. The V5.1 source archive was inspected, but its Python files have **not yet been committed** here. Historical source snapshots for earlier versions are also not all recoverable.

## Planned V5.1 feature set (based on the supplied package README)
- Teacher dashboard and student client
- UDP teacher discovery with configured-IP fallback
- TCP communication and automatic reconnection
- Student computer identification as PC-01 through PC-16
- English/Persian interface
- Yes/No voting, four-option quiz, and 1–10 rating modes
- Optional comments and revoting
- Teacher-side student allow/block controls
- Timed exam mode with a teacher-controlled timer and answer key
- Aggregate student results

## Network defaults
- TCP: 5000
- UDP discovery: 5001
- Maximum student computers: 16

The teacher and student computers must be on the same local network. Configure Windows Firewall to allow the required TCP and UDP traffic.

## Development history

See [history/DEVELOPMENT_HISTORY.md](history/DEVELOPMENT_HISTORY.md) for the version timeline and the distinction between recoverable source snapshots and milestones documented from prior discussions.

## Important
This project has not been independently tested on every classroom network configuration. Test on the target LAN before classroom use.
