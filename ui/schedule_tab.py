"""Schedule and tasks management UI."""
from __future__ import annotations

from typing import Optional

import tkinter as tk
from tkinter import ttk


def create_tab(app) -> None:
    tab = tk.Frame(app.notebook, bg=app.colors["bg"])
    app.notebook.add(tab, text="📅 Schedule & Tasks")

    canvas = tk.Canvas(tab, bg=app.colors["bg"])
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=app.colors["bg"])

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    pref_frame = tk.LabelFrame(
        scrollable_frame,
        text="⚙️ Daily Preferences",
        font=("Arial", 14, "bold"),
        bg=app.colors["card"],
        padx=25,
        pady=20,
    )
    pref_frame.pack(fill="x", padx=30, pady=15)

    prefs = app.commitments.get("preferences", {})

    row1 = tk.Frame(pref_frame, bg=app.colors["card"])
    row1.pack(fill="x", pady=8)
    tk.Label(row1, text="⏰ Wake Time:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)

    wake_frame = tk.Frame(row1, bg=app.colors["card"])
    wake_frame.pack(side="left")
    app.wake_hour_var = tk.StringVar(value="7")
    app.wake_min_var = tk.StringVar(value="00")
    app.wake_period_var = tk.StringVar(value="AM")

    tk.Spinbox(wake_frame, from_=1, to=12, textvariable=app.wake_hour_var, width=4, font=("Arial", 11)).pack(side="left", padx=2)
    tk.Label(wake_frame, text=":", font=("Arial", 11, "bold"), bg=app.colors["card"]).pack(side="left")
    tk.Spinbox(wake_frame, from_=0, to=59, textvariable=app.wake_min_var, width=4, format="%02.0f", font=("Arial", 11)).pack(side="left", padx=2)
    ttk.Combobox(wake_frame, textvariable=app.wake_period_var, values=["AM", "PM"], width=5, state="readonly", font=("Arial", 10)).pack(side="left", padx=5)

    row2 = tk.Frame(pref_frame, bg=app.colors["card"])
    row2.pack(fill="x", pady=8)
    tk.Label(row2, text="🌙 Sleep Time:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)

    sleep_frame = tk.Frame(row2, bg=app.colors["card"])
    sleep_frame.pack(side="left")
    app.sleep_hour_var = tk.StringVar(value="11")
    app.sleep_min_var = tk.StringVar(value="00")
    app.sleep_period_var = tk.StringVar(value="PM")

    tk.Spinbox(sleep_frame, from_=1, to=12, textvariable=app.sleep_hour_var, width=4, font=("Arial", 11)).pack(side="left", padx=2)
    tk.Label(sleep_frame, text=":", font=("Arial", 11, "bold"), bg=app.colors["card"]).pack(side="left")
    tk.Spinbox(sleep_frame, from_=0, to=59, textvariable=app.sleep_min_var, width=4, format="%02.0f", font=("Arial", 11)).pack(side="left", padx=2)
    ttk.Combobox(sleep_frame, textvariable=app.sleep_period_var, values=["AM", "PM"], width=5, state="readonly", font=("Arial", 10)).pack(side="left", padx=5)

    row3 = tk.Frame(pref_frame, bg=app.colors["card"])
    row3.pack(fill="x", pady=8)
    tk.Label(row3, text="💪 Gym Days/Week:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)
    app.gym_freq_var = tk.IntVar(value=prefs.get("gym_frequency", 3))
    tk.Scale(row3, from_=0, to=7, orient="horizontal", variable=app.gym_freq_var, bg=app.colors["card"], font=("Arial", 10)).pack(side="left", padx=5)

    row4 = tk.Frame(pref_frame, bg=app.colors["card"])
    row4.pack(fill="x", pady=8)
    tk.Label(row4, text="🎯 Focus Block:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)
    app.focus_length_var = tk.IntVar(value=prefs.get("focus_block_length", 50))
    tk.Scale(row4, from_=25, to=90, orient="horizontal", variable=app.focus_length_var, bg=app.colors["card"], font=("Arial", 10)).pack(side="left", padx=5)
    tk.Label(row4, text="minutes", font=("Arial", 10), bg=app.colors["card"]).pack(side="left")

    row5 = tk.Frame(pref_frame, bg=app.colors["card"])
    row5.pack(fill="x", pady=8)
    tk.Label(row5, text="☕ Break Length:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)
    app.break_length_var = tk.IntVar(value=prefs.get("break_length", 10))
    tk.Scale(row5, from_=5, to=30, orient="horizontal", variable=app.break_length_var, bg=app.colors["card"], font=("Arial", 10)).pack(side="left", padx=5)
    tk.Label(row5, text="minutes", font=("Arial", 10), bg=app.colors["card"]).pack(side="left")

    row6 = tk.Frame(pref_frame, bg=app.colors["card"])
    row6.pack(fill="x", pady=8)
    tk.Label(row6, text="🍽️ Meals Per Day:", width=18, anchor="w", font=("Arial", 11), bg=app.colors["card"]).pack(side="left", padx=5)
    app.meals_var = tk.IntVar(value=prefs.get("meals_per_day", 3))
    tk.Scale(row6, from_=1, to=5, orient="horizontal", variable=app.meals_var, bg=app.colors["card"], font=("Arial", 10)).pack(side="left", padx=5)
    tk.Label(row6, text="(1=OMAD, 3=Standard)", font=("Arial", 9), fg=app.colors["text_light"], bg=app.colors["card"]).pack(side="left", padx=10)

    events_frame = tk.LabelFrame(
        scrollable_frame,
        text="📅 Weekly Recurring Events",
        font=("Arial", 14, "bold"),
        bg=app.colors["card"],
        padx=25,
        pady=20,
    )
    events_frame.pack(fill="both", expand=True, padx=30, pady=15)

    tk.Label(
        events_frame,
        text="Classes, work shifts, appointments that repeat weekly",
        fg=app.colors["text_light"],
        bg=app.colors["card"],
        font=("Arial", 10),
    ).pack(anchor="w", pady=(0, 10))

    app.events_container = tk.Frame(events_frame, bg=app.colors["card"])
    app.events_container.pack(fill="x")

    tk.Button(
        events_frame,
        text="➕ Add Event",
        command=lambda: add_event_entry(app),
        bg=app.colors["primary"],
        fg="white",
        font=("Arial", 11, "bold"),
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2",
    ).pack(pady=10)

    app.event_entries: list = []
    load_event_entries(app)

    tasks_frame = tk.LabelFrame(
        scrollable_frame,
        text="✅ Priority Tasks",
        font=("Arial", 14, "bold"),
        bg=app.colors["card"],
        padx=25,
        pady=20,
    )
    tasks_frame.pack(fill="both", expand=True, padx=30, pady=15)

    tk.Label(
        tasks_frame,
        text="List tasks you want scheduled today",
        fg=app.colors["text_light"],
        bg=app.colors["card"],
        font=("Arial", 10),
    ).pack(anchor="w", pady=(0, 10))

    app.tasks_container = tk.Frame(tasks_frame, bg=app.colors["card"])
    app.tasks_container.pack(fill="x")

    tk.Button(
        tasks_frame,
        text="➕ Add Task",
        command=lambda: add_task_entry(app),
        bg=app.colors["success"],
        fg="white",
        font=("Arial", 11, "bold"),
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2",
    ).pack(pady=10)

    app.task_entries: list = []
    load_task_entries(app)

    tk.Button(
        scrollable_frame,
        text="Save Schedule",
        command=app.save_all_schedule_data,
        font=("Arial", 12, "bold"),
        bg="#4CAF50",
        fg="white",
        padx=30,
        pady=10,
    ).pack(pady=20)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


def load_event_entries(app) -> None:
    for event in app.commitments.get("weekly_events", []):
        add_event_entry(app, event)


def _populate_time_fields(hour_var, min_var, period_var, time_str: str, default_period: str) -> None:
    try:
        hour_24, minute = map(int, time_str.split(":"))
        if hour_24 == 0:
            hour_var.set("12")
            period_var.set("AM")
        elif hour_24 == 12:
            hour_var.set("12")
            period_var.set("PM")
        elif hour_24 > 12:
            hour_var.set(str(hour_24 - 12))
            period_var.set("PM")
        else:
            hour_var.set(str(hour_24))
            period_var.set("AM")
        min_var.set(f"{minute:02d}")
    except ValueError:
        hour_var.set("10")
        min_var.set("00")
        period_var.set(default_period)


def add_event_entry(app, event_data: Optional[dict] = None) -> None:
    frame = tk.Frame(app.events_container, relief="solid", bd=1, bg="#ffffff")
    frame.pack(fill="x", pady=8, padx=5)

    inner = tk.Frame(frame, bg="#ffffff")
    inner.pack(fill="x", padx=15, pady=15)

    tk.Label(inner, text="Day:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
    day_var = tk.StringVar(value=(event_data.get("day") if event_data else "Monday"))
    ttk.Combobox(inner, textvariable=day_var, values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], state="readonly", width=12, font=("Arial", 10)).grid(row=0, column=1, sticky="w")

    tk.Label(inner, text="Start:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(20, 5))
    start_frame = tk.Frame(inner, bg="#ffffff")
    start_frame.grid(row=0, column=3, sticky="w")

    start_hour_var = tk.StringVar()
    start_min_var = tk.StringVar()
    start_period_var = tk.StringVar()
    _populate_time_fields(start_hour_var, start_min_var, start_period_var, event_data.get("start", "07:00") if event_data else "07:00", "AM")

    tk.Spinbox(start_frame, from_=1, to=12, textvariable=start_hour_var, width=3, font=("Arial", 10)).pack(side="left", padx=1)
    tk.Label(start_frame, text=":", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left")
    tk.Spinbox(start_frame, from_=0, to=59, textvariable=start_min_var, width=3, format="%02.0f", font=("Arial", 10)).pack(side="left", padx=1)
    ttk.Combobox(start_frame, textvariable=start_period_var, values=["AM", "PM"], width=4, state="readonly", font=("Arial", 9)).pack(side="left", padx=3)

    tk.Label(inner, text="End:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=0, column=4, sticky="w", padx=(20, 5))
    end_frame = tk.Frame(inner, bg="#ffffff")
    end_frame.grid(row=0, column=5, sticky="w")

    end_hour_var = tk.StringVar()
    end_min_var = tk.StringVar()
    end_period_var = tk.StringVar()
    _populate_time_fields(end_hour_var, end_min_var, end_period_var, event_data.get("end", "09:00") if event_data else "09:00", "AM")

    tk.Spinbox(end_frame, from_=1, to=12, textvariable=end_hour_var, width=3, font=("Arial", 10)).pack(side="left", padx=1)
    tk.Label(end_frame, text=":", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left")
    tk.Spinbox(end_frame, from_=0, to=59, textvariable=end_min_var, width=3, format="%02.0f", font=("Arial", 10)).pack(side="left", padx=1)
    ttk.Combobox(end_frame, textvariable=end_period_var, values=["AM", "PM"], width=4, state="readonly", font=("Arial", 9)).pack(side="left", padx=3)

    tk.Label(inner, text="Title:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=(10, 0))
    title_var = tk.StringVar(value=event_data.get("title", "") if event_data else "")
    tk.Entry(inner, textvariable=title_var, width=60, font=("Arial", 11)).grid(row=1, column=1, columnspan=5, sticky="ew", padx=5, pady=(10, 0))

    tk.Button(
        inner,
        text="🗑️ Remove",
        command=lambda: remove_event_entry(app, frame),
        bg=app.colors["danger"],
        fg="white",
        font=("Arial", 9, "bold"),
        padx=10,
        pady=5,
        relief="flat",
        cursor="hand2",
    ).grid(row=0, column=6, rowspan=2, padx=15)

    app.event_entries.append(
        {
            "frame": frame,
            "day": day_var,
            "start_hour": start_hour_var,
            "start_min": start_min_var,
            "start_period": start_period_var,
            "end_hour": end_hour_var,
            "end_min": end_min_var,
            "end_period": end_period_var,
            "title": title_var,
        }
    )


def remove_event_entry(app, frame: tk.Frame) -> None:
    app.event_entries = [entry for entry in app.event_entries if entry["frame"] != frame]
    frame.destroy()


def load_task_entries(app) -> None:
    for task in app.tasks.get("tasks", []):
        add_task_entry(app, task)


def add_task_entry(app, task_data: Optional[dict] = None) -> None:
    frame = tk.Frame(app.tasks_container, relief="solid", bd=1, bg="#ffffff")
    frame.pack(fill="x", pady=8, padx=5)

    inner = tk.Frame(frame, bg="#ffffff")
    inner.pack(fill="x", padx=15, pady=15)

    tk.Label(inner, text="Task Name:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=5)
    task_var = tk.StringVar(value=task_data.get("name", "") if task_data else "")
    tk.Entry(inner, textvariable=task_var, width=50, font=("Arial", 11)).grid(row=0, column=1, columnspan=3, padx=5, sticky="ew")

    tk.Label(inner, text="Duration:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=(10, 0))
    duration_var = tk.IntVar(value=task_data.get("duration", 30) if task_data else 30)
    duration_frame = tk.Frame(inner, bg="#ffffff")
    duration_frame.grid(row=1, column=1, sticky="w", pady=(10, 0))
    tk.Scale(
        duration_frame,
        from_=15,
        to=120,
        orient="horizontal",
        variable=duration_var,
        bg="#ffffff",
        font=("Arial", 9),
        length=200,
    ).pack(side="left")
    tk.Label(duration_frame, text="minutes", font=("Arial", 10), bg="#ffffff").pack(side="left", padx=5)

    tk.Label(inner, text="Priority:", bg="#ffffff", font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", padx=(20, 5), pady=(10, 0))
    priority_var = tk.StringVar(value=task_data.get("priority", "medium") if task_data else "medium")
    ttk.Combobox(
        inner,
        textvariable=priority_var,
        values=["high", "medium", "low"],
        state="readonly",
        width=12,
        font=("Arial", 10),
    ).grid(row=1, column=3, sticky="w", pady=(10, 0))

    tk.Button(
        inner,
        text="🗑️ Remove",
        command=lambda: remove_task_entry(app, frame),
        bg=app.colors["danger"],
        fg="white",
        font=("Arial", 9, "bold"),
        padx=10,
        pady=5,
        relief="flat",
        cursor="hand2",
    ).grid(row=0, column=4, rowspan=2, padx=15)

    inner.columnconfigure(1, weight=1)

    app.task_entries.append(
        {
            "frame": frame,
            "name": task_var,
            "duration": duration_var,
            "priority": priority_var,
        }
    )


def remove_task_entry(app, frame: tk.Frame) -> None:
    app.task_entries = [entry for entry in app.task_entries if entry["frame"] != frame]
    frame.destroy()
