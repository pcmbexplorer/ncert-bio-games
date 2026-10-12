from __future__ import annotations
import csv
import random
import os
import sys
from pathlib import Path
from typing import Set, List, Dict, Optional

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


def clear():
    os.system("clear")


def load_words(picks: List[str]) -> Dict[str, Dict]:
    words: Dict[str, Dict] = {}
    for p in picks:
        path = CLASS_FILES[p][1]
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                chapter = row.get("Chapter", "").strip()
                if kw and defn and kw.replace(" ", "").isalpha():
                    key = kw.lower()
                    if key not in words:
                        words[key] = {"word": kw, "definition": defn, "chapter": chapter}
    return words


def words_by_letter(words: Dict[str, Dict]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for key in words:
        letter = key[0]
        index.setdefault(letter, []).append(key)
    return index


def select_class() -> tuple:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th       —    361 keywords\n\n"
        "[bold]  2.[/bold]  10th      —    213 keywords\n\n"
        "[bold]  3.[/bold]  11th      —  1,169 keywords\n\n"
        "[bold]  4.[/bold]  12th      —    658 keywords\n\n"
        "[bold]  5.[/bold]  [bold magenta]Advanced[/bold magenta]  —  2,312 keywords  [dim](Wikipedia + Biology Dictionary)[/dim]",
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


def draw_chain(chain: List[str], words: Dict[str, Dict], current_letter: str,
               streak: int, show_def: Optional[str] = None):
    clear()
    console.print(Panel(
        Align.center(
            f"[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"
            + (f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else "")
        ),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()

    if chain:
        recent = chain[-6:]
        lines = []
        for i, w in enumerate(recent):
            entry = words.get(w.lower(), {})
            who = "[bold cyan]🖥 [/bold cyan]" if i % 2 == (len(chain) - len(recent)) % 2 else "[bold green]👤[/bold green]"
            lines.append(f"  {who}  [bold]{w}[/bold]  [dim]— {entry.get('chapter', '')}[/dim]")
        console.print(Panel(
            "\n".join(lines),
            title=f"[dim]Chain ({len(chain)} words)[/dim]",
            box=box.ROUNDED,
        ))
    console.print()

    if show_def:
        entry = words.get(show_def.lower(), {})
        console.print(Panel(
            f"[italic]{entry.get('definition', '')}[/italic]",
            title=f"[dim]💡 {show_def}[/dim]",
            box=box.SIMPLE, style="dim",
        ))
        console.print()

    console.print(
        f"  Next word must start with  [bold yellow]{current_letter.upper()}[/bold yellow]"
    )
    console.print()
    console.print("  [dim]? = show last word definition   q = quit[/dim]")
    console.print()


def computer_pick(letter: str, used: Set[str], index: Dict[str, List[str]]) -> Optional[str]:
    candidates = [k for k in index.get(letter, []) if k not in used]
    if not candidates:
        return None
    return random.choice(candidates)


def show_analysis(streak: int, chain: List[str], reason: str):
    clear()
    console.print(Panel(
        Align.center("[bold cyan]📊  GAME OVER[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22)
    t.add_column(style="bold")
    t.add_row("Chain Length", str(len(chain)))
    t.add_row("Best Streak", f"[yellow]🔥 {streak}[/yellow]")
    t.add_row("Reason", f"[red]{reason}[/red]")
    if chain:
        t.add_row("Last Word", chain[-1])
    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    words = load_words(picks)
    index = words_by_letter(words)

    clear()
    console.print(Panel(
        Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "  Chain biology keywords — each word must start with\n"
        "  the [bold yellow]last letter[/bold yellow] of the previous word.\n\n"
        "  No repeating words. First one stuck [bold red]loses[/bold red]!\n\n"
        f"  [dim]Loaded [bold]{len(words)}[/bold] keywords from {class_name}[/dim]",
        title="[bold]How to Play[/bold]",
        box=box.ROUNDED, padding=(1, 2),
    ))
    console.print()
    try:
        input("  Press Enter to start...")
    except (EOFError, KeyboardInterrupt):
        return

    while True:
        chain: List[str] = []
        used: Set[str] = set()
        streak = 0
        show_def_word: Optional[str] = None

        # Computer goes first
        first_key = random.choice(list(words.keys()))
        first_word = words[first_key]["word"]
        chain.append(first_word)
        used.add(first_key)
        current_letter = first_key[-1]

        while True:
            draw_chain(chain, words, current_letter, streak, show_def_word)
            show_def_word = None

            console.print(f"  Your word: ", end="")
            try:
                user_input = input().strip()
            except (EOFError, KeyboardInterrupt):
                show_analysis(streak, chain, "Quit")
                return

            if not user_input:
                continue

            if user_input.lower() == "q":
                show_analysis(streak, chain, "Quit")
                return

            if user_input == "?":
                show_def_word = chain[-1]
                continue

            # Validate
            user_key = user_input.lower()

            if user_key[0] != current_letter:
                draw_chain(chain, words, current_letter, streak)
                console.print(
                    f"\n  [red]Must start with [bold]{current_letter.upper()}[/bold]![/red]  "
                    f"[dim]'{user_input}' starts with '{user_input[0].upper()}'[/dim]"
                )
                input("  [Enter] to continue...")
                continue

            if user_key not in words:
                draw_chain(chain, words, current_letter, streak)
                console.print(f"\n  [red]'{user_input}' is not in the keyword list![/red]")
                input("  [Enter] to continue...")
                continue

            if user_key in used:
                draw_chain(chain, words, current_letter, streak)
                console.print(f"\n  [red]'{user_input}' was already used![/red]")
                input("  [Enter] to continue...")
                continue

            # Valid user word
            chain.append(words[user_key]["word"])
            used.add(user_key)
            streak += 1
            next_letter = user_key[-1]

            # Computer's turn
            comp_key = computer_pick(next_letter, used, index)
            if comp_key is None:
                draw_chain(chain, words, next_letter, streak)
                console.print(
                    f"\n  [bold green]🎉 Computer has no word starting with "
                    f"[bold]{next_letter.upper()}[/bold]! You win![/bold green]"
                )
                input("  [Enter]...")
                show_analysis(streak, chain, "Computer stuck!")
                break

            comp_word = words[comp_key]["word"]
            chain.append(comp_word)
            used.add(comp_key)
            current_letter = comp_key[-1]

        # Play again?
        clear()
        console.print(Panel(
            Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
            box=box.DOUBLE_EDGE, style="cyan",
        ))
        console.print()
        try:
            again = Prompt.ask("  Play again?", choices=["y", "n"], default="y")
        except (EOFError, KeyboardInterrupt):
            break
        if again != "y":
            break

    clear()
    console.print(Align.center("\n[dim]Thanks for playing Biology Atlas! 🗺[/dim]\n"))


if __name__ == "__main__":
    main()
