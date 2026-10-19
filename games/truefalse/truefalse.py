from __future__ import annotations
import csv, random, os, sys
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from rich import box

console = Console()

DATA_DIR = Path(__file__).parent.parent / "hangman" / "data"

CLASS_FILES = {
    "1": ("9th",      DATA_DIR / "keywords-glossary-9th.tsv"),
    "2": ("10th",     DATA_DIR / "keywords-glossary-10th.tsv"),
    "3": ("11th",     DATA_DIR / "keywords-glossary-11th.tsv"),
    "4": ("12th",     DATA_DIR / "keywords-glossary-12th.tsv"),
    "5": ("Advanced", DATA_DIR / "keywords-glossary-advanced.tsv"),
}

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 5,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "replenish": False},
}


def clear(): os.system("clear")

def truncate(s: str, n: int = 110) -> str:
    return s if len(s) <= n else s[:n-1] + "…"

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"


def load_entries(picks):
    entries, seen = [], set()
    for p in picks:
        with open(CLASS_FILES[p][1], encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                if kw and defn and kw.lower() not in seen:
                    seen.add(kw.lower())
                    entries.append({"keyword": kw, "definition": defn, "chapter": ch})
    return entries


def build_questions(entries):
    definitions = [e["definition"] for e in entries]
    qs = []
    for e in entries:
        # TRUE: correct pair
        qs.append({"keyword": e["keyword"], "definition": e["definition"],
                   "chapter": e["chapter"], "answer": True, "fake_def": None})
        # FALSE: correct keyword, wrong definition
        wrong_def = random.choice([d for d in definitions if d != e["definition"]])
        qs.append({"keyword": e["keyword"], "definition": wrong_def,
                   "chapter": e["chapter"], "answer": False,
                   "real_def": e["definition"], "fake_def": wrong_def})
    random.shuffle(qs)
    return qs


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]✅  TRUE OR FALSE[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th\n\n[bold]  2.[/bold]  10th\n\n"
        "[bold]  3.[/bold]  11th\n\n[bold]  4.[/bold]  12th\n\n"
        "[bold]  5.[/bold]  [bold magenta]Advanced[/bold magenta]",
        title="[bold]Select Class(es)[/bold]", box=box.ROUNDED))
    console.print()
    while True:
        raw = Prompt.ask("  Your choice", default="3").replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_FILES]
        if picks: break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    return "+".join(CLASS_FILES[p][0] for p in picks), picks


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]✅  TRUE OR FALSE[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 5 lives · +1 on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · no replenishment",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1","2","3"], default="2")
    return MODES[choice]


def draw_question(q, lives, max_lives, mode, streak, q_num, answered, class_name):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    console.print(Panel(
        Align.center(f"[bold cyan]✅  TRUE OR FALSE[/bold cyan]  [dim]· {class_name}[/dim]"
                     f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    console.print(Panel(
        f"\n  [bold]{q['keyword']}[/bold]\n\n"
        f"  [italic]{q['definition']}[/italic]\n",
        title=f"[dim]{q['chapter']}[/dim]  —  [dim]Is this definition correct for this term?[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    if answered is None:
        console.print("  [bold green]T[/bold green] = True    [bold red]F[/bold red] = False    [dim]q = quit[/dim]")
    elif answered == q["answer"]:
        console.print(Align.center(Panel("[bold green]✓  Correct![/bold green]",
                                         box=box.HEAVY, style="green", width=30)))
        if not q["answer"] and q.get("real_def"):
            console.print()
            console.print(Panel(f"[dim]Correct definition:\n{q['real_def']}[/dim]",
                                box=box.SIMPLE, style="dim"))
    else:
        correct_word = "TRUE" if q["answer"] else "FALSE"
        console.print(Align.center(Panel(
            f"[bold red]✗  Wrong!  Answer was {correct_word}[/bold red]",
            box=box.HEAVY, style="red", width=40)))
        if not q["answer"] and q.get("real_def"):
            console.print()
            console.print(Panel(f"[dim]Correct definition:\n{q['real_def']}[/dim]",
                                box=box.SIMPLE, style="dim"))
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  TRUE OR FALSE  ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",   str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("True Correct",  f"[green]{stats['true_correct']}[/green][dim]/{stats['true_total']}[/dim]")
    t.add_row("False Correct", f"[green]{stats['false_correct']}[/green][dim]/{stats['false_total']}[/dim]")
    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]

    console.print("[dim]Loading…[/dim]")
    entries   = load_entries(picks)
    questions = build_questions(entries)
    console.print(f"[dim]{len(questions)} questions ready.[/dim]")

    lives = mode["lives"]; max_lives = mode["max_lives"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0,
             "true_correct":0,"true_total":0,"false_correct":0,"false_total":0}

    while True:
        if idx >= len(questions):
            random.shuffle(questions); idx = 0

        q = questions[idx]; idx += 1

        draw_question(q, lives, max_lives, mode, streak, stats["played"]+1, None, class_name)
        console.print("  Answer: ", end="")
        try:
            user = input().strip().upper()
        except (EOFError, KeyboardInterrupt):
            show_analysis(stats, mode); sys.exit()

        if user == "Q":
            show_analysis(stats, mode); sys.exit()

        if user not in ("T", "F"):
            continue

        answer = user == "T"
        correct = answer == q["answer"]

        if q["answer"]:
            stats["true_total"] += 1
            if correct: stats["true_correct"] += 1
        else:
            stats["false_total"] += 1
            if correct: stats["false_correct"] += 1

        stats["played"] += 1
        if correct:
            stats["won"] += 1
            streak += 1
            if streak > best_streak:
                best_streak = streak
                stats["best_streak"] = best_streak
            if mode["replenish"] and max_lives < 999:
                lives = min(lives + 1, max_lives + 2)
        else:
            stats["lost"] += 1
            streak = 0
            if max_lives < 999: lives -= 1

        draw_question(q, lives, max_lives, mode, streak, stats["played"], answer, class_name)
        input("\n  [Enter] next…")

        if lives <= 0:
            show_analysis(stats, mode)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q": break
            except (EOFError, KeyboardInterrupt): break
            lives = mode["lives"]; streak = best_streak = idx = 0
            stats = {"played":0,"won":0,"lost":0,"best_streak":0,
                     "true_correct":0,"true_total":0,"false_correct":0,"false_total":0}
            random.shuffle(questions)


if __name__ == "__main__":
    main()
