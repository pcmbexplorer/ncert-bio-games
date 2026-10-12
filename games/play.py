import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.prompt import Prompt
from rich import box

console = Console()


def clear():
    os.system("clear")


def main():
    while True:
        clear()
        console.print(Panel(
            Align.center(
                "[bold cyan]🧬  NCERT BIO GAMES[/bold cyan]\n"
                "[dim]Learn Biology through play[/dim]"
            ),
            box=box.DOUBLE_EDGE, style="cyan", padding=(1, 4),
        ))
        console.print()
        console.print(Panel(
            "[bold green]  1.  Hangman[/bold green]\n"
            "      [dim]Guess the keyword · pick any class(es) · 2,400 words[/dim]\n\n"
            "[bold yellow]  2.  Bio MCQ[/bold yellow]\n"
            "      [dim]Auto-generated MCQ from reference TSVs · 4,500 questions[/dim]\n\n"
            "[bold magenta]  3.  NEET[/bold magenta]\n"
            "      [dim]Test papers + real NEET exam questions · 8,950 questions[/dim]\n\n"
            "[bold cyan]  4.  Biology Atlas[/bold cyan]\n"
            "      [dim]Word chain game · each keyword starts with last letter of previous[/dim]",
            title="[bold]Select Game[/bold]",
            box=box.ROUNDED, padding=(1, 2),
        ))
        console.print()

        try:
            choice = Prompt.ask("  Enter [1/2/3/4] or Q to quit",
                                choices=["1", "2", "3", "4", "q", "Q"],
                                default="1")
        except (EOFError, KeyboardInterrupt):
            break

        if choice.upper() == "Q":
            break

        # Run selected game as a subprocess so it gets a clean terminal
        import subprocess
        games_dir = Path(__file__).parent
        game_map = {
            "1": games_dir / "hangman" / "hangman.py",
            "2": games_dir / "bio_mcq" / "mcq.py",
            "3": games_dir / "neet"    / "neet.py",
            "4": games_dir / "atlas"   / "atlas.py",
        }
        subprocess.run([sys.executable, str(game_map[choice])])

    clear()
    console.print(Align.center("\n[dim]Thanks for playing! 🧬[/dim]\n"))


if __name__ == "__main__":
    main()
