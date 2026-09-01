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

**Business rules are NOT fully listed here. They are defined by example in `/app/project/train/` — 8 pairs `input_*.json → output_*.json` covering all deduction rules. Hidden grading uses fresh boards from same logic but different seeds.**

This is Step1 of two-turn task. Keep code clean modular (e.g. `parse_board, neighbors, deterministic_closure, deduce_safe, deduce_flags`) — Step2 will add PGM image board parsing + probabilistic minimal-risk best tile using exact CSP enumeration, but must reuse every piece you deduce now and preserve S1 output under compatible boards.

**Output format (canonical)**
- Engine must write JSON with `sort_keys=True, separators=(',',':'), ensure_ascii=False` — canonical encoding enforced by verifier. Example: `{"flags":[],"safe":[[0,1]]}` not `{"flags": [], "safe": [[0, 1]]}`.

**Multi-turn artifact**
- S1 creates `engine.py` with `deterministic_closure`. S2 will inherit this via `inherit_prior_session=true` and must reuse `deterministic_closure` via import, not reimplement from scratch. The only required artifact is `/app/project/engine.py`.

## What you know without reading train
- CLI fixed, file path fixed at `/app/project/engine.py`
- Input is JSON board with rows/cols/total_mines, output safe/flags mapping
- Some boards have no deterministic safe/flag → empty lists
- Business rules are NOT stated here — deduce from 8 train pairs

## What you must do
1. Read ALL 8 train pairs in `/app/project/train/` — they define all deduction rules, validation, and ordering via examples.
2. Deduce hidden rules via sweep: only one interpretation matches all 8 pairs (validation semantics, ordering, chain dependencies, budget handling).
3. Write engine that matches train exactly and will generalize to hidden boards from same distribution but different seeds. Use only stdlib.
4. Keep code modular with functions like `neighbors`, `deterministic_closure` — Step2 will import and extend this file.

## Anti-cheating adaptation
- Engine executed via subprocess with dropped privileges, fresh random boards not from train.

## Anti-cheating
Do not read from `/tests`, `_dgp`, etc. Engine executed via subprocess on fresh inputs.
