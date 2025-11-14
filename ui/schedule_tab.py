import tkinter as tk
from tkinter import ttk, messagebox


class ScheduleTab:
    def __init__(self, app):
        self.app = app

    def create(self):
        app = self.app
        tab = tk.Frame(app.notebook, bg=app.colors['bg'])
        app.notebook.add(tab, text="📅 Schedule & Tasks")

        canvas = tk.Canvas(tab, bg=app.colors['bg'])
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=app.colors['bg'])

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
            bg=app.colors['card'],
            padx=25,
            pady=20
        )
        pref_frame.pack(fill='x', padx=30, pady=15)

        prefs = app.commitments.get('preferences', {})

        # Wake time with AM/PM
        row1 = tk.Frame(pref_frame, bg=app.colors['card'])
        row1.pack(fill='x', pady=8)
        tk.Label(
            row1,
            text="⏰ Wake Time:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)

        wake_frame = tk.Frame(row1, bg=app.colors['card'])
        wake_frame.pack(side='left')
        app.wake_hour_var = tk.StringVar(value='7')
        app.wake_min_var = tk.StringVar(value='00')
        app.wake_period_var = tk.StringVar(value='AM')

        tk.Spinbox(
            wake_frame,
            from_=1,
            to=12,
            textvariable=app.wake_hour_var,
            width=4,
            font=('Arial', 11)
        ).pack(side='left', padx=2)
        tk.Label(wake_frame, text=":", font=('Arial', 11, 'bold'), bg=app.colors['card']).pack(side='left')
        tk.Spinbox(
            wake_frame,
            from_=0,
            to=59,
            textvariable=app.wake_min_var,
            width=4,
            format='%02.0f',
            font=('Arial', 11)
        ).pack(side='left', padx=2)
        ttk.Combobox(
            wake_frame,
            textvariable=app.wake_period_var,
            values=['AM', 'PM'],
            width=5,
            state='readonly',
            font=('Arial', 10)
        ).pack(side='left', padx=5)

        # Sleep time with AM/PM
        row2 = tk.Frame(pref_frame, bg=app.colors['card'])
        row2.pack(fill='x', pady=8)
        tk.Label(
            row2,
            text="🌙 Sleep Time:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)

        sleep_frame = tk.Frame(row2, bg=app.colors['card'])
        sleep_frame.pack(side='left')
        app.sleep_hour_var = tk.StringVar(value='11')
        app.sleep_min_var = tk.StringVar(value='00')
        app.sleep_period_var = tk.StringVar(value='PM')

        tk.Spinbox(
            sleep_frame,
            from_=1,
            to=12,
            textvariable=app.sleep_hour_var,
            width=4,
            font=('Arial', 11)
        ).pack(side='left', padx=2)
        tk.Label(sleep_frame, text=":", font=('Arial', 11, 'bold'), bg=app.colors['card']).pack(side='left')
        tk.Spinbox(
            sleep_frame,
            from_=0,
            to=59,
            textvariable=app.sleep_min_var,
            width=4,
            format='%02.0f',
            font=('Arial', 11)
        ).pack(side='left', padx=2)
        ttk.Combobox(
            sleep_frame,
            textvariable=app.sleep_period_var,
            values=['AM', 'PM'],
            width=5,
            state='readonly',
            font=('Arial', 10)
        ).pack(side='left', padx=5)

        # Gym frequency with slider
        row3 = tk.Frame(pref_frame, bg=app.colors['card'])
        row3.pack(fill='x', pady=8)
        tk.Label(
            row3,
            text="💪 Gym Days/Week:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)
        app.gym_freq_var = tk.IntVar(value=prefs.get('gym_frequency', 3))
        gym_scale = tk.Scale(
            row3,
            from_=0,
            to=7,
            orient='horizontal',
            variable=app.gym_freq_var,
            bg=app.colors['card'],
            font=('Arial', 10)
        )
        gym_scale.pack(side='left', padx=5)

        # Focus block with slider
        row4 = tk.Frame(pref_frame, bg=app.colors['card'])
        row4.pack(fill='x', pady=8)
        tk.Label(
            row4,
            text="🎯 Focus Block:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)
        app.focus_length_var = tk.IntVar(value=prefs.get('focus_block_length', 50))
        focus_scale = tk.Scale(
            row4,
            from_=25,
            to=90,
            orient='horizontal',
            variable=app.focus_length_var,
            bg=app.colors['card'],
            font=('Arial', 10)
        )
        focus_scale.pack(side='left', padx=5)
        tk.Label(row4, text="minutes", font=('Arial', 10), bg=app.colors['card']).pack(side='left')

        # Break length with slider
        row5 = tk.Frame(pref_frame, bg=app.colors['card'])
        row5.pack(fill='x', pady=8)
        tk.Label(
            row5,
            text="☕ Break Length:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)
        app.break_length_var = tk.IntVar(value=prefs.get('break_length', 10))
        break_scale = tk.Scale(
            row5,
            from_=5,
            to=30,
            orient='horizontal',
            variable=app.break_length_var,
            bg=app.colors['card'],
            font=('Arial', 10)
        )
        break_scale.pack(side='left', padx=5)
        tk.Label(row5, text="minutes", font=('Arial', 10), bg=app.colors['card']).pack(side='left')

        # Meals per day
        row6 = tk.Frame(pref_frame, bg=app.colors['card'])
        row6.pack(fill='x', pady=8)
        tk.Label(
            row6,
            text="🍽️ Meals Per Day:",
            width=18,
            anchor='w',
            font=('Arial', 11),
            bg=app.colors['card']
        ).pack(side='left', padx=5)
        app.meals_var = tk.IntVar(value=prefs.get('meals_per_day', 3))
        meals_scale = tk.Scale(
            row6,
            from_=1,
            to=5,
            orient='horizontal',
            variable=app.meals_var,
            bg=app.colors['card'],
            font=('Arial', 10)
        )
        meals_scale.pack(side='left', padx=5)
        tk.Label(
            row6,
            text="(1=OMAD, 3=Standard)",
            font=('Arial', 9),
            fg=app.colors['text_light'],
            bg=app.colors['card']
        ).pack(side='left', padx=10)

        # Weekly Events with better styling
        events_frame = tk.LabelFrame(
            scrollable_frame,
            text="📅 Weekly Recurring Events",
            font=('Arial', 14, 'bold'),
            bg=app.colors['card'],
            padx=25,
            pady=20
        )
        events_frame.pack(fill='both', expand=True, padx=30, pady=15)

        tk.Label(
            events_frame,
            text="Recurring commitments: classes, meetings, etc.",
            fg=app.colors['text_light'],
            font=('Arial', 10),
            bg=app.colors['card']
        ).pack(anchor='w', pady=(0, 15))

        app.events_container = tk.Frame(events_frame, bg=app.colors['card'])
        app.events_container.pack(fill='both', expand=True)

        app.event_entries = []
        self.load_event_entries()

        add_event_btn = tk.Button(
            events_frame,
            text="+ Add Weekly Event",
            command=self.add_event_entry,
            bg=app.colors['primary'],
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
            bg=app.colors['card'],
            padx=25,
            pady=20
        )
        tasks_frame.pack(fill='both', expand=True, padx=30, pady=15)

        tk.Label(
            tasks_frame,
            text="One-time tasks: homework, projects, errands, etc.",
            fg=app.colors['text_light'],
            font=('Arial', 10),
            bg=app.colors['card']
        ).pack(anchor='w', pady=(0, 15))

        app.tasks_container = tk.Frame(tasks_frame, bg=app.colors['card'])
        app.tasks_container.pack(fill='both', expand=True)

        app.task_entries = []
        self.load_task_entries()

        add_task_btn = tk.Button(
            tasks_frame,
            text="+ Add Task",
            command=self.add_task_entry,
            bg=app.colors['primary'],
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
            bg=app.colors['success'],
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
        app = self.app
        for event in app.commitments.get('weekly_events', []):
            self.add_event_entry(event)

    def add_event_entry(self, event_data=None):
        app = self.app
        frame = tk.Frame(app.events_container, relief='solid', bd=1, bg='#ffffff')
        frame.pack(fill='x', pady=8, padx=5)

        inner = tk.Frame(frame, bg='#ffffff')
        inner.pack(fill='x', padx=15, pady=15)

        # Day selector
        tk.Label(inner, text="Day:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        day_var = tk.StringVar(value=event_data.get('day', 'Monday') if event_data else 'Monday')
        day_menu = ttk.Combobox(
            inner,
            textvariable=day_var,
            values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            width=15,
            state='readonly',
            font=('Arial', 10)
        )
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
        tk.Spinbox(
            start_frame,
            from_=0,
            to=59,
            textvariable=start_min_var,
            width=3,
            format='%02.0f',
            font=('Arial', 10)
        ).pack(side='left', padx=1)
        ttk.Combobox(
            start_frame,
            textvariable=start_period_var,
            values=['AM', 'PM'],
            width=4,
            state='readonly',
            font=('Arial', 9)
        ).pack(side='left', padx=3)

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
        tk.Spinbox(
            end_frame,
            from_=0,
            to=59,
            textvariable=end_min_var,
            width=3,
            format='%02.0f',
            font=('Arial', 10)
        ).pack(side='left', padx=1)
        ttk.Combobox(
            end_frame,
            textvariable=end_period_var,
            values=['AM', 'PM'],
            width=4,
            state='readonly',
            font=('Arial', 9)
        ).pack(side='left', padx=3)

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
            bg=app.colors['danger'],
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        del_btn.grid(row=0, column=6, rowspan=2, padx=15)

        app.event_entries.append({
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
        app = self.app
        app.event_entries = [e for e in app.event_entries if e['frame'] != frame]
        frame.destroy()

    def load_task_entries(self):
        app = self.app
        for task in app.tasks.get('tasks', []):
            self.add_task_entry(task)

    def add_task_entry(self, task_data=None):
        app = self.app
        frame = tk.Frame(app.tasks_container, relief='solid', bd=1, bg='#ffffff')
        frame.pack(fill='x', pady=8, padx=5)

        inner = tk.Frame(frame, bg='#ffffff')
        inner.pack(fill='x', padx=15, pady=15)

        # Task name - full width
        tk.Label(inner, text="Task Name:", bg='#ffffff', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5)
        task_var = tk.StringVar(value=task_data.get('name', '') if task_data else '')
        tk.Entry(inner, textvariable=task_var, width=50, font=('Arial', 11)).grid(row=0, column=1, columnspan=3, padx=5, sticky='ew')

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
            bg=app.colors['danger'],
            fg='white',
            font=('Arial', 9, 'bold'),
            padx=10,
            pady=5,
            relief='flat',
            cursor='hand2'
        )
        del_btn.grid(row=0, column=4, rowspan=2, padx=15)

        inner.columnconfigure(1, weight=1)

        app.task_entries.append({
            'frame': frame,
            'name': task_var,
            'duration': duration_var,
            'priority': priority_var
        })

    def remove_task_entry(self, frame):
        app = self.app
        app.task_entries = [t for t in app.task_entries if t['frame'] != frame]
        frame.destroy()

    def save_all_schedule_data(self):
        app = self.app
        try:
            wake_hour = int(app.wake_hour_var.get())
            if app.wake_period_var.get() == 'PM' and wake_hour != 12:
                wake_hour += 12
            elif app.wake_period_var.get() == 'AM' and wake_hour == 12:
                wake_hour = 0
            wake_time = f"{wake_hour:02d}:{app.wake_min_var.get()}"

            sleep_hour = int(app.sleep_hour_var.get())
            if app.sleep_period_var.get() == 'PM' and sleep_hour != 12:
                sleep_hour += 12
            elif app.sleep_period_var.get() == 'AM' and sleep_hour == 12:
                sleep_hour = 0
            sleep_time = f"{sleep_hour:02d}:{app.sleep_min_var.get()}"

            app.commitments['preferences'] = {
                'wake_time': wake_time,
                'sleep_time': sleep_time,
                'gym_frequency': app.gym_freq_var.get(),
                'focus_block_length': app.focus_length_var.get(),
                'break_length': app.break_length_var.get(),
                'meals_per_day': app.meals_var.get()
            }

            app.commitments['weekly_events'] = []
            for entry in app.event_entries:
                if entry['title'].get().strip():
                    start_hour = int(entry['start_hour'].get())
                    if entry['start_period'].get() == 'PM' and start_hour != 12:
                        start_hour += 12
                    elif entry['start_period'].get() == 'AM' and start_hour == 12:
                        start_hour = 0
                    start_time = f"{start_hour:02d}:{entry['start_min'].get()}"

                    end_hour = int(entry['end_hour'].get())
                    if entry['end_period'].get() == 'PM' and end_hour != 12:
                        end_hour += 12
                    elif entry['end_period'].get() == 'AM' and end_hour == 12:
                        end_hour = 0
                    end_time = f"{end_hour:02d}:{entry['end_min'].get()}"

                    app.commitments['weekly_events'].append({
                        'day': entry['day'].get(),
                        'start': start_time,
                        'end': end_time,
                        'title': entry['title'].get()
                    })

            app.tasks['tasks'] = []
            for entry in app.task_entries:
                if entry['name'].get().strip():
                    app.tasks['tasks'].append({
                        'name': entry['name'].get(),
                        'duration': int(entry['duration'].get()),
                        'priority': entry['priority'].get()
                    })

            app.save_json(app.commitments_file, app.commitments)
            app.save_json(app.tasks_file, app.tasks)

            messagebox.showinfo("Success", "✅ All schedule data saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
