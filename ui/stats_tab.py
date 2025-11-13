"""Statistics tab UI."""
from __future__ import annotations

import tkinter as tk


def _create_large_stat_card(app, parent, title, value, subtitle, color):
    card = tk.Frame(parent, bg=app.colors["card"], relief="solid", bd=1)

    header = tk.Frame(card, bg=color, height=10)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(
        card,
        text=title,
        font=("Arial", 12, "bold"),
        bg=app.colors["card"],
        fg=app.colors["text"],
    ).pack(pady=(15, 5))

    tk.Label(
        card,
        text=value,
        font=("Arial", 32, "bold"),
        bg=app.colors["card"],
        fg=color,
    ).pack(pady=10)

    tk.Label(
        card,
        text=subtitle,
        font=("Arial", 9),
        bg=app.colors["card"],
        fg=app.colors["text_light"],
    ).pack(pady=(0, 15))

    return card


def _show_achievement_badges(app, parent):
    achievements = [
        ("🌱", "First Step", app.stats["sessions_completed"] >= 1, "Complete your first session"),
        ("💪", "Consistent", app.stats["current_streak"] >= 3, "3 day streak"),
        ("🔥", "On Fire", app.stats["current_streak"] >= 7, "7 day streak"),
        ("⭐", "Focused", app.stats["total_focus_time"] >= 300, "5+ hours of focus"),
        ("🏆", "Master", app.stats["sessions_completed"] >= 50, "50+ sessions"),
    ]

    for emoji, name, unlocked, desc in achievements:
        badge_container = tk.Frame(parent, bg=app.colors["card"])
        badge_container.pack(side="left", padx=15, pady=10)

        badge_card = tk.Frame(
            badge_container,
            bg="#10b981" if unlocked else "#e5e7eb",
            relief="solid",
            bd=2,
            width=100,
            height=100,
        )
        badge_card.pack()
        badge_card.pack_propagate(False)

        tk.Label(
            badge_card,
            text=emoji,
            font=("Arial", 36),
            bg="#10b981" if unlocked else "#e5e7eb",
        ).pack(expand=True)

        tk.Label(
            badge_container,
            text=name,
            font=("Arial", 10, "bold"),
            fg=app.colors["text"],
            bg=app.colors["card"],
        ).pack(pady=(5, 2))

        tk.Label(
            badge_container,
            text=desc,
            font=("Arial", 8),
            fg=app.colors["text_light"],
            bg=app.colors["card"],
        ).pack()


def create_tab(app) -> None:
    tab = tk.Frame(app.notebook, bg=app.colors["bg"])
    app.notebook.add(tab, text="📈 Stats")

    header = tk.Frame(tab, bg=app.colors["card"])
    header.pack(fill="x", pady=(20, 0), padx=20)

    tk.Label(
        header,
        text="Your Progress & Achievements",
        font=("Arial", 24, "bold"),
        bg=app.colors["card"],
        fg=app.colors["text"],
    ).pack(pady=20)

    stats_grid = tk.Frame(tab, bg=app.colors["bg"])
    stats_grid.pack(fill="both", expand=True, padx=30, pady=20)

    row1 = tk.Frame(stats_grid, bg=app.colors["bg"])
    row1.pack(fill="x", pady=10)
    _create_large_stat_card(
        app,
        row1,
        "⏱️ Total Focus Time",
        f"{app.stats['total_focus_time'] // 60}h {app.stats['total_focus_time'] % 60}m",
        "Time spent in deep focus",
        app.colors["primary"],
    ).pack(side="left", fill="both", expand=True, padx=10)
    _create_large_stat_card(
        app,
        row1,
        "✅ Sessions Completed",
        str(app.stats["sessions_completed"]),
        "Successful focus sessions",
        app.colors["success"],
    ).pack(side="left", fill="both", expand=True, padx=10)

    row2 = tk.Frame(stats_grid, bg=app.colors["bg"])
    row2.pack(fill="x", pady=10)
    _create_large_stat_card(
        app,
        row2,
        "🔥 Current Streak",
        f"{app.stats['current_streak']} days",
        "Consecutive days of focus",
        app.colors["warning"],
    ).pack(side="left", fill="both", expand=True, padx=10)
    _create_large_stat_card(
        app,
        row2,
        "🏆 Longest Streak",
        f"{app.stats['longest_streak']} days",
        "Your personal best",
        app.colors["info"],
    ).pack(side="left", fill="both", expand=True, padx=10)

    achievements = tk.Frame(tab, bg=app.colors["card"], relief="solid", bd=1)
    achievements.pack(fill="x", padx=30, pady=20)

    tk.Label(
        achievements,
        text="🎖️ Achievements",
        font=("Arial", 16, "bold"),
        bg=app.colors["card"],
        fg=app.colors["text"],
    ).pack(pady=15, padx=15, anchor="w")

    badge_frame = tk.Frame(achievements, bg=app.colors["card"])
    badge_frame.pack(fill="x", padx=20, pady=(0, 20))
    _show_achievement_badges(app, badge_frame)

    tk.Button(
        tab,
        text="🔄 Reset Statistics",
        command=app.reset_stats,
        font=("Arial", 10),
        bg=app.colors["danger"],
        fg="white",
        padx=20,
        pady=10,
        relief="flat",
        cursor="hand2",
    ).pack(pady=10)
