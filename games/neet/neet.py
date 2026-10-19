from __future__ import annotations
import csv, json, re, random, os, sys
from pathlib import Path
from typing import List, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box

console = Console()

DATA      = Path(__file__).parent / "data"
MD_11     = DATA / "11th"
MD_12     = DATA / "12th"
APP_JSON  = DATA / "neet_app" / "neet_biology_questions.json"

MODES = {
    "1": {"name": "Easy",   "color": "green",  "lives": 999, "hints": 999, "replenish": False},
    "2": {"name": "Medium", "color": "yellow", "lives": 3,   "hints": 3,   "replenish": True},
    "3": {"name": "Hard",   "color": "red",    "lives": 3,   "hints": 3,   "replenish": False},
}

LABELS = ["A", "B", "C", "D"]

CHAPTER_NAMES = {
    "chapter-1":"The Living World","chapter-2":"Biological Classification",
    "chapter-3":"Plant Kingdom","chapter-4":"Animal Kingdom",
    "chapter-5":"Morphology of Flowering Plants","chapter-6":"Anatomy of Flowering Plants",
    "chapter-7":"Structural Organisation in Animals","chapter-8":"Cell: The Unit of Life",
    "chapter-9":"Biomolecules","chapter-10":"Cell Cycle and Cell Division",
    "chapter-11":"Transport in Plants","chapter-12":"Mineral Nutrition",
    "chapter-13":"Photosynthesis in Higher Plants","chapter-14":"Respiration in Plants",
    "chapter-15":"Plant Growth and Development","chapter-16":"Digestion and Absorption",
    "chapter-17":"Breathing and Exchange of Gases","chapter-18":"Body Fluids and Circulation",
    "chapter-19":"Excretory Products and their Elimination","chapter-20":"Locomotion and Movement",
    "chapter-21":"Neural Control and Coordination","chapter-22":"Chemical Coordination and Integration",
    "chapter-23":"Reproduction in Organisms","chapter-24":"Sexual Reproduction in Flowering Plants",
    "chapter-25":"Human Reproduction","chapter-26":"Reproductive Health",
    "chapter-27":"Principles of Inheritance and Variation","chapter-28":"Molecular Basis of Inheritance",
    "chapter-29":"Evolution","chapter-30":"Human Health and Disease",
    "chapter-31":"Strategies for Enhancement in Food Production","chapter-32":"Microbes in Human Welfare",
    "chapter-33":"Biotechnology: Principles and Processes","chapter-34":"Biotechnology and its Applications",
    "chapter-35":"Organisms and Populations","chapter-36":"Ecosystem",
    "chapter-37":"Biodiversity and Conservation","chapter-38":"Environmental Issues",
}


# ── Parsers ────────────────────────────────────────────────────────────────────

def parse_answer_key_11th(text: str) -> Dict[str, Dict[int, str]]:
    answer_map: Dict[str, Dict[int, str]] = {}
    for m in re.finditer(
        r'\*\*Test Paper (\d+)\*\*\s*\n\s*\|[^\n]+\|\s*\n\s*\|[-| ]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)', text
    ):
        ans_dict: Dict[int, str] = {}
        for row in m.group(2).strip().split("\n"):
            cells = [c.strip() for c in row.strip("|").split("|")]
            for i in range(0, len(cells) - 1, 2):
                if cells[i].isdigit():
                    ans_dict[int(cells[i])] = cells[i+1].strip()
        answer_map[m.group(1)] = ans_dict
    return answer_map


def parse_answer_key_12th(text: str) -> Dict[str, Dict[int, str]]:
    answer_map: Dict[str, Dict[int, str]] = {}
    for m in re.finditer(
        r'### Answer Key — Test Paper (\d+).*?\*\*Quick Reference Grid\*\*\s*\n\s*\|[^\n]+\|\s*\n\s*\|[-| ]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)',
        text, re.DOTALL
    ):
        ans_dict: Dict[int, str] = {}
        for row in m.group(2).strip().split("\n"):
            for cell in [c.strip() for c in row.strip("|").split("|")]:
                cm = re.match(r'(\d+)\.\s*([ABCD])', cell)
                if cm:
                    ans_dict[int(cm.group(1))] = cm.group(2)
        answer_map[m.group(1)] = ans_dict
    return answer_map


def parse_md_file(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8")
    answer_map = parse_answer_key_12th(text) or parse_answer_key_11th(text)
    if not answer_map:
        return []

    questions = []
    chapter = path.stem.replace("-tests", "")
    for block in re.split(r'(?=## Test Paper \d+)', text):
        pm = re.match(r'## Test Paper (\d+)\s*[—–-]\s*(.+)', block)
        if not pm:
            continue
        paper_num, topic = pm.group(1), pm.group(2).strip()
        ans_dict = answer_map.get(paper_num, {})

        for qb in re.split(r'(?=\*\*Q\d+\.\*\*)', block):
            qm = re.match(r'\*\*Q(\d+)\.\*\*\s*(.+)', qb, re.DOTALL)
            if not qm:
                continue
            q_num = int(qm.group(1))
            body  = re.sub(r'\n>\s*\*\*Answer:.*', '', qm.group(2))
            opts  = {l: t.strip().replace("\n"," ") for l,t in re.findall(
                r'\(([ABCD])\)\s*(.*?)(?=\n\([ABCD]\)|\n\n|\Z)', body, re.DOTALL)}
            if not all(k in opts for k in list("ABCD")):
                continue
            correct_label = ans_dict.get(q_num, "")
            if correct_label not in LABELS:
                continue
            q_text = re.split(r'\n\(A\)', body)[0].strip().replace("\n"," ")
            q_text = re.sub(r'\|[-| ]+\|', '', q_text)
            q_text = re.sub(r'\s{2,}', ' ', q_text)
            questions.append({
                "q": q_text[:200], "opts": [opts["A"],opts["B"],opts["C"],opts["D"]],
                "correct": LABELS.index(correct_label),
                "chapter": chapter, "topic": topic, "source": "NCERT Test Papers",
            })
    return questions


def load_test_paper_questions(classes: List[str]) -> List[Dict]:
    qs = []
    dirs = []
    if "11th" in classes: dirs.append(MD_11)
    if "12th" in classes: dirs.append(MD_12)
    for d in dirs:
        for f in sorted(d.glob("*.md")):
            qs.extend(parse_md_file(f))
    return qs


def load_app_questions(chapters: List[str]) -> List[Dict]:
    with open(APP_JSON, encoding="utf-8") as f:
        data = json.load(f)
    qs = []
    for ch in chapters:
        ch_name = CHAPTER_NAMES.get(ch, ch)
        for q in data.get(ch, []):
            if "<img" in q.get("question","") or any("<img" in o for o in q["options"].values()):
                continue
            opts = q["options"]
            if not all(k in opts for k in list("ABCD")):
                continue
            cl = q["correct_answer"].replace("answer","").upper()
            if cl not in LABELS:
                continue
            qs.append({
                "q": q["question"].strip()[:200],
                "opts": [opts["A"],opts["B"],opts["C"],opts["D"]],
                "correct": LABELS.index(cl),
                "chapter": ch_name, "topic": ch_name, "source": "NEET Exam",
            })
    return qs


# ── Selection screens ─────────────────────────────────────────────────────────

def clear():
    os.system("clear")


def select_source() -> str:
    clear()
    console.print(Panel(Align.center("[bold cyan]🎯  NEET BIOLOGY[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  NCERT Test Papers  [dim]— 1,620 questions (11th & 12th)[/dim]\n\n"
        "[bold]  2.[/bold]  NEET Exam Questions [dim]— 7,330 questions (38 chapters)[/dim]\n\n"
        "[bold]  3.[/bold]  Both combined       [dim]— 8,950 questions[/dim]",
        title="[bold]Select Source[/bold]", box=box.ROUNDED,
    ))
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Enter [1/2/3]: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "2"
        if raw in ("1", "2", "3"): return raw
        console.print("  [red]Enter 1, 2, or 3[/red]")


def select_test_paper_classes() -> List[str]:
    clear()
    console.print(Panel(Align.center("[bold cyan]🎯  NEET BIOLOGY — Test Papers[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold]  1.[/bold]  11th  —  450 questions (19 chapters)\n\n"
        "[bold]  2.[/bold]  12th  — 1,170 questions (13 chapters)",
        title="[bold]Select Class(es)  —  space/comma separated[/bold]", box=box.ROUNDED,
    ))
    console.print()
    console.print("  Examples:  [cyan]1[/cyan]  or  [cyan]1 2[/cyan]")
    console.print()
    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Your choice: ").strip()
        if raw.lower() == "q": sys.exit()
        if raw.lower() == "b": return None
        if not raw: raw = "1 2"
        raw = raw.replace(",", " ")
        picks = [t for t in raw.split() if t in ("1","2")]
        if picks:
            return ["11th" if p=="1" else "12th" for p in picks]
        console.print("  [red]Enter 1, 2, or 1 2[/red]")


def select_app_chapters() -> tuple:
    clear()
    console.print(Panel(Align.center("[bold cyan]🎯  NEET BIOLOGY — NEET Exam[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()

    with open(APP_JSON) as f:
        data = json.load(f)
    all_chapters = sorted(data.keys(), key=lambda x: int(x.split("-")[1]))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    t.add_column(style="bold cyan", width=4)
    t.add_column(width=36)
    t.add_column(style="dim", width=5)
    for ch in all_chapters:
        num = ch.split("-")[1]
        name = CHAPTER_NAMES.get(ch, ch)
        count = sum(1 for q in data[ch]
                    if "<img" not in q.get("question","")
                    and all("<img" not in o for o in q["options"].values()))
        t.add_row(f"  {num}.", name[:36], f"{count}q")
    console.print(Panel(t, title="[bold]38 chapters · 7,330 questions[/bold]", box=box.ROUNDED))
    console.print()
    console.print("  [dim]Enter chapter numbers: all / 1 / 1,5 / 1-15[/dim]")
    console.print()

    console.print("  [dim]b = back · q = quit[/dim]")
    console.print()
    while True:
        raw = input("  Your choice: ").strip().lower()
        if raw == "q": sys.exit()
        if raw == "b": return None
        if not raw: raw = "all"
        if raw == "all":
            picks = all_chapters
            break
        tokens = raw.replace(",", " ").split()
        nums, valid = set(), True
        for tok in tokens:
            if "-" in tok:
                try:
                    s,e = tok.split("-"); nums.update(range(int(s), int(e)+1))
                except Exception: valid = False
            elif tok.isdigit():
                nums.add(int(tok))
            else:
                valid = False
        picks = [f"chapter-{n}" for n in sorted(nums) if f"chapter-{n}" in data]
        if picks and valid:
            break
        console.print("  [red]Invalid. Try: all  1  1,5  1-15[/red]")

    label = "all" if len(picks)==38 else (
        "+".join(p.split("-")[1] for p in picks[:4]) +
        (f"+…({len(picks)}ch)" if len(picks)>4 else "")
    )
    return label, picks


def select_mode() -> Dict:
    clear()
    console.print(Panel(Align.center("[bold cyan]🎯  NEET BIOLOGY[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    console.print()
    console.print(Panel(
        "[bold green]  1.  Easy[/bold green]    — Unlimited lives & hints\n\n"
        "[bold yellow]  2.  Medium[/bold yellow]  — 3 lives · 3 hints · +1 each on correct answer\n\n"
        "[bold red]  3.  Hard[/bold red]    — 3 lives · 3 hints · no replenishment",
        title="[bold]Select Mode[/bold]", box=box.ROUNDED,
    ))
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


# ── Game UI ───────────────────────────────────────────────────────────────────

def render_lives(lives, max_lives, color):
    if max_lives >= 999: return f"[{color}]❤  ∞[/{color}]"
    return f"[{color}]❤  {lives}[/{color}][dim]/{max_lives}[/dim]"

def render_hints(hints, max_hints, color):
    if max_hints >= 999: return f"[{color}]💡 ∞[/{color}]"
    return f"[{color}]💡 {hints}[/{color}][dim]/{max_hints}[/dim]"


def draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                  q_num, eliminated, answered, label):
    clear()
    color = mode["color"]
    sb = f"  [yellow]🔥 {streak}[/yellow]" if streak > 0 else ""
    console.print(Panel(
        Align.center(f"🎯  NEET BIOLOGY · [bold]{label}[/bold]   [bold {color}]{mode['name']}[/bold {color}]{sb}"),
        box=box.DOUBLE_EDGE, style="cyan",
    ))
    console.print(
        f"  {render_lives(lives,max_lives,color)}    "
        f"{render_hints(hints,max_hints,color)}    "
        f"[dim]Q{q_num}[/dim]   [dim]{q['source']}[/dim]"
    )
    console.print()
    console.print(Panel(f"\n  {q['q']}\n", title=f"[dim]{q['chapter']}[/dim]",
                        box=box.ROUNDED, style="white"))
    console.print()
    for i, (lbl, opt) in enumerate(zip(LABELS, q["opts"])):
        txt = opt[:100] + "…" if len(opt) > 100 else opt
        if i in eliminated:
            console.print(f"  [dim strike]{lbl}.  {txt}[/dim strike]")
        elif answered is not None:
            if i == q["correct"]:   console.print(f"  [bold green]{lbl}.  {txt}  ✓[/bold green]")
            elif lbl == answered:   console.print(f"  [bold red]{lbl}.  {txt}  ✗[/bold red]")
            else:                   console.print(f"  [dim]{lbl}.  {txt}[/dim]")
        else:
            console.print(f"  [bold]{lbl}.[/bold]  {txt}")
    console.print()


def show_analysis(stats, mode, label):
    clear()
    color = mode["color"]
    total = stats["played"]
    acc   = f"{stats['won']/total*100:.0f}%" if total else "—"
    console.print(Panel(Align.center("[bold cyan]📊  NEET ANALYSIS[/bold cyan]"),
                        box=box.DOUBLE_EDGE, style="cyan"))
    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column(style="dim", width=22); t.add_column(style="bold")
    t.add_row("Selection",   f"[bold]{label}[/bold]")
    t.add_row("Mode",        f"[{color}]{mode['name']}[/{color}]")
    t.add_row("Questions",   str(total))
    t.add_row("Correct",     f"[green]{stats['won']}[/green]")
    t.add_row("Wrong",       f"[red]{stats['lost']}[/red]")
    t.add_row("Accuracy",    f"[yellow]{acc}[/yellow]")
    t.add_row("Best Streak", f"[yellow]🔥 {stats['best_streak']}[/yellow]")
    t.add_row("Hints Used",  str(stats["hints_used"]))
    bd = stats["by_chapter"]
    if bd:
        t.add_section()
        for ch, (c, tot) in sorted(bd.items(), key=lambda x: -x[1][1]):
            pct = f"{c/tot*100:.0f}%" if tot else "—"
            bar = "█"*int(c/tot*10)+"░"*(10-int(c/tot*10)) if tot else ""
            t.add_row(f"  {ch[:20]}", f"[dim]{bar}[/dim] {c}/{tot}  [yellow]{pct}[/yellow]")
    console.print(Align.center(t))
    if stats["missed"]:
        console.print()
        lines = [
            f"  [red]✗[/red]  [dim]{m['q'][:65]}[/dim]\n"
            f"      [bold]Ans:[/bold] {m['correct_ans'][:60]}   [dim]{m['chapter']}[/dim]"
            for m in stats["missed"][-6:]
        ]
        console.print(Panel("\n".join(lines), title="[dim]Recently Missed[/dim]",
                            box=box.ROUNDED, style="dim"))
    console.print()


def play_round(q, lives, hints, mode, streak, max_lives, max_hints, stats, label):
    eliminated, wrong_indices = [], [i for i in range(4) if i != q["correct"]]
    while True:
        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"]+1, eliminated, None, label)
        hs = "[dim]? = eliminate wrong[/dim]" if hints > 0 else "[dim](no hints)[/dim]"
        console.print(f"  [A/B/C/D]  {hs}  [dim]q = quit[/dim]: ", end="")
        try:
            user = input().strip().upper()
        except (EOFError, KeyboardInterrupt):
            show_analysis(stats, mode, label); sys.exit()

        if user == "Q":
            show_analysis(stats, mode, label); sys.exit()

        if user == "?":
            if hints <= 0:
                console.print("  [red]No hints left![/red]"); input("  [Enter]..."); continue
            rem = [i for i in wrong_indices if i not in eliminated]
            if not rem: continue
            eliminated.append(random.choice(rem))
            stats["hints_used"] += 1
            if max_hints < 999: hints -= 1
            continue

        if user not in LABELS: continue

        idx = LABELS.index(user)
        correct = idx == q["correct"]
        correct_ans = q["opts"][q["correct"]]
        ch = q["chapter"]
        if ch not in stats["by_chapter"]: stats["by_chapter"][ch] = [0,0]
        stats["by_chapter"][ch][1] += 1
        stats["played"] += 1
        if correct:
            stats["won"] += 1; stats["by_chapter"][ch][0] += 1
        else:
            stats["lost"] += 1
            stats["missed"].append({"q":q["q"],"correct_ans":correct_ans,"chapter":ch})
            if max_lives < 999: lives -= 1

        draw_question(q, lives, hints, mode, streak, max_lives, max_hints,
                      stats["played"], eliminated, user, label)
        if correct:
            console.print(Align.center(Panel("[bold green]✓  Correct![/bold green]",
                                            box=box.HEAVY, style="green", width=30)))
        else:
            console.print(Align.center(Panel(
                f"[bold red]✗  Wrong![/bold red]\n[dim]{correct_ans[:70]}[/dim]",
                box=box.HEAVY, style="red", width=52)))
        input("\n  [Enter] next question...")
        return correct, lives, hints


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
        raw = input("  Number of questions: ").strip()
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
        source = select_source()
        if source is None: return

        questions = []
        label_parts = []
        back = False

        if source in ("1", "3"):
            classes = select_test_paper_classes()
            if classes is None: back = True
            else:
                qs = load_test_paper_questions(classes)
                questions.extend(qs)
                label_parts.append("+".join(classes))

        if not back and source in ("2", "3"):
            result = select_app_chapters()
            if result is None: back = True
            else:
                ch_label, ch_picks = result
                qs = load_app_questions(ch_picks)
                questions.extend(qs)
                label_parts.append(f"NEET({ch_label})")

        if back: continue

        label = " + ".join(label_parts)
        random.shuffle(questions)

        if not questions:
            console.print("[red]No questions found.[/red]"); sys.exit()

        console.print(f"\n  [dim]Loaded {len(questions)} questions.[/dim]")

        result = select_mode()
        if result is None: continue
        mode = result
        target = select_target(mode)
        if target is None: continue
        break
    mode["max_lives"] = mode["lives"]
    mode["max_hints"] = mode["hints"]
    lives, hints = mode["lives"], mode["hints"]
    max_lives, max_hints = mode["max_lives"], mode["max_hints"]
    streak, best_streak, idx = 0, 0, 0

    stats: Dict = {"played":0,"won":0,"lost":0,"hints_used":0,
                   "best_streak":0,"missed":[],"by_chapter":{}}

    while True:
        if idx >= len(questions): random.shuffle(questions); idx = 0
        q = questions[idx]; idx += 1

        correct, lives, hints = play_round(
            q, lives, hints, mode, streak, max_lives, max_hints, stats, label)

        if correct:
            streak += 1
            if streak > best_streak: best_streak = streak; stats["best_streak"] = best_streak
            if mode["replenish"]: lives += 1; hints += 1
        else:
            streak = 0

        if stats["played"] >= target:
            show_target_result(stats, mode, target)
            console.print("  [dim]Enter = new game · q = quit[/dim]")
            try:
                if input().strip().lower() == "q": return
            except (EOFError, KeyboardInterrupt): return
            lives, hints, streak, best_streak = mode["lives"], mode["hints"], 0, 0
            stats = {"played":0,"won":0,"lost":0,"hints_used":0,
                     "best_streak":0,"missed":[],"by_chapter":{}}
            random.shuffle(questions); idx = 0
            continue

        if not correct and lives <= 0:
            show_analysis(stats, mode, label)
            console.print("  [dim]Enter to restart · q to quit[/dim]")
            try:
                if input().strip().lower() == "q":
                    break
            except (EOFError, KeyboardInterrupt): break
            lives, hints, streak, best_streak = mode["lives"], mode["hints"], 0, 0
            stats = {"played":0,"won":0,"lost":0,"hints_used":0,
                     "best_streak":0,"missed":[],"by_chapter":{}}
            random.shuffle(questions); idx = 0


if __name__ == "__main__":
    main()
