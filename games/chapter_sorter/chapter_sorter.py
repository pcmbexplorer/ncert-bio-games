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

CLASS_FILES = {
    "9th":  DATA_DIR / "keywords-glossary-9th.tsv",
    "10th": DATA_DIR / "keywords-glossary-10th.tsv",
    "11th": DATA_DIR / "keywords-glossary-11th.tsv",
    "12th": DATA_DIR / "keywords-glossary-12th.tsv",
}

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 0,   "replenish": False},
}

VALID_INPUT = {"9", "10", "11", "12", "9th", "10th", "11th", "12th"}

def normalise(s: str) -> str:
    s = s.strip().lower().replace("th", "")
    return s + "th" if s.isdigit() else ""


def clear(): os.system("clear")

def truncate(s, n=100):
    return s if len(s) <= n else s[:n-1] + "…"

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def load_entries() -> List[Dict]:
    entries, seen = [], set()
    for cls, path in CLASS_FILES.items():
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                if kw and kw.lower() not in seen:
                    seen.add(kw.lower())
                    entries.append({"keyword": kw, "definition": defn,
                                    "chapter": ch, "class": cls})
    return entries


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]📚  CLASS SORTER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints  [dim](? = show definition)[/dim]\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · no hints",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1","2","3"], default="2")
    return MODES[choice]


def draw_screen(entry, lives, hints, mode, streak, q_num,
                show_def, answered=None):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    max_lives = mode["lives"]; max_hints = mode["hints"]

    console.print(Panel(
        Align.center(f"[bold cyan]📚  CLASS SORTER[/bold cyan]"
                     f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    "
                  f"{render_hints(hints, max_hints, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    body = f"\n  [bold]{entry['keyword']}[/bold]\n"
    if show_def and entry["definition"]:
        body += f"\n  [dim italic]{truncate(entry['definition'])}[/dim italic]\n"
        body += f"  [dim]{entry['chapter']}[/dim]\n"

    console.print(Panel(body,
        title="[dim]Which class does this term belong to?[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    if answered is not None:
        correct_cls = entry["class"]
        if answered == correct_cls:
            console.print(Align.center(Panel(
                f"[bold green]✓  {correct_cls}[/bold green]",
                box=box.HEAVY, style="green", width=30)))
        else:
            console.print(Align.center(Panel(
                f"[bold red]✗  Answer: {correct_cls}[/bold red]\n"
                f"[dim]{entry['chapter']}[/dim]",
                box=box.HEAVY, style="red", width=50)))
    else:
        hint_txt = "[dim]? = show definition[/dim]" if mode["hints"] > 0 else ""
        console.print(f"  Type class:  [bold]9[/bold]  [bold]10[/bold]  [bold]11[/bold]  [bold]12[/bold]"
                      f"   {hint_txt}   [dim]q = quit[/dim]")
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  CLASS SORTER  ANALYSIS[/bold cyan]"),
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

    if stats["by_class"]:
        t.add_section()
        for cls in ["9th", "10th", "11th", "12th"]:
            c, tot = stats["by_class"].get(cls, (0, 0))
            if tot:
                pct = f"{c/tot*100:.0f}%"
                t.add_row(f"  {cls}", f"{c}/{tot}  [yellow]{pct}[/yellow]")

    console.print(Align.center(t))
    console.print()


def main():
    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    entries = load_entries()
    random.shuffle(entries)
    console.print(f"[dim]{len(entries)} terms loaded across 9th–12th.[/dim]")

    lives = mode["lives"]; hints = mode["hints"]
    max_lives = mode["max_lives"]; max_hints = mode["max_hints"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0,
             "hints_used":0,"by_class":{}}

    while True:
        if idx >= len(entries):
            random.shuffle(entries); idx = 0

        entry = entries[idx]; idx += 1
        show_def = mode["name"] == "Easy"

        while True:
            draw_screen(entry, lives, hints, mode, streak,
                        stats["played"]+1, show_def)
            console.print("  Your answer: ", end="")
            try:
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                show_analysis(stats, mode); sys.exit()

            if not raw: continue

            if raw.lower() == "q":
                show_analysis(stats, mode); sys.exit()

            if raw == "?":
                if hints <= 0:
                    console.print("  [red]No hints![/red]"); input("  [Enter]..."); continue
                show_def = True
                stats["hints_used"] += 1
                if max_hints < 999: hints -= 1
                continue

            answer = normalise(raw)
            if not answer:
                console.print("  [red]Enter 9, 10, 11, or 12[/red]")
                input("  [Enter]...")
                continue

            correct_cls = entry["class"]
            correct = answer == correct_cls

            cls_stats = stats["by_class"].setdefault(correct_cls, [0, 0])
            cls_stats[1] += 1
            stats["played"] += 1

            if correct:
                stats["won"] += 1
                cls_stats[0] += 1
                streak += 1
                if streak > best_streak:
                    best_streak = streak
                    stats["best_streak"] = best_streak
                if mode["replenish"]:
                    lives += 1; hints += 1
            else:
                stats["lost"] += 1
                streak = 0
                if max_lives < 999: lives -= 1

            draw_screen(entry, lives, hints, mode, streak,
                        stats["played"], True, answered=answer)
            input("  [Enter] next…")
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
                     "hints_used":0,"by_class":{}}
            random.shuffle(entries)


if __name__ == "__main__":
    main()
