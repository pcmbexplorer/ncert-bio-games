from __future__ import annotations
import csv
import random
import os
import sys
import select
import time
from pathlib import Path
from typing import Set, List, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
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
    "1": {"name": "Easy",   "color": "green"},
    "2": {"name": "Medium", "color": "yellow"},
    "3": {"name": "Hard",   "color": "red"},
}

MEDIUM_WARMUP   = 15   # user words before Medium timer activates
MEDIUM_BASE     = 15   # Medium per-turn seconds at activation (+1 per word after)
HARD_TOTAL      = 300  # Hard total game time in seconds (5 minutes)
HARD_BONUS      = 15   # seconds added to total clock per valid user word


def clear():
    os.system("clear")


def fmt_time(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60}:{s % 60:02d}"


def input_timed(prompt: str, timeout: float) -> Optional[str]:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    ready, _, _ = select.select([sys.stdin], [], [], max(0.1, timeout))
    if ready:
        return sys.stdin.readline().rstrip("\n")
    return None


def load_words(picks: List[str]) -> Dict[str, Dict]:
    words: Dict[str, Dict] = {}
    for p in picks:
        with open(CLASS_FILES[p][1], encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                if kw and defn and kw.replace(" ", "").isalpha():
                    key = kw.lower()
                    if key not in words:
                        words[key] = {"word": kw, "definition": defn, "chapter": ch}
    return words


def words_by_letter(words: Dict[str, Dict]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for key in words:
        index.setdefault(key[0], []).append(key)
    return index


def select_class() -> tuple:
    clear()
    console.print(Panel(Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th       —    361 keywords\n\n"
        "[bold]  2.[/bold]  10th      —    213 keywords\n\n"
        "[bold]  3.[/bold]  11th      —  1,169 keywords\n\n"
        "[bold]  4.[/bold]  12th      —    658 keywords\n\n"
        "[bold]  5.[/bold]  [bold magenta]Advanced[/bold magenta]  —  2,312 keywords  [dim](Wikipedia + Biology Dictionary)[/dim]",
        title="[bold]Select Class(es)  —  type numbers separated by space/comma[/bold]",
        box=box.ROUNDED))
    console.print()
    console.print("  Examples:  [cyan]3[/cyan]  or  [cyan]3 4[/cyan]  or  [cyan]1,2,3,4[/cyan]")
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Your choice: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "3"
        raw = raw.replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_FILES]
        if picks: break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    return "+".join(CLASS_FILES[p][0] for p in picks), picks


def select_mode() -> dict:
    clear()
    console.print(Panel(Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]\n"
        "      [dim]No timer — play at your own pace[/dim]\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]\n"
        "      [dim]First 15 words free · then 15s per turn · +1s for each word earned[/dim]\n\n"
        "[bold red]  3.  Hard[/bold red]\n"
        "      [dim]5-minute total clock · +15s added for each word you give[/dim]",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED, padding=(1, 2)))
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Enter [1/2/3]: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "2"
        if raw in MODES: return MODES[raw]
        console.print("  [red]Enter 1, 2, or 3[/red]")


def draw_chain(chain: List[str], words: Dict[str, Dict], current_letter: str,
               streak: int, mode: dict, timer_str: str = "",
               show_def: Optional[str] = None):
    clear()
    color = mode["color"]
    console.print(Panel(
        Align.center(
            f"[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"
            + (f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else "")
            + (f"   [{color}]{mode['name']}[/{color}]")
            + (f"   {timer_str}" if timer_str else "")
        ),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()

    if chain:
        recent = chain[-6:]
        lines = []
        for i, w in enumerate(recent):
            entry = words.get(w.lower(), {})
            who = "[bold cyan]🖥 [/bold cyan]" if i % 2 == (len(chain) - len(recent)) % 2 else "[bold green]👤[/bold green]"
            lines.append(f"  {who}  [bold]{w}[/bold]  [dim]— {entry.get('chapter', '')}[/dim]")
        console.print(Panel("\n".join(lines),
                            title=f"[dim]Chain ({len(chain)} words)[/dim]",
                            box=box.ROUNDED))
    console.print()

    if show_def:
        entry = words.get(show_def.lower(), {})
        console.print(Panel(f"[italic]{entry.get('definition', '')}[/italic]",
                            title=f"[dim]💡 {show_def}[/dim]",
                            box=box.SIMPLE, style="dim"))
        console.print()

    console.print(f"  Next word must start with  [bold yellow]{current_letter.upper()}[/bold yellow]")
    console.print()
    console.print("  [dim]? = show last word definition   q = quit[/dim]")
    console.print()


def computer_pick(letter: str, used: Set[str], index: Dict[str, List[str]]) -> Optional[str]:
    candidates = [k for k in index.get(letter, []) if k not in used]
    return random.choice(candidates) if candidates else None


def show_analysis(streak: int, chain: List[str], reason: str, elapsed: float = 0):
    clear()
    console.print(Panel(Align.center("[bold cyan]📊  GAME OVER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22)
    t.add_column(style="bold")
    t.add_row("Chain Length", str(len(chain)))
    t.add_row("Best Streak",  f"[yellow]🔥 {streak}[/yellow]")
    t.add_row("Reason",       f"[red]{reason}[/red]")
    if chain:
        t.add_row("Last Word", chain[-1])
    if elapsed:
        t.add_row("Time Played", fmt_time(elapsed))
    console.print(Align.center(t))
    console.print()


def play_round(words, index, mode, class_name):
    """Play one round. Returns (None, user_count) for round end, (False, user_count) to quit."""
    chain: List[str] = []
    used:  Set[str]  = set()
    streak       = 0
    user_count   = 0
    show_def_word: Optional[str] = None
    game_start   = time.time()
    hard_bonus   = 0   # accumulated bonus seconds from valid words

    # Computer goes first
    first_key  = random.choice(list(words.keys()))
    first_word = words[first_key]["word"]
    chain.append(first_word)
    used.add(first_key)
    current_letter = first_key[-1]

    mode_name = mode["name"]

    while True:
        # ── compute this turn's timeout and display string ──────────────
        elapsed       = time.time() - game_start
        total_left    = HARD_TOTAL - elapsed if mode_name == "Hard" else None

        if mode_name == "Easy":
            turn_timeout = None
            timer_str    = ""

        elif mode_name == "Medium":
            if user_count < MEDIUM_WARMUP:
                turn_timeout = None
                timer_str    = f"[dim]warmup {user_count}/{MEDIUM_WARMUP}[/dim]"
            else:
                turn_timeout = float(MEDIUM_BASE + (user_count - MEDIUM_WARMUP))
                timer_str    = f"[bold red]⏱ {int(turn_timeout)}s[/bold red]"

        else:  # Hard
            total_left = HARD_TOTAL + hard_bonus - elapsed
            if total_left <= 0:
                draw_chain(chain, words, current_letter, streak, mode,
                           timer_str="[bold red]🕐 0:00[/bold red]")
                console.print("\n  [bold red]⏰ TOTAL TIME UP![/bold red]")
                input("  [Enter]...")
                show_analysis(streak, chain, "Total clock expired", elapsed)
                return None, user_count
            turn_timeout = total_left
            timer_str    = f"[bold red]🕐 {fmt_time(total_left)}[/bold red]  [dim]+{HARD_BONUS}s/word[/dim]"

        # ── draw and get input ──────────────────────────────────────────
        draw_chain(chain, words, current_letter, streak, mode,
                   timer_str=timer_str, show_def=show_def_word)
        show_def_word = None

        try:
            if turn_timeout is not None:
                user_input = input_timed("  Your word:  ", turn_timeout)
                if user_input is None:
                    elapsed = time.time() - game_start
                    draw_chain(chain, words, current_letter, streak, mode)
                    if mode_name == "Hard":
                        console.print("\n  [bold red]⏰ TOTAL TIME UP![/bold red]")
                        show_analysis(streak, chain, "Total clock expired", elapsed)
                    else:
                        console.print(f"\n  [bold red]⏰ TIME'S UP!  You had {int(turn_timeout)}s.[/bold red]")
                        show_analysis(streak, chain, f"Timed out ({int(turn_timeout)}s)", elapsed)
                    input("  [Enter]...")
                    return None, user_count
                user_input = user_input.strip()
            else:
                console.print("  Your word: ", end="")
                user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            show_analysis(streak, chain, "Quit", time.time() - game_start)
            return False, user_count

        if not user_input:
            continue
        if user_input.lower() == "q":
            show_analysis(streak, chain, "Quit", time.time() - game_start)
            return False, user_count
        if user_input == "?":
            show_def_word = chain[-1]
            continue

        # ── validate ────────────────────────────────────────────────────
        user_key = user_input.lower()

        if user_key[0] != current_letter:
            draw_chain(chain, words, current_letter, streak, mode, timer_str=timer_str)
            console.print(f"\n  [red]Must start with [bold]{current_letter.upper()}[/bold]![/red]  "
                          f"[dim]'{user_input}' starts with '{user_input[0].upper()}'[/dim]")
            input("  [Enter] to continue...")
            continue

        if user_key not in words:
            draw_chain(chain, words, current_letter, streak, mode, timer_str=timer_str)
            console.print(f"\n  [red]'{user_input}' is not in the keyword list![/red]")
            input("  [Enter] to continue...")
            continue

        if user_key in used:
            draw_chain(chain, words, current_letter, streak, mode, timer_str=timer_str)
            console.print(f"\n  [red]'{user_input}' was already used![/red]")
            input("  [Enter] to continue...")
            continue

        # ── valid user word ─────────────────────────────────────────────
        chain.append(words[user_key]["word"])
        used.add(user_key)
        streak += 1
        user_count += 1
        next_letter = user_key[-1]
        if mode_name == "Hard":
            hard_bonus += HARD_BONUS

        # ── computer's turn ─────────────────────────────────────────────
        comp_key = computer_pick(next_letter, used, index)
        if comp_key is None:
            draw_chain(chain, words, next_letter, streak, mode)
            console.print(f"\n  [bold green]🎉 Computer has no word starting with "
                          f"[bold]{next_letter.upper()}[/bold]! You win![/bold green]")
            input("  [Enter]...")
            show_analysis(streak, chain, "Computer stuck!", time.time() - game_start)
            return None, user_count

        chain.append(words[comp_key]["word"])
        used.add(comp_key)
        current_letter = comp_key[-1]


def select_target(mode):
    clear()
    console.print(Panel(Align.center("[bold cyan]🎯  SET YOUR TARGET[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        f"  [bold {mode['color']}]{mode['name']}[/bold {mode['color']}] mode\n\n"
        f"  Win by chaining your target number of words in total across rounds",
        title="[bold]What's your target today?[/bold]", box=box.ROUNDED))
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Words to chain: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "20"
        if raw.isdigit() and int(raw) > 0: return int(raw)
        console.print("  [red]Enter a positive number (e.g. 10, 20, 50)[/red]")


def show_target_result_atlas(session_words, target):
    clear()
    won   = session_words >= target
    color = "green" if won else "red"
    icon  = "🏆" if won else "💔"
    console.print(Panel(
        Align.center(f"[bold {color}]{icon}  {'Target Achieved!' if won else 'Target Missed'}[/bold {color}]"),
        box=box.DOUBLE_EDGE, style=color))
    console.print()
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=20); t.add_column(style="bold")
    t.add_row("Target",        str(target))
    t.add_row("Words Chained", f"[{'green' if won else 'red'}]{session_words}[/{'green' if won else 'red'}]")
    console.print(Align.center(t))
    console.print()


def main():
    while True:
        result = select_class()
        if result is None: return
        class_name, picks = result
        result = select_mode()
        if result is None: continue
        mode = result
        target = select_target(mode)
        if target is None: continue
        break
    words = load_words(picks)
    index = words_by_letter(words)

    clear()
    console.print(Panel(Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "  Chain biology keywords — each word must start with\n"
        "  the [bold yellow]last letter[/bold yellow] of the previous word.\n\n"
        "  No repeating words. First one stuck [bold red]loses[/bold red]!\n\n"
        f"  [dim]Loaded [bold]{len(words)}[/bold] keywords from {class_name}[/dim]",
        title="[bold]How to Play[/bold]", box=box.ROUNDED, padding=(1, 2)))
    console.print()
    try:
        input("  Press Enter to start...")
    except (EOFError, KeyboardInterrupt):
        return

    session_words = 0
    while True:
        status, round_words = play_round(words, index, mode, class_name)
        session_words += round_words
        if status is False:   # user quit
            break
        # round ended (timeout / computer stuck / win)
        if session_words >= target:
            show_target_result_atlas(session_words, target)
            console.print("  [dim]Enter = new game · q = quit[/dim]")
            try:
                if input().strip().lower() == "q": break
            except (EOFError, KeyboardInterrupt): break
            session_words = 0
            random.shuffle(list(words.keys()))
            continue
        clear()
        console.print(Panel(Align.center("[bold cyan]🗺  BIOLOGY ATLAS[/bold cyan]"),
                            box=box.DOUBLE_EDGE, style="cyan"))
        console.print(f"  [dim]Words chained so far: [bold]{session_words}[/bold] / {target}[/dim]")
        console.print()
        try:
            again = input("  Play again? [y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break
        if again not in ("y", ""):
            break

    clear()
    console.print(Align.center("\n[dim]Thanks for playing Biology Atlas! 🗺[/dim]\n"))


if __name__ == "__main__":
    main()
