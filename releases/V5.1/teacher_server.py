import json
import socket
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

CONFIG_FILE = Path(__file__).resolve().with_name("config.json")
HOST = "0.0.0.0"
DEFAULT_TCP_PORT = 5000
DEFAULT_DISCOVERY_PORT = 5001
DEFAULT_MAX_STUDENTS = 16

TEXTS = {
    "en": {
        "title": "Classroom Voting Dashboard", "question": "Question",
        "start": "START VOTING", "end": "END VOTING", "online": "SERVER ONLINE",
        "mode": "Voting mode", "anonymous": "Anonymous", "non_anonymous": "Non-Anonymous",
        "responses": "Responses", "students": "Students", "waiting": "WAITING", "voted": "VOTED",
        "connected": "CONNECTED", "not_connected": "OFFLINE", "final": "FINAL RESULTS",
        "total": "Total votes", "yes": "YES", "no": "NO", "close": "CLOSE",
        "question_required": "Please enter a question first.",
        "confirm_end": "End voting and show the final results?", "language": "EN | فارسی",
        "idle": "Ready for a new question", "active": "Voting is active",
        "question_type": "Question type", "yes_no": "Yes / No", "quiz": "Single 4-option quiz", "exam": "Timed exam", "exam_setup": "Configure exam", "exam_title": "Exam title", "exam_duration": "Exam time (minutes)", "add_question": "Add question", "save_exam": "Save exam", "exam_instructions": "Fill in each question and its four answer choices.", "comments_enabled": "Allow comments on questions", "minutes": "min", "options": "Options", "correct_answer_label": "Correct answer", "incomplete_question": "Each used question needs a question text and all four choices.", "need_exam_question": "Add at least one complete question.", "exam_duration_summary": "Exam duration", "responses_summary": "Responses", "average_score": "Average score", "rating": "Rating 1–10",
        "allowed": "ALLOW", "disabled": "BLOCKED", "show_results": "Show results to students",
        "average": "Average rating", "comments": "Student feedback", "option": "Option", "hint_yes_no": "Students choose Yes or No.", "hint_quiz": "Students choose one of four options.", "hint_exam": "Build a multi-question exam and set one total time limit.", "hint_rating": "Students give a score from 1 to 10; comments are optional."
    },
    "fa": {
        "title": "داشبورد رأی‌گیری کلاس", "question": "سؤال",
        "start": "شروع رأی‌گیری", "end": "پایان رأی‌گیری", "online": "سرور فعال است",
        "mode": "نوع رأی‌گیری", "anonymous": "ناشناس", "non_anonymous": "غیرناشناس",
        "responses": "پاسخ‌ها", "students": "دانش‌آموزان", "waiting": "در انتظار", "voted": "رأی داده",
        "connected": "متصل", "not_connected": "آفلاین", "final": "نتیجه نهایی",
        "total": "کل آرا", "yes": "بله", "no": "خیر", "close": "بستن",
        "question_required": "لطفاً ابتدا سؤال را وارد کنید.",
        "confirm_end": "رأی‌گیری پایان داده شود و نتیجه نهایی نمایش داده شود؟", "language": "فارسی | EN",
        "idle": "آماده برای سؤال جدید", "active": "رأی‌گیری فعال است",
        "question_type": "نوع سؤال", "yes_no": "بله / خیر", "quiz": "سؤال چهارگزینه‌ای", "exam": "آزمون زمان‌دار", "exam_setup": "تنظیم آزمون", "exam_title": "عنوان آزمون", "exam_duration": "زمان آزمون (دقیقه)", "add_question": "افزودن سؤال", "save_exam": "ذخیره آزمون", "exam_instructions": "متن هر سؤال و چهار گزینه آن را وارد کنید.", "comments_enabled": "امکان ثبت نظر برای سؤال‌ها", "minutes": "دقیقه", "options": "گزینه‌ها", "correct_answer_label": "پاسخ صحیح", "incomplete_question": "برای هر سؤال، متن سؤال و هر چهار گزینه را کامل کنید.", "need_exam_question": "حداقل یک سؤال کامل وارد کنید.", "exam_duration_summary": "زمان آزمون", "responses_summary": "پاسخ‌ها", "average_score": "میانگین نمره", "rating": "امتیاز ۱ تا ۱۰",
        "allowed": "مجاز", "disabled": "مسدود", "show_results": "نمایش نتیجه به دانش‌آموزان",
        "average": "میانگین امتیاز", "comments": "نظرهای دانش‌آموزان", "option": "گزینه", "hint_yes_no": "دانش‌آموزان بله یا خیر را انتخاب می‌کنند.", "hint_quiz": "دانش‌آموزان یکی از چهار گزینه را انتخاب می‌کنند.", "hint_exam": "چند سؤال بسازید و یک زمان کلی برای آزمون تعیین کنید.", "hint_rating": "دانش‌آموزان امتیازی از ۱ تا ۱۰ می‌دهند؛ ثبت نظر اختیاری است."
    }
}


def load_config():
    data = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass
    return {
        "tcp_port": int(data.get("tcp_port", DEFAULT_TCP_PORT)),
        "discovery_port": int(data.get("discovery_port", DEFAULT_DISCOVERY_PORT)),
        "max_students": int(data.get("max_students", DEFAULT_MAX_STUDENTS)),
    }


class TeacherServer:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.tcp_port = self.config["tcp_port"]
        self.discovery_port = self.config["discovery_port"]
        self.max_students = max(1, min(99, self.config["max_students"]))

        self.language = "en"
        self.running = True
        self.server_socket = None
        self.discovery_socket = None
        self.clients = {}
        self.clients_lock = threading.Lock()

        self.voted_computers = set()
        # Latest submission per computer; replacement enables revoting without double-counting.
        self.votes = {}
        self.pc_enabled = {f"PC-{i:02d}": True for i in range(1, self.max_students + 1)}
        self.question = ""
        self.vote_active = False
        self.voting_mode = "anonymous"
        self.question_type = "yes_no"
        self.exam_questions = []
        self.exam_duration_minutes = 10
        self.comments_enabled = False
        self.exam_timer_job = None
        self.exam_started_at = None
        self.last_results = None

        self.build_ui()
        threading.Thread(target=self.tcp_server, daemon=True).start()
        threading.Thread(target=self.discovery_server, daemon=True).start()

    def t(self, key):
        return TEXTS[self.language][key]

    def build_ui(self):
        self.root.title(self.t("title"))
        self.root.geometry("1040x720")
        self.root.minsize(900, 650)
        self.root.configure(bg="#0f172a")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        top = tk.Frame(self.root, bg="#111827", height=82)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.title_label = tk.Label(top, text=self.t("title"), font=("Segoe UI", 22, "bold"), fg="white", bg="#111827")
        self.title_label.pack(side="left", padx=28)

        self.server_label = tk.Label(top, text="●  " + self.t("online"), font=("Segoe UI", 10, "bold"), fg="#22c55e", bg="#111827")
        self.server_label.pack(side="left", padx=20)

        self.lang_btn = tk.Button(top, text=self.t("language"), command=self.switch_language,
                                  font=("Segoe UI", 10, "bold"), fg="white", bg="#334155",
                                  activebackground="#475569", activeforeground="white", relief="flat",
                                  padx=14, pady=7, cursor="hand2")
        self.lang_btn.pack(side="right", padx=20)

        main = tk.Frame(self.root, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=26, pady=24)

        left = tk.Frame(main, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        self.question_caption = tk.Label(left, text=self.t("question"), font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b")
        self.question_caption.pack(anchor="w", padx=24, pady=(24, 8))

        self.question_entry = tk.Text(left, height=4, wrap="word", font=("Segoe UI", 14), bg="#0f172a", fg="white",
                                      insertbackground="white", relief="flat", padx=12, pady=10)
        self.question_entry.pack(fill="x", padx=24)

        self.mode_label = tk.Label(left, text=self.t("mode"), font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b")
        self.mode_label.pack(anchor="w", padx=24, pady=(22, 8))

        self.mode_var = tk.StringVar(value="anonymous")
        modes = tk.Frame(left, bg="#1e293b")
        modes.pack(anchor="w", padx=20)
        self.anon_radio = tk.Radiobutton(modes, text=self.t("anonymous"), variable=self.mode_var, value="anonymous",
                                         font=("Segoe UI", 11), bg="#1e293b", fg="white", selectcolor="#0f172a",
                                         activebackground="#1e293b", activeforeground="white")
        self.anon_radio.pack(side="left", padx=5)
        self.named_radio = tk.Radiobutton(modes, text=self.t("non_anonymous"), variable=self.mode_var, value="named",
                                          font=("Segoe UI", 11), bg="#1e293b", fg="white", selectcolor="#0f172a",
                                          activebackground="#1e293b", activeforeground="white")
        self.named_radio.pack(side="left", padx=5)

        self.type_label = tk.Label(left, text=self.t("question_type"), font=("Segoe UI", 10, "bold"), fg="#94a3b8", bg="#1e293b")
        self.type_label.pack(anchor="w", padx=24, pady=(14, 5))
        self.type_var = tk.StringVar(value=self.t("yes_no"))
        self.type_menu = tk.OptionMenu(left, self.type_var, *[self.t(k) for k in ("yes_no", "quiz", "exam", "rating")], command=lambda _value: self.update_type_ui())
        self.type_menu.config(font=("Segoe UI", 10), bg="#334155", fg="white", activebackground="#475569", relief="flat", highlightthickness=0)
        self.type_menu["menu"].config(bg="#1e293b", fg="white")
        self.type_menu.pack(anchor="w", padx=24)
        self.type_hint = tk.Label(left, text=self.t("hint_yes_no"), font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b", wraplength=390, justify="left")
        self.type_hint.pack(anchor="w", padx=26, pady=(4, 0))
        self.type_specific_frame = tk.Frame(left, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        self.type_specific_frame.pack(fill="x", padx=24, pady=(10, 0))
        extra = tk.Frame(self.type_specific_frame, bg="#1e293b")
        extra.pack(fill="x", padx=10, pady=8)
        self.exam_setup_btn = tk.Button(extra, text=self.t("exam_setup"), command=self.configure_exam, font=("Segoe UI", 9, "bold"), bg="#334155", fg="white", relief="flat", padx=9, pady=5)
        self.exam_setup_btn.pack(side="left")
        self.duration_label = tk.Label(extra, text=self.t("exam_duration"), font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b")
        self.duration_label.pack(side="left", padx=(10, 5))
        self.duration_var = tk.StringVar(value="10")
        self.duration_entry = tk.Entry(extra, textvariable=self.duration_var, width=4, bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        self.duration_entry.pack(side="left")
        self.comments_var = tk.BooleanVar(value=False)
        self.comments_check = tk.Checkbutton(left, text=self.t("comments_enabled"), variable=self.comments_var, font=("Segoe UI", 9), bg="#1e293b", fg="#cbd5e1", selectcolor="#0f172a", activebackground="#1e293b", activeforeground="white")
        self.comments_check.pack(anchor="w", padx=22, pady=(10, 0))

        self.start_btn = tk.Button(left, text=self.t("start"), command=self.start_voting,
                                   font=("Segoe UI", 13, "bold"), bg="#2563eb", fg="white",
                                   activebackground="#1d4ed8", relief="flat", pady=12, cursor="hand2")
        self.start_btn.pack(fill="x", padx=24, pady=(26, 10))

        self.end_btn = tk.Button(left, text=self.t("end"), command=self.end_voting,
                                 font=("Segoe UI", 12, "bold"), bg="#7f1d1d", fg="#94a3b8",
                                 activebackground="#991b1b", relief="flat", pady=10, cursor="hand2", state="disabled")
        self.end_btn.pack(fill="x", padx=24)

        self.status_text = tk.Label(left, text=self.t("idle"), font=("Segoe UI", 10), fg="#64748b", bg="#1e293b")
        self.status_text.pack(pady=20)

        right = tk.Frame(main, bg="#1e293b", highlightthickness=1, highlightbackground="#334155")
        right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        self.students_title = tk.Label(right, text=self.t("students"), font=("Segoe UI", 14, "bold"), fg="white", bg="#1e293b")
        self.students_title.pack(anchor="w", padx=24, pady=(24, 10))

        self.response_label = tk.Label(right, text=f"0 / {self.max_students}", font=("Segoe UI", 26, "bold"), fg="#93c5fd", bg="#1e293b")
        self.response_label.pack(anchor="w", padx=24)

        self.response_caption = tk.Label(right, text=self.t("responses"), font=("Segoe UI", 9), fg="#64748b", bg="#1e293b")
        self.response_caption.pack(anchor="w", padx=24, pady=(0, 14))

        self.list_frame = tk.Frame(right, bg="#0f172a")
        self.list_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.student_labels = {}
        for i in range(1, self.max_students + 1):
            pc = f"PC-{i:02d}"
            row = tk.Frame(self.list_frame, bg="#0f172a")
            row.pack(fill="x", padx=10, pady=3)
            name = tk.Label(row, text=pc, font=("Segoe UI", 10, "bold"), fg="#cbd5e1", bg="#0f172a", width=9, anchor="w")
            name.pack(side="left")
            allow_var = tk.BooleanVar(value=True)
            allow = tk.Checkbutton(row, text=self.t("allowed"), variable=allow_var, command=lambda cid=pc, var=allow_var: self.set_pc_enabled(cid, var.get()),
                                   font=("Segoe UI", 8), bg="#0f172a", fg="#94a3b8", selectcolor="#1e293b", activebackground="#0f172a", activeforeground="white")
            allow.pack(side="left", padx=4)
            status = tk.Label(row, text=self.t("not_connected"), font=("Segoe UI", 9, "bold"), fg="#64748b", bg="#0f172a", anchor="e")
            status.pack(side="right")
            self.student_labels[pc] = status
            self.pc_enabled[pc] = True
            if not hasattr(self, "pc_allow_vars"):
                self.pc_allow_vars = {}
            self.pc_allow_vars[pc] = allow_var
            self.pc_allow_widgets = getattr(self, "pc_allow_widgets", {})
            self.pc_allow_widgets[pc] = allow
        self.update_type_ui()

    def switch_language(self):
        previous_key = next((key for key in ("yes_no", "quiz", "exam", "rating") if self.type_var.get() == self.t(key)), "yes_no")
        self.language = "fa" if self.language == "en" else "en"
        self.type_var.set(self.t(previous_key))
        menu = self.type_menu["menu"]
        menu.delete(0, "end")
        for key in ("yes_no", "quiz", "exam", "rating"):
            menu.add_command(label=self.t(key), command=lambda k=key: (self.type_var.set(self.t(k)), self.update_type_ui()))
        self.root.title(self.t("title"))
        self.title_label.config(text=self.t("title"))
        self.server_label.config(text="●  " + self.t("online"))
        self.lang_btn.config(text=self.t("language"))
        self.question_caption.config(text=self.t("question"))
        self.mode_label.config(text=self.t("mode"))
        self.type_label.config(text=self.t("question_type"))
        self.type_hint.config(text=self.t("hint_" + previous_key))
        self.exam_setup_btn.config(text=self.t("exam_setup"))
        self.duration_label.config(text=self.t("exam_duration"))
        self.comments_check.config(text=self.t("comments_enabled"))
        self.anon_radio.config(text=self.t("anonymous"))
        self.named_radio.config(text=self.t("non_anonymous"))
        self.start_btn.config(text=self.t("start"))
        self.end_btn.config(text=self.t("end"))
        self.students_title.config(text=self.t("students"))
        self.response_caption.config(text=self.t("responses"))
        self.update_type_ui()
        self.refresh_students()
        if not self.vote_active:
            self.status_text.config(text=self.t("idle"))

    def update_type_ui(self):
        selected = next((key for key in ("yes_no", "quiz", "exam", "rating") if self.type_var.get() == self.t(key)), "yes_no")
        is_exam = selected == "exam"
        can_edit = not self.vote_active
        self.exam_setup_btn.config(state="normal" if is_exam and can_edit else "disabled")
        self.duration_entry.config(state="normal" if is_exam and can_edit else "disabled")
        self.duration_label.config(fg="#cbd5e1" if is_exam else "#64748b")
        self.question_caption.config(text=self.t("exam_title") if is_exam else self.t("question"))
        self.type_hint.config(text=self.t("hint_" + selected))
        # Exam configuration is shown only for the timed-exam type, keeping
        # the dashboard clean for Yes/No, quiz, and rating questions.
        if is_exam:
            if not self.type_specific_frame.winfo_manager():
                self.type_specific_frame.pack(fill="x", padx=24, pady=(10, 0), after=self.type_menu)
        else:
            self.type_specific_frame.pack_forget()

    def configure_exam(self):
        win = tk.Toplevel(self.root)
        win.title(self.t("exam_setup"))
        win.geometry("980x720")
        win.minsize(820, 560)
        win.configure(bg="#0f172a")
        win.transient(self.root)
        tk.Label(win, text=self.t("exam_setup"), font=("Segoe UI", 19, "bold"), fg="white", bg="#0f172a").pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(win, text=self.t("exam_instructions"), font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").pack(anchor="w", padx=20, pady=(0, 10))
        outer = tk.Frame(win, bg="#0f172a")
        outer.pack(fill="both", expand=True, padx=18, pady=6)
        canvas = tk.Canvas(outer, bg="#0f172a", highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg="#0f172a")
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        rows = []
        def add_row(initial=None):
            initial = initial or {}
            index = len(rows) + 1
            card = tk.Frame(body, bg="#1e293b", padx=10, pady=8)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=f"Q{index}", font=("Segoe UI", 10, "bold"), fg="#93c5fd", bg="#1e293b", width=4).grid(row=0, column=0, sticky="nw")
            q = tk.Entry(card, font=("Segoe UI", 10), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
            q.grid(row=0, column=1, columnspan=4, sticky="ew", padx=4, pady=(0, 6), ipady=5)
            q.insert(0, initial.get("question", ""))
            opts=[]
            for j in range(4):
                e=tk.Entry(card, font=("Segoe UI", 9), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
                e.grid(row=1, column=j+1, sticky="ew", padx=3, ipady=4)
                e.insert(0, (initial.get("options", ["", "", "", ""])+["", "", "", ""])[j])
                opts.append(e)
            tk.Label(card, text=self.t("options") + ":", font=("Segoe UI", 8), fg="#94a3b8", bg="#1e293b").grid(row=1, column=0, sticky="w")
            tk.Label(card, text=self.t("correct_answer_label") + ":", font=("Segoe UI", 8, "bold"), fg="#a7f3d0", bg="#1e293b").grid(row=2, column=0, sticky="w", pady=(6,0))
            correct_var=tk.StringVar(value=str(initial.get("correct", "1")))
            for j in range(4):
                tk.Radiobutton(card,text=str(j+1),value=str(j+1),variable=correct_var,bg="#1e293b",fg="white",selectcolor="#0f172a",activebackground="#1e293b",activeforeground="white").grid(row=2,column=j+1,sticky="w",padx=5,pady=(6,0))
            for col in range(5): card.grid_columnconfigure(col, weight=1)
            rows.append((q, opts, correct_var, card))
        for item in (self.exam_questions or [{} for _ in range(5)]):
            add_row(item)
        bottom = tk.Frame(win, bg="#0f172a")
        bottom.pack(fill="x", padx=18, pady=14)
        tk.Button(bottom, text=self.t("add_question"), command=add_row, bg="#334155", fg="white", relief="flat", padx=12, pady=8).pack(side="left")
        def save():
            questions=[]
            for q, opts, correct_var, _card in rows:
                question=q.get().strip()
                values=[e.get().strip() for e in opts]
                if not question and not any(values):
                    continue
                if not question or not all(values):
                    messagebox.showwarning(self.t("exam_setup"), self.t("incomplete_question"), parent=win)
                    return
                questions.append({"question": question, "options": values, "correct": correct_var.get()})
            if not questions:
                messagebox.showwarning(self.t("exam_setup"), self.t("need_exam_question"), parent=win)
                return
            self.exam_questions=questions
            self.status_text.config(text=f"Exam configured: {len(questions)} questions")
            win.destroy()
        tk.Button(bottom, text=self.t("save_exam"), command=save, bg="#2563eb", fg="white", relief="flat", padx=18, pady=8).pack(side="right")

    def tcp_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, self.tcp_port))
            s.listen(32)
            self.server_socket = s
            while self.running:
                try:
                    client, address = s.accept()
                    threading.Thread(target=self.handle_client, args=(client, address), daemon=True).start()
                except OSError:
                    break
        except OSError as exc:
            self.root.after(0, lambda: self.server_label.config(text=f"● SERVER ERROR: {exc}", fg="#ef4444"))

    def discovery_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind(("", self.discovery_port))
            self.discovery_socket = s
            while self.running:
                try:
                    data, addr = s.recvfrom(2048)
                except OSError:
                    break
                try:
                    msg = json.loads(data.decode())
                except Exception:
                    continue
                if msg.get("type") == "discover" and msg.get("app") == "ClassroomVoting":
                    reply = json.dumps({"type": "teacher_here", "ip": self.get_best_local_ip(addr[0])}).encode()
                    try:
                        s.sendto(reply, addr)
                    except OSError:
                        pass
        except OSError:
            pass

    def get_best_local_ip(self, requester_ip=None):
        if requester_ip:
            try:
                x = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                x.connect((requester_ip, 9))
                ip = x.getsockname()[0]
                x.close()
                if ip and not ip.startswith("127."):
                    return ip
            except OSError:
                pass
        try:
            host = socket.gethostname()
            for item in socket.getaddrinfo(host, None, socket.AF_INET):
                ip = item[4][0]
                if not ip.startswith("127."):
                    return ip
        except Exception:
            pass
        return "127.0.0.1"

    def handle_client(self, sock, address):
        computer_id = None
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
                        msg = json.loads(line.decode())
                    except Exception:
                        continue

                    if msg.get("type") == "identify":
                        cid = msg.get("computer_id", "")
                        valid = {f"PC-{i:02d}" for i in range(1, self.max_students + 1)}
                        if cid not in valid:
                            continue
                        with self.clients_lock:
                            old = self.clients.get(cid)
                            if old and old["socket"] is not sock:
                                try:
                                    old["socket"].close()
                                except OSError:
                                    pass
                            self.clients[cid] = {"socket": sock, "address": address}
                            computer_id = cid
                        self.send_to(sock, {"type": "server_status", "voting": self.vote_active, "question": self.question if self.vote_active else "", "question_type": self.question_type, "exam_questions": [{"question": q.get("question", ""), "options": q.get("options", [])} for q in self.exam_questions] if self.vote_active and self.question_type == "exam" else [], "duration_seconds": max(1, self.exam_duration_minutes * 60 - int(time.monotonic() - self.exam_started_at)) if self.vote_active and self.question_type == "exam" and self.exam_started_at else 0, "exam_answers": (self.votes.get(cid, {}).get("answers", {}) if self.vote_active and self.question_type == "exam" else {}), "comments_enabled": self.comments_enabled, "allowed": self.pc_enabled.get(cid, True), "results": (self.student_safe_results(self.last_results) if self.last_results and not self.vote_active else None)})
                        self.root.after(0, self.refresh_students)

                    elif msg.get("type") == "vote" and computer_id:
                        self.process_vote(computer_id, msg.get("vote"), msg.get("comment", ""))
                    elif msg.get("type") == "exam_answer" and computer_id:
                        self.process_exam_answer(computer_id, msg.get("question_index"), msg.get("answer"), msg.get("comment", ""))
        except OSError:
            pass
        finally:
            if computer_id:
                with self.clients_lock:
                    current = self.clients.get(computer_id)
                    if current and current["socket"] is sock:
                        del self.clients[computer_id]
                self.root.after(0, self.refresh_students)
            try:
                sock.close()
            except OSError:
                pass

    def send_to(self, sock, msg):
        try:
            sock.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
            return True
        except OSError:
            return False

    def broadcast(self, msg):
        with self.clients_lock:
            clients = list(self.clients.items())
        for _, info in clients:
            if not self.send_to(info["socket"], msg):
                try:
                    info["socket"].close()
                except OSError:
                    pass

    def set_pc_enabled(self, computer_id, enabled):
        self.pc_enabled[computer_id] = bool(enabled)
        if self.vote_active:
            with self.clients_lock:
                info = self.clients.get(computer_id)
            if info:
                self.send_to(info["socket"], {"type": "access_status", "allowed": bool(enabled)})
        self.refresh_students()

    def process_vote(self, computer_id, answer, comment=""):
        if not self.vote_active or not self.pc_enabled.get(computer_id, True):
            return
        comment = str(comment or "")[:1000] if self.comments_enabled else ""
        if self.question_type == "yes_no":
            if answer not in ("YES", "NO"):
                return
        elif self.question_type == "quiz":
            if answer not in ("1", "2", "3", "4"):
                return
        elif self.question_type == "rating":
            try:
                answer = int(answer)
            except (TypeError, ValueError):
                return
            if not 1 <= answer <= 10:
                return
        else:
            return
        # Replace a previous submission rather than counting a second vote.
        self.votes[computer_id] = {"answer": answer, "comment": comment}
        self.voted_computers.add(computer_id)
        with self.clients_lock:
            info = self.clients.get(computer_id)
        if info:
            self.send_to(info["socket"], {"type": "vote_ack", "answer": answer})
        self.root.after(0, self.refresh_students)

    def process_exam_answer(self, computer_id, question_index, answer, comment=""):
        if not self.vote_active or self.question_type != "exam" or not self.pc_enabled.get(computer_id, True):
            return
        try:
            index = int(question_index)
        except (TypeError, ValueError):
            return
        if not 0 <= index < len(self.exam_questions) or str(answer) not in ("1", "2", "3", "4"):
            return
        submission = self.votes.setdefault(computer_id, {"answers": {}})
        if not isinstance(submission, dict) or "answers" not in submission:
            submission = {"answers": {}}
            self.votes[computer_id] = submission
        submission["answers"][str(index)] = {"answer": str(answer), "comment": str(comment or "")[:1000] if self.comments_enabled else ""}
        self.voted_computers.add(computer_id)
        with self.clients_lock:
            info = self.clients.get(computer_id)
        if info:
            self.send_to(info["socket"], {"type": "exam_ack", "question_index": index, "answer": str(answer)})
        self.root.after(0, self.refresh_students)

    def student_safe_results(self, payload):
        safe = dict(payload)
        safe.pop("individual", None)
        safe.pop("scores", None)
        safe.pop("comments", None)
        if safe.get("question_type") == "exam":
            safe["exam_questions"] = [dict(item) for item in safe.get("exam_questions", [])]
            for item in safe["exam_questions"]:
                item.pop("correct_answer", None)
                item.pop("correct_count", None)
                item.pop("comments", None)
        return safe

    def result_payload(self):
        submissions = list(self.votes.items())
        total = len(submissions)
        payload = {"question": self.question, "question_type": self.question_type, "total": total, "mode": self.voting_mode}
        if self.question_type == "exam":
            results=[]
            for index, question in enumerate(self.exam_questions):
                counts={str(i): 0 for i in range(1,5)}
                comments=[]
                answered=0
                correct_answer=str(question.get("correct", "1"))
                correct_count=0
                for cid, record in submissions:
                    answer_record=record.get("answers", {}).get(str(index), {}) if isinstance(record, dict) else {}
                    answer=answer_record.get("answer")
                    if answer in counts:
                        counts[answer]+=1; answered+=1
                        if answer == correct_answer: correct_count += 1
                    comment=answer_record.get("comment", "")
                    if comment.strip():
                        comments.append(({"computer":cid,"text":comment} if self.voting_mode == "named" else {"text":comment}))
                results.append({"question":question["question"], "options":question["options"], "counts":counts, "answered":answered, "correct_answer":correct_answer, "correct_count":correct_count, "comments":comments})
            scores=[]
            raw_scores=[]
            for cid, record in submissions:
                answers=record.get("answers", {}) if isinstance(record,dict) else {}
                score=sum(1 for idx,q in enumerate(self.exam_questions) if answers.get(str(idx),{}).get("answer") == str(q.get("correct", "1")))
                raw_scores.append(score)
                if self.voting_mode == "named":
                    scores.append({"computer":cid,"score":score,"out_of":len(self.exam_questions)})
            payload.update({"exam_questions":results,"duration_minutes":self.exam_duration_minutes,"comments_enabled":self.comments_enabled,"scores":scores,"average_score":round(sum(raw_scores)/len(raw_scores),2) if raw_scores else 0})
        elif self.question_type == "yes_no":
            yes=sum(1 for _,v in submissions if v.get("answer") == "YES")
            no=sum(1 for _,v in submissions if v.get("answer") == "NO")
            payload.update({"counts":{"YES":yes,"NO":no},"percentages":{"YES":round(yes*100/total,1) if total else 0,"NO":round(no*100/total,1) if total else 0}})
        elif self.question_type == "quiz":
            counts={str(i):0 for i in range(1,5)}
            for _,v in submissions:
                if str(v.get("answer")) in counts: counts[str(v["answer"])]+=1
            payload["counts"]=counts
        else:
            scores=[int(v["answer"]) for _,v in submissions if str(v.get("answer","")).isdigit()]
            payload["average"]=round(sum(scores)/len(scores),2) if scores else 0
            payload["distribution"]={str(i):scores.count(i) for i in range(1,11)}
            payload["comments"]=[({"computer":cid,"text":v.get("comment","")} if self.voting_mode=="named" else {"text":v.get("comment","")}) for cid,v in submissions if v.get("comment","").strip()]
        if self.comments_enabled and self.question_type not in ("exam", "rating"):
            payload["comments"]=[({"computer":cid,"text":v.get("comment","")} if self.voting_mode=="named" else {"text":v.get("comment","")}) for cid,v in submissions if v.get("comment","").strip()]
        if self.voting_mode == "named" and self.question_type != "exam":
            payload["individual"]=[{"computer":cid,"answer":v.get("answer"),"comment":v.get("comment","")} for cid,v in submissions]
        return payload

    def start_voting(self):
        question = self.question_entry.get("1.0", "end").strip()
        if not question:
            messagebox.showwarning(self.t("title"), self.t("question_required"))
            return
        self.question = question
        self.voting_mode = self.mode_var.get()
        self.question_type = next((key for key in ("yes_no", "quiz", "exam", "rating") if self.type_var.get() == self.t(key)), "yes_no")
        self.comments_enabled = bool(self.comments_var.get())
        if self.question_type == "exam":
            if not self.exam_questions:
                messagebox.showwarning(self.t("title"), "Configure at least one complete exam question first.")
                return
            try:
                self.exam_duration_minutes = max(1, min(240, int(self.duration_var.get())))
            except ValueError:
                messagebox.showwarning(self.t("title"), "Exam duration must be a whole number of minutes.")
                return
        self.voted_computers.clear()
        self.votes.clear()
        self.last_results = None
        self.vote_active = True
        self.question_entry.config(state="disabled")
        self.anon_radio.config(state="disabled")
        self.named_radio.config(state="disabled")
        self.type_menu.config(state="disabled")
        self.exam_setup_btn.config(state="disabled")
        self.duration_entry.config(state="disabled")
        self.comments_check.config(state="disabled")
        self.start_btn.config(state="disabled")
        self.end_btn.config(state="normal", fg="white")
        self.status_text.config(text=f"{self.t('responses')}: 0 / {sum(self.pc_enabled.values())}")
        self.broadcast({"type": "start_voting", "question": question, "question_type": self.question_type, "allowed": None,
                        "exam_questions": [{"question": q.get("question", ""), "options": q.get("options", [])} for q in self.exam_questions] if self.question_type == "exam" else [],
                        "duration_seconds": self.exam_duration_minutes * 60 if self.question_type == "exam" else 0,
                        "comments_enabled": self.comments_enabled})
        if self.question_type == "exam":
            self.exam_started_at = time.monotonic()
            self.exam_timer_job = self.root.after(self.exam_duration_minutes * 60 * 1000, self.end_voting_timeout)
        else:
            self.exam_started_at = None
        # Send each computer its own access state after the general start event.
        with self.clients_lock:
            clients = list(self.clients.items())
        for cid, info in clients:
            self.send_to(info["socket"], {"type": "access_status", "allowed": self.pc_enabled.get(cid, True)})
        self.refresh_students()

    def end_voting_timeout(self):
        self.exam_timer_job = None
        if self.vote_active and self.question_type == "exam":
            self.end_voting(from_timer=True)

    def end_voting(self, from_timer=False):
        if not self.vote_active:
            return
        if not from_timer and not messagebox.askyesno(self.t("title"), self.t("confirm_end")):
            return
        if self.exam_timer_job is not None:
            try: self.root.after_cancel(self.exam_timer_job)
            except Exception: pass
            self.exam_timer_job = None
        self.vote_active = False
        self.exam_started_at = None
        payload = self.result_payload()
        self.last_results = payload
        self.broadcast({"type": "end_voting"})
        student_payload = self.student_safe_results(payload)
        self.broadcast({"type": "final_results", "results": student_payload})
        self.question_entry.config(state="normal")
        self.anon_radio.config(state="normal")
        self.named_radio.config(state="normal")
        self.type_menu.config(state="normal")
        self.comments_check.config(state="normal")
        self.start_btn.config(state="normal")
        self.update_type_ui()
        self.end_btn.config(state="disabled", fg="#94a3b8")
        self.status_text.config(text=self.t("idle"))
        self.refresh_students()
        self.root.after(100, self.show_results)

    def show_results(self):
        data = self.result_payload()
        win = tk.Toplevel(self.root)
        win.title(self.t("final"))
        win.geometry("660x620")
        win.minsize(560, 500)
        win.configure(bg="#0f172a")
        win.transient(self.root)
        tk.Label(win, text=self.t("final"), font=("Segoe UI", 22, "bold"), fg="white", bg="#0f172a").pack(pady=(20, 8))
        tk.Label(win, text=self.question, font=("Segoe UI", 12), fg="#cbd5e1", bg="#0f172a", wraplength=580).pack(padx=30, pady=(0, 14))
        summary = tk.Frame(win, bg="#1e293b")
        summary.pack(fill="x", padx=28)
        kind = self.question_type
        if kind == "exam":
            tk.Label(summary, text=f"{self.t('exam_duration_summary')}: {data.get('duration_minutes', self.exam_duration_minutes)} min | {self.t('responses_summary')}: {data.get('total', 0)} | {self.t('average_score')}: {data.get('average_score', 0):.2f}/{len(self.exam_questions)}", font=("Segoe UI", 11, "bold"), fg="#93c5fd", bg="#1e293b").pack(pady=8)
            results_outer = tk.Frame(win, bg="#0f172a")
            results_outer.pack(fill="both", expand=True, padx=28, pady=10)
            results_canvas = tk.Canvas(results_outer, bg="#1e293b", highlightthickness=0)
            results_scroll = tk.Scrollbar(results_outer, orient="vertical", command=results_canvas.yview)
            box = tk.Frame(results_canvas, bg="#1e293b")
            box.bind("<Configure>", lambda _e: results_canvas.configure(scrollregion=results_canvas.bbox("all")))
            results_canvas.create_window((0, 0), window=box, anchor="nw")
            results_canvas.configure(yscrollcommand=results_scroll.set)
            results_canvas.pack(side="left", fill="both", expand=True)
            results_scroll.pack(side="right", fill="y")
            results_canvas.bind("<Configure>", lambda e: results_canvas.itemconfigure(results_canvas.find_all()[0], width=e.width))
            for index, item in enumerate(data.get("exam_questions", []), 1):
                tk.Label(box, text=f"Q{index}. {item['question']}", font=("Segoe UI", 10, "bold"), fg="white", bg="#1e293b", wraplength=570, justify="left").pack(anchor="w", padx=10, pady=(7, 3))
                tk.Label(box, text="   |   ".join(f"{i}: {item['counts'].get(str(i),0)}" for i in range(1,5)) + f"   |   Correct answer: {item.get('correct_answer')} ({item.get('correct_count',0)} correct)", font=("Segoe UI", 9), fg="#cbd5e1", bg="#1e293b").pack(anchor="w", padx=10)
                for comment in item.get("comments", []):
                    tk.Label(box, text=(comment.get("computer", "•") + ": " if "computer" in comment else "• ") + comment.get("text", ""), font=("Segoe UI", 9), fg="#a7f3d0", bg="#1e293b", wraplength=560, justify="left").pack(anchor="w", padx=18, pady=2)
            if data.get("scores"):
                tk.Label(box, text="Individual scores", font=("Segoe UI", 10, "bold"), fg="white", bg="#1e293b").pack(anchor="w", padx=10, pady=(10,3))
                for score in data["scores"]:
                    tk.Label(box, text=f"{score['computer']}: {score['score']} / {score['out_of']}", font=("Segoe UI", 9), fg="#cbd5e1", bg="#1e293b").pack(anchor="w", padx=18, pady=1)
        elif kind == "yes_no":
            counts = data["counts"]
            tk.Label(summary, text=f"{self.t('yes')}: {counts['YES']} ({data['percentages']['YES']:.1f}%)", font=("Segoe UI", 14, "bold"), fg="#86efac", bg="#1e293b").pack(pady=6)
            tk.Label(summary, text=f"{self.t('no')}: {counts['NO']} ({data['percentages']['NO']:.1f}%)", font=("Segoe UI", 14, "bold"), fg="#fca5a5", bg="#1e293b").pack(pady=6)
        elif kind == "quiz":
            for option in ("1", "2", "3", "4"):
                tk.Label(summary, text=f"{self.t('option')} {option}: {data['counts'][option]}", font=("Segoe UI", 13, "bold"), fg="#cbd5e1", bg="#1e293b").pack(pady=4)
        else:
            tk.Label(summary, text=f"{self.t('average')}: {data['average']:.2f} / 10", font=("Segoe UI", 16, "bold"), fg="#93c5fd", bg="#1e293b").pack(pady=8)
            tk.Label(summary, text=f"{self.t('total')}: {data['total']}", font=("Segoe UI", 11), fg="#cbd5e1", bg="#1e293b").pack(pady=(0, 10))
        if self.comments_enabled and kind != "exam" and data.get("comments"):
            box = tk.Frame(win, bg="#1e293b")
            box.pack(fill="both", expand=True, padx=28, pady=12)
            tk.Label(box, text=self.t("comments"), font=("Segoe UI", 11, "bold"), fg="white", bg="#1e293b").pack(anchor="w", padx=12, pady=8)
            text_box = tk.Text(box, bg="#0f172a", fg="#e2e8f0", wrap="word", relief="flat", font=("Segoe UI", 10), height=8)
            text_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            for item in data["comments"]:
                prefix = f"{item['computer']}: " if "computer" in item else "• "
                text_box.insert("end", prefix + item["text"] + "\n\n")
            text_box.config(state="disabled")
        if self.voting_mode == "named" and data.get("individual"):
            box = tk.Frame(win, bg="#1e293b")
            box.pack(fill="both", expand=True, padx=28, pady=10)
            for item in data["individual"]:
                tk.Label(box, text=f"{item['computer']}    {item['answer']}", font=("Segoe UI", 10, "bold"), fg="#cbd5e1", bg="#1e293b").pack(anchor="w", padx=14, pady=2)
        tk.Button(win, text=self.t("close"), command=win.destroy, font=("Segoe UI", 11, "bold"), bg="#334155", fg="white", activebackground="#475569", relief="flat", padx=30, pady=9).pack(pady=(4, 18))

    def refresh_students(self):
        with self.clients_lock:
            connected_ids = set(self.clients.keys())
        for i in range(1, self.max_students + 1):
            cid = f"PC-{i:02d}"
            label = self.student_labels[cid]
            if not self.pc_enabled.get(cid, True):
                label.config(text=self.t("disabled"), fg="#ef4444")
            elif cid not in connected_ids:
                label.config(text=self.t("not_connected"), fg="#64748b")
            elif cid in self.voted_computers:
                label.config(text=self.t("voted"), fg="#22c55e")
            else:
                label.config(text=self.t("connected"), fg="#60a5fa")
        count = len(self.votes)
        eligible = sum(self.pc_enabled.values())
        self.response_label.config(text=f"{count} / {eligible}")
        if self.vote_active:
            self.status_text.config(text=f"{self.t('responses')}: {count} / {eligible}")

    def close(self):
        self.running = False
        for sock in (self.server_socket, self.discovery_socket):
            try:
                if sock:
                    sock.close()
            except OSError:
                pass
        with self.clients_lock:
            clients = list(self.clients.values())
            self.clients.clear()
        for info in clients:
            try:
                info["socket"].close()
            except OSError:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    TeacherServer(root)
    root.mainloop()