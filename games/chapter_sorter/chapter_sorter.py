from __future__ import annotations
import csv, random, os, sys, re
from pathlib import Path
from typing import List, Dict, Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich import box

console = Console()

DATA_DIR = Path(__file__).parent.parent / "hangman" / "data"

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


def clear(): os.system("clear")

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"

def ch_num(chapter_str: str) -> int:
    """Extract chapter number from 'Ch3 Plant Kingdom' → 3."""
    m = re.search(r'\d+', chapter_str)
    return int(m.group()) if m else 0

def ch_short(chapter_str: str) -> str:
    """'Ch3 Plant Kingdom' → 'Plant Kingdom'"""
    return re.sub(r'^Ch\d+\s*', '', chapter_str).strip()


def load_class(pick: str):
    """Returns entries list, chapter_map {num: full_str}, keyword→set of valid ch nums."""
    cls_name, path = CLASS_FILES[pick]
    entries: List[Dict] = []
    chapter_map: Dict[int, str] = {}       # num → full chapter string
    kw_chapters: Dict[str, Set[int]] = {}  # keyword_lower → valid chapter numbers

    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            kw   = row.get("Keyword", "").strip()
            defn = row.get("Definition", "").strip()
            ch   = row.get("Chapter", "").strip()
            if not kw or not ch:
                continue
            num = ch_num(ch)
            chapter_map[num] = ch
            kw_lower = kw.lower()
            kw_chapters.setdefault(kw_lower, set()).add(num)
            # keep one entry per keyword (first seen); store all valid nums separately
            if not any(e["keyword"].lower() == kw_lower for e in entries):
                entries.append({"keyword": kw, "definition": defn, "chapter": ch,
                                "ch_num": num})

    # Update each entry's valid_chapters from the full kw_chapters index
    for e in entries:
        e["valid_chapters"] = kw_chapters[e["keyword"].lower()]

    return cls_name, entries, chapter_map


def select_class() -> tuple:
    clear()
    console.print(Panel(Align.center("[bold cyan]📚  CHAPTER SORTER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  9th\n\n[bold]  2.[/bold]  10th\n\n"
        "[bold]  3.[/bold]  11th\n\n[bold]  4.[/bold]  12th",
        title="[bold]Select Class[/bold]", box=box.ROUNDED))
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Enter [1/2/3/4]: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "3"
        if raw in ("1", "2", "3", "4"): return raw
        console.print("  [red]Enter 1, 2, 3, or 4[/red]")


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]📚  CHAPTER SORTER[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints  [dim](? = show definition)[/dim]\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · no hints",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Enter [1/2/3]: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "2"
        if raw in MODES: return MODES[raw]
        console.print("  [red]Enter 1, 2, or 3[/red]")


def draw_screen(entry, chapter_map, lives, hints, mode, streak, q_num, show_def, answered=None):
    clear()
    color     = mode["color"]
    max_lives = mode["lives"]
    max_hints = mode["hints"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""

    console.print(Panel(
        Align.center(f"[bold cyan]📚  CHAPTER SORTER[/bold cyan]"
                     f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    "
                  f"{render_hints(hints, max_hints, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    body = f"\n  [bold]{entry['keyword']}[/bold]\n"
    if show_def and entry["definition"]:
        body += f"\n  [dim italic]{entry['definition']}[/dim italic]\n"

    console.print(Panel(body,
        title="[dim]Which chapter is this term from?[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    # Chapter list — two columns
    nums = sorted(chapter_map.keys())
    mid  = (len(nums) + 1) // 2
    left_lines  = [f"  [dim]{n:>2}[/dim]  {ch_short(chapter_map[n])}" for n in nums[:mid]]
    right_lines = [f"  [dim]{n:>2}[/dim]  {ch_short(chapter_map[n])}" for n in nums[mid:]]
    # pad to same length
    while len(right_lines) < len(left_lines):
        right_lines.append("")
    ch_body = "\n".join(
        f"{l:<45}{r}" for l, r in zip(left_lines, right_lines)
    )
    console.print(Panel(ch_body, title="[dim]Chapters[/dim]", box=box.SIMPLE, style="dim"))
    console.print()

    if answered is not None:
        valid = entry["valid_chapters"]
        valid_str = "  or  ".join(
            f"Ch{n} — {ch_short(chapter_map[n])}" for n in sorted(valid)
        )
        if answered in valid:
            console.print(Align.center(Panel(
                f"[bold green]✓  Ch{answered} — {ch_short(chapter_map.get(answered, ''))}[/bold green]",
                box=box.HEAVY, style="green", width=52)))
        else:
            console.print(Align.center(Panel(
                f"[bold red]✗  Answer: {valid_str}[/bold red]",
                box=box.HEAVY, style="red", width=60)))
    else:
        hint_txt = "[dim]? = show definition[/dim]" if mode["hints"] > 0 else ""
        console.print(f"  Type chapter number{hint_txt and '  ·  ' + hint_txt}   [dim]q = quit[/dim]")
    console.print()


def show_analysis(stats, mode, chapter_map):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  CHAPTER SORTER  ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column(style="dim", width=26); t.add_column(style="bold")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",   str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",  str(stats["hints_used"]))

    if stats["by_chapter"]:
        t.add_section()
        for num in sorted(stats["by_chapter"]):
            c, tot = stats["by_chapter"][num]
            pct = f"{c/tot*100:.0f}%"
            name = ch_short(chapter_map.get(num, f"Ch{num}"))
            t.add_row(f"  Ch{num} {name[:18]}", f"{c}/{tot}  [yellow]{pct}[/yellow]")

    console.print(Align.center(t))
    console.print()


THRESHOLDS = {"Easy": 0.70, "Medium": 0.80, "Hard": 0.90}


def select_target(mode):
    clear()
    threshold_pct = int(THRESHOLDS[mode["name"]] * 100)
    console.print(Panel(Align.center("[bold cyan]🎯  SET YOUR TARGET[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        f"  [bold {mode['color']}]{mode['name']}[/bold {mode['color']}] mode · "
        f"win by answering [bold]{threshold_pct}%[/bold] or more correctly",
        title="[bold]What's your target today?[/bold]", box=box.ROUNDED))
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Number of terms: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "20"
        if raw.isdigit() and int(raw) > 0: return int(raw)
        console.print("  [red]Enter a positive number (e.g. 10, 20, 50)[/red]")


def show_target_result(stats, mode, target):
    clear()
    threshold = THRESHOLDS[mode["name"]]
    accuracy  = stats["won"] / stats["played"] if stats["played"] else 0
    won_flag  = accuracy >= threshold
    color     = "green" if won_flag else "red"
    icon      = "🏆" if won_flag else "💔"
    acc_pct   = int(accuracy * 100)
    req_pct   = int(threshold * 100)
    console.print(Panel(
        Align.center(f"[bold {color}]{icon}  {'Target Achieved!' if won_flag else 'Target Missed'}[/bold {color}]"),
        box=box.DOUBLE_EDGE, style=color))
    console.print()
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=20); t.add_column(style="bold")
    t.add_row("Target",      str(target))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]  [dim]/ {stats['played']}[/dim]")
    t.add_row("Accuracy",    f"[{color}]{acc_pct}%[/{color}]")
    t.add_row("Required",    f"[dim]{req_pct}%[/dim]")
    if stats.get("best_streak", 0):
        t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    console.print(Align.center(t))
    console.print()


def main():
    while True:
        pick = select_class()
        if pick is None: return
        result = select_mode()
        if result is None: continue
        mode = result
        target = select_target(mode)
        if target is None: continue
        break
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    cls_name, entries, chapter_map = load_class(pick)
    random.shuffle(entries)
    console.print(f"[dim]{len(entries)} terms loaded · {len(chapter_map)} chapters · {cls_name}[/dim]")

    lives     = mode["lives"]
    hints     = mode["hints"]
    max_lives = mode["max_lives"]
    max_hints = mode["max_hints"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0,"hints_used":0,"by_chapter":{}}

    while True:
        if idx >= len(entries):
            random.shuffle(entries); idx = 0

        entry    = entries[idx]; idx += 1
        show_def = mode["name"] == "Easy"

        while True:
            draw_screen(entry, chapter_map, lives, hints, mode,
                        streak, stats["played"]+1, show_def)
            console.print("  Chapter number: ", end="")
            try:
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                show_analysis(stats, mode, chapter_map); sys.exit()

            if not raw: continue

            if raw.lower() == "q":
                show_analysis(stats, mode, chapter_map); sys.exit()

            if raw == "?":
                if hints <= 0:
                    console.print("  [red]No hints![/red]"); input("  [Enter]..."); continue
                show_def = True
                stats["hints_used"] += 1
                if max_hints < 999: hints -= 1
                continue

            if not raw.isdigit():
                console.print("  [red]Type a chapter number[/red]")
                input("  [Enter]..."); continue

            answered = int(raw)
            if answered not in chapter_map:
                console.print(f"  [red]Ch{answered} doesn't exist in {cls_name}[/red]")
                input("  [Enter]..."); continue

            valid    = entry["valid_chapters"]
            correct  = answered in valid
            ch_stats = stats["by_chapter"].setdefault(entry["ch_num"], [0, 0])
            ch_stats[1] += 1
            stats["played"] += 1

            if correct:
                stats["won"] += 1
                ch_stats[0] += 1
                streak += 1
                if streak > best_streak:
                    best_streak = streak
                    stats["best_streak"] = best_streak
                if mode["replenish"]:
                    if max_lives < 999: lives = min(lives+1, max_lives+2)
                    if max_hints < 999: hints = min(hints+1, max_hints+2)
            else:
                stats["lost"] += 1
                streak = 0
                if max_lives < 999: lives -= 1

            draw_screen(entry, chapter_map, lives, hints, mode,
                        streak, stats["played"], True, answered=answered)
            input("  [Enter] next…")
            break

        if stats["played"] >= target:
            show_target_result(stats, mode, target)
            console.print("  [dim]Enter = new game · q = quit[/dim]")
            try:
                if input().strip().lower() == "q": return
            except (EOFError, KeyboardInterrupt): return
            lives = mode["lives"]; hints = mode["hints"]
            streak = best_streak = idx = 0
            stats = {"played":0,"won":0,"lost":0,"best_streak":0,"hints_used":0,"by_chapter":{}}
            random.shuffle(entries); continue

        if lives <= 0:
            show_analysis(stats, mode, chapter_map)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q": break
            except (EOFError, KeyboardInterrupt): break
            lives = mode["lives"]; hints = mode["hints"]
            streak = best_streak = idx = 0
            stats = {"played":0,"won":0,"lost":0,"best_streak":0,"hints_used":0,"by_chapter":{}}
            random.shuffle(entries)


if __name__ == "__main__":
    main()
