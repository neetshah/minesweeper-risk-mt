# Task — Step1 Build Deterministic Minesweeper Engine (example-driven)

We need a minesweeper deduction engine that finds guaranteed safe tiles and certain mines from a partially revealed board.

Implement `/app/project/engine.py` CLI:
```
python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON
```
Reads JSON, writes JSON. Stdlib only, deterministic.

**Input JSON**
```json
{
  "rows": int,
  "cols": int,
  "total_mines": int,
  "board": [[cell]]
}
```
`board` is 2D list rows x cols. Each cell:
- `-1` = hidden/unrevealed
- `"F"` = flagged as mine by player (input flag)
- `0..8` = revealed number count of adjacent mines

**Output JSON S1**
```json
{
  "safe": [[r,c],...],
  "flags": [[r,c],...]
}
```
- `safe`: hidden cells proven safe to open (not including already revealed). Sorted asc by row then col.
- `flags`: hidden cells proven to be mines (new deductions, not including input "F"). Sorted asc row col.
- No `best_tile` in Step1.

**Business rules are defined by example in `/app/project/train/` (8 pairs S1) and `/app/project/train_v2/` (8 pairs S2, intentionally visible from start for forward-compatibility).** S1 train covers deterministic closure, ordering, zero-reveal. S1 hidden grading also includes validation case `count(input "F") > total_mines` → empty safe/flags (invalid board, no retention). That rule is explicitly stated here and demonstrated in train_v2 pair 8 and added S1 pair 9 — ideal to do both per quality feedback.

This is Step1 of two-turn task. Keep code clean modular (e.g. `parse_board, neighbors, deterministic_closure, deduce_safe, deduce_flags`) — Step2 will add PGM image board parsing + probabilistic minimal-risk best tile using exact CSP enumeration, but must reuse every piece you deduce now and preserve S1 output under compatible boards.

**Output format (canonical)**
- Engine must write JSON with `sort_keys=True, separators=(',',':'), ensure_ascii=False` — canonical encoding enforced by verifier. Example: `{"flags":[],"safe":[[0,1]]}` not `{"flags": [], "safe": [[0, 1]]}`.

**Multi-turn artifact**
- S1 creates `engine.py` with `deterministic_closure`. S2 will inherit this via `inherit_prior_session=true` and should reuse `deterministic_closure` via import for preservation (behavioral contract verified by 30+30 seeds exact equality, not string import check). The only required artifact is `/app/project/engine.py`.

**Validation explicit (fixes R01/R02/R03 BAD_AMBIGUOUS):**
- If `count(cell == "F" in board) > total_mines` → invalid board → return `{"safe":[],"flags":[]}` empty (no retention, no best_tile in S1). This is required and checked by `test_zero_reveal_and_invalid_budget` and new train pair 9.
- `total_mines` global budget couples all hidden cells; flags (input F + deduced) must not exceed total else invalid.
- Some boards have no deterministic safe/flag → empty lists (valid).

## What you know without reading train
- CLI fixed, file path fixed at `/app/project/engine.py`
- Input is JSON board with rows/cols/total_mines, output safe/flags mapping
- Validation semantics visible in both `/app/project/train/` and `/app/project/train_v2/` (intentionally visible from start for MT)
- Business rules partially in train, partially explicitly stated here for invalid case

## What you must do
1. Read ALL train pairs in `/app/project/train/` (8 pairs) + `/app/project/train_v2/` (8 pairs intentionally visible from start — forward-compatible allowance). Full validation semantics (including invalid flag budget) are visible across both sets, plus explicit statement above.
2. Deduce hidden rules via sweep: only one interpretation matches all pairs (validation semantics flag>total → empty, ordering sorted row-col, chain dependencies requiring fixed-point, budget handling).
3. Write engine that matches train exactly and will generalize to hidden boards from same distribution but different seeds. Use only stdlib. Must handle invalid case explicitly.
4. Keep code modular with functions like `neighbors`, `deterministic_closure` — Step2 will import and extend this file, verified behaviorally via preservation tests (not import string check).

## Anti-cheating adaptation
- Engine executed via subprocess with dropped privileges, fresh random boards not from train.

## Anti-cheating
Do not read from `/tests`, `_dgp`, etc. Engine executed via subprocess on fresh inputs.
