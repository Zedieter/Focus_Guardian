"""Focus lock tab UI."""

import datetime
import threading
import time
import tkinter as tk
from tkinter import messagebox


class FocusLockTab:
    """Encapsulates the Focus Lock tab construction."""

    def __init__(self, app):
        self.app = app

    def create(self):
        """Create the focus lock tab UI."""
        app = self.app

        tab = tk.Frame(app.notebook, bg=app.colors["bg"])
        app.notebook.add(tab, text="🔒 Focus Lock")

        title_frame = tk.Frame(tab, bg=app.colors["card"])
        title_frame.pack(fill="x", pady=(20, 0), padx=20)

        tk.Label(
            title_frame,
            text="Focus Session",
            font=("Arial", 28, "bold"),
            bg=app.colors["card"],
            fg=app.colors["text"],
        ).pack(pady=20)

        app.status_frame = tk.Frame(tab, bg="#e0e7ff", relief="flat", bd=0)
        app.status_frame.pack(pady=20, padx=40, fill="x", ipady=20)

        app.status_label = tk.Label(
            app.status_frame,
            text="✨ Ready to Focus\nNo active session",
            font=("Arial", 16),
            bg="#e0e7ff",
            fg=app.colors["text"],
        )
        app.status_label.pack(pady=15)

        duration_frame = tk.Frame(tab, bg=app.colors["bg"])
        duration_frame.pack(pady=30)

        tk.Label(
            duration_frame,
            text="Choose Focus Duration:",
            font=("Arial", 13),
            bg=app.colors["bg"],
            fg=app.colors["text"],
        ).pack(pady=(0, 10))

        button_row = tk.Frame(duration_frame, bg=app.colors["bg"])
        button_row.pack()

        app.duration_var = tk.StringVar(value="25")
        for duration in ["25", "50", "90", "120"]:
            btn = tk.Radiobutton(
                button_row,
                text=f"{duration} min",
                variable=app.duration_var,
                value=duration,
                font=("Arial", 11, "bold"),
                bg=app.colors["card"],
                fg=app.colors["text"],
                selectcolor=app.colors["primary"],
                indicatoron=False,
                width=10,
                relief="flat",
                padx=15,
                pady=10,
                cursor="hand2",
            )
            btn.pack(side="left", padx=5)

        button_frame = tk.Frame(tab, bg=app.colors["bg"])
        button_frame.pack(pady=30)

        app.start_btn = tk.Button(
            button_frame,
            text="🚀 Start Focus Session",
            command=self.start,
            font=("Arial", 16, "bold"),
            bg=app.colors["success"],
            fg="white",
            padx=40,
            pady=20,
            relief="flat",
            cursor="hand2",
            borderwidth=0,
        )
        app.start_btn.pack(side="left", padx=10)

        app.stop_btn = tk.Button(
            button_frame,
            text="⏹️ Stop Session",
            command=self.stop,
            font=("Arial", 16, "bold"),
            bg=app.colors["danger"],
            fg="white",
            padx=40,
            pady=20,
            relief="flat",
            cursor="hand2",
            state="disabled",
            borderwidth=0,
        )
        app.stop_btn.pack(side="left", padx=10)

        info_card = tk.Frame(tab, bg=app.colors["card"], relief="solid", bd=1)
        info_card.pack(pady=20, padx=60, fill="x")

        info_text = """
Focus Lock Features:

Blocks distracting websites (YouTube, Reddit, TikTok, etc.)
Blocks specified applications
Timer-based sessions with countdown
Re-enables access automatically when done
Hard Mode prevents early stopping (enable in Settings)
    """

        tk.Label(
            info_card,
            text=info_text,
            font=("Arial", 11),
            justify="left",
            bg=app.colors["card"],
            fg=app.colors["text_light"],
        ).pack(pady=20, padx=20)

        if app.lock_active:
            self.update_timer()

        return tab

    def start(self):
        """Public wrapper to start a focus session."""
        return self.start_focus_session()

    def stop(self):
        """Public wrapper to stop a focus session."""
        return self.stop_focus_session()

    def update_timer(self):
        """Public wrapper to refresh the timer display."""
        return self.update_focus_ui()

    def start_focus_session(self):
        """Start a focus lock session."""
        admin_check = getattr(self.app, "is_admin", None)
        if not callable(admin_check) or not admin_check():
            messagebox.showerror(
                "Admin Required",
                "Please run as administrator to enable focus lock.",
            )
            return

        duration = int(self.app.duration_var.get())
        self.app.lock_end_time = datetime.datetime.now() + datetime.timedelta(
            minutes=duration
        )
        self.app.lock_active = True

        self.app.save_json(
            self.app.lock_state_file,
            {
                "end_time": self.app.lock_end_time.isoformat(),
                "hard_mode": self.app.config["hard_mode"],
            },
        )

        self.app.apply_blocks()
        self.update_focus_ui()

        self.app.lock_thread = threading.Thread(
            target=self.lock_countdown,
            daemon=True,
        )
        self.app.lock_thread.start()

        messagebox.showinfo(
            "Focus Lock Active",
            f"Focus mode enabled for {duration} minutes!",
        )

    def stop_focus_session(self):
        """Stop the focus session."""
        if self.app.config["hard_mode"]:
            messagebox.showwarning(
                "Hard Mode",
                "Hard mode is enabled. Session cannot be stopped early!",
            )
            return

        self.app.lock_active = False
        self.app.lock_end_time = None
        self.app.remove_blocks()
        self.update_focus_ui()

        if self.app.lock_state_file.exists():
            self.app.lock_state_file.unlink()

        messagebox.showinfo("Focus Lock", "Focus session stopped.")

    def lock_countdown(self):
        """Background thread to monitor lock time."""
        while self.app.lock_active and datetime.datetime.now() < self.app.lock_end_time:
            time.sleep(1)
            self.app.root.after(0, self.update_focus_ui)

        if self.app.lock_active:
            duration = int(self.app.duration_var.get())
            self.app.update_stats(duration)

            self.app.lock_active = False
            self.app.lock_end_time = None
            self.app.remove_blocks()
            self.app.root.after(0, self.update_focus_ui)
            self.app.root.after(0, self.app.dashboard_tab.update_dashboard)

            if self.app.lock_state_file.exists():
                self.app.lock_state_file.unlink()

            self.app.root.after(
                0,
                lambda: messagebox.showinfo(
                    "🎉 Session Complete!",
                    f"Great job! You completed a {duration} minute focus session.\n\n"
                    f"Total focus time: {self.app.stats['total_focus_time'] // 60}h "
                    f"{self.app.stats['total_focus_time'] % 60}m",
                ),
            )

    def update_focus_ui(self):
        """Update the focus tab UI."""
        if self.app.lock_active and self.app.lock_end_time:
            remaining = self.app.lock_end_time - datetime.datetime.now()
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)

            self.app.status_label.config(
                text=f"🔒 Focus Mode Active\n⏱️ {minutes:02d}:{seconds:02d} Remaining",
                fg="white",
                font=("Arial", 18, "bold"),
            )
            self.app.status_frame.config(bg="#10b981")
            self.app.status_label.config(bg="#10b981")

            self.app.start_btn.config(state="disabled")
            self.app.stop_btn.config(
                state="normal" if not self.app.config["hard_mode"] else "disabled"
            )
        else:
            self.app.status_label.config(
                text="✨ Ready to Focus\nNo active session",
                fg=self.app.colors["text"],
                font=("Arial", 16),
            )
            self.app.status_frame.config(bg="#e0e7ff")
            self.app.status_label.config(bg="#e0e7ff")

            self.app.start_btn.config(state="normal")
            self.app.stop_btn.config(state="disabled")
            app.update_focus_ui()

        return tab
