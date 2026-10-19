from __future__ import annotations
import csv, random, os, sys
from pathlib import Path
from typing import List, Dict, Set

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

GRID = 5          # 5×5
FREE = (2, 2)     # centre free square


def clear(): os.system("clear")

def truncate(s, n=100):
    return s if len(s) <= n else s[:n-1] + "…"


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


def make_card(entries) -> List[List[Dict]]:
    chosen = random.sample(entries, GRID * GRID)
    card = [chosen[i*GRID:(i+1)*GRID] for i in range(GRID)]
    return card


def check_bingo(marked: Set[tuple]) -> bool:
    # rows
    for r in range(GRID):
        if all((r, c) in marked for c in range(GRID)):
            return True
    # cols
    for c in range(GRID):
        if all((r, c) in marked for r in range(GRID)):
            return True
    # diagonals
    if all((i, i) in marked for i in range(GRID)):
        return True
    if all((i, GRID-1-i) in marked for i in range(GRID)):
        return True
    return False


def winning_lines(marked: Set[tuple]) -> Set[tuple]:
    """Return all cells that are part of a winning line."""
    winners = set()
    for r in range(GRID):
        if all((r,c) in marked for c in range(GRID)):
            for c in range(GRID): winners.add((r,c))
    for c in range(GRID):
        if all((r,c) in marked for r in range(GRID)):
            for r in range(GRID): winners.add((r,c))
    if all((i,i) in marked for i in range(GRID)):
        for i in range(GRID): winners.add((i,i))
    if all((i,GRID-1-i) in marked for i in range(GRID)):
        for i in range(GRID): winners.add((i,GRID-1-i))
    return winners


def draw_card(card, marked: Set[tuple]):
    win_cells = winning_lines(marked) if check_bingo(marked) else set()

    t = Table(box=box.SQUARE, show_header=True, header_style="bold cyan",
              padding=(0, 1))
    col_labels = ["①", "②", "③", "④", "⑤"]
    for lbl in col_labels:
        t.add_column(lbl, justify="center", width=18)

    for r in range(GRID):
        row_cells = []
        for c in range(GRID):
            entry = card[r][c]
            kw    = entry["keyword"]
            pos   = (r, c)
            short = kw if len(kw) <= 16 else kw[:15] + "…"

            if pos == FREE and (r, c) in marked:
                cell = "[bold green on dark_green] FREE ✓ [/bold green on dark_green]"
            elif pos in win_cells:
                cell = f"[bold black on yellow] {short} [/bold black on yellow]"
            elif pos in marked:
                cell = f"[bold green]✓ {short}[/bold green]"
            else:
                cell = f"[dim]{short}[/dim]"
            row_cells.append(cell)
        t.add_row(*row_cells)

    console.print(Align.center(t))


def draw_screen(card, marked, entry, lives, max_lives, streak, q_num,
                class_name, color, wrong_flash=""):
    clear()
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    lives_str = f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]" if max_lives < 999 \
                else f"[{color}]❤  ∞[/{color}]"

    console.print(Panel(
        Align.center(f"[bold cyan]🎱  BIO BINGO[/bold cyan]  [dim]· {class_name}[/dim]"
                     f"   {lives_str}    [dim]Q{q_num}[/dim]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()

    draw_card(card, marked)
    console.print()

    if entry:
        console.print(Panel(
            f"\n  [bold]{truncate(entry['definition'])}[/bold]\n",
            title="[dim]Find this term on your card and type it[/dim]",
            box=box.ROUNDED, style="white"))
    if wrong_flash:
        console.print(f"\n  [red]{wrong_flash}[/red]")
    console.print()


def show_result(card, marked, stats, won: bool):
    clear()
    win_cells = winning_lines(marked)

    t = Table(box=box.SQUARE, show_header=True, header_style="bold cyan", padding=(0,1))
    col_labels = ["①", "②", "③", "④", "⑤"]
    for lbl in col_labels:
        t.add_column(lbl, justify="center", width=18)
    for r in range(GRID):
        row_cells = []
        for c in range(GRID):
            kw    = card[r][c]["keyword"]
            short = kw if len(kw) <= 16 else kw[:15] + "…"
            pos   = (r, c)
            if pos in win_cells:
                row_cells.append(f"[bold black on yellow] {short} [/bold black on yellow]")
            elif pos in marked:
                row_cells.append(f"[bold green]✓ {short}[/bold green]")
            else:
                row_cells.append(f"[dim]{short}[/dim]")
        t.add_row(*row_cells)

    if won:
        console.print(Panel(Align.center("[bold yellow]🎉  B I N G O ![/bold yellow]"),
                            box=box.DOUBLE_EDGE, style="yellow"))
    else:
        console.print(Panel(Align.center("[bold red]Game Over[/bold red]"),
                            box=box.DOUBLE_EDGE, style="red"))
    console.print()
    console.print(Align.center(t))
    console.print()

    st = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    st.add_column(style="dim", width=20); st.add_column(style="bold")
    st.add_row("Cells Marked",   str(len(marked)))
    st.add_row("Correct",        f"[green]{stats['correct']}[/green]")
    st.add_row("Wrong",          f"[red]{stats['wrong']}[/red]")
    st.add_row("Best Streak",    f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    acc = f"{stats['correct']/(stats['correct']+stats['wrong'])*100:.0f}%" \
          if (stats['correct']+stats['wrong']) else "—"
    st.add_row("Accuracy",       f"[yellow]{acc}[/yellow]")
    console.print(Align.center(st))
    console.print()


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]🎱  BIO BINGO[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th\n\n[bold]  2.[/bold]  10th\n\n"
        "[bold]  3.[/bold]  11th\n\n[bold]  4.[/bold]  12th\n\n"
        "[bold]  5.[/bold]  [bold magenta]Advanced[/bold magenta]",
        title="[bold]Select Class(es)[/bold]", box=box.ROUNDED))
    console.print()
    console.print("  [dim]Need at least 25 keywords — mixing classes gives richer cards[/dim]")
    console.print()
    while True:
        raw = Prompt.ask("  Your choice", default="3").replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_FILES]
        if picks: break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    return "+".join(CLASS_FILES[p][0] for p in picks), picks


def select_lives():
    clear()
    console.print(Panel(Align.center("[bold cyan]🎱  BIO BINGO[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Chill[/bold green]    — Unlimited wrong guesses\n\n"
        "[bold yellow]  2.  Normal[/bold yellow]  — 5 wrong guesses allowed\n\n"
        "[bold red]  3.  Hardcore[/bold red]  — 3 wrong guesses allowed",
        title="[bold]Select Difficulty[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1","2","3"], default="2")
    lives_map = {"1": 999, "2": 5, "3": 3}
    colors    = {"1": "green", "2": "yellow", "3": "red"}
    return lives_map[choice], colors[choice]


def main():
    class_name, picks = select_class()
    max_lives, color  = select_lives()

    console.print("[dim]Loading…[/dim]")
    entries = load_entries(picks)
    if len(entries) < GRID * GRID:
        console.print(f"[red]Need at least 25 keywords. Got {len(entries)}. Add more classes.[/red]")
        return

    while True:
        card    = make_card(entries)
        # build lookup: keyword.lower() → (row, col)
        kw_map  = {card[r][c]["keyword"].lower(): (r,c)
                   for r in range(GRID) for c in range(GRID)}

        marked: Set[tuple] = set()
        marked.add(FREE)   # centre is always free

        # Shuffle remaining entries as the question queue (not on card)
        card_kws = {card[r][c]["keyword"].lower() for r in range(GRID) for c in range(GRID)}
        queue = [e for e in entries if e["keyword"].lower() not in card_kws]
        # Also include card entries as questions (definition shown, find on card)
        card_entries = [card[r][c] for r in range(GRID) for c in range(GRID)
                        if (r,c) != FREE]
        random.shuffle(card_entries)

        lives  = max_lives
        streak = best_streak = 0
        stats  = {"correct": 0, "wrong": 0, "best_streak": 0}
        wrong_flash = ""

        for entry in card_entries:
            while True:
                draw_screen(card, marked, entry, lives, max_lives, streak,
                            stats["correct"]+stats["wrong"]+1, class_name, color, wrong_flash)
                wrong_flash = ""

                console.print("  Type the term: ", end="")
                try:
                    user = input().strip()
                except (EOFError, KeyboardInterrupt):
                    show_result(card, marked, stats, False); sys.exit()

                if not user: continue
                if user.lower() == "q":
                    show_result(card, marked, stats, False); sys.exit()

                pos        = kw_map.get(user.lower())
                correct_kw = entry["keyword"].lower()

                if user.lower() == correct_kw:
                    if pos and pos not in marked:
                        marked.add(pos)
                    stats["correct"] += 1
                    streak += 1
                    if streak > best_streak:
                        best_streak = streak
                        stats["best_streak"] = best_streak
                    break
                else:
                    stats["wrong"] += 1
                    streak = 0
                    if max_lives < 999: lives -= 1
                    if pos and pos not in marked:
                        wrong_flash = f"'{user}' is on the card but not the right answer for this definition."
                    else:
                        wrong_flash = f"'{user}' is not the right term. Try again."
                    if lives <= 0:
                        draw_screen(card, marked, entry, lives, max_lives, streak,
                                    stats["correct"]+stats["wrong"], class_name, color)
                        break

            if lives <= 0:
                break

        # Win = all 25 cells marked (24 answers + free centre)
        won = len(marked) == GRID * GRID
        show_result(card, marked, stats, won)
        console.print("  [dim]Enter = new card · q = quit[/dim]")
        try:
            if input().strip().lower() == "q": break
        except (EOFError, KeyboardInterrupt): break


if __name__ == "__main__":
    main()
