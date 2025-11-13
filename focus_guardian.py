"""Focus Guardian - ADHD Productivity Application."""
from __future__ import annotations

import datetime
import json
import threading
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from core import blocking, blocks as block_utils, persistence, scheduler
from ui import dashboard, focus_tab, planner_tab, schedule_tab, stats_tab, settings_tab

try:
    import pytz

    HAS_PYTZ = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PYTZ = False
    print("Note: pytz not installed. Install with: pip install pytz")


class FocusGuardian:
    """Main Focus Guardian application."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Focus Guardian - ADHD Productivity Suite")
        self.root.geometry("1000x750")

        self.colors = {
            "primary": "#6366f1",
            "success": "#10b981",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6",
            "bg": "#f8fafc",
            "card": "#ffffff",
            "text": "#1e293b",
            "text_light": "#64748b",
        }
        self.root.configure(bg=self.colors["bg"])

        self.data_dir = Path.home() / ".focus_guardian"
        self.data_dir.mkdir(exist_ok=True)

        self.config_file = self.data_dir / "config.json"
        self.schedule_file = self.data_dir / "schedule.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.commitments_file = self.data_dir / "commitments.json"
        self.lock_state_file = self.data_dir / "lock_state.json"
        self.stats_file = self.data_dir / "stats.json"

        self.config: Dict[str, Any]
        self.schedule: Dict[str, Any]
        self.tasks: Dict[str, Any]
        self.commitments: Dict[str, Any]
        self.stats: Dict[str, Any]
        self.load_data()

        self.lock_active = False
        self.lock_end_time: Optional[datetime.datetime] = None
        self.lock_thread: Optional[threading.Thread] = None

        self.check_existing_lock()
        self.create_ui()
        self.monitor_schedule_locks()

    # ------------------------------------------------------------------
    # Data loading & persistence
    # ------------------------------------------------------------------
    def load_data(self) -> None:
        """Load configuration, schedule, commitments, tasks, and stats."""
        (
            self.config,
            self.schedule,
            self.tasks,
            self.commitments,
            self.stats,
        ) = persistence.load_application_state(
            self.config_file,
            self.schedule_file,
            self.tasks_file,
            self.commitments_file,
            self.stats_file,
        )

    def check_existing_lock(self) -> None:
        """Restore lock state if one was active when the app closed."""
        if not self.lock_state_file.exists():
            return

        try:
            with self.lock_state_file.open("r", encoding="utf-8") as handle:
                state = json.load(handle)
            lock_end = datetime.datetime.fromisoformat(state["end_time"])
            if datetime.datetime.now() < lock_end:
                self.lock_active = True
                self.lock_end_time = lock_end
                self.apply_blocks()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def create_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=[20, 10], font=("Arial", 10, "bold"))
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["primary"])],
            foreground=[("selected", "white")],
        )

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        dashboard.create_tab(self)
        focus_tab.create_tab(self)
        planner_tab.create_tab(self)
        schedule_tab.create_tab(self)
        stats_tab.create_tab(self)
        settings_tab.create_tab(self)

    # ------------------------------------------------------------------
    # Dashboard helpers
    # ------------------------------------------------------------------
    def update_dashboard(self) -> None:
        """Refresh dashboard preview."""
        self.dashboard_schedule.delete("1.0", "end")

        if not self.schedule.get("blocks"):
            self.dashboard_schedule.insert(
                "1.0",
                "No schedule for today.\nClick 'Generate Today's Plan' to create one!",
            )
            return

        now = datetime.datetime.now().strftime("%H:%M")
        for block in self.schedule["blocks"][:6]:
            start_12 = block_utils.convert_to_12hr(block["start"])
            end_12 = block_utils.convert_to_12hr(block["end"])
            prefix = "▶️ " if block["start"] <= now < block["end"] else "   "
            icon = "🔒" if block.get("focus_required") else "⏰"
            self.dashboard_schedule.insert(
                "end", f"{prefix}{icon} {start_12} - {end_12}: {block['title']}\n"
            )

    def quick_focus(self, minutes: int) -> None:
        """Start a focus session from the dashboard."""
        self.duration_var.set(str(minutes))
        self.notebook.select(1)
        self.start_focus_session()

    # ------------------------------------------------------------------
    # Schedule handling
    # ------------------------------------------------------------------
    def generate_daily_plan(self) -> None:
        """Generate a schedule via the OpenAI API."""
        api_key = self.config.get("api_key", "")
        if not api_key:
            messagebox.showerror("API Key Missing", "Please add your OpenAI API key in Settings.")
            return

        if HAS_PYTZ:
            now = datetime.datetime.now(pytz.timezone("US/Eastern"))
        else:
            now = datetime.datetime.now()

        today = now.strftime("%A, %B %d, %Y")
        today_name = now.strftime("%A")
        meals_count = self.commitments["preferences"].get("meals_per_day", 3)

        prompt_lines: List[str] = []
        prompt_lines.append(
            "You are an ADHD-optimized daily planner creating TODAY's schedule for "
            + today
            + ".\n"
        )
        prompt_lines.append("CRITICAL RULES:")
        prompt_lines.append("1. ONLY schedule tasks that are EXPLICITLY listed in the task list below")
        prompt_lines.append("2. DO NOT invent, create, or make up any tasks")
        prompt_lines.append(
            "3. ABSOLUTELY NO GAPS - Every single minute from wake time to sleep time MUST be assigned to a block"
        )
        prompt_lines.append(
            f"4. MANDATORY: Include EXACTLY {meals_count} meals spread throughout the day:"
        )
        meal_instructions = {
            3: ["Breakfast (morning, after waking)", "Lunch (midday)", "Dinner (evening)"],
            4: [
                "Breakfast (morning, after waking)",
                "Snack/Brunch (mid-morning)",
                "Lunch (midday)",
                "Dinner (evening)",
            ],
            5: [
                "Breakfast (morning, after waking)",
                "Mid-morning snack",
                "Lunch (midday)",
                "Afternoon snack",
                "Dinner (evening)",
            ],
            6: [
                "Breakfast (morning)",
                "Mid-morning snack",
                "Lunch (midday)",
                "Afternoon snack",
                "Dinner (evening)",
                "Evening snack",
            ],
        }
        for line in meal_instructions.get(meals_count, []):
            prompt_lines.append(f"   - {line}")
        if meals_count not in meal_instructions:
            prompt_lines.append(f"   - Distribute {meals_count} meals evenly throughout the day")
        prompt_lines.append("   Each meal should be 20-30 minutes")
        prompt_lines.append("   Meals can be scheduled flexibly between tasks/events")
        prompt_lines.append("5. After scheduling tasks, recurring events, and meals, fill ALL remaining minutes with either:")
        prompt_lines.append("   - Focus Blocks (title: 'Focus Block', focus_required: true)")
        prompt_lines.append("   - Explicit task/todo reminders pulled from the task list")
        prompt_lines.append("   Absolutely do NOT use labels like Free Time, Personal Projects, Buffer, Admin, or Rest.")
        prompt_lines.append(
            "6. REMEMBER: NO GAPS ALLOWED - if there's 10 minutes between events, create a 10-minute focus block or task reminder"
        )

        todays_events = [
            event
            for event in self.commitments.get("weekly_events", [])
            if event.get("day") == today_name
        ]

        prompt_lines.append("\nUSER DATA:\n" + json.dumps(self.commitments, indent=2))
        prompt_lines.append(
            "\nTODAY'S MANDATORY WEEKLY EVENTS (keep these EXACT times):\n"
            + json.dumps(todays_events, indent=2)
            + "\nIf this list is empty there are no fixed events today. Otherwise, each event must appear exactly at its start and end times without overlap."
        )
        prompt_lines.append(
            "\nTASKS TO SCHEDULE (ONLY THESE - DO NOT ADD ANY OTHERS):\n" + json.dumps(self.tasks, indent=2)
        )
        prefs = self.commitments["preferences"]
        prompt_lines.append("\nSCHEDULE REQUIREMENTS:")
        prompt_lines.append(f"- Start day at: {prefs.get('wake_time', '07:00')}")
        prompt_lines.append(f"- End day at: {prefs.get('sleep_time', '23:00')}")
        prompt_lines.append(f"- MUST include EXACTLY {meals_count} meal blocks")
        prompt_lines.append(f"- Focus blocks: {prefs.get('focus_block_length', 50)} min")
        prompt_lines.append(f"- Breaks after focus: {prefs.get('break_length', 10)} min")
        prompt_lines.append("- NO GAPS WHATSOEVER - Every minute must be in a block")
        prompt_lines.append("- Include morning routine at wake time")
        prompt_lines.append("- Include evening routine before sleep time")
        prompt_lines.append("- Add the user's weekly recurring events exactly at their listed times")
        prompt_lines.append("- For tasks: use the EXACT task name from the list")
        prompt_lines.append("- Mark deep work/study tasks as 'focus_required: true'")

        if not self.tasks.get("tasks"):
            focus_len = prefs.get("focus_block_length", 50)
            break_len = prefs.get("break_length", 10)
            prompt_lines.append(
                "\nSPECIAL INSTRUCTION: There are no one-time tasks today. Fill all non-meal, non-event time with repeated 'Focus Block' entries "
                f"of {focus_len} minutes (focus_required: true) followed by {break_len}-minute breaks as needed."
                " Do not create any other block types for these periods."
            )

        prompt_lines.append(
            """\nOUTPUT FORMAT (JSON only, no markdown):
{
  "blocks": [
    {
      "start": "07:00",
      "end": "07:30",
      "type": "morning_routine",
      "title": "Morning Routine",
      "focus_required": false
    },
    {
      "start": "07:30",
      "end": "08:00",
      "type": "meal",
      "title": "Breakfast",
      "focus_required": false
    }
  ]
}

CRITICAL: Notice how each block's end time EQUALS the next block's start time - NO GAPS!
Remember:
- Use EXACT task names from the provided list
- Include EXACTLY the specified number of meals
- Fill ALL time from wake to sleep with blocks
- NO time gaps allowed between blocks"""
        )

        try:
            import urllib.request

            payload = json.dumps(
                {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "\n".join(prompt_lines)}],
                    "temperature": 0.0,
                }
            ).encode("utf-8")

            request = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )

            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode("utf-8"))

            content = result["choices"][0]["message"]["content"].strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            self.schedule = json.loads(content.strip())
            self.post_process_schedule(meals_count, todays_events)
            persistence.save_json(self.schedule_file, self.schedule)
            self.display_schedule()
            self.update_dashboard()
            messagebox.showinfo("Success", "Daily plan generated!")
        except Exception as exc:
            messagebox.showerror("Generation Error", f"Failed to generate plan: {exc}\n\nPlease check your API key.")

    def post_process_schedule(
        self, meals_count: int, todays_events: Optional[Sequence[Dict[str, Any]]] = None
    ) -> None:
        """Normalize and enforce constraints on the generated schedule."""
        blocks = scheduler.post_process_schedule(
            self.schedule,
            self.commitments,
            self.tasks,
            meals_count,
            todays_events,
        )
        self.schedule["blocks"] = blocks

    def display_schedule(self) -> None:
        """Render schedule within the planner tab."""
        self.schedule_display.delete("1.0", "end")
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.schedule_display.insert("end", f"📅 TODAY'S SCHEDULE - {today}\n", "title")
        self.schedule_display.insert("end", "─" * 60 + "\n\n")

        for block in self.schedule.get("blocks", []):
            icon = "🔒 " if block.get("focus_required") else "⏰ "
            start_12 = block_utils.convert_to_12hr(block["start"])
            end_12 = block_utils.convert_to_12hr(block["end"])
            tag = "focus_time" if block.get("focus_required") else "time"
            self.schedule_display.insert("end", icon)
            self.schedule_display.insert("end", f"{start_12} - {end_12}\n", tag)
            self.schedule_display.insert("end", f"   {block['title']}\n", "block_title")
            if block.get("focus_required"):
                self.schedule_display.insert(
                    "end",
                    "   🎯 Focus Block - Distractions will be blocked\n",
                    "type_label",
                )
            else:
                self.schedule_display.insert("end", f"   Type: {block['type']}\n", "type_label")
            self.schedule_display.insert("end", "\n")

    # ------------------------------------------------------------------
    # Schedule persistence from UI
    # ------------------------------------------------------------------
    def save_all_schedule_data(self) -> None:
        """Persist preferences, events, and tasks collected from the schedule tab."""
        try:
            wake_hour = int(self.wake_hour_var.get())
            if self.wake_period_var.get() == "PM" and wake_hour != 12:
                wake_hour += 12
            elif self.wake_period_var.get() == "AM" and wake_hour == 12:
                wake_hour = 0
            wake_time = f"{wake_hour:02d}:{self.wake_min_var.get()}"

            sleep_hour = int(self.sleep_hour_var.get())
            if self.sleep_period_var.get() == "PM" and sleep_hour != 12:
                sleep_hour += 12
            elif self.sleep_period_var.get() == "AM" and sleep_hour == 12:
                sleep_hour = 0
            sleep_time = f"{sleep_hour:02d}:{self.sleep_min_var.get()}"

            self.commitments["preferences"] = {
                "wake_time": wake_time,
                "sleep_time": sleep_time,
                "gym_frequency": self.gym_freq_var.get(),
                "focus_block_length": self.focus_length_var.get(),
                "break_length": self.break_length_var.get(),
                "meals_per_day": self.meals_var.get(),
            }

            self.commitments["weekly_events"] = []
            for entry in self.event_entries:
                title = entry["title"].get().strip()
                if not title:
                    continue

                start_hour = int(entry["start_hour"].get())
                if entry["start_period"].get() == "PM" and start_hour != 12:
                    start_hour += 12
                elif entry["start_period"].get() == "AM" and start_hour == 12:
                    start_hour = 0
                start_time = f"{start_hour:02d}:{entry['start_min'].get()}"

                end_hour = int(entry["end_hour"].get())
                if entry["end_period"].get() == "PM" and end_hour != 12:
                    end_hour += 12
                elif entry["end_period"].get() == "AM" and end_hour == 12:
                    end_hour = 0
                end_time = f"{end_hour:02d}:{entry['end_min'].get()}"

                self.commitments["weekly_events"].append(
                    {
                        "day": entry["day"].get(),
                        "start": start_time,
                        "end": end_time,
                        "title": title,
                    }
                )

            self.tasks["tasks"] = []
            for entry in self.task_entries:
                name = entry["name"].get().strip()
                if not name:
                    continue
                self.tasks["tasks"].append(
                    {
                        "name": name,
                        "duration": int(entry["duration"].get()),
                        "priority": entry["priority"].get(),
                    }
                )

            persistence.save_json(self.commitments_file, self.commitments)
            persistence.save_json(self.tasks_file, self.tasks)
            messagebox.showinfo("Success", "✅ All schedule data saved successfully!")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save: {exc}")

    # ------------------------------------------------------------------
    # Statistics tab helpers
    # ------------------------------------------------------------------
    def reset_stats(self) -> None:
        """Clear tracked focus statistics."""
        if not messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            return

        self.stats = persistence.DEFAULT_STATS.copy()
        persistence.save_json(self.stats_file, self.stats)
        self.notebook.select(0)
        self.update_dashboard()
        messagebox.showinfo("Stats Reset", "All statistics have been reset!")

    # ------------------------------------------------------------------
    # Focus session / blocking controls
    # ------------------------------------------------------------------
    def start_focus_session(self) -> None:
        if not blocking.is_admin():
            messagebox.showerror(
                "Admin Required", "Please run as administrator to enable focus lock."
            )
            return

        duration = int(self.duration_var.get())
        self.lock_end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
        self.lock_active = True

        persistence.save_json(
            self.lock_state_file,
            {"end_time": self.lock_end_time.isoformat(), "hard_mode": self.config.get("hard_mode", False)},
        )

        self.apply_blocks()
        self.update_focus_ui()

        self.lock_thread = threading.Thread(target=self.lock_countdown, daemon=True)
        self.lock_thread.start()

        messagebox.showinfo("Focus Lock Active", f"Focus mode enabled for {duration} minutes!")

    def stop_focus_session(self) -> None:
        if self.config.get("hard_mode"):
            messagebox.showwarning("Hard Mode", "Hard mode is enabled. Session cannot be stopped early!")
            return

        self.lock_active = False
        self.lock_end_time = None
        self.remove_blocks()
        self.update_focus_ui()
        if self.lock_state_file.exists():
            self.lock_state_file.unlink()
        messagebox.showinfo("Focus Lock", "Focus session stopped.")

    def lock_countdown(self) -> None:
        while self.lock_active and datetime.datetime.now() < (self.lock_end_time or datetime.datetime.now()):
            time.sleep(1)
            self.root.after(0, self.update_focus_ui)

        if not self.lock_active:
            return

        duration = int(self.duration_var.get())
        self.update_stats(duration)
        self.lock_active = False
        self.lock_end_time = None
        self.remove_blocks()
        self.root.after(0, self.update_focus_ui)
        self.root.after(0, self.update_dashboard)
        if self.lock_state_file.exists():
            self.lock_state_file.unlink()
        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "🎉 Session Complete!",
                f"Great job! You completed a {duration} minute focus session.\n\n"
                f"Total focus time: {self.stats['total_focus_time'] // 60}h {self.stats['total_focus_time'] % 60}m",
            ),
        )

    def update_stats(self, duration_minutes: int) -> None:
        self.stats["total_focus_time"] += duration_minutes
        self.stats["sessions_completed"] += 1

        today = datetime.datetime.now().date().isoformat()
        last_date = self.stats.get("last_session_date")
        if last_date:
            last = datetime.datetime.fromisoformat(last_date).date()
            diff = (datetime.datetime.now().date() - last).days
            if diff == 1:
                self.stats["current_streak"] += 1
            elif diff > 1:
                self.stats["current_streak"] = 1
        else:
            self.stats["current_streak"] = 1

        if self.stats["current_streak"] > self.stats.get("longest_streak", 0):
            self.stats["longest_streak"] = self.stats["current_streak"]

        self.stats["last_session_date"] = today
        persistence.save_json(self.stats_file, self.stats)

    def update_focus_ui(self) -> None:
        if self.lock_active and self.lock_end_time:
            remaining = self.lock_end_time - datetime.datetime.now()
            minutes = max(0, int(remaining.total_seconds() // 60))
            seconds = max(0, int(remaining.total_seconds() % 60))
            self.status_label.config(
                text=f"🔒 Focus Mode Active\n⏱️ {minutes:02d}:{seconds:02d} Remaining",
                fg="white",
                font=("Arial", 18, "bold"),
            )
            self.status_frame.config(bg="#10b981")
            self.status_label.config(bg="#10b981")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal" if not self.config.get("hard_mode") else "disabled")
        else:
            self.status_label.config(
                text="✨ Ready to Focus\nNo active session",
                fg=self.colors["text"],
                font=("Arial", 16),
            )
            self.status_frame.config(bg="#e0e7ff")
            self.status_label.config(bg="#e0e7ff")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def apply_blocks(self) -> None:
        try:
            blocking.apply_blocks(self.config.get("blocked_sites", []))
        except Exception as exc:
            messagebox.showerror("Block Error", f"Failed to apply blocks: {exc}")

    def remove_blocks(self) -> None:
        try:
            blocking.remove_blocks()
        except Exception as exc:
            messagebox.showerror("Unblock Error", f"Failed to remove blocks: {exc}")

    def monitor_schedule_locks(self) -> None:
        def check_schedule() -> None:
            while True:
                if self.schedule.get("blocks") and not self.lock_active:
                    now = datetime.datetime.now().strftime("%H:%M")
                    for block in self.schedule["blocks"]:
                        if block.get("focus_required") and block["start"] <= now < block["end"]:
                            end_time = datetime.datetime.strptime(block["end"], "%H:%M")
                            end_time = end_time.replace(
                                year=datetime.datetime.now().year,
                                month=datetime.datetime.now().month,
                                day=datetime.datetime.now().day,
                            )
                            if end_time > datetime.datetime.now():
                                self.lock_end_time = end_time
                                self.lock_active = True
                                self.apply_blocks()
                                self.root.after(0, self.update_focus_ui)
                                break
                time.sleep(60)

        threading.Thread(target=check_schedule, daemon=True).start()

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------
    def save_settings(self) -> None:
        if self.config.get("password_hash"):
            password = simpledialog.askstring("Password", "Enter settings password:", show="*")
            if not password:
                return
            if hashlib.sha256(password.encode()).hexdigest() != self.config["password_hash"]:
                messagebox.showerror("Wrong Password", "Incorrect password!")
                return

        sites = [line.strip() for line in self.sites_text.get("1.0", "end").splitlines() if line.strip()]
        apps = [line.strip() for line in self.apps_text.get("1.0", "end").splitlines() if line.strip()]
        self.config["blocked_sites"] = sites
        self.config["blocked_apps"] = apps
        self.config["hard_mode"] = self.hard_mode_var.get()
        self.config["api_key"] = self.api_key_entry.get()
        persistence.save_json(self.config_file, self.config)
        messagebox.showinfo("Success", "Settings saved!")

    def set_password(self) -> None:
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("No Password", "Please enter a password.")
            return
        confirm = simpledialog.askstring("Confirm", "Re-enter password:", show="*")
        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords don't match!")
            return
        self.config["password_hash"] = hashlib.sha256(password.encode()).hexdigest()
        persistence.save_json(self.config_file, self.config)
        self.password_entry.delete(0, "end")
        messagebox.showinfo(
            "Success", "Password set! Share this with your accountability partner."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = FocusGuardian(root)
    root.mainloop()
