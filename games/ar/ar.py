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

OPTIONS_TEXT = (
    "[bold]1.[/bold] Both A and R are true, and R is the [bold]correct explanation[/bold] of A\n"
    "[bold]2.[/bold] Both A and R are true, but R is [bold]NOT[/bold] the correct explanation of A\n"
    "[bold]3.[/bold] A is true but R is [bold]false[/bold]\n"
    "[bold]4.[/bold] A is false but R is [bold]true[/bold]"
)

OPTIONS_PLAIN = {
    1: "Both A and R are true, R correctly explains A",
    2: "Both A and R are true, but R does NOT explain A",
    3: "A is true but R is false",
    4: "A is false but R is true",
}


def clear(): os.system("clear")

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"


CONTEXT_STARTS = (
    "these ", "this ", "such ", "they ", "it ", "it'", "hence", "therefore",
    "thus ", "similarly", "the former", "the latter", "in this", "in such",
    "both of", "all of them", "all such", "here,", "here ", "as mentioned",
    "as described", "as stated", "as noted", "as discussed",
)

def _context_dependent(s: str) -> bool:
    """True if the sentence opens with a pronoun/reference that needs prior context."""
    return s.lower().startswith(CONTEXT_STARTS)


def load_rows(picks):
    rows = []
    for p in picks:
        prefixes = CLASS_PREFIXES[p][1]
        for tsv in sorted(STATEMENTS_DIR.glob("*.tsv")):
            if not any(tsv.name.startswith(pfx) for pfx in prefixes):
                continue
            with open(tsv, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    chapter   = row.get("Chapter", "").strip()
                    true_stmt = row.get("True Statement", "").strip()
                    reason    = row.get("Reason", "").strip()
                    ar_opt_s  = row.get("AR Option", "").strip()
                    if not true_stmt or not reason or not ar_opt_s:
                        continue
                    if _context_dependent(true_stmt):
                        continue
                    try:
                        ar_opt = int(ar_opt_s)
                    except ValueError:
                        continue
                    false_variants = [
                        v.strip() for k, v in row.items()
                        if k.startswith("False") and v.strip()
                    ]
                    rows.append({
                        "chapter":  chapter,
                        "true":     true_stmt,
                        "reason":   reason,
                        "ar_option": ar_opt,
                        "false":    false_variants,
                    })
    return rows


EXPL = {
    1: "[green]A[/green] is true.  [green]R[/green] correctly explains A.",
    2: "[green]A[/green] is true.  [green]R[/green] is also true, but explains a [bold]different[/bold] fact — not this A.",
    3: "[green]A[/green] is true.  [red]R[/red] is a false statement.",
    4: "[red]A[/red] is false (contains a factual error).  [green]R[/green] is true.",
}

def build_questions(rows):
    """
    Native pair   : use TSV's own A+R with its AR Option as the answer (1, 2, or 3).
    Synthetic type 2: real A (ar_option=1 rows only) + foreign true reason → answer 2.
    Synthetic type 3: real A + false-variant from another row as R → answer 3.
    Synthetic type 4: false-variant as A + own R → answer 4.
    """
    questions = []
    all_reasons = [(r["chapter"], r["reason"]) for r in rows]
    all_false   = [(r["chapter"], fv) for r in rows for fv in r["false"]]

    for r in rows:
        ar_opt = r["ar_option"]

        # Native pair — answer comes from TSV
        questions.append({
            "chapter":     r["chapter"],
            "A":           r["true"],
            "R":           r["reason"],
            "answer":      ar_opt,
            "explanation": EXPL[ar_opt],
        })

        # Synthetic type 2: swap in a foreign reason (only valid when own pair is option 1,
        # so we know the foreign reason is genuinely unrelated to this A)
        if ar_opt == 1:
            foreign = _pick_other(all_reasons, r["reason"])
            if foreign:
                _, fr = foreign
                questions.append({
                    "chapter":     r["chapter"],
                    "A":           r["true"],
                    "R":           fr,
                    "answer":      2,
                    "explanation": EXPL[2],
                })

        # Synthetic type 3: real A + false variant from a different row as R
        false_r = _pick_other(all_false, None)
        if false_r:
            _, fr = false_r
            questions.append({
                "chapter":     r["chapter"],
                "A":           r["true"],
                "R":           fr,
                "answer":      3,
                "explanation": EXPL[3],
            })

        # Synthetic type 4: false variant as A + own R
        if r["false"]:
            fv = random.choice(r["false"])
            questions.append({
                "chapter":     r["chapter"],
                "A":           fv,
                "R":           r["reason"],
                "answer":      4,
                "explanation": EXPL[4],
            })

    random.shuffle(questions)
    return questions


def _pick_other(pool, exclude):
    candidates = [x for x in pool if x[1] != exclude]
    return random.choice(candidates) if candidates else None


def select_class():
    clear()
    console.print(Panel(Align.center("[bold magenta]🔬  ASSERTION-REASON[/bold magenta]"),
                        box=box.DOUBLE_EDGE, style="magenta"))
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
    console.print(Panel(Align.center("[bold magenta]🔬  ASSERTION-REASON[/bold magenta]"),
                        box=box.DOUBLE_EDGE, style="magenta"))
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
            f"[bold magenta]🔬  ASSERTION-REASON[/bold magenta]  [dim]· {class_name}[/dim]"
            f"   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"
        ), box=box.DOUBLE_EDGE, style="magenta"))
    console.print(f"  {render_lives(lives, max_lives, color)}    [dim]Q{q_num}[/dim]")
    console.print()

    console.print(Panel(
        f"\n  [bold]Assertion (A):[/bold]  [italic]{q['A']}[/italic]\n\n"
        f"  [bold]Reason    (R):[/bold]  [italic]{q['R']}[/italic]\n",
        title=f"[dim]{q['chapter']}[/dim]",
        box=box.ROUNDED, style="white"))
    console.print()

    if answered is None:
        console.print(Panel(OPTIONS_TEXT, title="[dim]Which option is correct?[/dim]",
                            box=box.SIMPLE, style="dim"))
        console.print()
        console.print("  [dim]Enter 1 / 2 / 3 / 4 · q = quit[/dim]")
    elif answered == q["answer"]:
        console.print(Align.center(Panel("[bold green]✓  Correct![/bold green]",
                                         box=box.HEAVY, style="green", width=30)))
        console.print()
        console.print(Panel(q["explanation"], title="[dim]Explanation[/dim]",
                            box=box.SIMPLE, style="dim"))
    else:
        console.print(Align.center(Panel(
            f"[bold red]✗  Wrong!  Answer was {q['answer']}[/bold red]\n"
            f"[dim]{OPTIONS_PLAIN[q['answer']]}[/dim]",
            box=box.HEAVY, style="red", width=60)))
        console.print()
        console.print(Panel(q["explanation"], title="[dim]Explanation[/dim]",
                            box=box.SIMPLE, style="dim"))
    console.print()


def show_analysis(stats, mode):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold magenta]📊  ASSERTION-REASON  ANALYSIS[/bold magenta]"),
                        box=box.DOUBLE_EDGE, style="magenta"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Mode",       f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",  str(total))
    t.add_row("Correct",    f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",      f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",   f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak",f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    for opt in (1, 2, 3, 4):
        key_c = f"opt{opt}_correct"; key_t = f"opt{opt}_total"
        t.add_row(f"Option {opt} Correct",
                  f"[green]{stats[key_c]}[/green][dim]/{stats[key_t]}[/dim]")
    console.print(Align.center(t))
    console.print()


def main():
    class_name, picks = select_class()
    mode = select_mode()
    mode["max_lives"] = mode["lives"]

    console.print("[dim]Loading…[/dim]")
    rows = load_rows(picks)
    if not rows:
        console.print("[red]No questions found for selected class(es).[/red]")
        sys.exit(1)
    questions = build_questions(rows)
    console.print(f"[dim]{len(questions)} questions ready.[/dim]")

    lives = mode["lives"]; max_lives = mode["max_lives"]
    streak = best_streak = idx = 0
    stats = {"played":0,"won":0,"lost":0,"best_streak":0}
    for opt in (1,2,3,4):
        stats[f"opt{opt}_correct"] = 0
        stats[f"opt{opt}_total"]   = 0

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

        if user not in ("1", "2", "3", "4"):
            continue

        answer = int(user)
        correct = answer == q["answer"]

        stats[f"opt{q['answer']}_total"] += 1
        if correct: stats[f"opt{q['answer']}_correct"] += 1

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
            stats = {"played":0,"won":0,"lost":0,"best_streak":0}
            for opt in (1,2,3,4):
                stats[f"opt{opt}_correct"] = 0
                stats[f"opt{opt}_total"]   = 0
            random.shuffle(questions)


if __name__ == "__main__":
    main()
