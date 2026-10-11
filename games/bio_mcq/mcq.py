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

DATA = Path(__file__).parent / "data"
REF  = DATA
ORIG = DATA

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 3,   "replenish": False},
}

LABELS = ["A", "B", "C", "D"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_tsv(path: Path) -> List[Dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows.append({k.strip(): (v.strip() if v else "") for k, v in row.items()})
    return rows


def pick_distractors(pool: List[str], correct: str, n: int = 3) -> List[str]:
    others = [x for x in pool if x.lower() != correct.lower() and x]
    return random.sample(others, min(n, len(others)))


def make_options(correct: str, distractors: List[str]) -> tuple:
    """Returns (options_list, correct_index). Options shuffled."""
    opts = distractors[:3] + [correct]
    random.shuffle(opts)
    return opts, opts.index(correct)


def truncate(s: str, n: int = 80) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


# ── Question builders ─────────────────────────────────────────────────────────

def build_keywords(rows: List[Dict]) -> List[Dict]:
    qs = []
    keywords = [r["Keyword"] for r in rows if r["Keyword"]]
    for r in rows:
        kw, defn, ch = r["Keyword"], r["Definition"], r["Chapter"]
        cls = r.get("Class", "")
        if not kw or not defn:
            continue
        d = pick_distractors(keywords, kw)
        if len(d) < 3:
            continue
        opts, ci = make_options(kw, d)
        qs.append({
            "q": truncate(f'Which term is defined as:\n  "{defn}"'),
            "opts": opts, "correct": ci,
            "source": "Keywords", "chapter": ch, "class": cls,
        })
    return qs


def build_scientific_names(rows: List[Dict]) -> List[Dict]:
    qs = []
    sci_names = [r["Scientific Name"] for r in rows if r["Scientific Name"]]
    common_names = [r["Common Name / Notes"] for r in rows if r["Common Name / Notes"]]
    for r in rows:
        sci, common, ch = r["Scientific Name"], r["Common Name / Notes"], r.get("Chapter", "")
        if not sci or not common:
            continue
        # Q1: common → scientific
        d = pick_distractors(sci_names, sci)
        if len(d) >= 3:
            opts, ci = make_options(sci, d)
            qs.append({
                "q": f"What is the scientific name of: {common}?",
                "opts": opts, "correct": ci,
                "source": "Scientific Names", "chapter": ch,
            })
        # Q2: scientific → common
        d2 = pick_distractors(common_names, common)
        if len(d2) >= 3:
            opts2, ci2 = make_options(common, d2)
            qs.append({
                "q": f"What is the common name for: {sci}?",
                "opts": opts2, "correct": ci2,
                "source": "Scientific Names", "chapter": ch,
            })
    return qs


def build_numbers(rows: List[Dict]) -> List[Dict]:
    qs = []
    numbers = [r["Number"] for r in rows if r["Number"]]
    for r in rows:
        num, desc, ch = r["Number"], r["Description"], r.get("Chapter", "")
        if not num or not desc:
            continue
        d = pick_distractors(numbers, num)
        if len(d) < 3:
            continue
        opts, ci = make_options(num, d)
        qs.append({
            "q": truncate(f"{desc}"),
            "opts": opts, "correct": ci,
            "source": "Numbers", "chapter": ch,
        })
    return qs


def build_scientists(rows: List[Dict]) -> List[Dict]:
    qs = []
    scientists = [r["Scientist"] for r in rows if r["Scientist"]]
    for r in rows:
        sc, contrib, ch = r["Scientist"], r["Discovery/Contribution"], r.get("Chapter", "")
        if not sc or not contrib:
            continue
        d = pick_distractors(scientists, sc)
        if len(d) < 3:
            continue
        opts, ci = make_options(sc, d)
        qs.append({
            "q": truncate(f'Who is credited with:\n  "{contrib}"?'),
            "opts": opts, "correct": ci,
            "source": "Scientists", "chapter": ch,
        })
    return qs


def build_dates(rows: List[Dict]) -> List[Dict]:
    qs = []
    years = [r["Year/Date"] for r in rows if r["Year/Date"]]
    for r in rows:
        yr, event, ch = r["Year/Date"], r["Event"], r.get("Chapter", "")
        if not yr or not event:
            continue
        d = pick_distractors(years, yr)
        if len(d) < 3:
            continue
        opts, ci = make_options(yr, d)
        qs.append({
            "q": truncate(f"In which year/period did this occur?\n  {event}"),
            "opts": opts, "correct": ci,
            "source": "Dates & Events", "chapter": ch,
        })
    return qs


def build_conservation(rows: List[Dict]) -> List[Dict]:
    qs = []
    parks  = [r["National Park"] for r in rows if r["National Park"]]
    states = [r["State"] for r in rows if r["State"]]
    fauna  = [r["Key Fauna"] for r in rows if r["Key Fauna"]]
    for r in rows:
        park, state, kf = r["National Park"], r["State"], r["Key Fauna"]
        if not park or not state:
            continue
        # Q1: park → state
        d = pick_distractors(states, state)
        if len(d) >= 3:
            opts, ci = make_options(state, d)
            qs.append({
                "q": f"In which state is {park} located?",
                "opts": opts, "correct": ci,
                "source": "Conservation", "chapter": "Biodiversity & Conservation",
            })
        # Q2: fauna → park
        if kf:
            d2 = pick_distractors(parks, park)
            if len(d2) >= 3:
                opts2, ci2 = make_options(park, d2)
                qs.append({
                    "q": truncate(f"Which national park is known for: {kf}?"),
                    "opts": opts2, "correct": ci2,
                    "source": "Conservation", "chapter": "Biodiversity & Conservation",
                })
    return qs


def build_hormones(rows: List[Dict]) -> List[Dict]:
    qs = []
    valid = [r for r in rows if r.get("Hormone") and r.get("Gland / Tissue")]
    glands   = [r["Gland / Tissue"] for r in valid]
    hormones = [r["Hormone"] for r in valid]
    funcs    = [r["Function"] for r in valid if r.get("Function")]
    for r in valid:
        gland, hormone, func = r["Gland / Tissue"], r["Hormone"], r.get("Function", "")
        # Q: hormone → gland
        d = pick_distractors(glands, gland)
        if len(d) >= 3:
            opts, ci = make_options(gland, d)
            qs.append({
                "q": f"Which gland/tissue secretes: {hormone}?",
                "opts": opts, "correct": ci,
                "source": "Hormones", "chapter": r.get("Class", "") + " Endocrinology",
            })
        # Q: gland → hormone
        d2 = pick_distractors(hormones, hormone)
        if len(d2) >= 3:
            opts2, ci2 = make_options(hormone, d2)
            qs.append({
                "q": f"Which hormone is secreted by: {gland}?",
                "opts": opts2, "correct": ci2,
                "source": "Hormones", "chapter": r.get("Class", "") + " Endocrinology",
            })
    return qs


def build_cranial(rows: List[Dict]) -> List[Dict]:
    qs = []
    names = [r["Cranial Nerve Name"] for r in rows if r["Cranial Nerve Name"]]
    types = ["Sensory", "Motor", "Both"]
    for r in rows:
        num, name, t = r["No."], r["Cranial Nerve Name"], r["Type (S/M/B)"]
        if not num or not name:
            continue
        # Q: number → name
        d = pick_distractors(names, name)
        if len(d) >= 3:
            opts, ci = make_options(name, d)
            qs.append({
                "q": f"What is cranial nerve {num}?",
                "opts": opts, "correct": ci,
                "source": "Cranial Nerves", "chapter": "Neural Control & Coordination",
            })
        # Q: name → type
        full_type = {"S": "Sensory", "M": "Motor", "B": "Both"}.get(t, "")
        if full_type:
            d2 = [x for x in types if x != full_type]
            opts2, ci2 = make_options(full_type, d2[:3])
            qs.append({
                "q": f"The {name} nerve (cranial nerve {num}) is:",
                "opts": opts2, "correct": ci2,
                "source": "Cranial Nerves", "chapter": "Neural Control & Coordination",
            })
    return qs


def build_category_examples(rows: List[Dict]) -> List[Dict]:
    qs = []
    cats     = [r["Category/Topic"] for r in rows if r["Category/Topic"]]
    examples = [r["Example(s)"] for r in rows
                if r["Example(s)"] and "," not in r["Example(s)"]]
    for r in rows:
        cat, ex, ch = r["Category/Topic"], r["Example(s)"], r.get("Chapter", "")
        if not cat or not ex or "," in ex:
            continue
        # Q: example → category
        d = pick_distractors(cats, cat)
        if len(d) >= 3:
            opts, ci = make_options(cat, d)
            qs.append({
                "q": f"{ex}  is an example of which category?",
                "opts": opts, "correct": ci,
                "source": "Category Examples", "chapter": ch,
            })
        # Q: category → correct example (odd-one-out style)
        d2 = pick_distractors(examples, ex)
        if len(d2) >= 3:
            opts2, ci2 = make_options(ex, d2)
            qs.append({
                "q": f"Which of the following is an example of:\n  {cat}?",
                "opts": opts2, "correct": ci2,
                "source": "Category Examples", "chapter": ch,
            })
    return qs


# ── Load all questions ─────────────────────────────────────────────────────────

def load_all_questions() -> List[Dict]:
    qs = []
    qs += build_keywords(read_tsv(REF / "keywords-glossary-v2.tsv"))
    qs += build_scientific_names(read_tsv(REF / "scientific-names.tsv"))
    qs += build_numbers(read_tsv(ORIG / "ncert_bio_numbers.tsv"))
    qs += build_scientists(read_tsv(REF / "scientists.tsv"))
    qs += build_dates(read_tsv(REF / "dates-events.tsv"))
    qs += build_conservation(read_tsv(REF / "conservation.tsv"))
    qs += build_hormones(read_tsv(REF / "hormones.tsv"))
    qs += build_cranial(read_tsv(REF / "cranial-nerves.tsv"))
    qs += build_category_examples(read_tsv(REF / "category-examples.tsv"))
    random.shuffle(qs)
    return qs


# ── UI ─────────────────────────────────────────────────────────────────────────

def clear():
    os.system("clear")


def render_lives(lives: int, max_lives: int, color: str) -> str:
    if max_lives >= 999:
        return f"[{color}]∞ lives[/{color}]"
    filled = min(lives, max_lives)
    return (f"[{color}]{'❤  ' * filled}[/{color}]"
            f"[dim]{'🖤  ' * (max_lives - filled)}[/dim]").strip()


def render_hints(hints: int, max_hints: int, color: str) -> str:
    if max_hints >= 999:
        return f"[{color}]∞ hints[/{color}]"
    filled = min(hints, max_hints)
    return (f"[{color}]{'💡 ' * filled}[/{color}]"
            f"[dim]{'○  ' * (max_hints - filled)}[/dim]").strip()


CLASS_FILTER = {
    "1": "All Classes",
    "2": "11th only",
    "3": "12th only",
    "4": "11th + 12th",
}

def select_class_filter() -> str:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]🧬  BIO MCQ[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  All Classes  (11th + 12th + extra topics)\n\n"
        "[bold]  2.[/bold]  11th only\n\n"
        "[bold]  3.[/bold]  12th only\n\n"
        "[bold]  4.[/bold]  11th + 12th",
        title="[bold]Select Class[/bold]", box=box.ROUNDED,
    ))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3/4]", choices=["1", "2", "3", "4"], default="1")
    return CLASS_FILTER[choice]


def select_mode() -> Dict:
    clear()
    console.print(Panel(
        Align.center("[bold cyan]🧬  BIO MCQ[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 each on correct answer\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · 3 hints · no replenishment",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED,
    ))
    console.print()
    choice = Prompt.ask("  Enter [1/2/3]", choices=["1", "2", "3"], default="2")
    return MODES[choice]


def draw_question(q: Dict, lives: int, hints: int, mode: Dict,
                  streak: int, max_lives: int, max_hints: int,
                  q_num: int, eliminated: List[int], answered: Optional[str]):
    clear()
    color = mode["color"]
    streak_badge = f"  [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""

    console.print(Panel(
        Align.center(f"🧬  BIO MCQ   [bold {color}]{mode['name']}[/bold {color}]{streak_badge}"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print(
        f"  {render_lives(lives, max_lives, color)}    "
        f"{render_hints(hints, max_hints, color)}    "
        f"[dim]Q{q_num}[/dim]   [dim]{q['source']}[/dim]"
    )
    console.print()

    # Question
    console.print(Panel(
        f"\n  {q['q']}\n",
        title=f"[dim]{q['chapter']}[/dim]",
        box=box.ROUNDED, style="white",
    ))
    console.print()

    # Options
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
        Align.center("[bold cyan]📊  MCQ ANALYSIS[/bold cyan]"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="dim", width=22)
    t.add_column(style="bold")
    t.add_row("Mode",           f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",      str(total))
    t.add_row("Correct",        f"[green]{won}[/green]")
    t.add_row("Wrong",          f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",       f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak",    f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",     str(stats["hints_used"]))

    # Breakdown by source
    breakdown = stats["by_source"]
    if breakdown:
        t.add_section()
        for src, (c, tot) in sorted(breakdown.items(), key=lambda x: -x[1][1]):
            pct = f"{c/tot*100:.0f}%" if tot else "—"
            bar = "█" * int(c / tot * 10) + "░" * (10 - int(c / tot * 10)) if tot else ""
            t.add_row(f"  {src}", f"[dim]{bar}[/dim] {c}/{tot}  [yellow]{pct}[/yellow]")

    console.print(Align.center(t))

    if stats["missed"]:
        console.print()
        missed_lines = []
        for m in stats["missed"][-8:]:
            missed_lines.append(
                f"  [red]✗[/red]  [dim]{m['q'][:60]}[/dim]\n"
                f"      [bold]Ans:[/bold] {m['correct_ans']}   [dim]{m['chapter']}[/dim]"
            )
        console.print(Panel(
            "\n".join(missed_lines),
            title="[dim]Recently Missed[/dim]",
            box=box.ROUNDED, style="dim",
        ))
    console.print()


def play_round(q: Dict, lives: int, hints: int, mode: Dict,
               streak: int, max_lives: int, max_hints: int, stats: Dict):
    eliminated: List[int] = []
    wrong_indices = [i for i in range(4) if i != q["correct"]]

    while True:
        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"] + 1, eliminated, None)

        hint_key = "[dim]? = eliminate wrong option[/dim]" if hints > 0 else "[dim](no hints)[/dim]"
        console.print(f"  Answer [A/B/C/D]  {hint_key}  [dim]q = quit[/dim]: ", end="")

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
        correct_ans = q["opts"][q["correct"]]
        src = q["source"]

        # Update source breakdown
        if src not in stats["by_source"]:
            stats["by_source"][src] = [0, 0]
        stats["by_source"][src][1] += 1

        stats["played"] += 1
        if correct:
            stats["won"] += 1
            stats["by_source"][src][0] += 1
        else:
            stats["lost"] += 1
            stats["missed"].append({
                "q": q["q"], "correct_ans": correct_ans, "chapter": q["chapter"]
            })
            if max_lives < 999:
                lives -= 1

        # Show result briefly
        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"], eliminated, user)

        if correct:
            console.print(Align.center(Panel(
                "[bold green]✓  Correct![/bold green]",
                box=box.HEAVY, style="green", width=30,
            )))
        else:
            console.print(Align.center(Panel(
                f"[bold red]✗  Wrong![/bold red]\n[dim]Answer: {correct_ans}[/dim]",
                box=box.HEAVY, style="red", width=40,
            )))

        input("\n  [Enter] next question...")
        return correct, lives, hints


def main():
    class_filter = select_class_filter()
    console.print("[dim]Loading questions…[/dim]")
    all_qs = load_all_questions()

    def matches(q, target):
        cls = q.get("class", "")
        ch  = q.get("chapter", "")
        if not cls:
            return True  # no class tag → include in all filters
        return target in cls

    if class_filter == "11th only":
        questions = [q for q in all_qs if matches(q, "11th")]
    elif class_filter == "12th only":
        questions = [q for q in all_qs if matches(q, "12th")]
    elif class_filter == "11th + 12th":
        questions = [q for q in all_qs if matches(q, "11th") or matches(q, "12th")]
    else:
        questions = all_qs

    console.print(f"[dim]Loaded {len(questions)} questions ({class_filter}).[/dim]")

    mode = select_mode()
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]

    lives      = mode["lives"]
    hints      = mode["hints"]
    max_lives  = mode["max_lives"]
    max_hints  = mode["max_hints"]
    streak     = 0
    best_streak = 0
    idx        = 0

    stats: Dict = {
        "played": 0, "won": 0, "lost": 0,
        "hints_used": 0, "best_streak": 0,
        "missed": [], "by_source": {},
    }

    while True:
        if idx >= len(questions):
            random.shuffle(questions)
            idx = 0

        q = questions[idx]
        idx += 1

        correct, lives, hints = play_round(
            q, lives, hints, mode, streak, max_lives, max_hints, stats
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
                lives  = mode["lives"]
                hints  = mode["hints"]
                streak = 0
                best_streak = 0
                stats = {
                    "played": 0, "won": 0, "lost": 0,
                    "hints_used": 0, "best_streak": 0,
                    "missed": [], "by_source": {},
                }
                random.shuffle(questions)
                idx = 0


if __name__ == "__main__":
    main()
