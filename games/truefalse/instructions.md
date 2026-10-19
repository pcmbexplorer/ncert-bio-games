# T/F Statement TSV — Build Instructions

Working directory: /home/kuldeep/Downloads/NCERT Bio
Global rule: never use the Agent tool (no forks, no subagents) for any part of this task — do all work directly in this session, regardless of size.

TASK: Build a true/false statement TSV for {CLASS} Ch{NN} ({CHAPTER_NAME}), following the exact spec and methodology below. This TSV is distinct from the existing games/truefalse/truefalse.py game data — it's a new, richer, textbook-grounded true/false question bank.

## SOURCE FILE
Read the full chapter at: /home/kuldeep/Downloads/NCERT Bio/converted/{CLASS}/ch{NN}.md

## OUTPUT FILE
/home/kuldeep/Downloads/NCERT Bio/games/truefalse/statements/{class-lowercase}-ch{NN}.tsv
(e.g. 12th-ch02.tsv — see games/truefalse/statements/12th-ch01.tsv for the reference format already built)

## STEP 1 — Extract true statements
Go through the chapter line by line and convert every factual/declarative sentence into its own row — don't skip any. EXCLUDE only:
- Figure/diagram captions (lines in [Fig ...] brackets or figure labels like "(a)", "(b)")
- In-text activity prompts and rhetorical questions aimed at the student ("Can you...", "Find out...", "Observe...", "Why do you think...")
- The chapter's end-of-chapter exercise questions (the numbered list, e.g. "1. Name the parts of...")
- Page-header artifacts (repeated chapter titles like "HUMAN REPRODUCTION" injected mid-text by the source conversion)
Weak/vague sentences with no concrete fact to invert (pure color commentary) can also be skipped.

## STEP 2 — Generate false variants using these 7 categories, checked EXHAUSTIVELY against every single true statement (not opportunistically — go through all 7 for each row, every time):

1. **Antonym/quantifier/number swap** — more↔few, most↔least, all↔none, increase↔decrease, high↔low, before↔after, large↔small, single↔multiple, and swapping specific numbers/percentages/measurements for other plausible-but-wrong ones.
2. **Sibling-term swap** — confuse two real, distinct structures/processes from the SAME chapter (e.g. stigma↔style, synergid↔antipodal, syngamy↔triple fusion, autogamy↔xenogamy, meiosis↔mitosis, epicotyl↔hypocotyl). Must be real chapter terms, not fabricated ones.
3. **Named-example swap** — swap a correct species/family/genus name for another real one named ELSEWHERE in the same chapter that doesn't fit this particular claim. Never invent a species not in the chapter, and never pick a substitute that would accidentally make the false statement still true.
4. **Reversed causation** — "A because B" → "B because A", only where the sentence has genuine cause→effect phrasing (because, due to, leads to, results in, so that).
5. **Scope/frequency-qualifier swap** — generally↔rarely, commonly↔occasionally, majority↔minority — distinct from the strict antonym pairs already covered in category 1.
6. **Functional-role swap** — swap which structure is said to perform a stated function with a different real structure from the chapter (e.g. "tapetum nourishes pollen" → "epidermis nourishes pollen").
7. **Singular/plural swap** — "a single X" ↔ "several Xs", only when the sentence's main fact isn't already a number (keeps this distinct from category 1).

## RULES:
- No cap on false-statement count per row. If a sentence genuinely supports 5 or 6 independent, non-overlapping swaps, write all of them. If it only supports 1 (common for simple one-clause sentences — there's only one fact to invert), leave it at 1.
- Quality over quantity: never pad with a weak, contrived, repetitive, or barely-different variant just to hit a higher count. Every false statement must be a clean, independent, textbook-grounded error — not a rephrasing of another false variant already written for that row.
- Never produce a "false" statement that's accidentally still true (e.g. don't swap in a named example that actually also fits the claim).
- Keep each false statement as close to the original true statement's wording as possible — change only what's needed to make the swap, don't rewrite the whole sentence.

## STEP 3 — Output format (TSV, tab-separated)
Header row: `Chapter     True Statement  False 1 False 2 False 3 ...` (as many False N columns as the richest row needs — short rows simply end early with fewer tabs; this is normal/expected TSV shape, not an error)
- Column 1 (every row): `"{CLASS} Ch{NN} - {Chapter Title}"` exactly as it appears in the chapter heading.
- Column 2: the true statement.
- Columns 3+: the false variants for that row, one per column, no fixed count.

## STEP 4 — Validate before finishing
Run a quick Python/csv check: count total true statements, count total false statements, and print the distribution of how many rows have 1/2/3/4+ false statements, so you can report the final tally the same way this was reported for Ch01 (202 true statements → 282 false statements, distribution 134/56/12 across 1/2/3).

Report back: total true statements, total false statements, and the 1/2/3+ distribution, plus the output file path.
