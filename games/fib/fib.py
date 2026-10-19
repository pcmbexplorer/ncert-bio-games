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
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 3,   "replenish": False},
}


def clear(): os.system("clear")

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"

def extract_answer(true_stmt: str, fib: str) -> str:
    parts = fib.split("___", 1)
    if len(parts) != 2:
        return ""
    prefix, suffix = parts
    if suffix:
        return true_stmt[len(prefix): len(true_stmt) - len(suffix)]
    return true_stmt[len(prefix):]

def hint_text(answer: str) -> str:
    if not answer:
        return ""
    return answer[0] + " _ " * (len(answer) - 1) + f"[dim]({len(answer)} chars)[/dim]"


def load_questions(picks):
    questions = []
    for p in picks:
        prefixes = CLASS_PREFIXES[p][1]
        for tsv in sorted(STATEMENTS_DIR.glob("*.tsv")):
            if not any(tsv.name.startswith(pfx) for pfx in prefixes):
                continue
            with open(tsv, encoding="utf-8") as f:
                for row in csv.DictReader(f, delimiter="\t"):
                    chapter   = row.get("Chapter", "").strip()
                    true_stmt = row.get("True Statement", "").strip()
                    if not true_stmt:
                        continue
                    for k, v in row.items():
                        if not k.startswith("FIB"):
                            continue
                        fib = v.strip()
                        if not fib:
                            continue
                        answer = extract_answer(true_stmt, fib)
                        if not answer:
                            continue
                        questions.append({
                            "chapter":   chapter,
                            "fib":       fib,
                            "answer":    answer,
                            "true_stmt": true_stmt,
                        })
    random.shuffle(questions)
    return questions


def select_class():
    clear()
    console.print(Panel(Align.center("[bold cyan]📝  FILL IN THE BLANKS[/bold cyan]"),
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
        if picks:
            break
        console.print("  [red]Enter one or more of: 1  2  3  4  5[/red]")
    label = "+".join(CLASS_PREFIXES[p][0] for p in picks)
    return label, picks


def select_mode():
    clear()
    console.print(Panel(Align.center("[bold cyan]📝  FILL IN THE BLANKS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints · hint shown automatically\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 in both on correct  [dim](? = hint)[/dim]\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · 3 hints · no replenishment  [dim](? = hint)[/dim]",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1", "2", "3"], default="2")
    return MODES[choice]


def draw_question(q, lives, max_lives, hints, max_hints, mode, streak, q_num,
                  answered, class_name, show_hint=False):
    clear()
    color = mode["color"]
    streak_badge = f"   [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    console.print(Panel(
        Align.center(
            f"[bold cyan]📝  FILL IN THE BLANKS[/bold cyan]  [dim]· {class_name}[/dim]"
            f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"
        ), box=box.DOUBLE_EDGE, style="cyan"))
    console.print(f"  {render_lives(lives, max_lives, color)}    "
                  f"{render_hints(hints, max_hints, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    fib_display = q["fib"].replace("___", "[bold yellow]___[/bold yellow]")
    console.print(Panel(
        f"\n  {fib_display}\n",
        title=f"[dim]{q['chapter']}[/dim]  —  [dim]Fill in the blank[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    if answered is None:
        if show_hint or max_hints >= 999:
            console.print(f"  [dim]Hint: [/dim][cyan]{hint_text(q['answer'])}[/cyan]")
            console.print()
        hint_prompt = "" if max_hints >= 999 else "  [dim]? = hint[/dim]"
        console.print(f"  [dim]Type your answer{hint_prompt}   q = quit[/dim]")
    elif answered:
        console.print(Align.center(Panel("[bold green]✓  Correct![/bold green]",
                                         box=box.HEAVY, style="green", width=30)))
        console.print()
        console.print(Panel(f"[dim]{q['true_stmt']}[/dim]",
                            title="[dim]Full statement[/dim]", box=box.SIMPLE, style="dim"))
    else:
        console.print(Align.center(Panel(
            f"[bold red]✗  Wrong!  Answer: [white]{q['answer']}[/white][/bold red]",
            box=box.HEAVY, style="red", width=50)))
        console.print()
        console.print(Panel(f"[dim]{q['true_stmt']}[/dim]",
                            title="[dim]Full statement[/dim]", box=box.SIMPLE, style="dim"))
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  FILL IN THE BLANKS  ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",   str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",  str(stats["hints_used"]))
    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    console.print("[dim]Loading…[/dim]")
    questions = load_questions(picks)
    if not questions:
        console.print("[red]No questions found for selected class(es).[/red]")
        sys.exit(1)
    console.print(f"[dim]{len(questions)} questions ready.[/dim]")

    lives     = mode["lives"];  max_lives = mode["max_lives"]
    hints     = mode["hints"];  max_hints = mode["max_hints"]
    streak = best_streak = idx = 0
    stats = {"played": 0, "won": 0, "lost": 0, "best_streak": 0, "hints_used": 0}

    while True:
        if idx >= len(questions):
            random.shuffle(questions); idx = 0

        q = questions[idx]; idx += 1
        show_hint = False

        while True:
            draw_question(q, lives, max_lives, hints, max_hints, mode,
                          streak, stats["played"] + 1, None, class_name, show_hint)
            console.print("  Answer: ", end="")
            try:
                user = input().strip()
            except (EOFError, KeyboardInterrupt):
                show_analysis(stats, mode); sys.exit()

            if user.lower() == "q":
                show_analysis(stats, mode); sys.exit()

            if user == "?" and max_hints < 999:
                if hints <= 0:
                    console.print("  [red]No hints left![/red]")
                    input("  [Enter]...")
                else:
                    show_hint = True
                    hints -= 1
                    stats["hints_used"] += 1
                continue

            break

        correct = user.strip().lower() == q["answer"].strip().lower()

        stats["played"] += 1
        if correct:
            stats["won"] += 1
            streak += 1
            if streak > best_streak:
                best_streak = streak
                stats["best_streak"] = best_streak
            if mode["replenish"]:
                if max_lives < 999: lives = min(lives + 1, max_lives + 2)
                if max_hints < 999: hints = min(hints + 1, max_hints + 2)
        else:
            stats["lost"] += 1
            streak = 0
            if max_lives < 999:
                lives -= 1

        draw_question(q, lives, max_lives, hints, max_hints, mode,
                      streak, stats["played"], correct, class_name)
        input("\n  [Enter] next…")

        if lives <= 0:
            show_analysis(stats, mode)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q":
                    break
            except (EOFError, KeyboardInterrupt):
                break
            lives = mode["lives"]; hints = mode["hints"]
            streak = best_streak = idx = 0
            stats = {"played": 0, "won": 0, "lost": 0, "best_streak": 0, "hints_used": 0}
            random.shuffle(questions)


if __name__ == "__main__":
    main()
