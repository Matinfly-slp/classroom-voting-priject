# Classroom Voting System

A Python desktop application for conducting classroom polls, quizzes, ratings, and timed assessments over a local area network (LAN).

> **Project status:** Portfolio prototype — V5.1 source code is included. This repository documents the project and its development history; it is not presented as a production-hardened or fully validated deployment.

## Overview

The project uses a teacher-hosted server and student clients to collect responses from computers connected to the same local network. It is designed for a classroom environment where student computers may not have internet access.

## Features documented for V5.1

- Teacher dashboard and student client built with Python and Tkinter
- English and Persian interface
- UDP-based teacher discovery with a configurable IP fallback
- TCP communication between the teacher and student applications
- Student computer identification for PC-01 through PC-16
- Anonymous and named voting modes
- Yes/No polls and four-option quizzes
- 1–10 rating questions with optional comments
- Timed exams containing multiple four-option questions
- Teacher controls for allowing or blocking individual student computers
- Reconnection handling and final-result display

These are the features described by the supplied V5.1 project package. They should not be interpreted as a claim that every feature has been independently validated on every network setup.

## Repository structure

```text
.
├── history/
│   └── DEVELOPMENT_HISTORY.md
├── releases/
│   └── V5.1/
│       ├── teacher_server.py
│       ├── student_client.py
│       ├── config.json
│       ├── README.txt
│       └── .gitignore
└── README.md
```

The V5.1 source files are committed in this repository. Earlier development stages are documented in the history file, but complete matching source snapshots for every earlier version were not recoverable. No missing releases have been fabricated.

## Getting started

### Requirements

- Python 3
- Tkinter (included with many standard Python distributions)
- Teacher and student computers connected to the same LAN

### Run from source

1. Download or clone this repository.
2. Open the `releases/V5.1/` directory.
3. Start `teacher_server.py` on the teacher computer.
4. Start `student_client.py` on each student computer.
5. If automatic discovery is unavailable, set `teacher_ip` in `config.json` to the teacher computer's LAN IPv4 address.

### Network configuration

| Setting | Default |
|---|---:|
| TCP communication port | 5000 |
| UDP discovery port | 5001 |
| Maximum student computers | 16 |

The applications are intended to communicate on the same local network. Windows Firewall may need inbound rules for TCP port 5000 and UDP port 5001.

## Testing and limitations

- The source files are included; packaged Windows executable files are not currently provided.
- The repository does not claim a complete 16-computer classroom acceptance test.
- Network behavior can depend on local firewall, router, and IP-address configuration.
- The application is a learning/portfolio prototype, not a security-hardened voting platform. Do not use it for sensitive, official, or high-stakes elections or assessments without further security and reliability work.

## Development history

See [DEVELOPMENT_HISTORY.md](history/DEVELOPMENT_HISTORY.md) for the documented milestones and the availability of historical source snapshots.

## Future improvements

- Add reproducible automated tests and a documented multi-client LAN test report
- Improve client authentication and transport security
- Add verified screenshots and a short demonstration
- Publish packaged builds and release notes when they are ready
- Recover and archive earlier complete source versions if available

---

**Maintainer:** [@Matinfly-slp](https://github.com/Matinfly-slp)
