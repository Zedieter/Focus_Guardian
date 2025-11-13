"""Focus lock tab UI."""
from __future__ import annotations

import tkinter as tk


def create_tab(app) -> None:
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
        command=app.start_focus_session,
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
        command=app.stop_focus_session,
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
        app.update_focus_ui()
