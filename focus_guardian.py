"""Focus Guardian - ADHD Productivity Application

IMPORTANT: Run this as Administrator for blocking features to work!
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import json
import os
import sys
import subprocess
import ctypes
import datetime
import threading
import time
from pathlib import Path
import hashlib

# Optional timezone support
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False
    print("Note: pytz not installed. Install with: pip install pytz")

def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class FocusGuardian:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Guardian - ADHD Productivity Suite")
        self.root.geometry("1000x750")
        
        # Modern color scheme
        self.colors = {
            'primary': '#6366f1',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'bg': '#f8fafc',
            'card': '#ffffff',
            'text': '#1e293b',
            'text_light': '#64748b'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Data directory
        self.data_dir = Path.home() / ".focus_guardian"
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.config_file = self.data_dir / "config.json"
        self.schedule_file = self.data_dir / "schedule.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.commitments_file = self.data_dir / "commitments.json"
        self.lock_state_file = self.data_dir / "lock_state.json"
        self.stats_file = self.data_dir / "stats.json"
        
        # Load or initialize data
        self.load_data()
        
        # Statistics tracking
        self.stats = self.load_json(self.stats_file, {
            'total_focus_time': 0,
            'sessions_completed': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'last_session_date': None
        })
        
        # Active lock tracking
        self.lock_active = False
        self.lock_end_time = None
        self.lock_thread = None
        
        # Check for existing lock
        self.check_existing_lock()
        
        # Create UI
        self.create_ui()
        
        # Start lock monitoring
        self.monitor_schedule_locks()

    def load_data(self):
        """Load all configuration and data files"""
        default_config = {
            "blocked_sites": [
                "youtube.com", "www.youtube.com",
                "reddit.com", "www.reddit.com",
                "tiktok.com", "www.tiktok.com",
                "twitter.com", "x.com",
                "facebook.com", "instagram.com",
                "twitch.tv", "netflix.com"
            ],
            "blocked_apps": [
                "steam.exe", "chrome.exe", "firefox.exe",
                "msedge.exe", "discord.exe"
            ],
            "hard_mode": False,
            "run_on_startup": False,
            "password_hash": None,
            "api_key": ""
        }
        
        self.config = self.load_json(self.config_file, default_config)
        self.schedule = self.load_json(self.schedule_file, {"blocks": []})
        self.tasks = self.load_json(self.tasks_file, {"tasks": []})
        self.commitments = self.load_json(self.commitments_file, {
            "weekly_events": [],
            "preferences": {
                "wake_time": "07:00",
                "sleep_time": "23:00",
                "gym_frequency": 3,
                "focus_block_length": 50,
                "break_length": 10,
                "meals_per_day": 3
            }
        })

    def load_json(self, path, default):
        """Load JSON file or return default"""
        if path.exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def save_json(self, path, data):
        """Save data to JSON file"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def check_existing_lock(self):
        """Check if a lock was active when app closed"""
        if self.lock_state_file.exists():
            try:
                with open(self.lock_state_file, 'r') as f:
                    state = json.load(f)
                
                lock_end = datetime.datetime.fromisoformat(state['end_time'])
                if datetime.datetime.now() < lock_end:
                    self.lock_active = True
                    self.lock_end_time = lock_end
                    self.apply_blocks()
                else:
                    self.lock_state_file.unlink()
            except:
                pass

    def create_ui(self):
        """Create the main user interface"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], font=('Arial', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.colors['primary'])], 
                  foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=0, pady=0)
        
        self.create_dashboard_tab()
        self.create_focus_tab()
        self.create_planner_tab()
        self.create_schedule_tab()
        self.create_stats_tab()
        self.create_settings_tab()

    def create_dashboard_tab(self):
        """Dashboard overview tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📊 Dashboard")
        
        header = tk.Frame(tab, bg=self.colors['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(
            header, 
            text="Focus Guardian",
            font=('Arial', 24, 'bold'),
            bg=self.colors['primary'],
            fg='white'
        )
        title.pack(pady=20)
        
        content = tk.Frame(tab, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=30, pady=30)
        
        stats_row = tk.Frame(content, bg=self.colors['bg'])
        stats_row.pack(fill='x', pady=(0, 20))
        
        self.create_stat_card(
            stats_row, 
            "⏱️ Total Focus Time",
            f"{self.stats['total_focus_time'] // 60}h {self.stats['total_focus_time'] % 60}m",
            self.colors['primary']
        ).pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_stat_card(
            stats_row,
            "✅ Sessions Completed",
            str(self.stats['sessions_completed']),
            self.colors['success']
        ).pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_stat_card(
            stats_row,
            "🔥 Current Streak",
            f"{self.stats['current_streak']} days",
            self.colors['warning']
        ).pack(side='left', fill='both', expand=True, padx=5)
        
        schedule_card = tk.Frame(content, bg=self.colors['card'], relief='solid', bd=1)
        schedule_card.pack(fill='both', expand=True, pady=10)
        
        tk.Label(
            schedule_card,
            text="📅 Today's Schedule Preview",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=15, padx=15, anchor='w')
        
        self.dashboard_schedule = scrolledtext.ScrolledText(
            schedule_card,
            height=10,
            font=('Consolas', 10),
            wrap='word',
            bg='#f8fafc',
            relief='flat'
        )
        self.dashboard_schedule.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        actions = tk.Frame(content, bg=self.colors['bg'])
        actions.pack(fill='x', pady=10)
        
        tk.Button(
            actions,
            text="🚀 Start Quick Focus",
            command=lambda: self.quick_focus(25),
            font=('Arial', 12, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            padx=20,
            pady=12,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            actions,
            text="🤖 Generate Today's Plan",
            command=self.generate_daily_plan,
            font=('Arial', 12, 'bold'),
            bg=self.colors['info'],
            fg='white',
            padx=20,
            pady=12,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        self.update_dashboard()

    def create_stat_card(self, parent, title, value, color):
        """Create a statistics card"""
        card = tk.Frame(parent, bg=self.colors['card'], relief='solid', bd=1)
        
        inner = tk.Frame(card, bg=color)
        inner.pack(fill='x')
        
        tk.Label(
            inner,
            text=title,
            font=('Arial', 10),
            bg=color,
            fg='white'
        ).pack(pady=(10, 5))
        
        tk.Label(
            card,
            text=value,
            font=('Arial', 24, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=15)
        
        return card

    def update_dashboard(self):
        """Update dashboard with current data"""
        self.dashboard_schedule.delete('1.0', 'end')
        
        if not self.schedule.get('blocks'):
            self.dashboard_schedule.insert('1.0', "No schedule for today.\nClick 'Generate Today's Plan' to create one!")
        else:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            
            for block in self.schedule['blocks'][:6]:
                start_12 = self.convert_to_12hr(block['start'])
                end_12 = self.convert_to_12hr(block['end'])
                
                if block['start'] <= current_time < block['end']:
                    prefix = "▶️ "
                else:
                    prefix = "   "
                
                icon = "🔒" if block.get('focus_required') else "⏰"
                self.dashboard_schedule.insert('end', f"{prefix}{icon} {start_12} - {end_12}: {block['title']}\n")

    def quick_focus(self, minutes):
        """Quick focus session from dashboard"""
        self.duration_var.set(str(minutes))
        self.notebook.select(1)
        self.start_focus_session()

    def create_focus_tab(self):
        """Main focus lock tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🔒 Focus Lock")
        
        title_frame = tk.Frame(tab, bg=self.colors['card'])
        title_frame.pack(fill='x', pady=(20, 0), padx=20)
        
        title = tk.Label(
            title_frame,
            text="Focus Session",
            font=('Arial', 28, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        title.pack(pady=20)
        
        self.status_frame = tk.Frame(tab, bg='#e0e7ff', relief='flat', bd=0)
        self.status_frame.pack(pady=20, padx=40, fill='x', ipady=20)
        
        self.status_label = tk.Label(
            self.status_frame, 
            text="✨ Ready to Focus\nNo active session",
            font=('Arial', 16),
            bg='#e0e7ff',
            fg=self.colors['text']
        )
        self.status_label.pack(pady=15)
        
        duration_frame = tk.Frame(tab, bg=self.colors['bg'])
        duration_frame.pack(pady=30)
        
        tk.Label(
            duration_frame,
            text="Choose Focus Duration:",
            font=('Arial', 13),
            bg=self.colors['bg'],
            fg=self.colors['text']
        ).pack(pady=(0, 10))
        
        button_row = tk.Frame(duration_frame, bg=self.colors['bg'])
        button_row.pack()
        
        self.duration_var = tk.StringVar(value="25")
        
        for duration in ["25", "50", "90", "120"]:
            btn = tk.Radiobutton(
                button_row,
                text=f"{duration} min",
                variable=self.duration_var,
                value=duration,
                font=('Arial', 11, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text'],
                selectcolor=self.colors['primary'],
                indicatoron=False,
                width=10,
                relief='flat',
                padx=15,
                pady=10,
                cursor='hand2'
            )
            btn.pack(side='left', padx=5)
        
        button_frame = tk.Frame(tab, bg=self.colors['bg'])
        button_frame.pack(pady=30)
        
        self.start_btn = tk.Button(
            button_frame,
            text="🚀 Start Focus Session",
            command=self.start_focus_session,
            font=('Arial', 16, 'bold'),
            bg=self.colors['success'],
            fg='white',
            padx=40,
            pady=20,
            relief='flat',
            cursor='hand2',
            borderwidth=0
        )
        self.start_btn.pack(side='left', padx=10)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ Stop Session",
            command=self.stop_focus_session,
            font=('Arial', 16, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            padx=40,
            pady=20,
            relief='flat',
            cursor='hand2',
            state='disabled',
            borderwidth=0
        )
        self.stop_btn.pack(side='left', padx=10)
        
        info_card = tk.Frame(tab, bg=self.colors['card'], relief='solid', bd=1)
        info_card.pack(pady=20, padx=60, fill='x')
        
        info_text = """
    Focus Lock Features:

Blocks distracting websites (YouTube, Reddit, TikTok, etc.)
Blocks specified applications  
Timer-based sessions with countdown
Re-enables access automatically when done
Hard Mode prevents early stopping (enable in Settings)
        """
        info = tk.Label(
            info_card,
            text=info_text,
            font=('Arial', 11),
            justify='left',
            bg=self.colors['card'],
            fg=self.colors['text_light']
        )
        info.pack(pady=20, padx=20)
        
        if self.lock_active:
            self.update_focus_ui()

    def create_planner_tab(self):
        """AI planner tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🤖 AI Planner")
        
        header = tk.Frame(tab, bg=self.colors['card'])
        header.pack(fill='x', pady=(20, 0), padx=20)
        
        title = tk.Label(
            header,
            text="AI Daily Planner",
            font=('Arial', 24, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        title.pack(pady=20)
        
        generate_btn = tk.Button(
            tab,
            text="✨ Generate Today's Plan",
            command=self.generate_daily_plan,
            font=('Arial', 14, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            padx=40,
            pady=18,
            relief='flat',
            cursor='hand2'
        )
        generate_btn.pack(pady=15)
        
        schedule_frame = tk.Frame(tab, bg=self.colors['card'], relief='solid', bd=1)
        schedule_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(
            schedule_frame,
            text="📋 Today's Schedule:",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=15, padx=15, anchor='w')
        
        self.schedule_display = scrolledtext.ScrolledText(
            schedule_frame,
            height=20,
            font=('Consolas', 11),
            wrap='word',
            bg='#f8fafc',
            relief='flat',
            padx=10,
            pady=10
        )
        self.schedule_display.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        self.display_schedule()

    def create_schedule_tab(self):
        """Schedule and tasks management tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📅 Schedule & Tasks")
        
        canvas = tk.Canvas(tab, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        pref_frame = tk.LabelFrame(
            scrollable_frame, 
            text="⚙️ Daily Preferences", 
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            padx=25,
            pady=20
        )
        pref_frame.pack(fill='x', padx=30, pady=15)
        
        prefs = self.commitments.get('preferences', {})
        
        # Wake time with AM/PM
        row1 = tk.Frame(pref_frame, bg=self.colors['card'])
        row1.pack(fill='x', pady=8)
        tk.Label(row1, text="⏰ Wake Time:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        
        wake_frame = tk.Frame(row1, bg=self.colors['card'])
        wake_frame.pack(side='left')
        self.wake_hour_var = tk.StringVar(value='7')
        self.wake_min_var = tk.StringVar(value='00')
        self.wake_period_var = tk.StringVar(value='AM')
        
        tk.Spinbox(wake_frame, from_=1, to=12, textvariable=self.wake_hour_var, width=4, font=('Arial', 11)).pack(side='left', padx=2)
        tk.Label(wake_frame, text=":", font=('Arial', 11, 'bold'), bg=self.colors['card']).pack(side='left')
        tk.Spinbox(wake_frame, from_=0, to=59, textvariable=self.wake_min_var, width=4, format='%02.0f', font=('Arial', 11)).pack(side='left', padx=2)
        ttk.Combobox(wake_frame, textvariable=self.wake_period_var, values=['AM', 'PM'], width=5, state='readonly', font=('Arial', 10)).pack(side='left', padx=5)
        
        # Sleep time with AM/PM
        row2 = tk.Frame(pref_frame, bg=self.colors['card'])
        row2.pack(fill='x', pady=8)
        tk.Label(row2, text="🌙 Sleep Time:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        
        sleep_frame = tk.Frame(row2, bg=self.colors['card'])
        sleep_frame.pack(side='left')
        self.sleep_hour_var = tk.StringVar(value='11')
        self.sleep_min_var = tk.StringVar(value='00')
        self.sleep_period_var = tk.StringVar(value='PM')
        
        tk.Spinbox(sleep_frame, from_=1, to=12, textvariable=self.sleep_hour_var, width=4, font=('Arial', 11)).pack(side='left', padx=2)
        tk.Label(sleep_frame, text=":", font=('Arial', 11, 'bold'), bg=self.colors['card']).pack(side='left')
        tk.Spinbox(sleep_frame, from_=0, to=59, textvariable=self.sleep_min_var, width=4, format='%02.0f', font=('Arial', 11)).pack(side='left', padx=2)
        ttk.Combobox(sleep_frame, textvariable=self.sleep_period_var, values=['AM', 'PM'], width=5, state='readonly', font=('Arial', 10)).pack(side='left', padx=5)
        
        # Gym frequency with slider
        row3 = tk.Frame(pref_frame, bg=self.colors['card'])
        row3.pack(fill='x', pady=8)
        tk.Label(row3, text="💪 Gym Days/Week:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        self.gym_freq_var = tk.IntVar(value=prefs.get('gym_frequency', 3))
        gym_scale = tk.Scale(row3, from_=0, to=7, orient='horizontal', variable=self.gym_freq_var, bg=self.colors['card'], font=('Arial', 10))
        gym_scale.pack(side='left', padx=5)
        
        # Focus block with slider
        row4 = tk.Frame(pref_frame, bg=self.colors['card'])
        row4.pack(fill='x', pady=8)
        tk.Label(row4, text="🎯 Focus Block:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        self.focus_length_var = tk.IntVar(value=prefs.get('focus_block_length', 50))
        focus_scale = tk.Scale(row4, from_=25, to=90, orient='horizontal', variable=self.focus_length_var, bg=self.colors['card'], font=('Arial', 10))
        focus_scale.pack(side='left', padx=5)
        tk.Label(row4, text="minutes", font=('Arial', 10), bg=self.colors['card']).pack(side='left')
        
        # Break length with slider
        row5 = tk.Frame(pref_frame, bg=self.colors['card'])
        row5.pack(fill='x', pady=8)
        tk.Label(row5, text="☕ Break Length:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        self.break_length_var = tk.IntVar(value=prefs.get('break_length', 10))
        break_scale = tk.Scale(row5, from_=5, to=30, orient='horizontal', variable=self.break_length_var, bg=self.colors['card'], font=('Arial', 10))
        break_scale.pack(side='left', padx=5)
        tk.Label(row5, text="minutes", font=('Arial', 10), bg=self.colors['card']).pack(side='left')
        
        # Meals per day
        row6 = tk.Frame(pref_frame, bg=self.colors['card'])
        row6.pack(fill='x', pady=8)
        tk.Label(row6, text="🍽️ Meals Per Day:", width=18, anchor='w', font=('Arial', 11), bg=self.colors['card']).pack(side='left', padx=5)
        self.meals_var = tk.IntVar(value=prefs.get('meals_per_day', 3))
        meals_scale = tk.Scale(row6, from_=1, to=5, orient='horizontal', variable=self.meals_var, bg=self.colors['card'], font=('Arial', 10))
        meals_scale.pack(side='left', padx=5)
        tk.Label(row6, text="(1=OMAD, 3=Standard)", font=('Arial', 9), fg=self.colors['text_light'], bg=self.colors['card']).pack(side='left', padx=10)
        
        # Weekly Events with better styling
        events_frame = tk.LabelFrame(
            scrollable_frame,
            text="📅 Weekly Recurring Events",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            padx=25,
            pady=20
        )
        events_frame.pack(fill='both', expand=True, padx=30, pady=15)
        
        tk.Label(
            events_frame,
            text="Classes, work shifts, appointments that repeat weekly",
            fg=self.colors['text_light'],
            font=('Arial', 10),
            bg=self.colors['card']
        ).pack(anchor='w', pady=(0, 15))
        
        self.events_container = tk.Frame(events_frame, bg=self.colors['card'])
        self.events_container.pack(fill='both', expand=True)
        
        self.event_entries = []
        self.load_event_entries()
        
        add_event_btn = tk.Button(
            events_frame,
            text="+ Add Weekly Event",
            command=self.add_event_entry,
            bg=self.colors['primary'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        add_event_btn.pack(pady=15)
        
        # Tasks with better styling
        tasks_frame = tk.LabelFrame(
            scrollable_frame,
            text="✅ Tasks & To-Dos",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            padx=25,
            pady=20
        )
        tasks_frame.pack(fill='both', expand=True, padx=30, pady=15)
        
        tk.Label(
            tasks_frame,
            text="One-time tasks: homework, projects, errands, etc.",
            fg=self.colors['text_light'],
            font=('Arial', 10),
            bg=self.colors['card']
        ).pack(anchor='w', pady=(0, 15))
        
        self.tasks_container = tk.Frame(tasks_frame, bg=self.colors['card'])
        self.tasks_container.pack(fill='both', expand=True)
        
        self.task_entries = []
        self.load_task_entries()
        
        add_task_btn = tk.Button(
            tasks_frame,
            text="+ Add Task",
            command=self.add_task_entry,
            bg=self.colors['primary'],
            fg='white',
            font=('Arial', 11, 'bold'),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        add_task_btn.pack(pady=15)
        
        # Big save button
        save_all_btn = tk.Button(
            scrollable_frame,
            text="💾 Save All Schedule & Tasks",
            command=self.save_all_schedule_data,
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 14, 'bold'),
            padx=50,
            pady=20,
            relief='flat',
            cursor='hand2'
        )
        save_all_btn.pack(pady=30)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def load_event_entries(self):
        """Load existing weekly events into form"""
        for event in self.commitments.get('weekly_events', []):
            self.add_event_entry(event)

    def add_event_entry(self, event_data=None):
        """Add a new event entry row"""
        frame = tk.Frame(self.events_container, relief='solid', bd=1, bg='#ffffff')
        frame.pack(fill='x', pady=8, padx=5)
        
        inner = tk.Frame(frame, bg='#ffffff')
        inner.pack(fill='x', padx=15, pady=15)
        
        # Day selector
        tk.Label(inner, text="Day:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        day_var = tk.StringVar(value=event_data.get('day', 'Monday') if event_data else 'Monday')
        day_menu = ttk.Combobox(inner, textvariable=day_var, values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], width=15, state='readonly', font=('Arial', 10))
        day_menu.grid(row=0, column=1, padx=5, sticky='w')
        
        # Start time with AM/PM
        tk.Label(inner, text="Start:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=2, sticky='w', padx=(20, 5))
        start_frame = tk.Frame(inner, bg='#ffffff')
        start_frame.grid(row=0, column=3, sticky='w')
        
        start_hour_var = tk.StringVar(value='9')
        start_min_var = tk.StringVar(value='00')
        start_period_var = tk.StringVar(value='AM')
        
        tk.Spinbox(start_frame, from_=1, to=12, textvariable=start_hour_var, width=3, font=('Arial', 10)).pack(side='left', padx=1)
        tk.Label(start_frame, text=":", font=('Arial', 10, 'bold'), bg='#ffffff').pack(side='left')
        tk.Spinbox(start_frame, from_=0, to=59, textvariable=start_min_var, width=3, format='%02.0f', font=('Arial', 10)).pack(side='left', padx=1)
        ttk.Combobox(start_frame, textvariable=start_period_var, values=['AM', 'PM'], width=4, state='readonly', font=('Arial', 9)).pack(side='left', padx=3)
        
        # End time with AM/PM
        tk.Label(inner, text="End:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=4, sticky='w', padx=(20, 5))
        end_frame = tk.Frame(inner, bg='#ffffff')
        end_frame.grid(row=0, column=5, sticky='w')
        
        end_hour_var = tk.StringVar(value='10')
        end_min_var = tk.StringVar(value='00')
        end_period_var = tk.StringVar(value='AM')
        
        tk.Spinbox(end_frame, from_=1, to=12, textvariable=end_hour_var, width=3, font=('Arial', 10)).pack(side='left', padx=1)
        tk.Label(end_frame, text=":", font=('Arial', 10, 'bold'), bg='#ffffff').pack(side='left')
        tk.Spinbox(end_frame, from_=0, to=59, textvariable=end_min_var, width=3, format='%02.0f', font=('Arial', 10)).pack(side='left', padx=1)
        ttk.Combobox(end_frame, textvariable=end_period_var, values=['AM', 'PM'], width=4, state='readonly', font=('Arial', 9)).pack(side='left', padx=3)
        
        # Title
        tk.Label(inner, text="Title:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=(10, 0))
        title_var = tk.StringVar(value=event_data.get('title', '') if event_data else '')
        title_entry = tk.Entry(inner, textvariable=title_var, width=60, font=('Arial', 11))
        title_entry.grid(row=1, column=1, columnspan=5, sticky='ew', padx=5, pady=(10, 0))
        
        # Delete button
        del_btn = tk.Button(
            inner,
            text="🗑️ Remove",
            command=lambda: self.remove_event_entry(frame),
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        del_btn.grid(row=0, column=6, rowspan=2, padx=15)
        
        self.event_entries.append({
            'frame': frame,
            'day': day_var,
            'start_hour': start_hour_var,
            'start_min': start_min_var,
            'start_period': start_period_var,
            'end_hour': end_hour_var,
            'end_min': end_min_var,
            'end_period': end_period_var,
            'title': title_var
        })

    def remove_event_entry(self, frame):
        """Remove an event entry"""
        self.event_entries = [e for e in self.event_entries if e['frame'] != frame]
        frame.destroy()

    def load_task_entries(self):
        """Load existing tasks into form"""
        for task in self.tasks.get('tasks', []):
            self.add_task_entry(task)

    def add_task_entry(self, task_data=None):
        """Add a new task entry row"""
        frame = tk.Frame(self.tasks_container, relief='solid', bd=1, bg='#ffffff')
        frame.pack(fill='x', pady=8, padx=5)
        
        inner = tk.Frame(frame, bg='#ffffff')
        inner.pack(fill='x', padx=15, pady=15)
        
        # Task name - full width
        tk.Label(inner, text="Task Name:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        task_var = tk.StringVar(value=task_data.get('name', '') if task_data else '')
        task_entry = tk.Entry(inner, textvariable=task_var, width=50, font=('Arial', 11))
        task_entry.grid(row=0, column=1, columnspan=3, padx=5, sticky='ew')
        
        # Duration with slider
        tk.Label(inner, text="Duration:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', padx=5, pady=(10, 0))
        duration_var = tk.IntVar(value=task_data.get('duration', 30) if task_data else 30)
        duration_frame = tk.Frame(inner, bg='#ffffff')
        duration_frame.grid(row=1, column=1, sticky='w', pady=(10, 0))
        duration_scale = tk.Scale(
            duration_frame,
            from_=15,
            to=120,
            orient='horizontal',
            variable=duration_var,
            bg='#ffffff',
            font=('Arial', 9),
            length=200
        )
        duration_scale.pack(side='left')
        tk.Label(duration_frame, text="minutes", font=('Arial', 10), bg='#ffffff').pack(side='left', padx=5)
        
        # Priority dropdown
        tk.Label(inner, text="Priority:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=1, column=2, sticky='w', padx=(20, 5), pady=(10, 0))
        priority_var = tk.StringVar(value=task_data.get('priority', 'medium') if task_data else 'medium')
        priority_menu = ttk.Combobox(
            inner,
            textvariable=priority_var,
            values=['high', 'medium', 'low'],
            width=12,
            state='readonly',
            font=('Arial', 10)
        )
        priority_menu.grid(row=1, column=3, padx=5, sticky='w', pady=(10, 0))
        
        # Delete button
        del_btn = tk.Button(
            inner,
            text="🗑️ Remove",
            command=lambda: self.remove_task_entry(frame),
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        del_btn.grid(row=0, column=4, rowspan=2, padx=15)
        
        inner.columnconfigure(1, weight=1)
        
        self.task_entries.append({
            'frame': frame,
            'name': task_var,
            'duration': duration_var,
            'priority': priority_var
        })

    def remove_task_entry(self, frame):
        """Remove a task entry"""
        self.task_entries = [t for t in self.task_entries if t['frame'] != frame]
        frame.destroy()

    def save_all_schedule_data(self):
        """Save all preferences, events, and tasks"""
        try:
            # Convert AM/PM to 24-hour format
            wake_hour = int(self.wake_hour_var.get())
            if self.wake_period_var.get() == 'PM' and wake_hour != 12:
                wake_hour += 12
            elif self.wake_period_var.get() == 'AM' and wake_hour == 12:
                wake_hour = 0
            wake_time = f"{wake_hour:02d}:{self.wake_min_var.get()}"
            
            sleep_hour = int(self.sleep_hour_var.get())
            if self.sleep_period_var.get() == 'PM' and sleep_hour != 12:
                sleep_hour += 12
            elif self.sleep_period_var.get() == 'AM' and sleep_hour == 12:
                sleep_hour = 0
            sleep_time = f"{sleep_hour:02d}:{self.sleep_min_var.get()}"
            
            self.commitments['preferences'] = {
                'wake_time': wake_time,
                'sleep_time': sleep_time,
                'gym_frequency': self.gym_freq_var.get(),
                'focus_block_length': self.focus_length_var.get(),
                'break_length': self.break_length_var.get(),
                'meals_per_day': self.meals_var.get()
            }
            
            # Save events with AM/PM conversion
            self.commitments['weekly_events'] = []
            for entry in self.event_entries:
                if entry['title'].get().strip():
                    # Convert start time
                    start_hour = int(entry['start_hour'].get())
                    if entry['start_period'].get() == 'PM' and start_hour != 12:
                        start_hour += 12
                    elif entry['start_period'].get() == 'AM' and start_hour == 12:
                        start_hour = 0
                    start_time = f"{start_hour:02d}:{entry['start_min'].get()}"
                    
                    # Convert end time
                    end_hour = int(entry['end_hour'].get())
                    if entry['end_period'].get() == 'PM' and end_hour != 12:
                        end_hour += 12
                    elif entry['end_period'].get() == 'AM' and end_hour == 12:
                        end_hour = 0
                    end_time = f"{end_hour:02d}:{entry['end_min'].get()}"
                    
                    self.commitments['weekly_events'].append({
                        'day': entry['day'].get(),
                        'start': start_time,
                        'end': end_time,
                        'title': entry['title'].get()
                    })
            
            # Save tasks
            self.tasks['tasks'] = []
            for entry in self.task_entries:
                if entry['name'].get().strip():
                    self.tasks['tasks'].append({
                        'name': entry['name'].get(),
                        'duration': int(entry['duration'].get()),
                        'priority': entry['priority'].get()
                    })
            
            self.save_json(self.commitments_file, self.commitments)
            self.save_json(self.tasks_file, self.tasks)
            
            messagebox.showinfo("Success", "✅ All schedule data saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def create_stats_tab(self):
        """Statistics and achievements tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📈 Stats")
        
        header = tk.Frame(tab, bg=self.colors['card'])
        header.pack(fill='x', pady=(20, 0), padx=20)
        
        tk.Label(
            header,
            text="Your Progress & Achievements",
            font=('Arial', 24, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=20)
        
        stats_grid = tk.Frame(tab, bg=self.colors['bg'])
        stats_grid.pack(fill='both', expand=True, padx=30, pady=20)
        
        row1 = tk.Frame(stats_grid, bg=self.colors['bg'])
        row1.pack(fill='x', pady=10)
        
        self.create_large_stat_card(
            row1,
            "⏱️ Total Focus Time",
            f"{self.stats['total_focus_time'] // 60}h {self.stats['total_focus_time'] % 60}m",
            "Time spent in deep focus",
            self.colors['primary']
        ).pack(side='left', fill='both', expand=True, padx=10)
        
        self.create_large_stat_card(
            row1,
            "✅ Sessions Completed",
            str(self.stats['sessions_completed']),
            "Successful focus sessions",
            self.colors['success']
        ).pack(side='left', fill='both', expand=True, padx=10)
        
        row2 = tk.Frame(stats_grid, bg=self.colors['bg'])
        row2.pack(fill='x', pady=10)
        
        self.create_large_stat_card(
            row2,
            "🔥 Current Streak",
            f"{self.stats['current_streak']} days",
            "Consecutive days of focus",
            self.colors['warning']
        ).pack(side='left', fill='both', expand=True, padx=10)
        
        self.create_large_stat_card(
            row2,
            "🏆 Longest Streak",
            f"{self.stats['longest_streak']} days",
            "Your personal best",
            self.colors['info']
        ).pack(side='left', fill='both', expand=True, padx=10)
        
        achievements = tk.Frame(tab, bg=self.colors['card'], relief='solid', bd=1)
        achievements.pack(fill='x', padx=30, pady=20)
        
        tk.Label(
            achievements,
            text="🎖️ Achievements",
            font=('Arial', 16, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=15, padx=15, anchor='w')
        
        badge_frame = tk.Frame(achievements, bg=self.colors['card'])
        badge_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.show_achievement_badges(badge_frame)
        
        tk.Button(
            tab,
            text="🔄 Reset Statistics",
            command=self.reset_stats,
            font=('Arial', 10),
            bg=self.colors['danger'],
            fg='white',
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        ).pack(pady=10)

    def create_large_stat_card(self, parent, title, value, subtitle, color):
        """Create a large statistics card"""
        card = tk.Frame(parent, bg=self.colors['card'], relief='solid', bd=1)
        
        header = tk.Frame(card, bg=color, height=10)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            card,
            text=title,
            font=('Arial', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=(15, 5))
        
        tk.Label(
            card,
            text=value,
            font=('Arial', 32, 'bold'),
            bg=self.colors['card'],
            fg=color
        ).pack(pady=10)
        
        tk.Label(
            card,
            text=subtitle,
            font=('Arial', 9),
            bg=self.colors['card'],
            fg=self.colors['text_light']
        ).pack(pady=(0, 15))
        
        return card

    def show_achievement_badges(self, parent):
        """Display achievement badges"""
        achievements = [
            ("🌱", "First Step", self.stats['sessions_completed'] >= 1, "Complete your first session"),
            ("💪", "Consistent", self.stats['current_streak'] >= 3, "3 day streak"),
            ("🔥", "On Fire", self.stats['current_streak'] >= 7, "7 day streak"),
            ("⭐", "Focused", self.stats['total_focus_time'] >= 300, "5+ hours of focus"),
            ("🏆", "Master", self.stats['sessions_completed'] >= 50, "50+ sessions"),
        ]
        
        for emoji, name, unlocked, desc in achievements:
            # Badge container
            badge_container = tk.Frame(parent, bg=self.colors['card'])
            badge_container.pack(side='left', padx=15, pady=10)
            
            # Badge card
            badge_card = tk.Frame(
                badge_container,
                bg='#10b981' if unlocked else '#e5e7eb',
                relief='solid',
                bd=2,
                width=100,
                height=100
            )
            badge_card.pack()
            badge_card.pack_propagate(False)
            
            # Emoji
            tk.Label(
                badge_card,
                text=emoji,
                font=('Arial', 36),
                bg='#10b981' if unlocked else '#e5e7eb'
            ).pack(expand=True)
            
            # Name
            tk.Label(
                badge_container,
                text=name,
                font=('Arial', 10, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['card']
            ).pack(pady=(5, 2))
            
            # Description
            tk.Label(
                badge_container,
                text=desc,
                font=('Arial', 8),
                fg=self.colors['text_light'],
                bg=self.colors['card']
            ).pack()

    def reset_stats(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Stats", "Are you sure you want to reset all statistics?"):
            self.stats = {
                'total_focus_time': 0,
                'sessions_completed': 0,
                'current_streak': 0,
                'longest_streak': 0,
                'last_session_date': None
            }
            self.save_json(self.stats_file, self.stats)
            self.notebook.select(0)
            self.update_dashboard()
            messagebox.showinfo("Stats Reset", "All statistics have been reset!")

    def create_settings_tab(self):
        """Settings and configuration tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")
        
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        tk.Label(scrollable_frame, text="Blocked Websites", font=('Arial', 12, 'bold')).pack(pady=10)
        self.sites_text = scrolledtext.ScrolledText(scrollable_frame, height=8, font=('Arial', 10))
        self.sites_text.pack(fill='x', padx=20)
        self.sites_text.insert('1.0', '\n'.join(self.config['blocked_sites']))
        
        tk.Label(scrollable_frame, text="Blocked Applications", font=('Arial', 12, 'bold')).pack(pady=10)
        self.apps_text = scrolledtext.ScrolledText(scrollable_frame, height=8, font=('Arial', 10))
        self.apps_text.pack(fill='x', padx=20)
        self.apps_text.insert('1.0', '\n'.join(self.config['blocked_apps']))
        
        self.hard_mode_var = tk.BooleanVar(value=self.config['hard_mode'])
        hard_mode_check = tk.Checkbutton(
            scrollable_frame,
            text="Hard Mode (Cannot stop sessions early)",
            variable=self.hard_mode_var,
            font=('Arial', 11, 'bold'),
            fg='#f44336'
        )
        hard_mode_check.pack(pady=10)
        
        tk.Label(scrollable_frame, text="OpenAI API Key", font=('Arial', 12, 'bold')).pack(pady=10)
        self.api_key_entry = tk.Entry(scrollable_frame, width=50, show='*', font=('Arial', 10))
        self.api_key_entry.pack()
        self.api_key_entry.insert(0, self.config.get('api_key', ''))
        
        tk.Label(scrollable_frame, text="Settings Password", font=('Arial', 12, 'bold')).pack(pady=10)
        password_frame = tk.Frame(scrollable_frame)
        password_frame.pack()
        
        self.password_entry = tk.Entry(password_frame, show='*', width=30, font=('Arial', 10))
        self.password_entry.pack(side='left', padx=5)
        
        set_password_btn = tk.Button(
            password_frame,
            text="Set Password",
            command=self.set_password,
            bg='#FF9800',
            fg='white'
        )
        set_password_btn.pack(side='left')
        
        save_btn = tk.Button(
            scrollable_frame,
            text="Save Settings",
            command=self.save_settings,
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10
        )
        save_btn.pack(pady=20)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def start_focus_session(self):
        """Start a focus lock session"""
        if not is_admin():
            messagebox.showerror("Admin Required", "Please run as administrator to enable focus lock.")
            return
        
        duration = int(self.duration_var.get())
        self.lock_end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
        self.lock_active = True
        
        self.save_json(self.lock_state_file, {
            'end_time': self.lock_end_time.isoformat(),
            'hard_mode': self.config['hard_mode']
        })
        
        self.apply_blocks()
        self.update_focus_ui()
        
        self.lock_thread = threading.Thread(target=self.lock_countdown, daemon=True)
        self.lock_thread.start()
        
        messagebox.showinfo("Focus Lock Active", f"Focus mode enabled for {duration} minutes!")

    def stop_focus_session(self):
        """Stop the focus session"""
        if self.config['hard_mode']:
            messagebox.showwarning("Hard Mode", "Hard mode is enabled. Session cannot be stopped early!")
            return
        
        self.lock_active = False
        self.lock_end_time = None
        self.remove_blocks()
        self.update_focus_ui()
        
        if self.lock_state_file.exists():
            self.lock_state_file.unlink()
        
        messagebox.showinfo("Focus Lock", "Focus session stopped.")

    def lock_countdown(self):
        """Background thread to monitor lock time"""
        while self.lock_active and datetime.datetime.now() < self.lock_end_time:
            time.sleep(1)
            self.root.after(0, self.update_focus_ui)
        
        if self.lock_active:
            duration = int(self.duration_var.get())
            self.update_stats(duration)
            
            self.lock_active = False
            self.lock_end_time = None
            self.remove_blocks()
            self.root.after(0, self.update_focus_ui)
            self.root.after(0, self.update_dashboard)
            
            if self.lock_state_file.exists():
                self.lock_state_file.unlink()
            
            self.root.after(0, lambda: messagebox.showinfo(
                "🎉 Session Complete!",
                f"Great job! You completed a {duration} minute focus session.\n\n"
                f"Total focus time: {self.stats['total_focus_time'] // 60}h {self.stats['total_focus_time'] % 60}m"
            ))

    def update_stats(self, duration_minutes):
        """Update statistics after a successful session"""
        self.stats['total_focus_time'] += duration_minutes
        self.stats['sessions_completed'] += 1
        
        today = datetime.datetime.now().date().isoformat()
        last_date = self.stats.get('last_session_date')
        
        if last_date:
            last = datetime.datetime.fromisoformat(last_date).date()
            diff = (datetime.datetime.now().date() - last).days
            
            if diff == 0:
                pass
            elif diff == 1:
                self.stats['current_streak'] += 1
            else:
                self.stats['current_streak'] = 1
        else:
            self.stats['current_streak'] = 1
        
        if self.stats['current_streak'] > self.stats['longest_streak']:
            self.stats['longest_streak'] = self.stats['current_streak']
        
        self.stats['last_session_date'] = today
        self.save_json(self.stats_file, self.stats)

    def update_focus_ui(self):
        """Update the focus tab UI"""
        if self.lock_active and self.lock_end_time:
            remaining = self.lock_end_time - datetime.datetime.now()
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            
            self.status_label.config(
                text=f"🔒 Focus Mode Active\n⏱️ {minutes:02d}:{seconds:02d} Remaining",
                fg='white',
                font=('Arial', 18, 'bold')
            )
            self.status_frame.config(bg='#10b981')
            self.status_label.config(bg='#10b981')
            
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal' if not self.config['hard_mode'] else 'disabled')
        else:
            self.status_label.config(
                text="✨ Ready to Focus\nNo active session",
                fg=self.colors['text'],
                font=('Arial', 16)
            )
            self.status_frame.config(bg='#e0e7ff')
            self.status_label.config(bg='#e0e7ff')
            
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')

    def apply_blocks(self):
        """Apply website and app blocks"""
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            
            with open(hosts_path, 'r') as f:
                hosts_content = f.read()
            
            if "# FOCUS_GUARDIAN_START" not in hosts_content:
                with open(hosts_path, 'a') as f:
                    f.write("\n# FOCUS_GUARDIAN_START\n")
                    for site in self.config['blocked_sites']:
                        f.write(f"127.0.0.1 {site}\n")
                    f.write("# FOCUS_GUARDIAN_END\n")
            
        except Exception as e:
            messagebox.showerror("Block Error", f"Failed to apply blocks: {str(e)}")

    def remove_blocks(self):
        """Remove website and app blocks"""
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
            
            with open(hosts_path, 'r') as f:
                lines = f.readlines()
            
            with open(hosts_path, 'w') as f:
                skip = False
                for line in lines:
                    if "# FOCUS_GUARDIAN_START" in line:
                        skip = True
                    elif "# FOCUS_GUARDIAN_END" in line:
                        skip = False
                        continue
                    elif not skip:
                        f.write(line)
            
        except Exception as e:
            messagebox.showerror("Unblock Error", f"Failed to remove blocks: {str(e)}")

    def generate_daily_plan(self):
        """Generate AI-powered daily plan"""
        api_key = self.config.get('api_key', '')
        
        if not api_key:
            messagebox.showerror("API Key Missing", "Please add your OpenAI API key in Settings.")
            return
        
        if HAS_PYTZ:
            est = pytz.timezone('US/Eastern')
            today = datetime.datetime.now(est).strftime("%A, %B %d, %Y")
        else:
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Calculate number of meals to schedule
        meals_count = self.commitments['preferences'].get('meals_per_day', 3)
        
        prompt = "You are an ADHD-optimized daily planner creating TODAY's schedule for " + today + ".\n\n"
        prompt += "CRITICAL RULES:\n"
        prompt += "1. ONLY schedule tasks that are EXPLICITLY listed in the task list below\n"
        prompt += "2. DO NOT invent, create, or make up any tasks\n"
        prompt += "3. ABSOLUTELY NO GAPS - Every single minute from wake time to sleep time MUST be assigned to a block\n"
        prompt += f"4. MANDATORY: Include EXACTLY {meals_count} meals spread throughout the day:\n"
        
        if meals_count == 3:
            prompt += "   - Breakfast (morning, after waking)\n"
            prompt += "   - Lunch (midday)\n"
            prompt += "   - Dinner (evening)\n"
        elif meals_count == 4:
            prompt += "   - Breakfast (morning, after waking)\n"
            prompt += "   - Snack/Brunch (mid-morning)\n"
            prompt += "   - Lunch (midday)\n"
            prompt += "   - Dinner (evening)\n"
        elif meals_count == 5:
            prompt += "   - Breakfast (morning, after waking)\n"
            prompt += "   - Mid-morning snack\n"
            prompt += "   - Lunch (midday)\n"
            prompt += "   - Afternoon snack\n"
            prompt += "   - Dinner (evening)\n"
        elif meals_count == 6:
            prompt += "   - Breakfast (morning)\n"
            prompt += "   - Mid-morning snack\n"
            prompt += "   - Lunch (midday)\n"
            prompt += "   - Afternoon snack\n"
            prompt += "   - Dinner (evening)\n"
            prompt += "   - Evening snack\n"
        else:
            prompt += f"   - Distribute {meals_count} meals evenly throughout the day\n"
            
        prompt += "   Each meal should be 20-30 minutes\n"
        prompt += "   Meals can be scheduled flexibly between tasks/events\n"
        prompt += "5. After scheduling tasks, recurring events, and meals, fill ALL remaining time with:\n"
        prompt += "   - 'Free Time / Flexibility Buffer'\n"
        prompt += "   - 'Personal Projects Time'\n"
        prompt += "   - 'Catch-up / Admin Work'\n"
        prompt += "   - 'Exercise/Movement'\n"
        prompt += "   - 'Rest & Recovery'\n"
        prompt += "6. REMEMBER: NO GAPS ALLOWED - if there's 10 minutes between events, create a 10-minute block\n\n"
        prompt += "USER DATA:\n" + json.dumps(self.commitments, indent=2) + "\n\n"
        prompt += "TASKS TO SCHEDULE (ONLY THESE - DO NOT ADD ANY OTHERS):\n" + json.dumps(self.tasks, indent=2) + "\n\n"
        prompt += "SCHEDULE REQUIREMENTS:\n"
        prompt += f"- Start day at: {self.commitments['preferences']['wake_time']}\n"
        prompt += f"- End day at: {self.commitments['preferences']['sleep_time']}\n"
        prompt += f"- MUST include EXACTLY {meals_count} meal blocks\n"
        prompt += f"- Focus blocks: {self.commitments['preferences']['focus_block_length']} min\n"
        prompt += f"- Breaks after focus: {self.commitments['preferences']['break_length']} min\n"
        prompt += "- NO GAPS WHATSOEVER - Every minute must be in a block\n"
        prompt += "- Include morning routine at wake time\n"
        prompt += "- Include evening routine before sleep time\n"
        prompt += "- Add the user's weekly recurring events if today is that day of week\n"
        prompt += "- For tasks: use the EXACT task name from the list\n"
        prompt += "- Mark deep work/study tasks as 'focus_required: true'\n\n"
        prompt += """OUTPUT FORMAT (JSON only, no markdown):
{{
  "blocks": [
    {{
      "start": "07:00",
      "end": "07:30",
      "type": "morning_routine",
      "title": "Morning Routine",
      "focus_required": false
    }},
    {{
      "start": "07:30",
      "end": "08:00",
      "type": "meal",
      "title": "Breakfast",
      "focus_required": false
    }},
    {{
      "start": "08:00",
      "end": "09:00",
      "type": "free_time",
      "title": "Free Time / Flexibility Buffer",
      "focus_required": false
    }},
    {{
      "start": "09:00",
      "end": "09:50",
      "type": "focus",
      "title": "[EXACT task name from task list]",
      "focus_required": true
    }},
    {{
      "start": "09:50",
      "end": "10:00",
      "type": "break",
      "title": "Break",
      "focus_required": false
    }},
    {{
      "start": "10:00",
      "end": "12:00",
      "type": "weekly_event",
      "title": "[Weekly recurring event name]",
      "focus_required": false
    }},
    {{
      "start": "12:00",
      "end": "12:30",
      "type": "meal",
      "title": "Lunch",
      "focus_required": false
    }}
  ]
}}

CRITICAL: Notice how each block's end time EQUALS the next block's start time - NO GAPS!

Remember: 
- Use EXACT task names from the provided list
- Include EXACTLY the specified number of meals
- Fill ALL time from wake to sleep with blocks
- NO time gaps allowed between blocks"""
        
        try:
            import urllib.request
            
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            content = result['choices'][0]['message']['content']
            
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            self.schedule = json.loads(content.strip())
            self.save_json(self.schedule_file, self.schedule)
            self.display_schedule()
            self.update_dashboard()
            
            messagebox.showinfo("Success", "Daily plan generated!")
            
        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate plan: {str(e)}\n\nPlease check your API key.")

    def convert_to_12hr(self, time_24):
        """Convert 24-hour time to 12-hour AM/PM format"""
        try:
            hour, minute = map(int, time_24.split(':'))
            period = 'AM' if hour < 12 else 'PM'
            hour_12 = hour if hour <= 12 else hour - 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            return f"{hour_12}:{minute:02d} {period}"
        except:
            return time_24

    def display_schedule(self):
        """Display the current schedule"""
        self.schedule_display.delete('1.0', 'end')
        
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        self.schedule_display.insert('end', f"📅 TODAY'S SCHEDULE - {today}\n", 'title')
        self.schedule_display.insert('end', "─" * 60 + "\n\n")
        
        for block in self.schedule['blocks']:
            is_focus = block.get('focus_required')
            icon = "🔒 " if is_focus else "⏰ "
            
            start_12 = self.convert_to_12hr(block['start'])
            end_12 = self.convert_to_12hr(block['end'])
            
            time_tag = 'focus_time' if is_focus else 'time'
            
            self.schedule_display.insert('end', icon)
            self.schedule_display.insert('end', f"{start_12} - {end_12}\n", time_tag)
            self.schedule_display.insert('end', f"   {block['title']}\n", 'block_title')
            
            if is_focus:
                self.schedule_display.insert('end', "   🎯 Focus Block - Distractions will be blocked\n", 'type_label')
            else:
                self.schedule_display.insert('end', f"   Type: {block['type']}\n", 'type_label')
            
            self.schedule_display.insert('end', "\n")

    def monitor_schedule_locks(self):
        """Check if current time matches a focus block"""
        def check_schedule():
            while True:
                if self.schedule.get('blocks') and not self.lock_active:
                    now = datetime.datetime.now()
                    current_time = now.strftime("%H:%M")
                    
                    for block in self.schedule['blocks']:
                        if block.get('focus_required') and block['start'] <= current_time < block['end']:
                            end_time = datetime.datetime.strptime(block['end'], "%H:%M")
                            end_time = end_time.replace(year=now.year, month=now.month, day=now.day)
                            
                            if end_time > now:
                                self.lock_end_time = end_time
                                self.lock_active = True
                                self.apply_blocks()
                                self.root.after(0, self.update_focus_ui)
                                break
                
                time.sleep(60)
        
        thread = threading.Thread(target=check_schedule, daemon=True)
        thread.start()

    def save_settings(self):
        """Save configuration settings"""
        if self.config.get('password_hash'):
            password = simpledialog.askstring("Password", "Enter settings password:", show='*')
            if not password:
                return
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != self.config['password_hash']:
                messagebox.showerror("Wrong Password", "Incorrect password!")
                return
        
        sites = self.sites_text.get('1.0', 'end').strip().split('\n')
        self.config['blocked_sites'] = [s.strip() for s in sites if s.strip()]
        
        apps = self.apps_text.get('1.0', 'end').strip().split('\n')
        self.config['blocked_apps'] = [a.strip() for a in apps if a.strip()]
        
        self.config['hard_mode'] = self.hard_mode_var.get()
        self.config['api_key'] = self.api_key_entry.get()
        
        self.save_json(self.config_file, self.config)
        messagebox.showinfo("Success", "Settings saved!")

    def set_password(self):
        """Set settings password"""
        password = self.password_entry.get()
        if not password:
            messagebox.showwarning("No Password", "Please enter a password.")
            return
        
        confirm = simpledialog.askstring("Confirm", "Re-enter password:", show='*')
        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords don't match!")
            return
        
        self.config['password_hash'] = hashlib.sha256(password.encode()).hexdigest()
        self.save_json(self.config_file, self.config)
        self.password_entry.delete(0, 'end')
        
        messagebox.showinfo("Success", "Password set! Share this with your accountability partner.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FocusGuardian(root)
    root.mainloop()