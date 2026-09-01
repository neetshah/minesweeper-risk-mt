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
- CLI fixed, file path fixed
- Input is JSON board, output safe/flags mapping sorted
- Deduction is closure: flagging a mine can unlock new safe deductions iteratively (needs loop until fixed point)
- Some boards have no deterministic safe/flag → empty lists
- Flags consume total_mines budget
- Validation: flag count > total_mines? How to handle? Deduce from train (hint: see input_.. invalid case returns empty)

## What you must do
1. Read ALL 8 train pairs
2. Deduce: validation rules, deterministic rule: for each revealed number `v`, let `flagged_neighbors = count flagged input + deduced`, `hidden_neighbors = list -1 not yet decided`. If `v - flagged == 0` → all hidden safe. If `v - flagged == len(hidden)` → all hidden are mines. Iterate closure.
3. Ordering: output sorted row asc col asc independent of file order. Why? Train shows shuffled hidden positions but expected sorted.
4. Tightest-fit analog: overlapping clues require intersection; single-pass first-fit misses chain dependencies. Train includes chain case where flagging one enables safe elsewhere.
5. Write engine that matches train exactly and will generalize. Use only stdlib.
6. Keep modular because Step2 needs override.

## Hints for deduction
- Look at board with 0 revealed: what hidden cells are safe?
- Look at board with single hidden neighbor beside 1: what is flagged?
- Chain board input_3: first flag in one region makes safe in another?
- Sorted order: check output_4 where safe list out-of-file-order input but sorted.
- Duplicate handling? Board is 2D so no dedup but flag vs safe overlap must not happen.
- Preservation for Step2: your safe/flags logic will be reused; Step2 must equal S1 when no probabilistic fallback needed.

## Anti-cheating
Do not read from `/tests`, `_dgp`, etc. Engine executed via subprocess on fresh inputs.
