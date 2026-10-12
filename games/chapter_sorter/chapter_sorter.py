from __future__ import annotations
import csv, random, os, sys
from pathlib import Path
from typing import List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from rich import box

console = Console()

DATA_DIR = Path(__file__).parent.parent / "hangman" / "data"

# Chapter sorter works best with NCERT classes that have proper chapter names
CLASS_FILES = {
    "1": ("9th",  DATA_DIR / "keywords-glossary-9th.tsv"),
    "2": ("10th", DATA_DIR / "keywords-glossary-10th.tsv"),
    "3": ("11th", DATA_DIR / "keywords-glossary-11th.tsv"),
    "4": ("12th", DATA_DIR / "keywords-glossary-12th.tsv"),
}

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 0,   "replenish": False},
}

LABELS = ["A", "B", "C", "D"]


def clear(): os.system("clear")

def truncate(s, n=70):
    return s if len(s) <= n else s[:n-1] + "…"

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def load_entries(picks):
    entries, seen = [], set()
    for p in picks:
        with open(CLASS_FILES[p][1], encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                cls  = row.get("Class", "").strip()
                if kw and ch and kw.lower() not in seen:
                    seen.add(kw.lower())
                    entries.append({"keyword": kw, "definition": defn,
                                    "chapter": ch, "class": cls})
    return entries


def build_questions(entries):
    chapters = list({e["chapter"] for e in entries})
    if len(chapters) < 4:
        return []
    qs = []
    for e in entries:
        wrong_chs = [c for c in chapters if c != e["chapter"]]
        if len(wrong_chs) < 3:
            continue
        distractors = random.sample(wrong_chs, 3)
        opts = distractors + [e["chapter"]]
        random.shuffle(opts)
        qs.append({
            "keyword":    e["keyword"],
            "definition": e["definition"],
            "chapter":    e["chapter"],
            "class":      e["class"],
            "opts":       opts,
            "correct":    opts.index(e["chapter"]),
        })
    random.shuffle(qs)
    return qs


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]📚  CHAPTER SORTER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th\n\n[bold]  2.[/bold]  10th\n\n"
        "[bold]  3.[/bold]  11th\n\n[bold]  4.[/bold]  12th\n\n"
        "[bold]  5.[/bold]  11th + 12th  [dim](recommended — most chapters)[/dim]",
        title="[bold]Select Class(es)[/bold]", box=box.ROUNDED))
    console.print()
    MAP = {"1":["1"],"2":["2"],"3":["3"],"4":["4"],"5":["3","4"]}
    choice = Prompt.ask("  Enter [1/2/3/4/5]", choices=list(MAP.keys()), default="5")
    picks = MAP[choice]
    name = "+".join(CLASS_FILES[p][0] for p in picks)
    return name, picks


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]📚  CHAPTER SORTER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints (shows definition)\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · no hints · keyword only",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1","2","3"], default="2")
    return MODES[choice]


def draw_question(q, lives, hints, mode, streak, q_num, eliminated, answered, class_name, show_def):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    console.print(Panel(
        Align.center(f"[bold cyan]📚  CHAPTER SORTER[/bold cyan]  [dim]· {class_name}[/dim]"
                     f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))

    max_lives = mode["lives"]; max_hints = mode["hints"]
    console.print(f"  {render_lives(lives, max_lives, color)}    "
                  f"{render_hints(hints, max_hints, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    body = f"\n  [bold]{q['keyword']}[/bold]\n"
    if show_def and q["definition"]:
        body += f"\n  [dim italic]{truncate(q['definition'], 100)}[/dim italic]\n"
    console.print(Panel(body,
        title="[dim]Which chapter does this term belong to?[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    for i, (label, opt) in enumerate(zip(LABELS, q["opts"])):
        short = truncate(opt, 55)
        if i in eliminated:
            console.print(f"  [dim strike]{label}.  {short}[/dim strike]")
        elif answered is not None:
            if i == q["correct"]:
                console.print(f"  [bold green]{label}.  {short}  ✓[/bold green]")
            elif label == answered:
                console.print(f"  [bold red]{label}.  {short}  ✗[/bold red]")
            else:
                console.print(f"  [dim]{label}.  {short}[/dim]")
        else:
            console.print(f"  [bold]{label}.[/bold]  {short}")
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  CHAPTER SORTER  ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",   str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",  str(stats["hints_used"]))

    if stats["missed_chapters"]:
        from collections import Counter
        t.add_section()
        for ch, n in Counter(stats["missed_chapters"]).most_common(5):
            t.add_row(f"  {truncate(ch, 35)}", f"[red]missed {n}×[/red]")

    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    entries   = load_entries(picks)
    questions = build_questions(entries)
    if not questions:
        console.print("[red]Not enough chapters in selected class(es).[/red]")
        return
    console.print(f"[dim]{len(questions)} questions · "
                  f"{len({q['chapter'] for q in questions})} chapters.[/dim]")

    lives = mode["lives"]; hints = mode["hints"]
    max_lives = mode["max_lives"]; max_hints = mode["max_hints"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0,
             "hints_used":0,"missed_chapters":[]}

    # Easy mode always shows definition
    show_def = mode["name"] == "Easy"

    while True:
        if idx >= len(questions):
            random.shuffle(questions); idx = 0

        q = questions[idx]; idx += 1
        eliminated = []
        wrong_indices = [i for i in range(4) if i != q["correct"]]
        hint_active = show_def

        while True:
            draw_question(q, lives, hints, mode, streak, stats["played"]+1,
                          eliminated, None, class_name, hint_active)
            hint_txt = "[dim]? = hint[/dim]" if hints > 0 and not show_def else ""
            console.print(f"  [A/B/C/D]  {hint_txt}  [dim]q = quit[/dim]: ", end="")
            try:
                user = input().strip().upper()
            except (EOFError, KeyboardInterrupt):
                show_analysis(stats, mode); sys.exit()

            if user == "Q":
                show_analysis(stats, mode); sys.exit()

            if user == "?" and not show_def:
                if hints <= 0:
                    console.print("  [red]No hints![/red]"); input("  [Enter]..."); continue
                remaining = [i for i in wrong_indices if i not in eliminated]
                if remaining:
                    eliminated.append(random.choice(remaining))
                    stats["hints_used"] += 1
                    if max_hints < 999: hints -= 1
                hint_active = True
                continue

            if user not in LABELS: continue

            chosen_idx = LABELS.index(user)
            correct = chosen_idx == q["correct"]
            stats["played"] += 1

            if correct:
                stats["won"] += 1
                streak += 1
                if streak > best_streak:
                    best_streak = streak
                    stats["best_streak"] = best_streak
                if mode["replenish"]:
                    lives += 1; hints += 1
            else:
                stats["lost"] += 1
                streak = 0
                stats["missed_chapters"].append(q["chapter"])
                if max_lives < 999: lives -= 1

            draw_question(q, lives, hints, mode, streak, stats["played"],
                          eliminated, user, class_name, True)
            input("\n  [Enter] next question...")
            break

        if lives <= 0:
            show_analysis(stats, mode)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q": break
            except (EOFError, KeyboardInterrupt): break
            lives = mode["lives"]; hints = mode["hints"]
            streak = best_streak = idx = 0
            stats = {"played":0,"won":0,"lost":0,"best_streak":0,
                     "hints_used":0,"missed_chapters":[]}
            random.shuffle(questions)


if __name__ == "__main__":
    main()
