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

        start_hour_var = tk.StringVar()
        start_min_var = tk.StringVar()
        start_period_var = tk.StringVar()

        if event_data and event_data.get('start'):
            try:
                hour_24, minute = map(int, event_data['start'].split(':'))
                if hour_24 == 0:
                    start_hour_var.set('12')
                    start_period_var.set('AM')
                elif hour_24 == 12:
                    start_hour_var.set('12')
                    start_period_var.set('PM')
                elif hour_24 > 12:
                    start_hour_var.set(str(hour_24 - 12))
                    start_period_var.set('PM')
                else:
                    start_hour_var.set(str(hour_24))
                    start_period_var.set('AM')
                start_min_var.set(f"{minute:02d}")
            except ValueError:
                start_hour_var.set('9')
                start_min_var.set('00')
                start_period_var.set('AM')
        else:
            start_hour_var.set('9')
            start_min_var.set('00')
            start_period_var.set('AM')
        
        tk.Spinbox(start_frame, from_=1, to=12, textvariable=start_hour_var, width=3, font=('Arial', 10)).pack(side='left', padx=1)
        tk.Label(start_frame, text=":", font=('Arial', 10, 'bold'), bg='#ffffff').pack(side='left')
        tk.Spinbox(start_frame, from_=0, to=59, textvariable=start_min_var, width=3, format='%02.0f', font=('Arial', 10)).pack(side='left', padx=1)
        ttk.Combobox(start_frame, textvariable=start_period_var, values=['AM', 'PM'], width=4, state='readonly', font=('Arial', 9)).pack(side='left', padx=3)
        
        # End time with AM/PM
        tk.Label(inner, text="End:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=4, sticky='w', padx=(20, 5))
        end_frame = tk.Frame(inner, bg='#ffffff')
        end_frame.grid(row=0, column=5, sticky='w')
        
        end_hour_var = tk.StringVar()
        end_min_var = tk.StringVar()
        end_period_var = tk.StringVar()

        if event_data and event_data.get('end'):
            try:
                hour_24, minute = map(int, event_data['end'].split(':'))
                if hour_24 == 0:
                    end_hour_var.set('12')
                    end_period_var.set('AM')
                elif hour_24 == 12:
                    end_hour_var.set('12')
                    end_period_var.set('PM')
                elif hour_24 > 12:
                    end_hour_var.set(str(hour_24 - 12))
                    end_period_var.set('PM')
                else:
                    end_hour_var.set(str(hour_24))
                    end_period_var.set('AM')
                end_min_var.set(f"{minute:02d}")
            except ValueError:
                end_hour_var.set('10')
                end_min_var.set('00')
                end_period_var.set('AM')
        else:
            end_hour_var.set('10')
            end_min_var.set('00')
            end_period_var.set('AM')
        
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
            now = datetime.datetime.now(est)
        else:
            now = datetime.datetime.now()

        today = now.strftime("%A, %B %d, %Y")
        today_name = now.strftime("%A")
        
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
        prompt += "5. After scheduling tasks, recurring events, and meals, fill ALL remaining minutes with either:\n"
        prompt += "   - Focus Blocks (title: 'Focus Block', focus_required: true)\n"
        prompt += "   - Explicit task/todo reminders pulled from the task list\n"
        prompt += "   Absolutely do NOT use labels like Free Time, Personal Projects, Buffer, Admin, or Rest.\n"
        prompt += "6. REMEMBER: NO GAPS ALLOWED - if there's 10 minutes between events, create a 10-minute focus block or task reminder\n\n"
        todays_events = [
            event for event in self.commitments.get('weekly_events', [])
            if event.get('day') == today_name
        ]

        prompt += "USER DATA:\n" + json.dumps(self.commitments, indent=2) + "\n\n"
        prompt += "TODAY'S MANDATORY WEEKLY EVENTS (keep these EXACT times):\n"
        prompt += json.dumps(todays_events, indent=2) + "\n"
        prompt += "If this list is empty there are no fixed events today. Otherwise, each event must appear exactly at its start and end times without overlap.\n\n"
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
        prompt += "- Add the user's weekly recurring events exactly at their listed times (see mandatory event list above)\n"
        prompt += "- For tasks: use the EXACT task name from the list\n"
        prompt += "- Mark deep work/study tasks as 'focus_required: true'\n\n"

        if not self.tasks.get('tasks'):
            focus_len = self.commitments['preferences']['focus_block_length']
            break_len = self.commitments['preferences']['break_length']
            prompt += (
                f"SPECIAL INSTRUCTION: There are no one-time tasks today. Fill all non-meal, non-event time with repeated 'Focus Block' entries of {focus_len} minutes (focus_required: true) followed by {break_len}-minute breaks as needed. Do not create any other block types for these periods.\n\n"
            )
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
      "type": "focus",
      "title": "Focus Block",
      "focus_required": true
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
            self.post_process_schedule(meals_count, todays_events)
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

    def parse_time_to_minutes(self, time_str):
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except Exception:
            return 0

    def minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM string"""
        try:
            minutes = int(round(minutes))
            minutes = minutes % (24 * 60)
            hour = minutes // 60
            minute = minutes % 60
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return "00:00"

    def normalize_minutes(self, value, wake_minutes, sleep_minutes, crosses_midnight):
        """Map a clock value into the scheduling timeline respecting wraparound"""
        if crosses_midnight and value < wake_minutes and value <= sleep_minutes:
            return value + 24 * 60
        return value

    def normalize_window(self, start_minutes, end_minutes, wake_minutes, sleep_minutes, crosses_midnight):
        """Normalize a start/end pair into a monotonically increasing window"""
        start = self.normalize_minutes(start_minutes, wake_minutes, sleep_minutes, crosses_midnight)
        end = self.normalize_minutes(end_minutes, wake_minutes, sleep_minutes, crosses_midnight)

        if end <= start:
            end += 24 * 60

        return start, end

    def get_expected_meal_titles(self, meals_count):
        """Return ordered list of expected meal titles"""
        mapping = {
            1: ["Main Meal"],
            2: ["Breakfast", "Dinner"],
            3: ["Breakfast", "Lunch", "Dinner"],
            4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
            5: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ],
            6: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner",
                "Evening Snack"
            ]
        }
        if meals_count in mapping:
            return mapping[meals_count]
        return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]

    def get_meal_ratios(self, meals_count):
        """Return normalized placement ratios for meals throughout the day"""
        ratio_map = {
            1: [0.5],
            2: [0.05, 0.75],
            3: [0.05, 0.5, 0.82],
            4: [0.04, 0.25, 0.55, 0.82],
            5: [0.04, 0.22, 0.45, 0.68, 0.88],
            6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9]
        }
        if meals_count in ratio_map:
            return ratio_map[meals_count]
        if meals_count <= 0:
            return []
        step = 0.85 / max(meals_count - 1, 1)
        return [min(0.9, i * step) for i in range(meals_count)]

    def calculate_meal_target(self, index, total, day_start, day_end):
        """Calculate target minute for a meal placement"""
        if total <= 0:
            return day_start
        ratios = self.get_meal_ratios(total)
        ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
        ratio = max(0.0, min(ratio, 0.95))
        span = max(day_end - day_start, 1)
        target = day_start + int(span * ratio)
        target = max(day_start, min(target, day_end - 30))
        return target - (target % 5)

    def violates_meal_spacing(self, entries, start, end, min_gap, ignore_entry=None):
        """Return True if placing a meal violates minimum spacing requirements"""
        if min_gap <= 0:
            return False
        for entry in entries:
            if entry is ignore_entry:
                continue
            block_type = (entry['block'].get('type') or '').lower()
            if block_type != 'meal':
                continue
            if start >= entry['end']:
                if start - entry['end'] < min_gap:
                    return True
            elif entry['start'] >= end:
                if entry['start'] - end < min_gap:
                    return True
            else:
                return True
        return False

    def compute_free_segments(self, entries, day_start, day_end):
        """Compute gaps between entries that can host new blocks"""
        segments = []
        cursor = day_start
        for entry in sorted(entries, key=lambda e: e['start']):
            if entry['start'] - cursor >= 20:
                segments.append((cursor, entry['start']))
            cursor = max(cursor, entry['end'])
        if day_end - cursor >= 20:
            segments.append((cursor, day_end))
        return segments

    def insert_meal_entry(self, entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=False):
        """Insert a meal entry either in a free segment or by splitting a block"""
        if day_end - day_start < 20:
            return None

        segments = self.compute_free_segments(entries, day_start, day_end)
        best_candidate = None
        best_distance = None

        for seg_start, seg_end in segments:
            if seg_end - seg_start < 20:
                continue
            placement_start = max(seg_start, min(target, seg_end - 30))
            placement_start -= placement_start % 5
            placement_end = placement_start + 30
            if placement_end > seg_end:
                placement_end = seg_end
                placement_start = max(seg_start, placement_end - 30)
            if placement_end - placement_start < 20:
                continue
            if self.violates_meal_spacing(entries, placement_start, placement_end, min_gap):
                continue
            distance = abs(placement_start - target)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_candidate = (placement_start, placement_end)

        if best_candidate:
            meal_block = {
                'start': self.minutes_to_time(best_candidate[0]),
                'end': self.minutes_to_time(best_candidate[1]),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            entry = {
                'start': best_candidate[0],
                'end': best_candidate[1],
                'block': meal_block
            }
            entries.append(entry)
            entries.sort(key=lambda e: e['start'])
            return entry

        filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]['start'])
        keywords = ['free', 'rest', 'buffer', 'flex', 'break', 'personal', 'catch', 'admin', 'exercise', 'transition', 'placeholder']
        for idx, entry in filler_candidates:
            block = entry['block']
            block_type = (block.get('type') or '').lower()
            if block_type in {'weekly_event', 'meal'}:
                continue
            if block.get('focus_required') and not allow_focus_override:
                continue
            convertible = any(keyword in block_type for keyword in keywords)
            if not convertible and not allow_focus_override:
                continue
            duration = entry['end'] - entry['start']
            if duration < 30:
                continue

            meal_start = max(entry['start'], min(target, entry['end'] - 30))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > entry['end']:
                meal_end = entry['end']
                meal_start = max(entry['start'], meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            new_entries = []

            if meal_start - entry['start'] >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(entry['start'])
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': entry['start'],
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if entry['end'] - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(entry['end'])
                new_entries.append({
                    'start': meal_end,
                    'end': entry['end'],
                    'block': after_block
                })

            entries.pop(idx)
            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        candidate_blocks = [
            (abs(((entry['start'] + entry['end']) / 2) - target), idx, entry)
            for idx, entry in enumerate(entries)
            if (entry['block'].get('type') or '').lower() not in {'weekly_event', 'meal'}
            and (allow_focus_override or not entry['block'].get('focus_required'))
        ]
        candidate_blocks.sort(key=lambda item: item[0])

        for _, idx, entry in candidate_blocks:
            start = entry['start']
            end = entry['end']
            if end - start < 20:
                continue
            meal_start = max(start, min(target, end - 25))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > end:
                meal_end = end
                meal_start = max(start, meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            entries.pop(idx)
            new_entries = []

            if meal_start - start >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(start)
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': start,
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if end - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(end)
                new_entries.append({
                    'start': meal_end,
                    'end': end,
                    'block': after_block
                })

            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        return None

    def ensure_meal_coverage(self, entries, meals_count, day_start, day_end):
        """Guarantee that the schedule contains the required number of meals"""
        if meals_count <= 0:
            entries[:] = [e for e in entries if (e['block'].get('type') or '').lower() != 'meal']
            return

        entries.sort(key=lambda e: e['start'])

        sanitized_entries = []
        for entry in entries:
            block_type = (entry['block'].get('type') or '').lower()
            if block_type == 'meal':
                placeholder_block = {
                    'title': 'Focus Block',
                    'type': 'focus_placeholder',
                    'focus_required': False
                }
                sanitized_entries.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'block': placeholder_block
                })
            else:
                sanitized_entries.append(entry)

        entries[:] = sanitized_entries
        expected_titles = self.get_expected_meal_titles(meals_count)

        for idx, title in enumerate(expected_titles):
            target = self.calculate_meal_target(idx, len(expected_titles), day_start, day_end)
            inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=True)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
            if not inserted:
                self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=20, allow_focus_override=True)

        entries.sort(key=lambda e: e['start'])
        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        if len(meal_entries) > len(expected_titles):
            for extra in meal_entries[len(expected_titles):]:
                extra['block']['type'] = 'focus'
                extra['block']['title'] = 'Focus Block'
                extra['block']['focus_required'] = True

        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(meal_entries):
            if idx >= len(expected_titles):
                break
            entry['block']['title'] = expected_titles[idx]
            entry['block']['type'] = 'meal'
            entry['block']['focus_required'] = False

    def enforce_weekly_events(self, entries, todays_events, day_start, day_end, wake_minutes, sleep_minutes, crosses_midnight):
        """Ensure weekly recurring events are present at their exact times"""
        if not todays_events:
            return

        for event in todays_events:
            try:
                raw_start = self.parse_time_to_minutes(event['start'])
                raw_end = self.parse_time_to_minutes(event['end'])
            except Exception:
                continue

            title = event.get('title') or 'Weekly Event'
            event_start, event_end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            event_start = max(day_start, event_start)
            event_end = min(day_end, event_end)

            if event_end - event_start < 5:
                continue

            adjusted_entries = []
            for entry in entries:
                if entry['end'] <= event_start or entry['start'] >= event_end:
                    adjusted_entries.append(entry)
                    continue

                if entry['start'] < event_start:
                    before_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': entry['start'],
                        'end': event_start,
                        'block': before_block
                    })

                if entry['end'] > event_end:
                    after_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': event_end,
                        'end': entry['end'],
                        'block': after_block
                    })

            event_block = {
                'type': 'weekly_event',
                'title': title,
                'focus_required': False,
                'start': self.minutes_to_time(event_start),
                'end': self.minutes_to_time(event_end)
            }
            adjusted_entries.append({
                'start': event_start,
                'end': event_end,
                'block': event_block
            })

            entries[:] = sorted(adjusted_entries, key=lambda e: e['start'])

    def is_fixed_block(self, block):
        """Return True if the block's start time should not be shifted"""
        block_type = str(block.get('type', '')).lower()
        if block_type in {'weekly_event', 'meal'}:
            return True
        return False

    def apply_task_duration_constraints(self, entries):
        """Clamp task/todo blocks to their saved durations and push flex time if needed"""
        task_map = {}
        for task in self.tasks.get('tasks', []):
            name = task.get('name', '').strip().lower()
            duration = int(task.get('duration', 0) or 0)
            if name and duration > 0:
                task_map[name] = duration

        if not task_map:
            return

        entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(entries):
            block = entry['block']
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip().lower()

            if block_type not in {'task', 'todo'} and title not in task_map:
                continue

            duration = task_map.get(title)
            if not duration:
                continue

            desired_end = entry['start'] + duration
            if desired_end <= entry['start']:
                continue

            entry['end'] = desired_end

            current_end = entry['end']
            for next_idx in range(idx + 1, len(entries)):
                next_entry = entries[next_idx]
                if next_entry['start'] >= current_end:
                    break

                overlap = current_end - next_entry['start']
                if overlap <= 0:
                    break

                if self.is_fixed_block(next_entry['block']):
                    entry['end'] = next_entry['start']
                    current_end = entry['end']
                    break

                next_entry['start'] += overlap
                next_entry['end'] += overlap
                current_end = max(current_end, next_entry['end'])

    def create_focus_entry(self, start, end, title='Focus Block'):
        """Create a focus block entry covering [start, end) minutes"""
        block = {
            'type': 'focus',
            'title': title,
            'focus_required': True
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def create_break_entry(self, start, end, title='Break'):
        """Create a short decompression block covering [start, end) minutes"""
        block = {
            'type': 'break',
            'title': title,
            'focus_required': False
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def create_free_time_entry(self, start, end, title='Free Time'):
        """Create a free time entry covering [start, end) minutes"""
        block = {
            'type': 'free_time',
            'title': title,
            'focus_required': False
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def is_focus_block(self, block):
        """Return True if the block should be treated as focus time"""
        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        block_type = str(block.get('type', '')).lower()
        title = str(block.get('title', '')).strip().lower()

        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine', 'todo', 'task'
        }

        if block_type in protected_types:
            return False

        if title in task_titles:
            return False

        if block.get('focus_required'):
            return True

        if 'focus' in block_type or 'focus' in title:
            return True

        return False

    def build_focus_sequence(self, start, end):
        """Generate focus, break, and free-time blocks to span [start, end)"""
        focus_len = max(5, int(self.commitments['preferences'].get('focus_block_length', 50)))
        break_len = max(0, int(self.commitments['preferences'].get('break_length', 0)))

        segments = []
        cursor = start

        while cursor + focus_len <= end - 1e-6:
            block_end = cursor + focus_len
            segments.append(self.create_focus_entry(cursor, block_end))
            cursor = block_end

            remaining = end - cursor
            if break_len >= 5 and remaining >= 5:
                gap = min(break_len, remaining)
                break_end = cursor + gap
                segments.append(self.create_break_entry(cursor, break_end))
                cursor = break_end

        if cursor < end - 1e-6:
            leftover = end - cursor
            if leftover >= 5:
                segments.append(self.create_free_time_entry(cursor, end))

        return segments

    def fill_gaps_with_focus(self, entries, day_start, day_end):
        """Fill uncovered time with focus blocks (and free time for leftovers)"""
        entries.sort(key=lambda e: e['start'])
        new_entries = []
        cursor = day_start

        for entry in entries:
            start = max(entry['start'], day_start)
            end = min(entry['end'], day_end)

            if end <= start:
                continue

            if start > cursor:
                new_entries.extend(self.build_focus_sequence(cursor, start))
                cursor = start
            else:
                start = max(start, cursor)

            block = entry['block']
            if self.is_focus_block(block):
                focus_segments = self.build_focus_sequence(start, end)
                new_entries.extend(focus_segments)
            else:
                entry['start'] = start
                entry['end'] = end
                new_entries.append(entry)

            cursor = max(cursor, end)

        if cursor < day_end:
            new_entries.extend(self.build_focus_sequence(cursor, day_end))

        entries[:] = new_entries

    def sanitize_filler_blocks(self, blocks):
        """Normalize filler-style blocks while keeping intentional free time"""
        filler_keywords = [
            'free', 'personal', 'project', 'buffer', 'catch', 'admin', 'rest',
            'recovery', 'flex', 'exercise', 'movement', 'leisure', 'downtime',
            'placeholder', 'unwind', 'relax', 'misc'
        ]
        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine', 'free_time'
        }

        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            raw_title = str(block.get('title', '')).strip()
            title = raw_title.lower()

            if block_type in protected_types:
                continue
            if block.get('focus_required'):
                continue
            if block_type.startswith('task') or 'todo' in block_type:
                continue
            if 'todo' in title or 'task' in title:
                continue
            if title.strip().lower() in task_titles:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            if any(keyword in block_type for keyword in filler_keywords) or any(keyword in title for keyword in filler_keywords):
                if 'free' in block_type or 'free' in title:
                    block['type'] = 'free_time'
                    block['title'] = raw_title or 'Free Time'
                    block['focus_required'] = False
                else:
                    block['type'] = 'focus'
                    block['title'] = 'Focus Block'
                    block['focus_required'] = True

    def normalize_focus_blocks(self, blocks):
        """Ensure non-event blocks default to focus work unless explicitly tasks"""
        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip()
            title_lower = title.lower()

            if block_type in {'meal', 'weekly_event'}:
                continue

            if block_type == 'free_time':
                block['title'] = title or 'Free Time'
                block['focus_required'] = False
                continue

            if block_type == 'break':
                block['title'] = title or 'Break'
                block['focus_required'] = False
                continue

            if block_type.startswith('task') or 'todo' in block_type:
                block.setdefault('focus_required', False)
                continue

            if title_lower in task_titles:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            if 'todo' in title_lower or 'task' in title_lower:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            block['type'] = 'focus'
            block['title'] = title or 'Focus Block'
            block['focus_required'] = True

    def post_process_schedule(self, meals_count, todays_events=None):
        """Sort, clip, and adjust the generated schedule"""
        todays_events = todays_events or []
        wake_time = self.commitments['preferences'].get('wake_time', '07:00')
        sleep_time = self.commitments['preferences'].get('sleep_time', '23:00')
        wake_minutes = self.parse_time_to_minutes(wake_time)
        sleep_minutes = self.parse_time_to_minutes(sleep_time)

        day_start = wake_minutes
        day_end = sleep_minutes
        crosses_midnight = False

        if day_end <= day_start:
            day_end += 24 * 60
            crosses_midnight = True

        if todays_events:
            earliest = day_start
            latest = day_end
            for event in todays_events:
                try:
                    raw_start = self.parse_time_to_minutes(event['start'])
                    raw_end = self.parse_time_to_minutes(event['end'])
                except Exception:
                    continue

                event_start, event_end = self.normalize_window(
                    raw_start,
                    raw_end,
                    wake_minutes,
                    sleep_minutes,
                    crosses_midnight
                )

                earliest = min(earliest, event_start)
                latest = max(latest, event_end)

            day_start = min(day_start, earliest)
            day_end = max(day_end, latest)

        raw_blocks = self.schedule.get('blocks', [])
        entries = []

        for block in raw_blocks:
            try:
                raw_start = self.parse_time_to_minutes(block['start'])
                raw_end = self.parse_time_to_minutes(block['end'])
            except Exception:
                continue

            start, end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            start_clamped = max(start, day_start)
            end_clamped = min(end, day_end)

            if end_clamped - start_clamped < 1:
                continue

            block_copy = dict(block)
            entries.append({
                'start': start_clamped,
                'end': end_clamped,
                'block': block_copy
            })

        entries.sort(key=lambda e: e['start'])

        self.enforce_weekly_events(
            entries,
            todays_events,
            day_start,
            day_end,
            wake_minutes,
            sleep_minutes,
            crosses_midnight
        )

        self.apply_task_duration_constraints(entries)

        self.ensure_meal_coverage(entries, meals_count, day_start, day_end)

        self.fill_gaps_with_focus(entries, day_start, day_end)

        entries.sort(key=lambda e: e['start'])
        new_blocks = []
        for entry in entries:
            block = entry['block']
            block['start'] = self.minutes_to_time(entry['start'])
            block['end'] = self.minutes_to_time(entry['end'])
            new_blocks.append(block)

        self.sanitize_filler_blocks(new_blocks)
        self.normalize_focus_blocks(new_blocks)
        self.schedule['blocks'] = new_blocks

    def parse_time_to_minutes(self, time_str):
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except Exception:
            return 0

    def minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM string"""
        try:
            minutes = int(round(minutes))
            minutes = minutes % (24 * 60)
            hour = minutes // 60
            minute = minutes % 60
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return "00:00"

    def normalize_minutes(self, value, wake_minutes, sleep_minutes, crosses_midnight):
        """Map a clock value into the scheduling timeline respecting wraparound"""
        if crosses_midnight and value < wake_minutes and value <= sleep_minutes:
            return value + 24 * 60
        return value

    def normalize_window(self, start_minutes, end_minutes, wake_minutes, sleep_minutes, crosses_midnight):
        """Normalize a start/end pair into a monotonically increasing window"""
        start = self.normalize_minutes(start_minutes, wake_minutes, sleep_minutes, crosses_midnight)
        end = self.normalize_minutes(end_minutes, wake_minutes, sleep_minutes, crosses_midnight)

        if end <= start:
            end += 24 * 60

        return start, end

    def get_expected_meal_titles(self, meals_count):
        """Return ordered list of expected meal titles"""
        mapping = {
            1: ["Main Meal"],
            2: ["Breakfast", "Dinner"],
            3: ["Breakfast", "Lunch", "Dinner"],
            4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
            5: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ],
            6: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner",
                "Evening Snack"
            ]
        }
        if meals_count in mapping:
            return mapping[meals_count]
        return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]

    def get_meal_ratios(self, meals_count):
        """Return normalized placement ratios for meals throughout the day"""
        ratio_map = {
            1: [0.5],
            2: [0.05, 0.75],
            3: [0.05, 0.5, 0.82],
            4: [0.04, 0.25, 0.55, 0.82],
            5: [0.04, 0.22, 0.45, 0.68, 0.88],
            6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9]
        }
        if meals_count in ratio_map:
            return ratio_map[meals_count]
        if meals_count <= 0:
            return []
        step = 0.85 / max(meals_count - 1, 1)
        return [min(0.9, i * step) for i in range(meals_count)]

    def calculate_meal_target(self, index, total, day_start, day_end):
        """Calculate target minute for a meal placement"""
        if total <= 0:
            return day_start
        ratios = self.get_meal_ratios(total)
        ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
        ratio = max(0.0, min(ratio, 0.95))
        span = max(day_end - day_start, 1)
        target = day_start + int(span * ratio)
        target = max(day_start, min(target, day_end - 30))
        return target - (target % 5)

    def violates_meal_spacing(self, entries, start, end, min_gap, ignore_entry=None):
        """Return True if placing a meal violates minimum spacing requirements"""
        if min_gap <= 0:
            return False
        for entry in entries:
            if entry is ignore_entry:
                continue
            block_type = (entry['block'].get('type') or '').lower()
            if block_type != 'meal':
                continue
            if start >= entry['end']:
                if start - entry['end'] < min_gap:
                    return True
            elif entry['start'] >= end:
                if entry['start'] - end < min_gap:
                    return True
            else:
                return True
        return False

    def compute_free_segments(self, entries, day_start, day_end):
        """Compute gaps between entries that can host new blocks"""
        segments = []
        cursor = day_start
        for entry in sorted(entries, key=lambda e: e['start']):
            if entry['start'] - cursor >= 20:
                segments.append((cursor, entry['start']))
            cursor = max(cursor, entry['end'])
        if day_end - cursor >= 20:
            segments.append((cursor, day_end))
        return segments

    def insert_meal_entry(self, entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=False):
        """Insert a meal entry either in a free segment or by splitting a block"""
        if day_end - day_start < 20:
            return None

        segments = self.compute_free_segments(entries, day_start, day_end)
        best_candidate = None
        best_distance = None

        for seg_start, seg_end in segments:
            if seg_end - seg_start < 20:
                continue
            placement_start = max(seg_start, min(target, seg_end - 30))
            placement_start -= placement_start % 5
            placement_end = placement_start + 30
            if placement_end > seg_end:
                placement_end = seg_end
                placement_start = max(seg_start, placement_end - 30)
            if placement_end - placement_start < 20:
                continue
            if self.violates_meal_spacing(entries, placement_start, placement_end, min_gap):
                continue
            distance = abs(placement_start - target)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_candidate = (placement_start, placement_end)

        if best_candidate:
            meal_block = {
                'start': self.minutes_to_time(best_candidate[0]),
                'end': self.minutes_to_time(best_candidate[1]),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            entry = {
                'start': best_candidate[0],
                'end': best_candidate[1],
                'block': meal_block
            }
            entries.append(entry)
            entries.sort(key=lambda e: e['start'])
            return entry

        filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]['start'])
        keywords = ['free', 'rest', 'buffer', 'flex', 'break', 'personal', 'catch', 'admin', 'exercise', 'transition', 'placeholder']
        for idx, entry in filler_candidates:
            block = entry['block']
            block_type = (block.get('type') or '').lower()
            if block_type in {'weekly_event', 'meal'}:
                continue
            if block.get('focus_required') and not allow_focus_override:
                continue
            convertible = any(keyword in block_type for keyword in keywords)
            if not convertible and not allow_focus_override:
                continue
            duration = entry['end'] - entry['start']
            if duration < 30:
                continue

            meal_start = max(entry['start'], min(target, entry['end'] - 30))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > entry['end']:
                meal_end = entry['end']
                meal_start = max(entry['start'], meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            new_entries = []

            if meal_start - entry['start'] >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(entry['start'])
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': entry['start'],
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if entry['end'] - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(entry['end'])
                new_entries.append({
                    'start': meal_end,
                    'end': entry['end'],
                    'block': after_block
                })

            entries.pop(idx)
            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        candidate_blocks = [
            (abs(((entry['start'] + entry['end']) / 2) - target), idx, entry)
            for idx, entry in enumerate(entries)
            if (entry['block'].get('type') or '').lower() not in {'weekly_event', 'meal'}
            and (allow_focus_override or not entry['block'].get('focus_required'))
        ]
        candidate_blocks.sort(key=lambda item: item[0])

        for _, idx, entry in candidate_blocks:
            start = entry['start']
            end = entry['end']
            if end - start < 20:
                continue
            meal_start = max(start, min(target, end - 25))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > end:
                meal_end = end
                meal_start = max(start, meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            entries.pop(idx)
            new_entries = []

            if meal_start - start >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(start)
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': start,
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if end - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(end)
                new_entries.append({
                    'start': meal_end,
                    'end': end,
                    'block': after_block
                })

            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        return None

    def ensure_meal_coverage(self, entries, meals_count, day_start, day_end):
        """Guarantee that the schedule contains the required number of meals"""
        if meals_count <= 0:
            entries[:] = [e for e in entries if (e['block'].get('type') or '').lower() != 'meal']
            return

        entries.sort(key=lambda e: e['start'])

        sanitized_entries = []
        for entry in entries:
            block_type = (entry['block'].get('type') or '').lower()
            if block_type == 'meal':
                placeholder_block = {
                    'title': 'Focus Block',
                    'type': 'focus_placeholder',
                    'focus_required': False
                }
                sanitized_entries.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'block': placeholder_block
                })
            else:
                sanitized_entries.append(entry)

        entries[:] = sanitized_entries
        expected_titles = self.get_expected_meal_titles(meals_count)

        for idx, title in enumerate(expected_titles):
            target = self.calculate_meal_target(idx, len(expected_titles), day_start, day_end)
            inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=True)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
            if not inserted:
                self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=20, allow_focus_override=True)

        entries.sort(key=lambda e: e['start'])
        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        if len(meal_entries) > len(expected_titles):
            for extra in meal_entries[len(expected_titles):]:
                extra['block']['type'] = 'focus'
                extra['block']['title'] = 'Focus Block'
                extra['block']['focus_required'] = True

        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(meal_entries):
            if idx >= len(expected_titles):
                break
            entry['block']['title'] = expected_titles[idx]
            entry['block']['type'] = 'meal'
            entry['block']['focus_required'] = False

    def enforce_weekly_events(self, entries, todays_events, day_start, day_end, wake_minutes, sleep_minutes, crosses_midnight):
        """Ensure weekly recurring events are present at their exact times"""
        if not todays_events:
            return

        for event in todays_events:
            try:
                raw_start = self.parse_time_to_minutes(event['start'])
                raw_end = self.parse_time_to_minutes(event['end'])
            except Exception:
                continue

            title = event.get('title') or 'Weekly Event'
            event_start, event_end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            event_start = max(day_start, event_start)
            event_end = min(day_end, event_end)

            if event_end - event_start < 5:
                continue

            adjusted_entries = []
            for entry in entries:
                if entry['end'] <= event_start or entry['start'] >= event_end:
                    adjusted_entries.append(entry)
                    continue

                if entry['start'] < event_start:
                    before_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': entry['start'],
                        'end': event_start,
                        'block': before_block
                    })

                if entry['end'] > event_end:
                    after_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': event_end,
                        'end': entry['end'],
                        'block': after_block
                    })

            event_block = {
                'type': 'weekly_event',
                'title': title,
                'focus_required': False,
                'start': self.minutes_to_time(event_start),
                'end': self.minutes_to_time(event_end)
            }
            adjusted_entries.append({
                'start': event_start,
                'end': event_end,
                'block': event_block
            })

            entries[:] = sorted(adjusted_entries, key=lambda e: e['start'])

    def apply_task_duration_constraints(self, entries):
        """Clamp task/todo blocks to their saved durations"""
        task_map = {}
        for task in self.tasks.get('tasks', []):
            name = task.get('name', '').strip().lower()
            duration = int(task.get('duration', 0) or 0)
            if name and duration > 0:
                task_map[name] = duration

        if not task_map:
            return

        entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(entries):
            block = entry['block']
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip().lower()

            if block_type not in {'task', 'todo'} and title not in task_map:
                continue

            duration = task_map.get(title)
            if not duration:
                continue

            desired_end = entry['start'] + duration
            if idx + 1 < len(entries):
                next_start = entries[idx + 1]['start']
                if desired_end > next_start:
                    desired_end = next_start

            if desired_end <= entry['start']:
                continue

            entry['end'] = desired_end

    def create_focus_entry(self, start, end, title='Focus Block'):
        """Create a focus block entry covering [start, end) minutes"""
        block = {
            'type': 'focus',
            'title': title,
            'focus_required': True
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def create_break_entry(self, start, end, title='Break'):
        """Create a short decompression block covering [start, end) minutes"""
        block = {
            'type': 'break',
            'title': title,
            'focus_required': False
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def is_focus_block(self, block):
        """Return True if the block should be treated as focus time"""
        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        block_type = str(block.get('type', '')).lower()
        title = str(block.get('title', '')).strip().lower()

        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine', 'todo', 'task'
        }

        if block_type in protected_types:
            return False

        if title in task_titles:
            return False

        if block.get('focus_required'):
            return True

        if 'focus' in block_type or 'focus' in title:
            return True

        return False

    def build_focus_sequence(self, start, end):
        """Generate focus (and optional break) blocks to span [start, end)"""
        focus_len = max(5, int(self.commitments['preferences'].get('focus_block_length', 50)))
        break_len = max(0, int(self.commitments['preferences'].get('break_length', 0)))

        segments = []
        cursor = start

        while cursor < end - 1e-6:
            remaining = end - cursor

            if remaining < 5:
                if segments:
                    segments[-1]['end'] = end
                break

            if remaining < focus_len:
                if break_len >= 5:
                    segments.append(self.create_break_entry(cursor, end))
                elif remaining >= 5:
                    segments.append(self.create_break_entry(cursor, end))
                elif segments:
                    segments[-1]['end'] = end
                break

            block_end = cursor + focus_len
            segments.append(self.create_focus_entry(cursor, block_end))
            cursor = block_end

            remaining = end - cursor
            if break_len >= 5 and remaining >= 5:
                gap = min(break_len, remaining)
                break_end = cursor + gap
                segments.append(self.create_break_entry(cursor, break_end))
                cursor = break_end

        return segments

    def fill_gaps_with_focus(self, entries, day_start, day_end):
        """Fill uncovered time with focus blocks so there are no gaps"""
        entries.sort(key=lambda e: e['start'])
        new_entries = []
        cursor = day_start

        for entry in entries:
            start = max(entry['start'], day_start)
            end = min(entry['end'], day_end)

            if end <= start:
                continue

            if start > cursor:
                new_entries.extend(self.build_focus_sequence(cursor, start))
                cursor = start
            else:
                start = max(start, cursor)

            block = entry['block']
            if self.is_focus_block(block):
                focus_segments = self.build_focus_sequence(start, end)
                new_entries.extend(focus_segments)
            else:
                entry['start'] = start
                entry['end'] = end
                new_entries.append(entry)

            cursor = max(cursor, end)

        if cursor < day_end:
            new_entries.extend(self.build_focus_sequence(cursor, day_end))

        entries[:] = new_entries

    def sanitize_filler_blocks(self, blocks):
        """Convert filler-style blocks into focus blocks to avoid free time"""
        filler_keywords = [
            'free', 'personal', 'project', 'buffer', 'catch', 'admin', 'rest',
            'recovery', 'flex', 'exercise', 'movement', 'leisure', 'downtime',
            'placeholder', 'unwind', 'relax', 'misc'
        ]
        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine'
        }

        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).lower()

            if block_type in protected_types:
                continue
            if block.get('focus_required'):
                continue
            if block_type.startswith('task') or 'todo' in block_type:
                continue
            if 'todo' in title or 'task' in title:
                continue
            if title.strip().lower() in task_titles:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            if any(keyword in block_type for keyword in filler_keywords) or any(keyword in title for keyword in filler_keywords):
                block['type'] = 'focus'
                block['title'] = 'Focus Block'
                block['focus_required'] = True

    def normalize_focus_blocks(self, blocks):
        """Ensure non-event blocks default to focus work unless explicitly tasks"""
        task_titles = {
            task.get('name', '').strip().lower()
            for task in self.tasks.get('tasks', [])
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip()
            title_lower = title.lower()

            if block_type in {'meal', 'weekly_event'}:
                continue

            if block_type.startswith('task') or 'todo' in block_type:
                block.setdefault('focus_required', False)
                continue

            if title_lower in task_titles:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            if 'todo' in title_lower or 'task' in title_lower:
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            block['type'] = 'focus'
            block['title'] = title or 'Focus Block'
            block['focus_required'] = True

    def post_process_schedule(self, meals_count, todays_events=None):
        """Sort, clip, and adjust the generated schedule"""
        todays_events = todays_events or []
        wake_time = self.commitments['preferences'].get('wake_time', '07:00')
        sleep_time = self.commitments['preferences'].get('sleep_time', '23:00')
        wake_minutes = self.parse_time_to_minutes(wake_time)
        sleep_minutes = self.parse_time_to_minutes(sleep_time)

        day_start = wake_minutes
        day_end = sleep_minutes
        crosses_midnight = False

        if day_end <= day_start:
            day_end += 24 * 60
            crosses_midnight = True

        if todays_events:
            earliest = day_start
            latest = day_end
            for event in todays_events:
                try:
                    raw_start = self.parse_time_to_minutes(event['start'])
                    raw_end = self.parse_time_to_minutes(event['end'])
                except Exception:
                    continue

                event_start, event_end = self.normalize_window(
                    raw_start,
                    raw_end,
                    wake_minutes,
                    sleep_minutes,
                    crosses_midnight
                )

                earliest = min(earliest, event_start)
                latest = max(latest, event_end)

            day_start = min(day_start, earliest)
            day_end = max(day_end, latest)

        raw_blocks = self.schedule.get('blocks', [])
        entries = []

        for block in raw_blocks:
            try:
                raw_start = self.parse_time_to_minutes(block['start'])
                raw_end = self.parse_time_to_minutes(block['end'])
            except Exception:
                continue

            start, end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            start_clamped = max(start, day_start)
            end_clamped = min(end, day_end)

            if end_clamped - start_clamped < 1:
                continue

            block_copy = dict(block)
            entries.append({
                'start': start_clamped,
                'end': end_clamped,
                'block': block_copy
            })

        entries.sort(key=lambda e: e['start'])

        self.enforce_weekly_events(
            entries,
            todays_events,
            day_start,
            day_end,
            wake_minutes,
            sleep_minutes,
            crosses_midnight
        )

        self.apply_task_duration_constraints(entries)

        self.ensure_meal_coverage(entries, meals_count, day_start, day_end)

        self.fill_gaps_with_focus(entries, day_start, day_end)

        entries.sort(key=lambda e: e['start'])
        new_blocks = []
        for entry in entries:
            block = entry['block']
            block['start'] = self.minutes_to_time(entry['start'])
            block['end'] = self.minutes_to_time(entry['end'])
            new_blocks.append(block)

        self.sanitize_filler_blocks(new_blocks)
        self.normalize_focus_blocks(new_blocks)
        self.schedule['blocks'] = new_blocks

    def parse_time_to_minutes(self, time_str):
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except Exception:
            return 0

    def minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM string"""
        try:
            minutes = int(round(minutes))
            minutes = minutes % (24 * 60)
            hour = minutes // 60
            minute = minutes % 60
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return "00:00"

    def normalize_minutes(self, value, wake_minutes, sleep_minutes, crosses_midnight):
        """Map a clock value into the scheduling timeline respecting wraparound"""
        if crosses_midnight and value < wake_minutes and value <= sleep_minutes:
            return value + 24 * 60
        return value

    def normalize_window(self, start_minutes, end_minutes, wake_minutes, sleep_minutes, crosses_midnight):
        """Normalize a start/end pair into a monotonically increasing window"""
        start = self.normalize_minutes(start_minutes, wake_minutes, sleep_minutes, crosses_midnight)
        end = self.normalize_minutes(end_minutes, wake_minutes, sleep_minutes, crosses_midnight)

        if end <= start:
            end += 24 * 60

        return start, end

    def get_expected_meal_titles(self, meals_count):
        """Return ordered list of expected meal titles"""
        mapping = {
            1: ["Main Meal"],
            2: ["Breakfast", "Dinner"],
            3: ["Breakfast", "Lunch", "Dinner"],
            4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
            5: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ],
            6: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner",
                "Evening Snack"
            ]
        }
        if meals_count in mapping:
            return mapping[meals_count]
        return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]

    def get_meal_ratios(self, meals_count):
        """Return normalized placement ratios for meals throughout the day"""
        ratio_map = {
            1: [0.5],
            2: [0.05, 0.75],
            3: [0.05, 0.5, 0.82],
            4: [0.04, 0.25, 0.55, 0.82],
            5: [0.04, 0.22, 0.45, 0.68, 0.88],
            6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9]
        }
        if meals_count in ratio_map:
            return ratio_map[meals_count]
        if meals_count <= 0:
            return []
        step = 0.85 / max(meals_count - 1, 1)
        return [min(0.9, i * step) for i in range(meals_count)]

    def calculate_meal_target(self, index, total, day_start, day_end):
        """Calculate target minute for a meal placement"""
        if total <= 0:
            return day_start
        ratios = self.get_meal_ratios(total)
        ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
        ratio = max(0.0, min(ratio, 0.95))
        span = max(day_end - day_start, 1)
        target = day_start + int(span * ratio)
        target = max(day_start, min(target, day_end - 30))
        return target - (target % 5)

    def violates_meal_spacing(self, entries, start, end, min_gap, ignore_entry=None):
        """Return True if placing a meal violates minimum spacing requirements"""
        if min_gap <= 0:
            return False
        for entry in entries:
            if entry is ignore_entry:
                continue
            block_type = (entry['block'].get('type') or '').lower()
            if block_type != 'meal':
                continue
            if start >= entry['end']:
                if start - entry['end'] < min_gap:
                    return True
            elif entry['start'] >= end:
                if entry['start'] - end < min_gap:
                    return True
            else:
                return True
        return False

    def compute_free_segments(self, entries, day_start, day_end):
        """Compute gaps between entries that can host new blocks"""
        segments = []
        cursor = day_start
        for entry in sorted(entries, key=lambda e: e['start']):
            if entry['start'] - cursor >= 20:
                segments.append((cursor, entry['start']))
            cursor = max(cursor, entry['end'])
        if day_end - cursor >= 20:
            segments.append((cursor, day_end))
        return segments

    def insert_meal_entry(self, entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=False):
        """Insert a meal entry either in a free segment or by splitting a block"""
        if day_end - day_start < 20:
            return None

        segments = self.compute_free_segments(entries, day_start, day_end)
        best_candidate = None
        best_distance = None

        for seg_start, seg_end in segments:
            if seg_end - seg_start < 20:
                continue
            placement_start = max(seg_start, min(target, seg_end - 30))
            placement_start -= placement_start % 5
            placement_end = placement_start + 30
            if placement_end > seg_end:
                placement_end = seg_end
                placement_start = max(seg_start, placement_end - 30)
            if placement_end - placement_start < 20:
                continue
            if self.violates_meal_spacing(entries, placement_start, placement_end, min_gap):
                continue
            distance = abs(placement_start - target)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_candidate = (placement_start, placement_end)

        if best_candidate:
            meal_block = {
                'start': self.minutes_to_time(best_candidate[0]),
                'end': self.minutes_to_time(best_candidate[1]),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            entry = {
                'start': best_candidate[0],
                'end': best_candidate[1],
                'block': meal_block
            }
            entries.append(entry)
            entries.sort(key=lambda e: e['start'])
            return entry

        filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]['start'])
        keywords = ['free', 'rest', 'buffer', 'flex', 'break', 'personal', 'catch', 'admin', 'exercise', 'transition', 'placeholder']
        for idx, entry in filler_candidates:
            block = entry['block']
            block_type = (block.get('type') or '').lower()
            if block_type in {'weekly_event', 'meal'}:
                continue
            if block.get('focus_required') and not allow_focus_override:
                continue
            convertible = any(keyword in block_type for keyword in keywords)
            if not convertible and not allow_focus_override:
                continue
            duration = entry['end'] - entry['start']
            if duration < 30:
                continue

            meal_start = max(entry['start'], min(target, entry['end'] - 30))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > entry['end']:
                meal_end = entry['end']
                meal_start = max(entry['start'], meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            new_entries = []

            if meal_start - entry['start'] >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(entry['start'])
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': entry['start'],
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if entry['end'] - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(entry['end'])
                new_entries.append({
                    'start': meal_end,
                    'end': entry['end'],
                    'block': after_block
                })

            entries.pop(idx)
            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        candidate_blocks = [
            (abs(((entry['start'] + entry['end']) / 2) - target), idx, entry)
            for idx, entry in enumerate(entries)
            if (entry['block'].get('type') or '').lower() not in {'weekly_event', 'meal'}
            and (allow_focus_override or not entry['block'].get('focus_required'))
        ]
        candidate_blocks.sort(key=lambda item: item[0])

        for _, idx, entry in candidate_blocks:
            start = entry['start']
            end = entry['end']
            if end - start < 20:
                continue
            meal_start = max(start, min(target, end - 25))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > end:
                meal_end = end
                meal_start = max(start, meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            entries.pop(idx)
            new_entries = []

            if meal_start - start >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(start)
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': start,
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if end - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(end)
                new_entries.append({
                    'start': meal_end,
                    'end': end,
                    'block': after_block
                })

            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        return None

    def ensure_meal_coverage(self, entries, meals_count, day_start, day_end):
        """Guarantee that the schedule contains the required number of meals"""
        if meals_count <= 0:
            entries[:] = [e for e in entries if (e['block'].get('type') or '').lower() != 'meal']
            return

        entries.sort(key=lambda e: e['start'])

        sanitized_entries = []
        for entry in entries:
            block_type = (entry['block'].get('type') or '').lower()
            if block_type == 'meal':
                placeholder_block = {
                    'title': 'Focus Block',
                    'type': 'focus_placeholder',
                    'focus_required': False
                }
                sanitized_entries.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'block': placeholder_block
                })
            else:
                sanitized_entries.append(entry)

        entries[:] = sanitized_entries
        expected_titles = self.get_expected_meal_titles(meals_count)

        for idx, title in enumerate(expected_titles):
            target = self.calculate_meal_target(idx, len(expected_titles), day_start, day_end)
            inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=True)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
            if not inserted:
                self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=20, allow_focus_override=True)

        entries.sort(key=lambda e: e['start'])
        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        if len(meal_entries) > len(expected_titles):
            for extra in meal_entries[len(expected_titles):]:
                extra['block']['type'] = 'focus'
                extra['block']['title'] = 'Focus Block'
                extra['block']['focus_required'] = True

        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(meal_entries):
            if idx >= len(expected_titles):
                break
            entry['block']['title'] = expected_titles[idx]
            entry['block']['type'] = 'meal'
            entry['block']['focus_required'] = False

    def enforce_weekly_events(self, entries, todays_events, day_start, day_end, wake_minutes, sleep_minutes, crosses_midnight):
        """Ensure weekly recurring events are present at their exact times"""
        if not todays_events:
            return

        for event in todays_events:
            try:
                raw_start = self.parse_time_to_minutes(event['start'])
                raw_end = self.parse_time_to_minutes(event['end'])
            except Exception:
                continue

            title = event.get('title') or 'Weekly Event'
            event_start, event_end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            event_start = max(day_start, event_start)
            event_end = min(day_end, event_end)

            if event_end - event_start < 5:
                continue

            adjusted_entries = []
            for entry in entries:
                if entry['end'] <= event_start or entry['start'] >= event_end:
                    adjusted_entries.append(entry)
                    continue

                if entry['start'] < event_start:
                    before_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': entry['start'],
                        'end': event_start,
                        'block': before_block
                    })

                if entry['end'] > event_end:
                    after_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': event_end,
                        'end': entry['end'],
                        'block': after_block
                    })

            event_block = {
                'type': 'weekly_event',
                'title': title,
                'focus_required': False,
                'start': self.minutes_to_time(event_start),
                'end': self.minutes_to_time(event_end)
            }
            adjusted_entries.append({
                'start': event_start,
                'end': event_end,
                'block': event_block
            })

            entries[:] = sorted(adjusted_entries, key=lambda e: e['start'])

    def create_focus_entry(self, start, end, title='Focus Block'):
        """Create a focus block entry covering [start, end) minutes"""
        block = {
            'type': 'focus',
            'title': title,
            'focus_required': True
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def fill_gaps_with_focus(self, entries, day_start, day_end):
        """Fill uncovered time with focus blocks so there are no gaps"""
        entries.sort(key=lambda e: e['start'])
        new_entries = []
        cursor = day_start

        for entry in entries:
            start = max(entry['start'], day_start)
            end = min(entry['end'], day_end)

            if end <= start:
                continue

            if start - cursor >= 5:
                new_entries.append(self.create_focus_entry(cursor, start))
            elif start > cursor:
                start = cursor

            entry['start'] = start
            entry['end'] = end
            new_entries.append(entry)
            cursor = max(cursor, end)

        if day_end - cursor >= 5:
            new_entries.append(self.create_focus_entry(cursor, day_end))

        entries[:] = new_entries

    def sanitize_filler_blocks(self, blocks):
        """Convert filler-style blocks into focus blocks to avoid free time"""
        filler_keywords = [
            'free', 'personal', 'project', 'buffer', 'catch', 'admin', 'rest',
            'recovery', 'flex', 'exercise', 'movement', 'leisure', 'downtime',
            'placeholder', 'unwind', 'relax', 'misc'
        ]
        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine'
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).lower()

            if block_type in protected_types:
                continue
            if block.get('focus_required'):
                continue
            if block_type.startswith('task') or 'todo' in block_type:
                continue
            if 'todo' in title or 'task' in title:
                continue

            if any(keyword in block_type for keyword in filler_keywords) or any(keyword in title for keyword in filler_keywords):
                block['type'] = 'focus'
                block['title'] = 'Focus Block'
                block['focus_required'] = True

    def normalize_focus_blocks(self, blocks):
        """Ensure non-event blocks default to focus work unless explicitly tasks"""
        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip()

            if block_type in {'meal', 'weekly_event'}:
                continue

            if block_type.startswith('task') or 'todo' in block_type:
                block.setdefault('focus_required', False)
                continue

            if 'todo' in title.lower() or 'task' in title.lower():
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            block['type'] = 'focus'
            block['title'] = title or 'Focus Block'
            block['focus_required'] = True

    def post_process_schedule(self, meals_count, todays_events=None):
        """Sort, clip, and adjust the generated schedule"""
        todays_events = todays_events or []
        wake_time = self.commitments['preferences'].get('wake_time', '07:00')
        sleep_time = self.commitments['preferences'].get('sleep_time', '23:00')
        wake_minutes = self.parse_time_to_minutes(wake_time)
        sleep_minutes = self.parse_time_to_minutes(sleep_time)

        day_start = wake_minutes
        day_end = sleep_minutes
        crosses_midnight = False

        if day_end <= day_start:
            day_end += 24 * 60
            crosses_midnight = True

        if todays_events:
            earliest = day_start
            latest = day_end
            for event in todays_events:
                try:
                    raw_start = self.parse_time_to_minutes(event['start'])
                    raw_end = self.parse_time_to_minutes(event['end'])
                except Exception:
                    continue

                event_start, event_end = self.normalize_window(
                    raw_start,
                    raw_end,
                    wake_minutes,
                    sleep_minutes,
                    crosses_midnight
                )

                earliest = min(earliest, event_start)
                latest = max(latest, event_end)

            day_start = min(day_start, earliest)
            day_end = max(day_end, latest)

        raw_blocks = self.schedule.get('blocks', [])
        entries = []

        for block in raw_blocks:
            try:
                raw_start = self.parse_time_to_minutes(block['start'])
                raw_end = self.parse_time_to_minutes(block['end'])
            except Exception:
                continue

            start, end = self.normalize_window(
                raw_start,
                raw_end,
                wake_minutes,
                sleep_minutes,
                crosses_midnight
            )

            start_clamped = max(start, day_start)
            end_clamped = min(end, day_end)

            if end_clamped - start_clamped < 1:
                continue

            block_copy = dict(block)
            entries.append({
                'start': start_clamped,
                'end': end_clamped,
                'block': block_copy
            })

        entries.sort(key=lambda e: e['start'])

        self.enforce_weekly_events(
            entries,
            todays_events,
            day_start,
            day_end,
            wake_minutes,
            sleep_minutes,
            crosses_midnight
        )

        self.ensure_meal_coverage(entries, meals_count, day_start, day_end)

        self.fill_gaps_with_focus(entries, day_start, day_end)

        entries.sort(key=lambda e: e['start'])
        new_blocks = []
        for entry in entries:
            block = entry['block']
            block['start'] = self.minutes_to_time(entry['start'])
            block['end'] = self.minutes_to_time(entry['end'])
            new_blocks.append(block)

        self.sanitize_filler_blocks(new_blocks)
        self.normalize_focus_blocks(new_blocks)
        self.schedule['blocks'] = new_blocks

    def parse_time_to_minutes(self, time_str):
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except Exception:
            return 0

    def minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM string"""
        try:
            minutes = int(round(minutes))
            minutes = minutes % (24 * 60)
            hour = minutes // 60
            minute = minutes % 60
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return "00:00"

    def get_expected_meal_titles(self, meals_count):
        """Return ordered list of expected meal titles"""
        mapping = {
            1: ["Main Meal"],
            2: ["Breakfast", "Dinner"],
            3: ["Breakfast", "Lunch", "Dinner"],
            4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
            5: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ],
            6: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner",
                "Evening Snack"
            ]
        }
        if meals_count in mapping:
            return mapping[meals_count]
        return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]

    def get_meal_ratios(self, meals_count):
        """Return normalized placement ratios for meals throughout the day"""
        ratio_map = {
            1: [0.5],
            2: [0.05, 0.75],
            3: [0.05, 0.5, 0.82],
            4: [0.04, 0.25, 0.55, 0.82],
            5: [0.04, 0.22, 0.45, 0.68, 0.88],
            6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9]
        }
        if meals_count in ratio_map:
            return ratio_map[meals_count]
        if meals_count <= 0:
            return []
        step = 0.85 / max(meals_count - 1, 1)
        return [min(0.9, i * step) for i in range(meals_count)]

    def calculate_meal_target(self, index, total, day_start, day_end):
        """Calculate target minute for a meal placement"""
        if total <= 0:
            return day_start
        ratios = self.get_meal_ratios(total)
        ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
        ratio = max(0.0, min(ratio, 0.95))
        span = max(day_end - day_start, 1)
        target = day_start + int(span * ratio)
        target = max(day_start, min(target, day_end - 30))
        return target - (target % 5)

    def violates_meal_spacing(self, entries, start, end, min_gap, ignore_entry=None):
        """Return True if placing a meal violates minimum spacing requirements"""
        if min_gap <= 0:
            return False
        for entry in entries:
            if entry is ignore_entry:
                continue
            block_type = (entry['block'].get('type') or '').lower()
            if block_type != 'meal':
                continue
            if start >= entry['end']:
                if start - entry['end'] < min_gap:
                    return True
            elif entry['start'] >= end:
                if entry['start'] - end < min_gap:
                    return True
            else:
                return True
        return False

    def compute_free_segments(self, entries, day_start, day_end):
        """Compute gaps between entries that can host new blocks"""
        segments = []
        cursor = day_start
        for entry in sorted(entries, key=lambda e: e['start']):
            if entry['start'] - cursor >= 20:
                segments.append((cursor, entry['start']))
            cursor = max(cursor, entry['end'])
        if day_end - cursor >= 20:
            segments.append((cursor, day_end))
        return segments

    def insert_meal_entry(self, entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=False):
        """Insert a meal entry either in a free segment or by splitting a block"""
        if day_end - day_start < 20:
            return None

        segments = self.compute_free_segments(entries, day_start, day_end)
        best_candidate = None
        best_distance = None

        for seg_start, seg_end in segments:
            if seg_end - seg_start < 20:
                continue
            placement_start = max(seg_start, min(target, seg_end - 30))
            placement_start -= placement_start % 5
            placement_end = placement_start + 30
            if placement_end > seg_end:
                placement_end = seg_end
                placement_start = max(seg_start, placement_end - 30)
            if placement_end - placement_start < 20:
                continue
            if self.violates_meal_spacing(entries, placement_start, placement_end, min_gap):
                continue
            distance = abs(placement_start - target)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_candidate = (placement_start, placement_end)

        if best_candidate:
            meal_block = {
                'start': self.minutes_to_time(best_candidate[0]),
                'end': self.minutes_to_time(best_candidate[1]),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            entry = {
                'start': best_candidate[0],
                'end': best_candidate[1],
                'block': meal_block
            }
            entries.append(entry)
            entries.sort(key=lambda e: e['start'])
            return entry

        filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]['start'])
        keywords = ['free', 'rest', 'buffer', 'flex', 'break', 'personal', 'catch', 'admin', 'exercise', 'transition', 'placeholder']
        for idx, entry in filler_candidates:
            block = entry['block']
            block_type = (block.get('type') or '').lower()
            if block_type in {'weekly_event', 'meal'}:
                continue
            if block.get('focus_required') and not allow_focus_override:
                continue
            convertible = any(keyword in block_type for keyword in keywords)
            if not convertible and not allow_focus_override:
                continue
            duration = entry['end'] - entry['start']
            if duration < 30:
                continue

            meal_start = max(entry['start'], min(target, entry['end'] - 30))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > entry['end']:
                meal_end = entry['end']
                meal_start = max(entry['start'], meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            new_entries = []

            if meal_start - entry['start'] >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(entry['start'])
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': entry['start'],
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if entry['end'] - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(entry['end'])
                new_entries.append({
                    'start': meal_end,
                    'end': entry['end'],
                    'block': after_block
                })

            entries.pop(idx)
            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        candidate_blocks = [
            (abs(((entry['start'] + entry['end']) / 2) - target), idx, entry)
            for idx, entry in enumerate(entries)
            if (entry['block'].get('type') or '').lower() not in {'weekly_event', 'meal'}
            and (allow_focus_override or not entry['block'].get('focus_required'))
        ]
        candidate_blocks.sort(key=lambda item: item[0])

        for _, idx, entry in candidate_blocks:
            start = entry['start']
            end = entry['end']
            if end - start < 20:
                continue
            meal_start = max(start, min(target, end - 25))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > end:
                meal_end = end
                meal_start = max(start, meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            entries.pop(idx)
            new_entries = []

            if meal_start - start >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(start)
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': start,
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if end - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(end)
                new_entries.append({
                    'start': meal_end,
                    'end': end,
                    'block': after_block
                })

            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        return None

    def ensure_meal_coverage(self, entries, meals_count, day_start, day_end):
        """Guarantee that the schedule contains the required number of meals"""
        if meals_count <= 0:
            entries[:] = [e for e in entries if (e['block'].get('type') or '').lower() != 'meal']
            return

        entries.sort(key=lambda e: e['start'])

        sanitized_entries = []
        for entry in entries:
            block_type = (entry['block'].get('type') or '').lower()
            if block_type == 'meal':
                placeholder_block = {
                    'title': 'Focus Block',
                    'type': 'focus_placeholder',
                    'focus_required': False
                }
                sanitized_entries.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'block': placeholder_block
                })
            else:
                sanitized_entries.append(entry)

        entries[:] = sanitized_entries
        expected_titles = self.get_expected_meal_titles(meals_count)

        for idx, title in enumerate(expected_titles):
            target = self.calculate_meal_target(idx, len(expected_titles), day_start, day_end)
            inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=True)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
            if not inserted:
                self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=20, allow_focus_override=True)

        entries.sort(key=lambda e: e['start'])
        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        if len(meal_entries) > len(expected_titles):
            for extra in meal_entries[len(expected_titles):]:
                extra['block']['type'] = 'focus'
                extra['block']['title'] = 'Focus Block'
                extra['block']['focus_required'] = True

        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(meal_entries):
            if idx >= len(expected_titles):
                break
            entry['block']['title'] = expected_titles[idx]
            entry['block']['type'] = 'meal'
            entry['block']['focus_required'] = False

    def enforce_weekly_events(self, entries, todays_events, day_start, day_end):
        """Ensure weekly recurring events are present at their exact times"""
        if not todays_events:
            return

        for event in todays_events:
            try:
                raw_start = self.parse_time_to_minutes(event['start'])
                raw_end = self.parse_time_to_minutes(event['end'])
            except Exception:
                continue

            title = event.get('title') or 'Weekly Event'
            event_start = raw_start
            event_end = raw_end

            if event_end <= event_start:
                event_end += 24 * 60

            if event_start < day_start and (day_start - event_start) > 12 * 60:
                event_start += 24 * 60
                event_end += 24 * 60

            event_start = max(day_start, event_start)
            event_end = min(day_end, event_end)

            if event_end - event_start < 5:
                continue

            adjusted_entries = []
            for entry in entries:
                if entry['end'] <= event_start or entry['start'] >= event_end:
                    adjusted_entries.append(entry)
                    continue

                if entry['start'] < event_start:
                    before_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': entry['start'],
                        'end': event_start,
                        'block': before_block
                    })

                if entry['end'] > event_end:
                    after_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': event_end,
                        'end': entry['end'],
                        'block': after_block
                    })

            event_block = {
                'type': 'weekly_event',
                'title': title,
                'focus_required': False,
                'start': self.minutes_to_time(event_start),
                'end': self.minutes_to_time(event_end)
            }
            adjusted_entries.append({
                'start': event_start,
                'end': event_end,
                'block': event_block
            })

            entries[:] = sorted(adjusted_entries, key=lambda e: e['start'])

    def create_focus_entry(self, start, end, title='Focus Block'):
        """Create a focus block entry covering [start, end) minutes"""
        block = {
            'type': 'focus',
            'title': title,
            'focus_required': True
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def fill_gaps_with_focus(self, entries, day_start, day_end):
        """Fill uncovered time with focus blocks so there are no gaps"""
        entries.sort(key=lambda e: e['start'])
        new_entries = []
        cursor = day_start

        for entry in entries:
            start = max(entry['start'], day_start)
            end = min(entry['end'], day_end)

            if end <= start:
                continue

            if start - cursor >= 5:
                new_entries.append(self.create_focus_entry(cursor, start))
            elif start > cursor:
                start = cursor

            entry['start'] = start
            entry['end'] = end
            new_entries.append(entry)
            cursor = max(cursor, end)

        if day_end - cursor >= 5:
            new_entries.append(self.create_focus_entry(cursor, day_end))

        entries[:] = new_entries

    def sanitize_filler_blocks(self, blocks):
        """Convert filler-style blocks into focus blocks to avoid free time"""
        filler_keywords = [
            'free', 'personal', 'project', 'buffer', 'catch', 'admin', 'rest',
            'recovery', 'flex', 'exercise', 'movement', 'leisure', 'downtime',
            'placeholder', 'unwind', 'relax', 'misc'
        ]
        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine'
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).lower()

            if block_type in protected_types:
                continue
            if block.get('focus_required'):
                continue
            if block_type.startswith('task') or 'todo' in block_type:
                continue
            if 'todo' in title or 'task' in title:
                continue

            if any(keyword in block_type for keyword in filler_keywords) or any(keyword in title for keyword in filler_keywords):
                block['type'] = 'focus'
                block['title'] = 'Focus Block'
                block['focus_required'] = True

    def normalize_focus_blocks(self, blocks):
        """Ensure non-event blocks default to focus work unless explicitly tasks"""
        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).strip()

            if block_type in {'meal', 'weekly_event'}:
                continue

            if block_type.startswith('task') or 'todo' in block_type:
                block.setdefault('focus_required', False)
                continue

            if 'todo' in title.lower() or 'task' in title.lower():
                block['type'] = 'todo'
                block.setdefault('focus_required', False)
                continue

            block['type'] = 'focus'
            block['title'] = title or 'Focus Block'
            block['focus_required'] = True

    def post_process_schedule(self, meals_count, todays_events=None):
        """Sort, clip, and adjust the generated schedule"""
        todays_events = todays_events or []
        wake_time = self.commitments['preferences'].get('wake_time', '07:00')
        sleep_time = self.commitments['preferences'].get('sleep_time', '23:00')
        day_start = self.parse_time_to_minutes(wake_time)
        day_end = self.parse_time_to_minutes(sleep_time)
        if day_end <= day_start:
            day_end += 24 * 60

        if todays_events:
            earliest = day_start
            latest = day_end
            for event in todays_events:
                try:
                    event_start = self.parse_time_to_minutes(event['start'])
                    event_end = self.parse_time_to_minutes(event['end'])
                except Exception:
                    continue

                if event_end <= event_start:
                    event_end += 24 * 60

                earliest = min(earliest, event_start)
                latest = max(latest, event_end)

            day_start = min(day_start, earliest)
            day_end = max(day_end, latest)

        raw_blocks = self.schedule.get('blocks', [])
        entries = []

        for block in raw_blocks:
            try:
                start = self.parse_time_to_minutes(block['start'])
                end = self.parse_time_to_minutes(block['end'])
            except Exception:
                continue

            if end <= start:
                end += 24 * 60

            if start < day_start and (day_start - start) > 12 * 60:
                start += 24 * 60
                end += 24 * 60

            start_clamped = max(start, day_start)
            end_clamped = min(end, day_end)

            if end_clamped - start_clamped < 1:
                continue

            block_copy = dict(block)
            entries.append({
                'start': start_clamped,
                'end': end_clamped,
                'block': block_copy
            })

        entries.sort(key=lambda e: e['start'])

        self.enforce_weekly_events(entries, todays_events, day_start, day_end)

        self.ensure_meal_coverage(entries, meals_count, day_start, day_end)

        self.fill_gaps_with_focus(entries, day_start, day_end)

        entries.sort(key=lambda e: e['start'])
        new_blocks = []
        for entry in entries:
            block = entry['block']
            block['start'] = self.minutes_to_time(entry['start'])
            block['end'] = self.minutes_to_time(entry['end'])
            new_blocks.append(block)

        self.sanitize_filler_blocks(new_blocks)
        self.normalize_focus_blocks(new_blocks)
        self.schedule['blocks'] = new_blocks

    def parse_time_to_minutes(self, time_str):
        """Convert HH:MM string to minutes since midnight"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except Exception:
            return 0

    def minutes_to_time(self, minutes):
        """Convert minutes since midnight to HH:MM string"""
        try:
            minutes = int(round(minutes))
            minutes = minutes % (24 * 60)
            hour = minutes // 60
            minute = minutes % 60
            return f"{hour:02d}:{minute:02d}"
        except Exception:
            return "00:00"

    def get_expected_meal_titles(self, meals_count):
        """Return ordered list of expected meal titles"""
        mapping = {
            1: ["Main Meal"],
            2: ["Breakfast", "Dinner"],
            3: ["Breakfast", "Lunch", "Dinner"],
            4: ["Breakfast", "Snack/Brunch", "Lunch", "Dinner"],
            5: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner"
            ],
            6: [
                "Breakfast",
                "Mid-morning Snack",
                "Lunch",
                "Afternoon Snack",
                "Dinner",
                "Evening Snack"
            ]
        }
        if meals_count in mapping:
            return mapping[meals_count]
        return [f"Meal {i + 1}" for i in range(max(meals_count, 0))]

    def get_meal_ratios(self, meals_count):
        """Return normalized placement ratios for meals throughout the day"""
        ratio_map = {
            1: [0.5],
            2: [0.05, 0.75],
            3: [0.05, 0.5, 0.82],
            4: [0.04, 0.25, 0.55, 0.82],
            5: [0.04, 0.22, 0.45, 0.68, 0.88],
            6: [0.04, 0.2, 0.38, 0.58, 0.78, 0.9]
        }
        if meals_count in ratio_map:
            return ratio_map[meals_count]
        if meals_count <= 0:
            return []
        step = 0.85 / max(meals_count - 1, 1)
        return [min(0.9, i * step) for i in range(meals_count)]

    def calculate_meal_target(self, index, total, day_start, day_end):
        """Calculate target minute for a meal placement"""
        if total <= 0:
            return day_start
        ratios = self.get_meal_ratios(total)
        ratio = ratios[index] if index < len(ratios) else index / max(total - 1, 1)
        ratio = max(0.0, min(ratio, 0.95))
        span = max(day_end - day_start, 1)
        target = day_start + int(span * ratio)
        target = max(day_start, min(target, day_end - 30))
        return target - (target % 5)

    def violates_meal_spacing(self, entries, start, end, min_gap, ignore_entry=None):
        """Return True if placing a meal violates minimum spacing requirements"""
        if min_gap <= 0:
            return False
        for entry in entries:
            if entry is ignore_entry:
                continue
            block_type = (entry['block'].get('type') or '').lower()
            if block_type != 'meal':
                continue
            if start >= entry['end']:
                if start - entry['end'] < min_gap:
                    return True
            elif entry['start'] >= end:
                if entry['start'] - end < min_gap:
                    return True
            else:
                return True
        return False

    def compute_free_segments(self, entries, day_start, day_end):
        """Compute gaps between entries that can host new blocks"""
        segments = []
        cursor = day_start
        for entry in sorted(entries, key=lambda e: e['start']):
            if entry['start'] - cursor >= 20:
                segments.append((cursor, entry['start']))
            cursor = max(cursor, entry['end'])
        if day_end - cursor >= 20:
            segments.append((cursor, day_end))
        return segments

    def insert_meal_entry(self, entries, target, title, day_start, day_end, min_gap=30, allow_focus_override=False):
        """Insert a meal entry either in a free segment or by splitting a block"""
        if day_end - day_start < 20:
            return None

        segments = self.compute_free_segments(entries, day_start, day_end)
        best_candidate = None
        best_distance = None

        for seg_start, seg_end in segments:
            if seg_end - seg_start < 20:
                continue
            placement_start = max(seg_start, min(target, seg_end - 30))
            placement_start -= placement_start % 5
            placement_end = placement_start + 30
            if placement_end > seg_end:
                placement_end = seg_end
                placement_start = max(seg_start, placement_end - 30)
            if placement_end - placement_start < 20:
                continue
            if self.violates_meal_spacing(entries, placement_start, placement_end, min_gap):
                continue
            distance = abs(placement_start - target)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_candidate = (placement_start, placement_end)

        if best_candidate:
            meal_block = {
                'start': self.minutes_to_time(best_candidate[0]),
                'end': self.minutes_to_time(best_candidate[1]),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            entry = {
                'start': best_candidate[0],
                'end': best_candidate[1],
                'block': meal_block
            }
            entries.append(entry)
            entries.sort(key=lambda e: e['start'])
            return entry

        filler_candidates = sorted(enumerate(entries), key=lambda item: item[1]['start'])
        keywords = ['free', 'rest', 'buffer', 'flex', 'break', 'personal', 'catch', 'admin', 'exercise', 'transition', 'placeholder']
        for idx, entry in filler_candidates:
            block = entry['block']
            block_type = (block.get('type') or '').lower()
            if block_type in {'weekly_event', 'meal'}:
                continue
            if block.get('focus_required') and not allow_focus_override:
                continue
            convertible = any(keyword in block_type for keyword in keywords)
            if not convertible and not allow_focus_override:
                continue
            duration = entry['end'] - entry['start']
            if duration < 30:
                continue

            meal_start = max(entry['start'], min(target, entry['end'] - 30))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > entry['end']:
                meal_end = entry['end']
                meal_start = max(entry['start'], meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            new_entries = []

            if meal_start - entry['start'] >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(entry['start'])
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': entry['start'],
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if entry['end'] - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(entry['end'])
                new_entries.append({
                    'start': meal_end,
                    'end': entry['end'],
                    'block': after_block
                })

            entries.pop(idx)
            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        candidate_blocks = [
            (abs(((entry['start'] + entry['end']) / 2) - target), idx, entry)
            for idx, entry in enumerate(entries)
            if (entry['block'].get('type') or '').lower() not in {'weekly_event', 'meal'}
            and (allow_focus_override or not entry['block'].get('focus_required'))
        ]
        candidate_blocks.sort(key=lambda item: item[0])

        for _, idx, entry in candidate_blocks:
            start = entry['start']
            end = entry['end']
            if end - start < 20:
                continue
            meal_start = max(start, min(target, end - 25))
            meal_start -= meal_start % 5
            meal_end = meal_start + 30
            if meal_end > end:
                meal_end = end
                meal_start = max(start, meal_end - 30)
            if meal_end - meal_start < 20:
                continue
            if self.violates_meal_spacing(entries, meal_start, meal_end, min_gap, ignore_entry=entry):
                continue

            base_block = entry['block']
            entries.pop(idx)
            new_entries = []

            if meal_start - start >= 5:
                before_block = dict(base_block)
                before_block['start'] = self.minutes_to_time(start)
                before_block['end'] = self.minutes_to_time(meal_start)
                new_entries.append({
                    'start': start,
                    'end': meal_start,
                    'block': before_block
                })

            meal_block = {
                'start': self.minutes_to_time(meal_start),
                'end': self.minutes_to_time(meal_end),
                'type': 'meal',
                'title': title,
                'focus_required': False
            }
            meal_entry = {
                'start': meal_start,
                'end': meal_end,
                'block': meal_block
            }
            new_entries.append(meal_entry)

            if end - meal_end >= 5:
                after_block = dict(base_block)
                after_block['start'] = self.minutes_to_time(meal_end)
                after_block['end'] = self.minutes_to_time(end)
                new_entries.append({
                    'start': meal_end,
                    'end': end,
                    'block': after_block
                })

            for offset, new_entry in enumerate(new_entries):
                entries.insert(idx + offset, new_entry)
            entries.sort(key=lambda e: e['start'])
            return meal_entry

        return None

    def ensure_meal_coverage(self, entries, meals_count, day_start, day_end):
        """Guarantee that the schedule contains the required number of meals"""
        if meals_count <= 0:
            entries[:] = [e for e in entries if (e['block'].get('type') or '').lower() != 'meal']
            return

        entries.sort(key=lambda e: e['start'])

        sanitized_entries = []
        for entry in entries:
            block_type = (entry['block'].get('type') or '').lower()
            if block_type == 'meal':
                placeholder_block = {
                    'title': 'Focus Block',
                    'type': 'focus_placeholder',
                    'focus_required': False
                }
                sanitized_entries.append({
                    'start': entry['start'],
                    'end': entry['end'],
                    'block': placeholder_block
                })
            else:
                sanitized_entries.append(entry)

        entries[:] = sanitized_entries
        expected_titles = self.get_expected_meal_titles(meals_count)

        for idx, title in enumerate(expected_titles):
            target = self.calculate_meal_target(idx, len(expected_titles), day_start, day_end)
            inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=35)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=25, allow_focus_override=True)
            if not inserted:
                inserted = self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=10, allow_focus_override=True)
            if not inserted:
                self.insert_meal_entry(entries, target, title, day_start, day_end, min_gap=0, allow_focus_override=True)

        entries.sort(key=lambda e: e['start'])
        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        if len(meal_entries) > len(expected_titles):
            for extra in meal_entries[len(expected_titles):]:
                extra['block']['type'] = 'focus'
                extra['block']['title'] = 'Focus Block'
                extra['block']['focus_required'] = True

        meal_entries = [e for e in entries if (e['block'].get('type') or '').lower() == 'meal']
        meal_entries.sort(key=lambda e: e['start'])

        for idx, entry in enumerate(meal_entries):
            if idx >= len(expected_titles):
                break
            entry['block']['title'] = expected_titles[idx]
            entry['block']['type'] = 'meal'
            entry['block']['focus_required'] = False

    def enforce_weekly_events(self, entries, todays_events, day_start, day_end):
        """Ensure weekly recurring events are present at their exact times"""
        if not todays_events:
            return

        for event in todays_events:
            try:
                raw_start = self.parse_time_to_minutes(event['start'])
                raw_end = self.parse_time_to_minutes(event['end'])
            except Exception:
                continue

            title = event.get('title') or 'Weekly Event'
            event_start = raw_start
            event_end = raw_end

            if event_end <= event_start:
                event_end += 24 * 60

            if event_start < day_start and (day_start - event_start) > 12 * 60:
                event_start += 24 * 60
                event_end += 24 * 60

            event_start = max(day_start, event_start)
            event_end = min(day_end, event_end)

            if event_end - event_start < 5:
                continue

            adjusted_entries = []
            for entry in entries:
                if entry['end'] <= event_start or entry['start'] >= event_end:
                    adjusted_entries.append(entry)
                    continue

                if entry['start'] < event_start:
                    before_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': entry['start'],
                        'end': event_start,
                        'block': before_block
                    })

                if entry['end'] > event_end:
                    after_block = dict(entry['block'])
                    adjusted_entries.append({
                        'start': event_end,
                        'end': entry['end'],
                        'block': after_block
                    })

            event_block = {
                'type': 'weekly_event',
                'title': title,
                'focus_required': False,
                'start': self.minutes_to_time(event_start),
                'end': self.minutes_to_time(event_end)
            }
            adjusted_entries.append({
                'start': event_start,
                'end': event_end,
                'block': event_block
            })

            entries[:] = sorted(adjusted_entries, key=lambda e: e['start'])

    def create_focus_entry(self, start, end, title='Focus Block'):
        """Create a focus block entry covering [start, end) minutes"""
        block = {
            'type': 'focus',
            'title': title,
            'focus_required': True
        }
        return {
            'start': start,
            'end': end,
            'block': block
        }

    def fill_gaps_with_focus(self, entries, day_start, day_end):
        """Fill uncovered time with focus blocks so there are no gaps"""
        entries.sort(key=lambda e: e['start'])
        new_entries = []
        cursor = day_start

        for entry in entries:
            start = max(entry['start'], day_start)
            end = min(entry['end'], day_end)

            if end <= start:
                continue

            if start - cursor >= 5:
                new_entries.append(self.create_focus_entry(cursor, start))
            elif start > cursor:
                start = cursor

            entry['start'] = start
            entry['end'] = end
            new_entries.append(entry)
            cursor = max(cursor, end)

        if day_end - cursor >= 5:
            new_entries.append(self.create_focus_entry(cursor, day_end))

        entries[:] = new_entries

    def sanitize_filler_blocks(self, blocks):
        """Convert filler-style blocks into focus blocks to avoid free time"""
        filler_keywords = [
            'free', 'personal', 'project', 'buffer', 'catch', 'admin', 'rest',
            'recovery', 'flex', 'exercise', 'movement', 'leisure', 'downtime',
            'placeholder'
        ]
        protected_types = {
            'meal', 'weekly_event', 'break', 'morning_routine', 'evening_routine'
        }

        for block in blocks:
            block_type = str(block.get('type', '')).lower()
            title = str(block.get('title', '')).lower()

            if block_type in protected_types:
                continue
            if block.get('focus_required'):
                continue
            if block_type.startswith('task') or 'todo' in block_type:
                continue
            if 'todo' in title or 'task' in title:
                continue

            if any(keyword in block_type for keyword in filler_keywords) or any(keyword in title for keyword in filler_keywords):
                block['type'] = 'focus'
                block['title'] = 'Focus Block'
                block['focus_required'] = True

    def post_process_schedule(self, meals_count, todays_events=None):
        """Sort, clip, and adjust the generated schedule"""
        todays_events = todays_events or []
        wake_time = self.commitments['preferences'].get('wake_time', '07:00')
        sleep_time = self.commitments['preferences'].get('sleep_time', '23:00')
        day_start = self.parse_time_to_minutes(wake_time)
        day_end = self.parse_time_to_minutes(sleep_time)
        if day_end <= day_start:
            day_end += 24 * 60

        if todays_events:
            earliest = day_start
            latest = day_end
            for event in todays_events:
                try:
                    event_start = self.parse_time_to_minutes(event['start'])
                    event_end = self.parse_time_to_minutes(event['end'])
                except Exception:
                    continue

                if event_end <= event_start:
                    event_end += 24 * 60

                earliest = min(earliest, event_start)
                latest = max(latest, event_end)

            day_start = min(day_start, earliest)
            day_end = max(day_end, latest)

        raw_blocks = self.schedule.get('blocks', [])
        entries = []

        for block in raw_blocks:
            try:
                start = self.parse_time_to_minutes(block['start'])
                end = self.parse_time_to_minutes(block['end'])
            except Exception:
                continue

            if end <= start:
                end += 24 * 60

            if start < day_start and (day_start - start) > 12 * 60:
                start += 24 * 60
                end += 24 * 60

            start_clamped = max(start, day_start)
            end_clamped = min(end, day_end)

            if end_clamped - start_clamped < 1:
                continue

            block_copy = dict(block)
            entries.append({
                'start': start_clamped,
                'end': end_clamped,
                'block': block_copy
            })

        entries.sort(key=lambda e: e['start'])

        self.enforce_weekly_events(entries, todays_events, day_start, day_end)

        self.ensure_meal_coverage(entries, meals_count, day_start, day_end)

        self.fill_gaps_with_focus(entries, day_start, day_end)

        entries.sort(key=lambda e: e['start'])
        new_blocks = []
        for entry in entries:
            block = entry['block']
            block['start'] = self.minutes_to_time(entry['start'])
            block['end'] = self.minutes_to_time(entry['end'])
            new_blocks.append(block)

        self.sanitize_filler_blocks(new_blocks)
        self.schedule['blocks'] = new_blocks

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