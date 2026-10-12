from __future__ import annotations
import csv
import random
import os
import sys
from pathlib import Path
from typing import Set, List, Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.prompt import Prompt
from rich import box

console = Console()

DATA_DIR = Path(__file__).parent / "data"

CLASS_FILES = {
    "1": ("9th",      DATA_DIR / "keywords-glossary-9th.tsv"),
    "2": ("10th",     DATA_DIR / "keywords-glossary-10th.tsv"),
    "3": ("11th",     DATA_DIR / "keywords-glossary-11th.tsv"),
    "4": ("12th",     DATA_DIR / "keywords-glossary-12th.tsv"),
    "5": ("Advanced", DATA_DIR / "keywords-glossary-advanced.tsv"),
}

HANGMAN_ART = [
    ["       ", "       ", "       ", "       ", "       ", "       "],
    ["  ___  ", " |   | ", " |     ", " |     ", " |     ", "_|_    "],
    ["  ___  ", " |   | ", " |   O ", " |     ", " |     ", "_|_    "],
    ["  ___  ", " |   | ", " |   O ", " |   | ", " |     ", "_|_    "],
]

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 3,   "replenish": False},
}


def load_words_from(path: Path) -> List[Dict]:
    words = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            kw = row.get("Keyword", "").strip()
            defn = row.get("Definition", "").strip()
            chapter = row.get("Chapter", "").strip()
            if kw and defn and len(kw) >= 3 and kw.replace(" ", "").isalpha():
                words.append({"word": kw, "definition": defn, "chapter": chapter})
    return words


def select_class() -> tuple:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]🧬  BIO HANGMAN[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th       —  361 keywords\n\n"
        "[bold]  2.[/bold]  10th      —  213 keywords\n\n"
        "[bold]  3.[/bold]  11th      — 1,169 keywords\n\n"
        "[bold]  4.[/bold]  12th      —   658 keywords\n\n"
        "[bold]  5.[/bold]  [bold magenta]Advanced[/bold magenta]  —   344 keywords  [dim](Wikipedia Biology Glossary)[/dim]",
        title="[bold]Select Class(es)  —  type numbers separated by space/comma[/bold]",
        box=box.ROUNDED,
    ))
    console.print()
    console.print("  Examples:  [cyan]3[/cyan]  or  [cyan]3 4[/cyan]  or  [cyan]1,2,3,4[/cyan]")
    console.print()

    while True:
        raw = Prompt.ask("  Your choice", default="3").replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_FILES]
        if picks:
            break
        console.print("  [red]Enter one or more of: 1  2  3  4[/red]")

    names = "+".join(CLASS_FILES[p][0] for p in picks)
    return names, picks


def load_words(class_name: str, picks: List[str]) -> List[Dict]:
    words = []
    seen = set()
    for p in picks:
        path = CLASS_FILES[p][1]
        for w in load_words_from(path):
            key = w["word"].lower()
            if key not in seen:
                seen.add(key)
                words.append(w)
    return words


def clear():
    os.system("clear")


def render_word(word: str, guessed: Set[str]) -> str:
    parts = []
    for ch in word:
        if ch == " ":
            parts.append("  ")
        elif ch.lower() in guessed:
            parts.append(f"[bold green]{ch.upper()}[/bold green]")
        else:
            parts.append("[bold white]_[/bold white]")
    return "  ".join(parts)


def render_lives(lives: int, max_lives: int, color: str) -> str:
    if max_lives >= 999:
        return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"


def render_hints(hints: int, max_hints: int, color: str) -> str:
    if max_hints >= 999:
        return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def render_art(wrong_count: int) -> str:
    idx = min(wrong_count, len(HANGMAN_ART) - 1)
    return "\n".join(HANGMAN_ART[idx])


def select_mode() -> Dict:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]🧬  BIO HANGMAN[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 each on correct word\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · 3 hints · no replenishment",
        title="[bold]Select Mode[/bold]",
        box=box.ROUNDED,
    ))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1", "2", "3"], default="2")
    return MODES[choice]


def draw_screen(entry: Dict, word: str, guessed: Set[str], wrong: Set[str],
                lives: int, hints: int, mode: Dict, streak: int,
                hint_used: bool, max_lives: int, max_hints: int,
                class_name: str = ""):
    clear()
    color = mode["color"]

    streak_badge = f"  [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    class_badge = f" · [bold]{class_name}[/bold]" if class_name else ""
    console.print(Panel(
        Align.center(f"🧬  BIO HANGMAN{class_badge}   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))

    console.print(f"  {render_lives(lives, max_lives, color)}    {render_hints(hints, max_hints, color)}")
    console.print()

    wrong_str = "  ".join(f"[bold red]{c.upper()}[/bold red]" for c in sorted(wrong)) or "[dim]—[/dim]"
    art_panel = Panel(render_art(len(wrong)), box=box.SIMPLE, style="dim cyan", width=16)
    info_panel = Panel(
        f"\n  [bold]Wrong:[/bold]  {wrong_str}\n\n"
        f"  [dim]Letters guessed: {len(guessed)}[/dim]",
        box=box.SIMPLE, width=44,
    )
    console.print(Columns([art_panel, info_panel]))

    console.print()
    console.print(Align.center(render_word(word, guessed)))
    console.print(Align.center(f"[dim]({len(word)} letters)[/dim]"))
    console.print()

    if hint_used:
        console.print(Panel(
            f"[italic]{entry['definition']}[/italic]",
            title="[dim]💡 Hint[/dim]",
            box=box.SIMPLE, style="dim",
        ))

    hint_prompt = "[dim]? = hint[/dim]" if not hint_used else "[dim](hint active)[/dim]"
    console.print(f"  {hint_prompt}   [dim]q = quit[/dim]")


def show_analysis(stats: Dict, mode: Dict):
    clear()
    color = mode["color"]
    total = stats["played"]
    won = stats["won"]
    lost = stats["lost"]
    acc = f"{won / total * 100:.0f}%" if total else "—"

    console.print(Panel(
        Align.center("[bold cyan]📊  GAME ANALYSIS[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22)
    t.add_column(style="bold")

    t.add_row("Mode", f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Words Played", str(total))
    t.add_row("Correct", f"[green]{won}[/green]")
    t.add_row("Wrong", f"[red]{lost}[/red]")
    t.add_row("Accuracy", f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used", str(stats["hints_used"]))
    t.add_row("Word Guesses", str(stats["word_guesses"]))
    t.add_row("Avg Wrong/Word", f"{stats['total_wrong'] / total:.1f}" if total else "—")

    console.print(Align.center(t))

    if stats["missed_words"]:
        console.print()
        console.print(Panel(
            "\n".join(
                f"  [red]✗[/red]  [bold]{w['word']}[/bold]  [dim]— {w['chapter']}[/dim]"
                for w in stats["missed_words"][-10:]
            ),
            title="[dim]Words Missed (last 10)[/dim]",
            box=box.ROUNDED, style="dim",
        ))

    console.print()


def play_round(entry: Dict, lives: int, hints: int, mode: Dict, streak: int,
               max_lives: int, max_hints: int, stats: Dict, class_name: str = ""):
    word = entry["word"].lower()
    unique = {c for c in word if c.isalpha()}

    guessed: Set[str] = set()
    wrong: Set[str] = set()
    hint_used = False
    round_wrong = 0

    guessed.add(random.choice(list(unique)))

    while True:
        draw_screen(entry, word, guessed, wrong, lives, hints, mode, streak,
                    hint_used, max_lives, max_hints, class_name)

        if unique <= guessed:
            console.print()
            console.print(Align.center(Panel(
                f"[bold green]✓  {entry['word'].upper()}[/bold green]",
                box=box.HEAVY, style="green", width=40,
            )))
            console.print(Align.center(f"[dim]{entry['chapter']}[/dim]"))
            stats["played"] += 1
            stats["won"] += 1
            stats["total_wrong"] += round_wrong
            input("\n  [Enter] next word...")
            return True, lives, hints

        if lives <= 0:
            console.print()
            console.print(Align.center(Panel(
                f"[bold red]✗  {entry['word'].upper()}[/bold red]\n"
                f"[dim]{entry['definition']}[/dim]",
                box=box.HEAVY, style="red", width=52,
            )))
            stats["played"] += 1
            stats["lost"] += 1
            stats["total_wrong"] += round_wrong
            stats["missed_words"].append({"word": entry["word"], "chapter": entry["chapter"]})
            input("\n  [Enter] next word...")
            return False, lives, hints

        console.print(f"\n  Guess (letter, full word, or q to quit): ", end="")
        try:
            user = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            show_analysis(stats, mode)
            sys.exit()

        if not user:
            continue

        if user == "q":
            show_analysis(stats, mode)
            sys.exit()

        # ── Hint ────────────────────────────────────────────────────────────
        if user == "?":
            if hint_used:
                continue
            if hints <= 0:
                console.print("  [red]No hints left![/red]")
                input("  [Enter]...")
                continue
            hint_used = True
            stats["hints_used"] += 1
            if max_hints < 999:
                hints -= 1
            continue

        # ── Full word guess ──────────────────────────────────────────────────
        if len(user) > 1:
            stats["word_guesses"] += 1
            if user.replace(" ", "") == word.replace(" ", ""):
                guessed = unique  # reveal all
            else:
                console.print(f"  [red]Wrong word![/red]")
                round_wrong += 1
                if max_lives < 999:
                    lives -= 1
                input("  [Enter]...")
            continue

        # ── Single letter ────────────────────────────────────────────────────
        letter = user[0]
        if not letter.isalpha():
            continue

        if letter in guessed or letter in wrong:
            console.print(f"  [yellow]Already guessed '{letter.upper()}'[/yellow]")
            input("  [Enter]...")
            continue

        if letter in unique:
            guessed.add(letter)
        else:
            wrong.add(letter)
            round_wrong += 1
            if max_lives < 999:
                lives -= 1


def main():
    class_name, picks = select_class()
    words = load_words(class_name, picks)
    random.shuffle(words)

    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    lives = mode["lives"]
    hints = mode["hints"]
    max_lives = mode["max_lives"]
    max_hints = mode["max_hints"]
    streak = 0
    best_streak = 0
    idx = 0

    stats: Dict = {
        "played": 0, "won": 0, "lost": 0,
        "total_wrong": 0, "hints_used": 0,
        "word_guesses": 0, "best_streak": 0,
        "missed_words": [],
    }

    while True:
        entry = words[idx % len(words)]
        idx += 1

        won, lives, hints = play_round(
            entry, lives, hints, mode, streak, max_lives, max_hints, stats, class_name
        )

        if won:
            streak += 1
            if streak > best_streak:
                best_streak = streak
                stats["best_streak"] = best_streak
            if mode["replenish"]:
                lives += 1
                hints += 1
        else:
            streak = 0
            if lives <= 0:
                show_analysis(stats, mode)
                console.print("  [dim]Press Enter to restart or type q to quit[/dim]")
                try:
                    if input().strip().lower() == "q":
                        break
                except (EOFError, KeyboardInterrupt):
                    break
                lives = mode["lives"]
                hints = mode["hints"]
                stats = {
                    "played": 0, "won": 0, "lost": 0,
                    "total_wrong": 0, "hints_used": 0,
                    "word_guesses": 0, "best_streak": 0,
                    "missed_words": [],
                }
                streak = 0
                best_streak = 0
                random.shuffle(words)
                idx = 0


if __name__ == "__main__":
    main()
