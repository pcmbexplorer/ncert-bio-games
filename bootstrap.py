"""
One-line installer + launcher for NCERT Bio Games.

Usage in Termux:
    curl -sL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/bootstrap.py | python3

After install, launch anytime with:
    python3 ~/ncert-bio-games/games/play.py
"""

import os, sys, subprocess, urllib.request
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
REPO_RAW  = "https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main"
INSTALL   = Path.home() / "ncert-bio-games"
PLAY      = INSTALL / "games" / "play.py"

FILES = [
    "games/play.py",
    # Hangman
    "games/hangman/hangman.py",
    "games/hangman/data/keywords-glossary-9th.tsv",
    "games/hangman/data/keywords-glossary-10th.tsv",
    "games/hangman/data/keywords-glossary-11th.tsv",
    "games/hangman/data/keywords-glossary-12th.tsv",
    # Bio MCQ
    "games/bio_mcq/mcq.py",
    "games/bio_mcq/data/keywords-glossary-v2.tsv",
    "games/bio_mcq/data/scientists.tsv",
    "games/bio_mcq/data/scientific-names.tsv",
    "games/bio_mcq/data/hormones.tsv",
    "games/bio_mcq/data/cranial-nerves.tsv",
    "games/bio_mcq/data/dates-events.tsv",
    "games/bio_mcq/data/ncert_bio_numbers.tsv",
    "games/bio_mcq/data/conservation.tsv",
    "games/bio_mcq/data/category-examples.tsv",
    # NEET
    "games/neet/neet.py",
    "games/neet/data/neet_app/neet_biology_questions.json",
    # NEET 11th test papers
    "games/neet/data/11th/ch01-tests.md",
    "games/neet/data/11th/ch02-tests.md",
    "games/neet/data/11th/ch03-tests.md",
    "games/neet/data/11th/ch04-tests.md",
    "games/neet/data/11th/ch05-tests.md",
    "games/neet/data/11th/ch06-tests.md",
    "games/neet/data/11th/ch07-tests.md",
    "games/neet/data/11th/ch08-tests.md",
    "games/neet/data/11th/ch09-tests.md",
    "games/neet/data/11th/ch10-tests.md",
    "games/neet/data/11th/ch11-tests.md",
    "games/neet/data/11th/ch12-tests.md",
    "games/neet/data/11th/ch13-tests.md",
    "games/neet/data/11th/ch14-tests.md",
    "games/neet/data/11th/ch15-tests.md",
    "games/neet/data/11th/ch16-tests.md",
    "games/neet/data/11th/ch17-tests.md",
    "games/neet/data/11th/ch18-tests.md",
    "games/neet/data/11th/ch19-tests.md",
    # NEET 12th test papers
    "games/neet/data/12th/ch01-tests.md",
    "games/neet/data/12th/ch02-tests.md",
    "games/neet/data/12th/ch03-tests.md",
    "games/neet/data/12th/ch04-tests.md",
    "games/neet/data/12th/ch05-tests.md",
    "games/neet/data/12th/ch06-tests.md",
    "games/neet/data/12th/ch07-tests.md",
    "games/neet/data/12th/ch08-tests.md",
    "games/neet/data/12th/ch09-tests.md",
    "games/neet/data/12th/ch10-tests.md",
    "games/neet/data/12th/ch11-tests.md",
    "games/neet/data/12th/ch12-tests.md",
    "games/neet/data/12th/ch13-tests.md",
]

already_installed = PLAY.exists()


def step(msg):
    print(f"\033[36m▶  {msg}\033[0m")


def ok(msg):
    print(f"\033[32m✓  {msg}\033[0m")


def install():
    step("Installing dependency: rich")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "rich", "-q"],
        check=True,
    )
    ok("rich ready")

    total = len(FILES)
    for i, rel in enumerate(FILES, 1):
        dest = INSTALL / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"{REPO_RAW}/{rel}"
        print(f"  [{i}/{total}] {rel.split('/')[-1]}", end="\r", flush=True)
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print(f"\n\033[31m✗  Failed: {rel}\033[0m  ({e})")
            sys.exit(1)

    print()
    ok(f"All {total} files downloaded to {INSTALL}")


def launch():
    step(f"Launching  →  {PLAY}")
    os.execv(sys.executable, [sys.executable, str(PLAY)])


# ── Main ───────────────────────────────────────────────────────────────────────
print("\033[1m\n  🧬  NCERT Bio Games\033[0m")

if already_installed:
    print(f"\n  Already installed at {INSTALL}")
    print("  [1] Play now (use existing files)")
    print("  [2] Update all files from GitHub, then play")
    print()
    choice = input("  Choice [1/2]: ").strip()
    if choice == "2":
        install()
else:
    install()

launch()
