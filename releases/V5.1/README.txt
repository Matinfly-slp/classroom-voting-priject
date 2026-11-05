Classroom Voting V5.1

This folder contains the V5.1 teacher server and student client source files.

Run teacher_server.py on the teacher computer and student_client.py on each student computer. Both applications use config.json beside the script. Configure Windows Firewall to allow TCP port 5000 and UDP discovery port 5001. The teacher and students must be on the same local network.

The teacher_ip setting is intentionally blank in this repository. The student client attempts automatic UDP discovery and can use a manually configured teacher IP if discovery is unavailable. Set teacher_ip in config.json to the teacher computer's LAN IPv4 address only when manual fallback is needed.

The original classroom-specific IP has been cleared to avoid publishing a local network address.
