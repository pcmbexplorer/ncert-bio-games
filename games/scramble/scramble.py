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
    "1": ("9th",      DATA_DIR / "keywords-glossary-9th.tsv"),
    "2": ("10th",     DATA_DIR / "keywords-glossary-10th.tsv"),
    "3": ("11th",     DATA_DIR / "keywords-glossary-11th.tsv"),
    "4": ("12th",     DATA_DIR / "keywords-glossary-12th.tsv"),
    "5": ("Advanced", DATA_DIR / "keywords-glossary-advanced.tsv"),
}

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 0,   "replenish": False},
}


def clear(): os.system("clear")

def truncate(s, n=100):
    return s if len(s) <= n else s[:n-1] + "…"

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def scramble_word(word: str) -> str:
    """Scramble each word's letters; guarantee result differs from original."""
    parts = word.split()
    for _ in range(100):
        shuffled = []
        for p in parts:
            letters = list(p)
            random.shuffle(letters)
            shuffled.append("".join(letters))
        result = " ".join(shuffled)
        if result.lower() != word.lower():
            return result
    # fallback: reverse
    return " ".join(p[::-1] for p in parts)


def load_entries(picks):
    entries, seen = [], set()
    for p in picks:
        with open(CLASS_FILES[p][1], encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                # only purely alphabetic words (spaces allowed for multi-word)
                if kw and defn and kw.replace(" ", "").isalpha() and kw.lower() not in seen:
                    seen.add(kw.lower())
                    entries.append({"keyword": kw, "definition": defn, "chapter": ch})
    return entries


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]🔀  WORD SCRAMBLE[/bold cyan]"),
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
    console.print(Panel(Align.center("[bold cyan]🔀  WORD SCRAMBLE[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints (? = reveal first letter)\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · no hints",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1","2","3"], default="2")
    return MODES[choice]


def draw_screen(entry, scrambled, lives, hints, mode, streak, q_num,
                class_name, hint_letters, show_def, answered=None, correct_word=None):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    max_lives = mode["lives"]; max_hints = mode["hints"]

    console.print(Panel(
        Align.center(f"[bold cyan]🔀  WORD SCRAMBLE[/bold cyan]  [dim]· {class_name}[/dim]"
                     f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    "
                  f"{render_hints(hints, max_hints, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    # Build hint display: revealed letters + blanks
    word = entry["keyword"]
    if hint_letters:
        hint_str = ""
        revealed = set(range(hint_letters))
        for wi, part in enumerate(word.split()):
            if wi > 0: hint_str += "  "
            for ci, ch in enumerate(part):
                pos = sum(len(p)+1 for p in word.split()[:wi]) + ci
                if pos in revealed:
                    hint_str += f"[bold yellow]{ch.upper()}[/bold yellow] "
                else:
                    hint_str += "_ "
        hint_line = f"\n  [dim]Letters revealed:[/dim]  {hint_str}\n"
    else:
        hint_line = ""

    scramble_display = "  ".join(
        f"[bold white]{ch.upper()}[/bold white]" if ch != " " else "  "
        for ch in scrambled
    )

    body = f"\n  [dim]Unscramble this biology term:[/dim]\n\n"
    body += f"  {scramble_display}\n"
    body += f"\n  [dim]({len(word.replace(' ',''))} letters"
    if " " in word: body += f" · {len(word.split())} words"
    body += ")[/dim]\n"
    if hint_line: body += hint_line
    if show_def:
        body += f"\n  [dim italic]{truncate(entry['definition'])}[/dim italic]\n"

    console.print(Panel(body, title=f"[dim]{entry['chapter']}[/dim]",
                        box=box.ROUNDED, style="white"))
    console.print()

    if answered is not None:
        if answered:
            console.print(Align.center(Panel(
                f"[bold green]✓  {correct_word.upper()}[/bold green]",
                box=box.HEAVY, style="green", width=40)))
        else:
            console.print(Align.center(Panel(
                f"[bold red]✗  Answer: {correct_word.upper()}[/bold red]\n"
                f"[dim]{truncate(entry['definition'], 60)}[/dim]",
                box=box.HEAVY, style="red", width=66)))
    else:
        hint_prompt = "[dim]? = reveal next letter[/dim]" if mode["hints"] > 0 else ""
        console.print(f"  {hint_prompt}   [dim]q = quit[/dim]")
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  SCRAMBLE ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Words Played", str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",  str(stats["hints_used"]))
    console.print(Align.center(t))

    if stats["missed"]:
        console.print()
        console.print(Panel(
            "\n".join(f"  [red]✗[/red]  [bold]{w}[/bold]" for w in stats["missed"][-8:]),
            title="[dim]Missed Words[/dim]", box=box.ROUNDED, style="dim"))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    entries = load_entries(picks)
    random.shuffle(entries)
    console.print(f"[dim]{len(entries)} words loaded.[/dim]")

    lives = mode["lives"]; hints = mode["hints"]
    max_lives = mode["max_lives"]; max_hints = mode["max_hints"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0,"hints_used":0,"missed":[]}

    while True:
        if idx >= len(entries):
            random.shuffle(entries); idx = 0

        entry = entries[idx]; idx += 1
        scrambled = scramble_word(entry["keyword"])
        hint_letters = 0
        show_def = mode["name"] == "Easy"

        while True:
            draw_screen(entry, scrambled, lives, hints, mode, streak,
                        stats["played"]+1, class_name, hint_letters, show_def)
            console.print("  Your answer: ", end="")
            try:
                user = input().strip()
            except (EOFError, KeyboardInterrupt):
                show_analysis(stats, mode); sys.exit()

            if not user: continue

            if user.lower() == "q":
                show_analysis(stats, mode); sys.exit()

            if user == "?":
                if hints <= 0:
                    console.print("  [red]No hints left![/red]"); input("  [Enter]..."); continue
                hint_letters = min(hint_letters + 1, len(entry["keyword"]))
                show_def = True
                stats["hints_used"] += 1
                if max_hints < 999: hints -= 1
                continue

            correct = user.lower() == entry["keyword"].lower()
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
                stats["missed"].append(entry["keyword"])
                if max_lives < 999: lives -= 1

            draw_screen(entry, scrambled, lives, hints, mode, streak,
                        stats["played"], class_name, hint_letters, True,
                        answered=correct, correct_word=entry["keyword"])
            input("  [Enter] next word...")
            break

        if lives <= 0:
            show_analysis(stats, mode)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q": break
            except (EOFError, KeyboardInterrupt): break
            lives = mode["lives"]; hints = mode["hints"]
            streak = best_streak = idx = 0
            stats = {"played":0,"won":0,"lost":0,"best_streak":0,"hints_used":0,"missed":[]}
            random.shuffle(entries)


if __name__ == "__main__":
    main()
