import datetime
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

        app.schedule_display = self.schedule_display

        self.display_schedule()

        return tab

    def display_schedule(self):
        """Display the current schedule inside the planner tab."""
        app = self.app

        if not hasattr(self, 'schedule_display'):
            return

        display = self.schedule_display
        display.delete('1.0', 'end')

        today = datetime.datetime.now().strftime("%A, %B %d, %Y")

        display.insert('end', f"📅 TODAY'S SCHEDULE - {today}\n", 'title')
        display.insert('end', "─" * 60 + "\n\n")

        for block in app.schedule.get('blocks', []):
            is_focus = block.get('focus_required')
            icon = "🔒 " if is_focus else "⏰ "

            start_12 = app.convert_to_12hr(block['start'])
            end_12 = app.convert_to_12hr(block['end'])

            time_tag = 'focus_time' if is_focus else 'time'

            display.insert('end', icon)
            display.insert('end', f"{start_12} - {end_12}\n", time_tag)
            display.insert('end', f"   {block['title']}\n", 'block_title')

            if is_focus:
                display.insert('end', "   🎯 Focus Block - Distractions will be blocked\n", 'type_label')
            else:
                display.insert('end', f"   Type: {block['type']}\n", 'type_label')

            display.insert('end', "\n")
