# Classroom Voting

A Python/Tkinter classroom voting and assessment system for a local wired LAN.

## Current package: V5.1

The current source package is provided in `releases/V5.1/ClassroomVoting_Final_v5_1.zip`.

### Features documented for V5.1
- Teacher dashboard and student client
- Teacher discovery over UDP with configured-IP fallback
- TCP communication and automatic reconnection
- Student computer identification as PC-01 through PC-16
- English/Persian interface
- Yes/No voting, four-option quiz, and 1–10 rating modes
- Optional comments and revoting
- Teacher-side student allow/block controls
- Timed exam mode with a teacher-controlled timer and answer key
- Aggregate student results

### Network defaults
- TCP: 5000
- UDP discovery: 5001
- Maximum student computers: 16

The teacher computer and student computers must be on the same local network. Configure Windows Firewall to allow the required TCP and UDP traffic. The student PCs do not need internet access for LAN communication.

### Configuration
Edit `config.json` on the relevant computers when needed. The package's teacher IP fallback is intentionally left blank; normally the student client should discover the teacher automatically. If discovery is blocked, enter the teacher computer's LAN IPv4 address in the configuration file.

### Running from source
Requires Python 3 and Tkinter. Start `teacher_server.py` on the teacher computer and `student_client.py` on each student computer. For classroom deployment, build Windows executables with PyInstaller on a compatible Windows machine. See the package README for the original build notes.

### Important
This repository documents development history, but the historical milestones are not all preserved as complete source snapshots. Only versions with recoverable original files are labelled as source snapshots. The project has not been independently tested on every classroom network configuration; test on the target LAN before classroom use.

## Repository layout
- `releases/V5.1/` — current V5.1 package
- `history/DEVELOPMENT_HISTORY.md` — development milestones and source availability
