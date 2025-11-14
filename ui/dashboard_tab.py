import datetime
import tkinter as tk
from tkinter import scrolledtext


class DashboardTab:
    def __init__(self, app):
        self.app = app

    def create(self):
        app = self.app

        tab = tk.Frame(app.notebook, bg=app.colors['bg'])
        app.notebook.add(tab, text="📊 Dashboard")

        header = tk.Frame(tab, bg=app.colors['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Focus Guardian",
            font=('Arial', 24, 'bold'),
            bg=app.colors['primary'],
            fg='white'
        ).pack(pady=20)

        content = tk.Frame(tab, bg=app.colors['bg'])
        content.pack(fill='both', expand=True, padx=30, pady=30)

        stats_row = tk.Frame(content, bg=app.colors['bg'])
        stats_row.pack(fill='x', pady=(0, 20))

        total_focus = f"{app.stats['total_focus_time'] // 60}h {app.stats['total_focus_time'] % 60}m"
        self._create_stat_card(
            stats_row,
            "⏱️ Total Focus Time",
            total_focus,
            app.colors['primary']
        ).pack(side='left', fill='both', expand=True, padx=5)

        self._create_stat_card(
            stats_row,
            "✅ Sessions Completed",
            str(app.stats['sessions_completed']),
            app.colors['success']
        ).pack(side='left', fill='both', expand=True, padx=5)

        self._create_stat_card(
            stats_row,
            "🔥 Current Streak",
            f"{app.stats['current_streak']} days",
            app.colors['warning']
        ).pack(side='left', fill='both', expand=True, padx=5)

        schedule_card = tk.Frame(content, bg=app.colors['card'], relief='solid', bd=1)
        schedule_card.pack(fill='both', expand=True, pady=10)

        tk.Label(
            schedule_card,
            text="📅 Today's Schedule Preview",
            font=('Arial', 14, 'bold'),
            bg=app.colors['card'],
            fg=app.colors['text']
        ).pack(pady=15, padx=15, anchor='w')

        app.dashboard_schedule = scrolledtext.ScrolledText(
            schedule_card,
            height=10,
            font=('Consolas', 10),
            wrap='word',
            bg='#f8fafc',
            relief='flat'
        )
        app.dashboard_schedule.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        actions = tk.Frame(content, bg=app.colors['bg'])
        actions.pack(fill='x', pady=10)

        tk.Button(
            actions,
            text="🚀 Start Quick Focus",
            command=lambda: app.quick_focus(25),
            font=('Arial', 12, 'bold'),
            bg=app.colors['primary'],
            fg='white',
            padx=20,
            pady=12,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)

        tk.Button(
            actions,
            text="🤖 Generate Today's Plan",
            command=app.generate_daily_plan,
            font=('Arial', 12, 'bold'),
            bg=app.colors['info'],
            fg='white',
            padx=20,
            pady=12,
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)

        self.update_dashboard()

    def _create_stat_card(self, parent, title, value, color):
        card = tk.Frame(parent, bg=self.app.colors['card'], relief='solid', bd=1)

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
            bg=self.app.colors['card'],
            fg=self.app.colors['text']
        ).pack(pady=15)

        return card

    def update_dashboard(self):
        app = self.app

        schedule_widget = getattr(app, 'dashboard_schedule', None)
        if schedule_widget is None:
            return

        schedule_widget.delete('1.0', 'end')

        blocks = app.schedule.get('blocks') if isinstance(app.schedule, dict) else None
        if not blocks:
            schedule_widget.insert(
                '1.0',
                "No schedule for today.\nClick 'Generate Today's Plan' to create one!"
            )
            return

        now = datetime.datetime.now()
        current_time = now.strftime('%H:%M')

        for block in blocks[:6]:
            start_12 = app.convert_to_12hr(block['start'])
            end_12 = app.convert_to_12hr(block['end'])

            if block['start'] <= current_time < block['end']:
                prefix = "▶️ "
            else:
                prefix = "   "

            icon = "🔒" if block.get('focus_required') else "⏰"
            schedule_widget.insert(
                'end',
                f"{prefix}{icon} {start_12} - {end_12}: {block['title']}\n"
            )
