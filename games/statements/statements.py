from __future__ import annotations
import csv, random, os, sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from rich import box

console = Console()

STATEMENTS_DIR = Path(__file__).parent.parent / "truefalse" / "statements"

CLASS_PREFIXES = {
    "1": ("8th",  ["8th-"]),
    "2": ("9th",  ["9th-"]),
    "3": ("10th", ["10th-"]),
    "4": ("11th", ["11th-"]),
    "5": ("12th", ["12th-"]),
}

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 5,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "replenish": False},
}


def clear(): os.system("clear")

def truncate(s: str, n: int = 105) -> str:
    return s if len(s) <= n else s[:n-1] + "…"

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"


def load_questions(picks):
    questions = []
    for p in picks:
        prefixes = CLASS_PREFIXES[p][1]
        for tsv in sorted(STATEMENTS_DIR.glob("*.tsv")):
            if not any(tsv.name.startswith(pfx) for pfx in prefixes):
                continue
            with open(tsv, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    chapter  = row.get("Chapter", "").strip()
                    true_stmt = row.get("True Statement", "").strip()
                    reason   = row.get("Reason", "").strip()
                    if not true_stmt:
                        continue
                    false_variants = [
                        v.strip() for k, v in row.items()
                        if k.startswith("False") and v.strip()
                    ]
                    # TRUE question
                    questions.append({
                        "chapter": chapter,
                        "statement": true_stmt,
                        "answer": True,
                        "true_stmt": true_stmt,
                        "reason": reason,
                    })
                    # FALSE questions (one per variant)
                    for fv in false_variants:
                        questions.append({
                            "chapter": chapter,
                            "statement": fv,
                            "answer": False,
                            "true_stmt": true_stmt,
                            "reason": reason,
                        })
    random.shuffle(questions)
    return questions


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]✅  TRUE OR FALSE — STATEMENTS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  8th\n\n[bold]  2.[/bold]  9th\n\n"
        "[bold]  3.[/bold]  10th\n\n[bold]  4.[/bold]  11th\n\n"
        "[bold]  5.[/bold]  12th",
        title="[bold]Select Class(es)[/bold]", box=box.ROUNDED))
    console.print()
    while True:
        raw = Prompt.ask("  Your choice (e.g. 4 or 4 5)", default="4").replace(",", " ")
        picks = [t.strip() for t in raw.split() if t.strip() in CLASS_PREFIXES]
        if picks: break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    label = "+".join(CLASS_PREFIXES[p][0] for p in picks)
    return label, picks


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]✅  TRUE OR FALSE — STATEMENTS[/bold cyan]"),
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
        Align.center(
            f"[bold cyan]✅  STATEMENTS T/F[/bold cyan]  [dim]· {class_name}[/dim]"
            f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"
        ), box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    console.print(Panel(
        f"\n  [italic]{truncate(q['statement'])}[/italic]\n",
        title=f"[dim]{q['chapter']}[/dim]  —  [dim]Is this statement True or False?[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    if answered is None:
        console.print("  [bold green]T[/bold green] = True    [bold red]F[/bold red] = False    [dim]q = quit[/dim]")
    elif answered == q["answer"]:
        console.print(Align.center(Panel("[bold green]✓  Correct![/bold green]",
                                         box=box.HEAVY, style="green", width=30)))
        if q["answer"] and q.get("reason"):
            console.print()
            console.print(Panel(f"[dim]{truncate(q['reason'], 100)}[/dim]",
                                title="[dim]Why it's true[/dim]", box=box.SIMPLE, style="dim"))
    else:
        correct_word = "TRUE" if q["answer"] else "FALSE"
        console.print(Align.center(Panel(
            f"[bold red]✗  Wrong!  It was {correct_word}[/bold red]",
            box=box.HEAVY, style="red", width=42)))
        if not q["answer"]:
            console.print()
            console.print(Panel(
                f"[dim]{truncate(q['true_stmt'], 100)}[/dim]",
                title="[dim]Correct statement[/dim]", box=box.SIMPLE, style="dim"))
        elif q.get("reason"):
            console.print()
            console.print(Panel(f"[dim]{truncate(q['reason'], 100)}[/dim]",
                                title="[dim]Why it's true[/dim]", box=box.SIMPLE, style="dim"))
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  STATEMENTS T/F  ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",           f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",      str(total))
    t.add_row("Correct",        f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",          f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",       f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak",    f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("True Correct",   f"[green]{stats['true_correct']}[/green][dim]/{stats['true_total']}[/dim]")
    t.add_row("False Correct",  f"[green]{stats['false_correct']}[/green][dim]/{stats['false_total']}[/dim]")
    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]

    console.print("[dim]Loading…[/dim]")
    questions = load_questions(picks)
    if not questions:
        console.print("[red]No questions found for selected class(es).[/red]")
        sys.exit(1)
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
