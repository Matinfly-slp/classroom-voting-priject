import json
import socket
import threading
import time
import tkinter as tk
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().with_name("config.json")
DEFAULT_TCP_PORT = 5000
DEFAULT_DISCOVERY_PORT = 5001
DEFAULT_MAX_STUDENTS = 16
DEFAULT_RECONNECT_SECONDS = 2
DISCOVERY_TIMEOUT = 1.2
DISCOVERY_FAILURES_BEFORE_MANUAL = 2

TEXTS = {
    "en": {
        "title": "Classroom Voting", "searching": "Searching for teacher...", "connecting": "Connecting...",
        "connected": "Connected", "offline": "Teacher not found", "reconnecting": "Connection lost — retrying...",
        "waiting": "Waiting for the next question", "question": "QUESTION", "yes": "YES", "no": "NO",
        "submit": "SUBMIT VOTE", "submitted": "Vote submitted", "end": "Voting ended", "language": "EN | فارسی",
        "select": "Select your answer", "auto_failed": "Automatic discovery failed.",
        "use_config": "Use configured IP", "retry": "Retry discovery", "config_missing": "config.json not found",
        "config_invalid": "teacher_ip in config.json is invalid", "computer": "Computer", "quiz_option": "Option", "rating": "Choose a rating from 1 to 10", "feedback": "Your comment or suggestion (optional)", "revote": "You can change your answer until voting ends", "blocked": "Voting is disabled for this computer", "results": "FINAL RESULTS", "total": "Total responses", "average": "Average rating", "comments": "Student feedback", "close": "CLOSE", "option": "Option", "exam": "EXAM", "previous": "PREVIOUS", "next": "NEXT", "finish_exam": "SUBMIT EXAM", "time_left": "Time left", "question_number": "Question", "exam_duration_summary": "Exam duration", "responses_summary": "Responses"
    },
    "fa": {
        "title": "رأی‌گیری کلاس", "searching": "در حال جست‌وجوی معلم...", "connecting": "در حال اتصال...",
        "connected": "متصل شد", "offline": "معلم پیدا نشد", "reconnecting": "ارتباط قطع شد — تلاش مجدد...",
        "waiting": "در انتظار سؤال بعدی", "question": "سؤال", "yes": "بله", "no": "خیر",
        "submit": "ثبت رأی", "submitted": "رأی ثبت شد", "end": "رأی‌گیری پایان یافت", "language": "فارسی | EN",
        "select": "پاسخ خود را انتخاب کنید", "auto_failed": "جست‌وجوی خودکار ناموفق بود.",
        "use_config": "استفاده از IP تنظیم‌شده", "retry": "تلاش دوباره", "config_missing": "config.json پیدا نشد",
        "config_invalid": "teacher_ip در config.json معتبر نیست", "computer": "رایانه", "quiz_option": "گزینه", "rating": "امتیاز خود را از ۱ تا ۱۰ انتخاب کنید", "feedback": "نظر یا پیشنهاد شما (اختیاری)", "revote": "تا پایان رأی‌گیری می‌توانید پاسخ خود را تغییر دهید", "blocked": "رأی‌دادن برای این رایانه غیرفعال است", "results": "نتیجه نهایی", "total": "کل پاسخ‌ها", "average": "میانگین امتیاز", "comments": "نظرهای دانش‌آموزان", "close": "بستن", "option": "گزینه", "exam": "آزمون", "previous": "قبلی", "next": "بعدی", "finish_exam": "ثبت آزمون", "time_left": "زمان باقی‌مانده", "question_number": "سؤال", "exam_duration_summary": "زمان آزمون", "responses_summary": "پاسخ‌ها"
    }
}


def load_config():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    return {
        "teacher_ip": str(data.get("teacher_ip", "")).strip(),
        "tcp_port": int(data.get("tcp_port", DEFAULT_TCP_PORT)),
        "discovery_port": int(data.get("discovery_port", DEFAULT_DISCOVERY_PORT)),
        "max_students": int(data.get("max_students", DEFAULT_MAX_STUDENTS)),
        "reconnect_seconds": float(data.get("reconnect_seconds", DEFAULT_RECONNECT_SECONDS)),
    }


def computer_id_from_ip(ip, max_students):
    try:
        last = int(ip.split(".")[-1])
        if 1 <= last <= max_students:
            return f"PC-{last:02d}"
    except Exception:
        pass
    return "PC-??"


class StudentClient:
    def __init__(self, root):
        self.root = root
        self.language = "en"
        self.running = True
        self.sock = None
        self.teacher_ip = None
        self.computer_id = "PC-??"
        self.connected = False
        self.voting = False
        self.question_text = ""
        self.selected_vote = None
        self.vote_submitted = False
        self.question_type = "yes_no"
        self.comments_enabled = False
        self.exam_questions = []
        self.exam_answers = {}
        self.exam_index = 0
        self.exam_window = None
        self.exam_timer_job = None
        self.exam_deadline = None
        self.allowed_to_vote = True
        self.choice_widgets = {}
        self.discovery_failures = 0
        self.manual_mode = False
        self.config = load_config()

        self.tcp_port = self.config["tcp_port"]
        self.discovery_port = self.config["discovery_port"]
        self.max_students = self.config["max_students"]
        self.reconnect_seconds = self.config["reconnect_seconds"]

        self.root.title(self.t("title"))
        self.root.geometry("760x520")
        self.root.minsize(680, 470)
        self.root.configure(bg="#0f172a")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.build_ui()
        self.set_status("searching")
        threading.Thread(target=self.connection_manager, daemon=True).start()

    def t(self, key):
        return TEXTS[self.language][key]

    def build_ui(self):
        self.header = tk.Frame(self.root, bg="#111827", height=82)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(self.header, text=self.t("title"), font=("Segoe UI", 22, "bold"), fg="white", bg="#111827")
        self.title_label.pack(side="left", padx=28)

        self.lang_btn = tk.Button(self.header, text=self.t("language"), command=self.switch_language,
                                  font=("Segoe UI", 10, "bold"), fg="white", bg="#334155",
                                  activebackground="#475569", activeforeground="white", relief="flat",
                                  padx=14, pady=7, cursor="hand2")
        self.lang_btn.pack(side="right", padx=20)

        self.status_frame = tk.Frame(self.root, bg="#0f172a")
        self.status_frame.pack(fill="x", padx=28, pady=(20, 8))
        self.status_dot = tk.Label(self.status_frame, text="●", font=("Segoe UI", 15, "bold"), fg="#f59e0b", bg="#0f172a")
        self.status_dot.pack(side="left")
        self.status_label = tk.Label(self.status_frame, text="", font=("Segoe UI", 11, "bold"), fg="#cbd5e1", bg="#0f172a")
        self.status_label.pack(side="left", padx=8)
        self.pc_label = tk.Label(self.status_frame, text="PC-??", font=("Segoe UI", 11, "bold"), fg="#93c5fd", bg="#0f172a")
        self.pc_label.pack(side="right")

        self.card = tk.Frame(self.root, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        self.card.pack(fill="both", expand=True, padx=28, pady=(8, 28))

        self.question_caption = tk.Label(self.card, text=self.t("question"), font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b")
        self.question_caption.pack(anchor="w", padx=28, pady=(28, 8))
        self.question_label = tk.Label(self.card, text=self.t("waiting"), font=("Segoe UI", 23, "bold"), fg="white", bg="#1e293b", wraplength=650, justify="center")
        self.question_label.pack(fill="x", padx=28, pady=(5, 18))
        self.select_label = tk.Label(self.card, text=self.t("select"), font=("Segoe UI", 10), fg="#94a3b8", bg="#1e293b")
        self.select_label.pack(pady=(0, 12))

        self.buttons_frame = tk.Frame(self.card, bg="#1e293b")
        self.buttons_frame.pack(pady=4)
        self.yes_btn = tk.Button(self.buttons_frame, text=self.t("yes"), command=lambda: self.select_vote("YES"),
                                 font=("Segoe UI", 18, "bold"), width=10, height=2, relief="flat", bg="#334155", fg="#94a3b8",
                                 activebackground="#16a34a", activeforeground="white", cursor="hand2", state="disabled")
        self.yes_btn.grid(row=0, column=0, padx=10)
        self.no_btn = tk.Button(self.buttons_frame, text=self.t("no"), command=lambda: self.select_vote("NO"),
                                font=("Segoe UI", 18, "bold"), width=10, height=2, relief="flat", bg="#334155", fg="#94a3b8",
                                activebackground="#dc2626", activeforeground="white", cursor="hand2", state="disabled")
        self.no_btn.grid(row=0, column=1, padx=10)
        self.comment_frame = tk.Frame(self.card, bg="#1e293b")
        self.comment_label = tk.Label(self.comment_frame, text=self.t("feedback"), font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b")
        self.comment_label.pack(anchor="w", padx=4, pady=(4, 3))
        self.comment_text = tk.Text(self.comment_frame, height=2, wrap="word", font=("Segoe UI", 10), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        self.comment_text.pack(fill="x", padx=4, pady=(0, 4))

        self.submit_btn = tk.Button(self.card, text=self.t("submit"), command=self.submit_vote,
                                    font=("Segoe UI", 12, "bold"), relief="flat", bg="#2563eb", fg="#94a3b8",
                                    activebackground="#1d4ed8", activeforeground="white", padx=28, pady=10, cursor="hand2", state="disabled")
        self.submit_btn.pack(pady=(22, 24))

        self.manual_panel = tk.Frame(self.root, bg="#1e293b", highlightthickness=1, highlightbackground="#475569")
        self.manual_text = tk.Label(self.manual_panel, text=self.t("auto_failed"), font=("Segoe UI", 9), fg="#cbd5e1", bg="#1e293b")
        self.manual_text.pack(side="left", padx=(12, 8), pady=8)
        self.use_config_btn = tk.Button(self.manual_panel, text=self.t("use_config"), command=self.use_config_ip,
                                        font=("Segoe UI", 9, "bold"), fg="white", bg="#2563eb", activebackground="#1d4ed8", relief="flat", padx=10, pady=5, cursor="hand2")
        self.use_config_btn.pack(side="left", padx=4, pady=6)
        self.retry_btn = tk.Button(self.manual_panel, text=self.t("retry"), command=self.retry_discovery,
                                   font=("Segoe UI", 9, "bold"), fg="white", bg="#334155", activebackground="#475569", relief="flat", padx=10, pady=5, cursor="hand2")
        self.retry_btn.pack(side="left", padx=4, pady=6)

    def set_status(self, state):
        def update():
            mapping = {
                "searching": (self.t("searching"), "#f59e0b"),
                "connecting": (self.t("connecting"), "#38bdf8"),
                "connected": (self.t("connected"), "#22c55e"),
                "reconnecting": (self.t("reconnecting"), "#f97316"),
                "offline": (self.t("offline"), "#ef4444")
            }
            text, dot = mapping.get(state, mapping["offline"])
            self.status_label.config(text=text)
            self.status_dot.config(fg=dot)
        self.root.after(0, update)

    def switch_language(self):
        self.language = "fa" if self.language == "en" else "en"
        self.root.title(self.t("title"))
        self.title_label.config(text=self.t("title"))
        self.lang_btn.config(text=self.t("language"))
        self.question_caption.config(text=self.t("question"))
        self.select_label.config(text=self.t("select"))
        self.submit_btn.config(text=self.t("submit") if not self.vote_submitted else self.t("submitted"))
        self.manual_text.config(text=self.t("auto_failed"))
        self.use_config_btn.config(text=self.t("use_config"))
        self.retry_btn.config(text=self.t("retry"))
        self.comment_label.config(text=self.t("feedback"))
        if not self.question_text:
            self.question_label.config(text=self.t("waiting"))
        else:
            self.select_label.config(text=self.t("rating") if self.question_type.startswith("rating") else self.t("select"))
            self.render_choices()
            self.apply_access_state()

    def show_manual_panel(self):
        if not self.manual_panel.winfo_ismapped():
            self.manual_panel.pack(fill="x", padx=28, pady=(0, 10), before=self.card)

    def hide_manual_panel(self):
        if self.manual_panel.winfo_ismapped():
            self.manual_panel.pack_forget()

    def retry_discovery(self):
        self.manual_mode = False
        self.discovery_failures = 0
        self.hide_manual_panel()
        self.set_status("searching")

    def use_config_ip(self):
        self.config = load_config()
        ip = self.config.get("teacher_ip", "").strip()
        if not ip:
            self.manual_text.config(text=self.t("config_missing"))
            return
        try:
            socket.inet_aton(ip)
        except OSError:
            self.manual_text.config(text=self.t("config_invalid"))
            return
        self.tcp_port = self.config.get("tcp_port", DEFAULT_TCP_PORT)
        self.reconnect_seconds = self.config.get("reconnect_seconds", DEFAULT_RECONNECT_SECONDS)
        self.teacher_ip = ip
        self.manual_mode = True
        self.hide_manual_panel()
        self.set_status("connecting")

    def discover_teacher(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(DISCOVERY_TIMEOUT)
        try:
            sock.bind(("", 0))
            payload = json.dumps({"type": "discover", "app": "ClassroomVoting"}).encode()
            sock.sendto(payload, ("255.255.255.255", self.discovery_port))
            while self.running:
                try:
                    data, addr = sock.recvfrom(2048)
                except socket.timeout:
                    break
                try:
                    msg = json.loads(data.decode())
                except Exception:
                    continue
                if msg.get("type") == "teacher_here":
                    return msg.get("ip") or addr[0]
        except OSError:
            return None
        finally:
            sock.close()
        return None

    def connection_manager(self):
        while self.running:
            if self.sock is not None:
                time.sleep(0.25)
                continue

            if self.manual_mode:
                ip = self.teacher_ip or self.config.get("teacher_ip", "")
                if not ip:
                    self.show_manual_panel()
                    self.set_status("offline")
                    time.sleep(self.reconnect_seconds)
                    continue
            else:
                self.set_status("searching")
                ip = self.discover_teacher()
                if not self.running:
                    break
                if not ip:
                    self.discovery_failures += 1
                    if self.discovery_failures >= DISCOVERY_FAILURES_BEFORE_MANUAL:
                        self.show_manual_panel()
                    time.sleep(self.reconnect_seconds)
                    continue
                self.discovery_failures = 0
                self.teacher_ip = ip
                self.hide_manual_panel()

            self.set_status("connecting")
            try:
                s = socket.create_connection((self.teacher_ip, self.tcp_port), timeout=3)
                s.settimeout(None)
                self.sock = s
                local_ip = s.getsockname()[0]
                self.computer_id = computer_id_from_ip(local_ip, self.max_students)
                self.root.after(0, lambda cid=self.computer_id: self.pc_label.config(text=cid))
                self.send({"type": "identify", "computer_id": self.computer_id})
                self.connected = True
                self.set_status("connected")
                self.read_loop(s)
            except Exception:
                self.close_socket()
                self.connected = False
                self.set_status("reconnecting")
                time.sleep(self.reconnect_seconds)

    def read_loop(self, sock):
        buffer = b""
        try:
            while self.running:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        msg = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue
                    self.handle_message(msg)
        except OSError:
            pass
        finally:
            self.close_socket()
            self.connected = False
            self.voting = False
            self.root.after(0, self.disable_voting_ui)

    def handle_message(self, msg):
        typ = msg.get("type")
        if typ == "server_status":
            self.allowed_to_vote = bool(msg.get("allowed", True))
            if msg.get("voting"):
                self.start_question(msg.get("question", ""), msg.get("question_type", "yes_no"), msg.get("comments_enabled", False), msg.get("exam_questions", []), msg.get("duration_seconds", 0), msg.get("exam_answers", {}))
            else:
                self.root.after(0, self.show_waiting)
                if msg.get("results"):
                    self.root.after(150, lambda data=msg.get("results"): self.show_student_results(data))
            self.root.after(0, self.apply_access_state)
        elif typ == "start_voting":
            self.allowed_to_vote = True
            self.start_question(msg.get("question", ""), msg.get("question_type", "yes_no"), msg.get("comments_enabled", False), msg.get("exam_questions", []), msg.get("duration_seconds", 0), msg.get("exam_answers", {}))
        elif typ == "access_status":
            self.allowed_to_vote = bool(msg.get("allowed", True))
            self.root.after(0, self.apply_access_state)
        elif typ == "vote_ack":
            self.vote_submitted = True
            self.root.after(0, self.update_submitted_state)
        elif typ == "end_voting":
            self.root.after(0, self.finish_voting)
        elif typ == "final_results":
            self.root.after(0, lambda data=msg.get("results", {}): self.show_student_results(data))

    def start_question(self, question, question_type="yes_no", comments_enabled=False, exam_questions=None, duration_seconds=0, exam_answers=None):
        self.question_text = question or ""
        self.question_type = question_type if question_type in ("yes_no", "quiz", "exam", "rating") else "yes_no"
        self.comments_enabled = bool(comments_enabled)
        self.voting = bool(self.question_text)
        self.selected_vote = None
        self.vote_submitted = False
        if self.question_type == "exam":
            self.exam_questions = exam_questions or []
            self.exam_answers = {int(k): v for k, v in (exam_answers or {}).items() if str(k).isdigit()}
            self.exam_index = 0
            self.exam_deadline = time.monotonic() + max(1, int(duration_seconds or 600))
            self.root.after(0, self.open_exam_window)
            return
        def update():
            self.root.geometry("760x600" if self.comments_enabled else "760x520")
            self.question_label.config(text=self.question_text or self.t("waiting"))
            self.select_label.config(text=self.t("rating") if self.question_type.startswith("rating") else self.t("select"))
            self.comment_text.config(state="normal")
            self.comment_text.delete("1.0", "end")
            if self.comments_enabled:
                self.comment_frame.pack(fill="x", padx=24, pady=(8, 0), before=self.submit_btn)
            else:
                self.comment_frame.pack_forget()
            self.render_choices()
            self.submit_btn.config(state="disabled", text=self.t("submit"), fg="#94a3b8")
            self.apply_access_state()
        self.root.after(0, update)

    def open_exam_window(self):
        if not self.exam_questions:
            self.question_label.config(text=self.t("waiting"))
            return
        if self.exam_window and self.exam_window.winfo_exists():
            self.exam_window.destroy()
        win=tk.Toplevel(self.root)
        self.exam_window=win
        win.title(self.t("exam"))
        win.geometry("850x650")
        win.minsize(700,560)
        win.configure(bg="#0f172a")
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        header=tk.Frame(win,bg="#111827")
        header.pack(fill="x")
        tk.Label(header,text=self.t("exam"),font=("Segoe UI",18,"bold"),fg="white",bg="#111827").pack(side="left",padx=20,pady=14)
        self.exam_timer_label=tk.Label(header,text="",font=("Segoe UI",12,"bold"),fg="#fbbf24",bg="#111827")
        self.exam_timer_label.pack(side="right",padx=20)
        self.exam_progress_label=tk.Label(win,text="",font=("Segoe UI",10,"bold"),fg="#93c5fd",bg="#0f172a")
        self.exam_progress_label.pack(anchor="w",padx=24,pady=(18,6))
        self.exam_question_label=tk.Label(win,text="",font=("Segoe UI",17,"bold"),fg="white",bg="#1e293b",wraplength=760,justify="left",padx=18,pady=18)
        self.exam_question_label.pack(fill="x",padx=22,pady=8)
        self.exam_choices_frame=tk.Frame(win,bg="#0f172a")
        self.exam_choices_frame.pack(fill="x",padx=22,pady=10)
        self.exam_choice_vars=tk.StringVar(value="")
        self.exam_comment_frame=tk.Frame(win,bg="#1e293b")
        self.exam_comment_label=tk.Label(self.exam_comment_frame,text=self.t("feedback"),font=("Segoe UI",10),fg="#cbd5e1",bg="#1e293b")
        self.exam_comment_label.pack(anchor="w",padx=12,pady=(10,4))
        self.exam_comment_text=tk.Text(self.exam_comment_frame,height=4,wrap="word",font=("Segoe UI",10),bg="#0f172a",fg="white",insertbackground="white",relief="flat")
        self.exam_comment_text.pack(fill="x",padx=12,pady=(0,10))
        self.exam_comment_text.bind("<FocusOut>", lambda _event: self.save_exam_current())
        self.exam_comment_text.bind("<KeyRelease>", lambda _event: self.save_exam_current())
        if self.comments_enabled:
            self.exam_comment_frame.pack(fill="x",padx=22,pady=8)
        nav=tk.Frame(win,bg="#0f172a")
        nav.pack(fill="x",padx=22,pady=14)
        self.exam_prev_btn=tk.Button(nav,text=self.t("previous"),command=lambda:self.change_exam_question(-1),bg="#334155",fg="white",relief="flat",padx=14,pady=9)
        self.exam_prev_btn.pack(side="left")
        self.exam_next_btn=tk.Button(nav,text=self.t("next"),command=lambda:self.change_exam_question(1),bg="#334155",fg="white",relief="flat",padx=14,pady=9)
        self.exam_next_btn.pack(side="left",padx=8)
        self.exam_finish_btn=tk.Button(nav,text=self.t("finish_exam"),command=self.finish_exam_early,bg="#2563eb",fg="white",relief="flat",padx=18,pady=9)
        self.exam_finish_btn.pack(side="right")
        self.render_exam_question()
        self.update_exam_timer()

    def save_exam_current(self):
        if not self.exam_questions or not self.exam_window or not self.exam_window.winfo_exists():
            return
        answer=self.exam_choice_vars.get()
        old=self.exam_answers.get(self.exam_index,{})
        comment=self.exam_comment_text.get("1.0","end").strip()[:1000] if self.comments_enabled else ""
        if answer:
            self.exam_answers[self.exam_index]={"answer":answer,"comment":comment}
            self.send({"type":"exam_answer","question_index":self.exam_index,"answer":answer,"comment":comment})
        elif comment:
            # Comments are associated with an answer; keep the comment locally until an option is selected.
            self.exam_answers[self.exam_index]={"answer":old.get("answer"),"comment":comment}

    def render_exam_question(self):
        if not self.exam_questions or not self.exam_window or not self.exam_window.winfo_exists(): return
        q=self.exam_questions[self.exam_index]
        self.exam_progress_label.config(text=f"{self.t('question_number')} {self.exam_index+1} / {len(self.exam_questions)}")
        self.exam_question_label.config(text=q.get("question", ""))
        self.exam_choice_vars.set("")
        for child in list(self.exam_choices_frame.winfo_children()): child.destroy()
        old=self.exam_answers.get(self.exam_index,{})
        self.exam_choice_vars.set(str(old.get("answer", "")))
        for i, option in enumerate(q.get("options", ["1","2","3","4"]),1):
            rb=tk.Radiobutton(self.exam_choices_frame,text=f"{i}.  {option}",value=str(i),variable=self.exam_choice_vars,command=self.save_exam_current,font=("Segoe UI",12),bg="#1e293b",fg="white",selectcolor="#2563eb",activebackground="#1e293b",activeforeground="white",wraplength=700,justify="left",anchor="w",padx=12,pady=9)
            rb.pack(fill="x",pady=4)
            if not self.allowed_to_vote: rb.config(state="disabled")
        self.exam_comment_text.config(state="normal")
        self.exam_comment_text.delete("1.0","end")
        self.exam_comment_text.insert("1.0",old.get("comment", ""))
        if not self.comments_enabled or not self.allowed_to_vote: self.exam_comment_text.config(state="disabled")
        self.exam_prev_btn.config(state="normal" if self.exam_index>0 else "disabled")
        self.exam_next_btn.config(state="normal" if self.exam_index<len(self.exam_questions)-1 else "disabled")
        self.exam_finish_btn.config(state="normal" if self.allowed_to_vote else "disabled")

    def change_exam_question(self, delta):
        self.save_exam_current()
        new_index=self.exam_index+delta
        if 0 <= new_index < len(self.exam_questions):
            self.exam_index=new_index
            self.render_exam_question()

    def finish_exam_early(self):
        self.save_exam_current()
        if self.exam_window and self.exam_window.winfo_exists():
            self.exam_window.destroy()
        self.exam_window=None
        # The server remains authoritative and closes the exam for everyone when the teacher ends it.
        self.question_label.config(text="Exam submitted. You may wait for the teacher to end the exam.")

    def update_exam_timer(self):
        if not self.exam_window or not self.exam_window.winfo_exists() or not self.voting: return
        remaining=max(0,int(self.exam_deadline-time.monotonic()))
        self.exam_timer_label.config(text=f"{self.t('time_left')}: {remaining//60:02d}:{remaining%60:02d}")
        if remaining <= 0:
            self.save_exam_current()
            self.exam_finish_btn.config(state="disabled")
            self.exam_timer_label.config(text="00:00")
            return
        self.exam_timer_job=self.root.after(500,self.update_exam_timer)

    def render_choices(self):
        for child in list(self.buttons_frame.winfo_children()):
            child.destroy()
        self.choice_widgets = {}
        if self.question_type == "yes_no":
            choices = [("YES", self.t("yes")), ("NO", self.t("no"))]
            columns = 2
        elif self.question_type == "quiz":
            choices = [(str(i), f"{self.t('option')} {i}") for i in range(1, 5)]
            columns = 4
        else:
            choices = [(str(i), str(i)) for i in range(1, 11)]
            columns = 5
        for idx, (value, label) in enumerate(choices):
            width = 10 if self.question_type == "yes_no" else 5
            btn = tk.Button(self.buttons_frame, text=label, command=lambda v=value: self.select_vote(v),
                            font=("Segoe UI", 16 if self.question_type == "yes_no" else 12, "bold"),
                            width=width, height=2 if self.question_type == "yes_no" else 1,
                            relief="flat", bg="#334155", fg="white", activebackground="#2563eb",
                            activeforeground="white", cursor="hand2", state="disabled")
            btn.grid(row=idx // columns, column=idx % columns, padx=5, pady=5, sticky="nsew")
            self.choice_widgets[value] = btn

    def show_waiting(self):
        self.voting = False
        self.question_text = ""
        self.selected_vote = None
        self.vote_submitted = False
        self.disable_voting_ui()

    def disable_voting_ui(self):
        self.voting = False
        if self.exam_timer_job is not None:
            try: self.root.after_cancel(self.exam_timer_job)
            except Exception: pass
            self.exam_timer_job = None
        if self.exam_window and self.exam_window.winfo_exists():
            self.exam_window.destroy()
        self.exam_window = None
        self.question_label.config(text=self.t("waiting"))
        for btn in self.choice_widgets.values():
            btn.config(state="disabled", bg="#334155", fg="#94a3b8")
        self.submit_btn.config(state="disabled", fg="#94a3b8")
        self.comment_text.config(state="disabled")

    def apply_access_state(self):
        if not self.allowed_to_vote:
            self.select_label.config(text=self.t("blocked"))
        elif self.question_text:
            self.select_label.config(text=self.t("rating") if self.question_type.startswith("rating") else self.t("select"))
        state = "normal" if self.voting and self.allowed_to_vote and self.question_type != "exam" else "disabled"
        for btn in self.choice_widgets.values():
            btn.config(state=state)
        self.comment_text.config(state="normal" if self.voting and self.allowed_to_vote and self.comments_enabled and self.question_type != "exam" else "disabled")
        if not self.allowed_to_vote:
            self.submit_btn.config(state="disabled")
        if self.question_type == "exam" and self.exam_window and self.exam_window.winfo_exists():
            self.render_exam_question()

    def finish_voting(self):
        self.voting = False
        if self.exam_timer_job is not None:
            try: self.root.after_cancel(self.exam_timer_job)
            except Exception: pass
            self.exam_timer_job = None
        if self.exam_window and self.exam_window.winfo_exists():
            self.exam_window.destroy()
        self.exam_window = None
        self.selected_vote = None
        self.question_label.config(text=self.t("end"))
        for btn in self.choice_widgets.values():
            btn.config(state="disabled")
        self.submit_btn.config(state="disabled", fg="#94a3b8")
        self.comment_text.config(state="disabled")

    def select_vote(self, vote):
        if not self.voting or not self.allowed_to_vote:
            return
        self.selected_vote = vote
        for value, btn in self.choice_widgets.items():
            btn.config(bg="#2563eb" if value == vote else "#334155", fg="white")
        self.submit_btn.config(state="normal", fg="white", text=self.t("submit"))

    def submit_vote(self):
        if not self.voting or not self.allowed_to_vote or self.selected_vote is None:
            return
        payload = {"type": "vote", "vote": self.selected_vote}
        if self.comments_enabled:
            payload["comment"] = self.comment_text.get("1.0", "end").strip()[:1000]
        if self.send(payload):
            self.vote_submitted = True
            self.submit_btn.config(state="normal", text=self.t("submitted"), fg="white")
            # Keep choices enabled: submitting again replaces the previous answer on the server.
            self.apply_access_state()

    def update_submitted_state(self):
        if self.voting and self.allowed_to_vote:
            self.submit_btn.config(state="normal", text=self.t("submitted"), fg="white")

    def show_student_results(self, data):
        win = tk.Toplevel(self.root)
        win.title(self.t("results"))
        win.geometry("560x520")
        win.minsize(460, 420)
        win.configure(bg="#0f172a")
        tk.Label(win, text=self.t("results"), font=("Segoe UI", 20, "bold"), fg="white", bg="#0f172a").pack(pady=(20, 8))
        tk.Label(win, text=data.get("question", ""), font=("Segoe UI", 12), fg="#cbd5e1", bg="#0f172a", wraplength=490).pack(padx=20, pady=(0, 12))
        kind = data.get("question_type", "yes_no")
        if kind == "exam":
            results_outer = tk.Frame(win, bg="#0f172a")
            results_outer.pack(fill="both", expand=True, padx=22, pady=8)
            results_canvas = tk.Canvas(results_outer, bg="#1e293b", highlightthickness=0)
            results_scroll = tk.Scrollbar(results_outer, orient="vertical", command=results_canvas.yview)
            panel = tk.Frame(results_canvas, bg="#1e293b")
            panel.bind("<Configure>", lambda _e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))
            results_canvas.create_window((0, 0), window=panel, anchor="nw")
            results_canvas.configure(yscrollcommand=results_scroll.set)
            results_canvas.pack(side="left", fill="both", expand=True)
            results_scroll.pack(side="right", fill="y")
            results_canvas.bind("<Configure>", lambda e: results_canvas.itemconfigure(results_canvas.find_all()[0], width=e.width))
            tk.Label(panel, text=f"{self.t('exam_duration_summary')}: {data.get('duration_minutes', 0)} min | {self.t('responses_summary')}: {data.get('total', 0)}", font=("Segoe UI", 11, "bold"), fg="#93c5fd", bg="#1e293b", wraplength=500).pack(pady=8)
            for index, item in enumerate(data.get("exam_questions", []), 1):
                tk.Label(panel, text=f"Q{index}. {item.get('question', '')}", font=("Segoe UI", 10, "bold"), fg="white", bg="#1e293b", wraplength=480, justify="left").pack(anchor="w", padx=10, pady=(7, 2))
                tk.Label(panel, text="   |   ".join(f"{i}: {item.get('counts', {}).get(str(i), 0)}" for i in range(1,5)), font=("Segoe UI", 9), fg="#cbd5e1", bg="#1e293b").pack(anchor="w", padx=10)
        elif kind == "yes_no":
            panel = tk.Frame(win, bg="#1e293b")
            panel.pack(fill="x", padx=22, pady=8)
            counts = data.get("counts", {})
            pct = data.get("percentages", {})
            tk.Label(panel, text=f"{self.t('yes')}: {counts.get('YES', 0)} ({pct.get('YES', 0):.1f}%)", font=("Segoe UI", 13, "bold"), fg="#86efac", bg="#1e293b").pack(pady=5)
            tk.Label(panel, text=f"{self.t('no')}: {counts.get('NO', 0)} ({pct.get('NO', 0):.1f}%)", font=("Segoe UI", 13, "bold"), fg="#fca5a5", bg="#1e293b").pack(pady=5)
        elif kind == "quiz":
            panel = tk.Frame(win, bg="#1e293b")
            panel.pack(fill="x", padx=22, pady=8)
            for option in ("1", "2", "3", "4"):
                tk.Label(panel, text=f"{self.t('option')} {option}: {data.get('counts', {}).get(option, 0)}", font=("Segoe UI", 12, "bold"), fg="#cbd5e1", bg="#1e293b").pack(pady=3)
        else:
            panel = tk.Frame(win, bg="#1e293b")
            panel.pack(fill="x", padx=22, pady=8)
            tk.Label(panel, text=f"{self.t('average')}: {data.get('average', 0):.2f} / 10", font=("Segoe UI", 15, "bold"), fg="#93c5fd", bg="#1e293b").pack(pady=7)
            tk.Label(panel, text=f"{self.t('total')}: {data.get('total', 0)}", font=("Segoe UI", 10), fg="#cbd5e1", bg="#1e293b").pack(pady=(0, 8))
        comments = data.get("comments", [])
        if comments:
            box = tk.Frame(win, bg="#1e293b")
            box.pack(fill="both", expand=True, padx=22, pady=8)
            tk.Label(box, text=self.t("comments"), font=("Segoe UI", 10, "bold"), fg="white", bg="#1e293b").pack(anchor="w", padx=10, pady=6)
            txt = tk.Text(box, height=7, bg="#0b1220", fg="#e2e8f0", wrap="word", relief="flat", font=("Segoe UI", 9))
            txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            for item in comments:
                txt.insert("end", (item.get("computer", "•") + ": " if "computer" in item else "• ") + item.get("text", "") + "\n\n")
            txt.config(state="disabled")
        tk.Button(win, text=self.t("close"), command=win.destroy, font=("Segoe UI", 10, "bold"), bg="#334155", fg="white", relief="flat", padx=25, pady=8).pack(pady=12)

    def send(self, msg):
        if self.sock is None:
            return False
        try:
            self.sock.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
            return True
        except OSError:
            return False

    def close_socket(self):
        sock = self.sock
        self.sock = None
        if sock:
            try:
                sock.close()
            except OSError:
                pass

    def on_close(self):
        self.running = False
        self.close_socket()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    StudentClient(root)
    root.mainloop()