from __future__ import annotations
import csv
import random
import os
import sys
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
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 3,   "replenish": False},
}

LABELS = ["A", "B", "C", "D"]


def clear():
    os.system("clear")


def truncate(s: str, n: int = 120) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def load_entries(picks: List[str]) -> List[Dict]:
    entries, seen = [], set()
    for p in picks:
        path = CLASS_FILES[p][1]
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                kw   = row.get("Keyword", "").strip()
                defn = row.get("Definition", "").strip()
                ch   = row.get("Chapter", "").strip()
                cls  = row.get("Class", "").strip()
                if kw and defn and kw.lower() not in seen:
                    seen.add(kw.lower())
                    entries.append({"keyword": kw, "definition": defn,
                                    "chapter": ch, "class": cls})
    return entries


def make_options(correct: str, pool: List[str]) -> tuple:
    distractors = [x for x in pool if x.lower() != correct.lower()]
    chosen = random.sample(distractors, min(3, len(distractors)))
    opts = chosen + [correct]
    random.shuffle(opts)
    return opts, opts.index(correct)


def build_questions(entries: List[Dict]) -> List[Dict]:
    keywords    = [e["keyword"]    for e in entries]
    definitions = [e["definition"] for e in entries]
    qs = []
    for e in entries:
        kw, defn, ch = e["keyword"], e["definition"], e["chapter"]

        # Direction 1: definition shown → pick the term
        opts, ci = make_options(kw, keywords)
        if len(opts) == 4:
            qs.append({
                "type": "def→term",
                "q": truncate(defn),
                "prompt": "Which term matches this definition?",
                "opts": opts, "correct": ci,
                "chapter": ch, "keyword": kw, "definition": defn,
            })

        # Direction 2: term shown → pick the definition
        opts2, ci2 = make_options(defn, definitions)
        if len(opts2) == 4:
            qs.append({
                "type": "term→def",
                "q": kw,
                "prompt": "Which definition matches this term?",
                "opts": [truncate(o, 90) for o in opts2],
                "correct": ci2,
                "chapter": ch, "keyword": kw, "definition": defn,
            })

    random.shuffle(qs)
    return qs


def select_class() -> tuple:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]📖  TERMINOLOGY[/bold cyan]"),
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
    console.print("  Examples:  [cyan]3[/cyan]  or  [cyan]3 4[/cyan]  or  [cyan]1,2,3,4,5[/cyan]")
    console.print()
    while True:
        raw = Prompt.ask("  Your choice", default="3").replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_FILES]
        if picks:
            break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    names = "+".join(CLASS_FILES[p][0] for p in picks)
    return names, picks



def select_mode() -> Dict:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]📖  TERMINOLOGY[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 each on correct\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · 3 hints · no replenishment",
        title="[bold]Select Mode[/bold]",
        box=box.ROUNDED,
    ))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1", "2", "3"], default="2")
    return MODES[choice]


def render_lives(lives: int, max_lives: int, color: str) -> str:
    if max_lives >= 999:
        return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"


def render_hints(hints: int, max_hints: int, color: str) -> str:
    if max_hints >= 999:
        return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def draw_question(q: Dict, lives: int, hints: int, mode: Dict,
                  streak: int, max_lives: int, max_hints: int,
                  q_num: int, eliminated: List[int],
                  answered: Optional[str], class_name: str):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    direction_icon = "📝" if q["type"] == "def→term" else "🔍"

    console.print(Panel(
        Align.center(
            f"[bold cyan]📖  TERMINOLOGY[/bold cyan]  [dim]·  {class_name}[/dim]"
            f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"
        ),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print(
        f"  {render_lives(lives, max_lives, color)}    "
        f"{render_hints(hints, max_hints, color)}    "
        f"[dim]Q{q_num}[/dim]"
    )
    console.print()

    console.print(Panel(
        f"\n  [dim]{q['prompt']}[/dim]\n\n"
        f"  [bold]{direction_icon}  {q['q']}[/bold]\n",
        title=f"[dim]{q['chapter']}[/dim]",
        box=box.ROUNDED, style="white",
    ))
    console.print()

    for i, (label, opt) in enumerate(zip(LABELS, q["opts"])):
        if i in eliminated:
            console.print(f"  [dim strike]{label}.  {opt}[/dim strike]")
        elif answered is not None:
            if i == q["correct"]:
                console.print(f"  [bold green]{label}.  {opt}  ✓[/bold green]")
            elif label == answered:
                console.print(f"  [bold red]{label}.  {opt}  ✗[/bold red]")
            else:
                console.print(f"  [dim]{label}.  {opt}[/dim]")
        else:
            console.print(f"  [bold]{label}.[/bold]  {opt}")

    console.print()


def show_analysis(stats: Dict, mode: Dict):
    clear()
    color = mode["color"]
    total = stats["played"]
    won   = stats["won"]
    acc   = f"{won / total * 100:.0f}%" if total else "—"

    console.print(Panel(
        Align.center("[bold cyan]📊  TERMINOLOGY ANALYSIS[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=24)
    t.add_column(style="bold")
    t.add_row("Mode",            f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",       str(total))
    t.add_row("Correct",         f"[green]{won}[/green]")
    t.add_row("Wrong",           f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",        f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak",     f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",      str(stats["hints_used"]))

    by_dir = stats["by_direction"]
    if by_dir:
        t.add_section()
        for d, (c, tot) in by_dir.items():
            pct = f"{c/tot*100:.0f}%" if tot else "—"
            label = "Def → Term" if d == "def→term" else "Term → Def"
            t.add_row(f"  {label}", f"{c}/{tot}  [yellow]{pct}[/yellow]")

    console.print(Align.center(t))

    if stats["missed"]:
        console.print()
        lines = []
        for m in stats["missed"][-6:]:
            lines.append(
                f"  [red]✗[/red]  [bold]{m['keyword']}[/bold]\n"
                f"      [dim]{truncate(m['definition'], 80)}[/dim]"
            )
        console.print(Panel(
            "\n".join(lines),
            title="[dim]Missed (last 6)[/dim]",
            box=box.ROUNDED, style="dim",
        ))
    console.print()


def play_round(q: Dict, lives: int, hints: int, mode: Dict,
               streak: int, max_lives: int, max_hints: int,
               stats: Dict, class_name: str):
    eliminated: List[int] = []
    wrong_indices = [i for i in range(4) if i != q["correct"]]

    while True:
        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"] + 1, eliminated, None, class_name)

        hint_txt = "[dim]? = remove a wrong option[/dim]" if hints > 0 else "[dim](no hints)[/dim]"
        console.print(f"  [A/B/C/D]  {hint_txt}  [dim]q = quit[/dim]: ", end="")

        try:
            user = input().strip().upper()
        except (EOFError, KeyboardInterrupt):
            show_analysis(stats, mode)
            sys.exit()

        if user == "Q":
            show_analysis(stats, mode)
            sys.exit()

        if user == "?":
            if hints <= 0:
                console.print("  [red]No hints left![/red]")
                input("  [Enter]...")
                continue
            remaining = [i for i in wrong_indices if i not in eliminated]
            if not remaining:
                continue
            eliminated.append(random.choice(remaining))
            stats["hints_used"] += 1
            if max_hints < 999:
                hints -= 1
            continue

        if user not in LABELS:
            continue

        chosen_idx = LABELS.index(user)
        correct = chosen_idx == q["correct"]
        direction = q["type"]

        stats["by_direction"].setdefault(direction, [0, 0])
        stats["by_direction"][direction][1] += 1
        stats["played"] += 1

        if correct:
            stats["won"] += 1
            stats["by_direction"][direction][0] += 1
        else:
            stats["lost"] += 1
            stats["missed"].append({"keyword": q["keyword"], "definition": q["definition"]})
            if max_lives < 999:
                lives -= 1

        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"], eliminated, user, class_name)

        if correct:
            console.print(Align.center(Panel(
                "[bold green]✓  Correct![/bold green]",
                box=box.HEAVY, style="green", width=30,
            )))
        else:
            ans = q["opts"][q["correct"]]
            console.print(Align.center(Panel(
                f"[bold red]✗  Wrong![/bold red]\n[dim]{truncate(ans, 60)}[/dim]",
                box=box.HEAVY, style="red", width=66,
            )))

        input("\n  [Enter] next question...")
        return correct, lives, hints


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    entries = load_entries(picks)
    questions = build_questions(entries)

    console.print(f"[dim]{len(questions)} questions ready ({class_name}).[/dim]")

    lives       = mode["lives"]
    hints       = mode["hints"]
    max_lives   = mode["max_lives"]
    max_hints   = mode["max_hints"]
    streak      = 0
    best_streak = 0
    idx         = 0

    stats: Dict = {
        "played": 0, "won": 0, "lost": 0,
        "hints_used": 0, "best_streak": 0,
        "missed": [], "by_direction": {},
    }

    while True:
        if idx >= len(questions):
            random.shuffle(questions)
            idx = 0

        q = questions[idx]
        idx += 1

        correct, lives, hints = play_round(
            q, lives, hints, mode, streak, max_lives, max_hints, stats, class_name
        )

        if correct:
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
                console.print("  [dim]Enter to restart · q to quit[/dim]")
                try:
                    if input().strip().lower() == "q":
                        break
                except (EOFError, KeyboardInterrupt):
                    break
                lives       = mode["lives"]
                hints       = mode["hints"]
                streak      = 0
                best_streak = 0
                stats = {
                    "played": 0, "won": 0, "lost": 0,
                    "hints_used": 0, "best_streak": 0,
                    "missed": [], "by_direction": {},
                }
                random.shuffle(questions)
                idx = 0


if __name__ == "__main__":
    main()
