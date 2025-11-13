"""Settings tab UI."""
from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk


def create_tab(app) -> None:
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="⚙️ Settings")

    canvas = tk.Canvas(tab)
    scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    tk.Label(scrollable_frame, text="Blocked Websites", font=("Arial", 12, "bold")).pack(pady=10)
    app.sites_text = scrolledtext.ScrolledText(scrollable_frame, height=8, font=("Arial", 10))
    app.sites_text.pack(fill="x", padx=20)
    app.sites_text.insert("1.0", "\n".join(app.config["blocked_sites"]))

    tk.Label(scrollable_frame, text="Blocked Applications", font=("Arial", 12, "bold")).pack(pady=10)
    app.apps_text = scrolledtext.ScrolledText(scrollable_frame, height=8, font=("Arial", 10))
    app.apps_text.pack(fill="x", padx=20)
    app.apps_text.insert("1.0", "\n".join(app.config["blocked_apps"]))

    app.hard_mode_var = tk.BooleanVar(value=app.config["hard_mode"])
    tk.Checkbutton(
        scrollable_frame,
        text="Hard Mode (Cannot stop sessions early)",
        variable=app.hard_mode_var,
        font=("Arial", 11, "bold"),
        fg="#f44336",
    ).pack(pady=10)

    tk.Label(scrollable_frame, text="OpenAI API Key", font=("Arial", 12, "bold")).pack(pady=10)
    app.api_key_entry = tk.Entry(scrollable_frame, width=50, show="*", font=("Arial", 10))
    app.api_key_entry.pack()
    app.api_key_entry.insert(0, app.config.get("api_key", ""))

    tk.Label(scrollable_frame, text="Settings Password", font=("Arial", 12, "bold")).pack(pady=10)
    password_frame = tk.Frame(scrollable_frame)
    password_frame.pack()

    app.password_entry = tk.Entry(password_frame, show="*", width=30, font=("Arial", 10))
    app.password_entry.pack(side="left", padx=5)

    tk.Button(
        password_frame,
        text="Set Password",
        command=app.set_password,
        bg="#FF9800",
        fg="white",
    ).pack(side="left")

    tk.Button(
        scrollable_frame,
        text="Save Settings",
        command=app.save_settings,
        font=("Arial", 12, "bold"),
        bg="#4CAF50",
        fg="white",
        padx=30,
        pady=10,
    ).pack(pady=20)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
