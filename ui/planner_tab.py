import tkinter as tk
from tkinter import scrolledtext


class PlannerTab:
    def __init__(self, app):
        self.app = app

    def create(self):
        app = self.app
        tab = tk.Frame(app.notebook, bg=app.colors['bg'])
        app.notebook.add(tab, text="🤖 AI Planner")

        header = tk.Frame(tab, bg=app.colors['card'])
        header.pack(fill='x', pady=(20, 0), padx=20)

        title = tk.Label(
            header,
            text="AI Daily Planner",
            font=('Arial', 24, 'bold'),
            bg=app.colors['card'],
            fg=app.colors['text']
        )
        title.pack(pady=20)

        generate_btn = tk.Button(
            tab,
            text="✨ Generate Today's Plan",
            command=app.generate_daily_plan,
            font=('Arial', 14, 'bold'),
            bg=app.colors['primary'],
            fg='white',
            padx=40,
            pady=18,
            relief='flat',
            cursor='hand2'
        )
        generate_btn.pack(pady=15)

        schedule_frame = tk.Frame(tab, bg=app.colors['card'], relief='solid', bd=1)
        schedule_frame.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Label(
            schedule_frame,
            text="📋 Today's Schedule:",
            font=('Arial', 14, 'bold'),
            bg=app.colors['card'],
            fg=app.colors['text']
        ).pack(pady=15, padx=15, anchor='w')

        app.schedule_display = scrolledtext.ScrolledText(
            schedule_frame,
            height=20,
            font=('Consolas', 11),
            wrap='word',
            bg='#f8fafc',
            relief='flat',
            padx=10,
            pady=10
        )
        app.schedule_display.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        app.display_schedule()

        return tab
