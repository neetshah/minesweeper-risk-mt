# Task — Step2 Override to Probabilistic Best-Tile + PGM Image Parsing (strongly dependent, example-driven)

That deterministic engine you shipped in Step1? It leaves money on the table when no guaranteed safe exists. Need minimal risk guess + image input support.

Same file, same CLI:
```
python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON
```
Reads JSON now with extra field `board_image_pgm` optional path to P2 plain PGM image plus all Step1 fields, writes same safe/flags plus new best_tile. Stdlib only.

**Input JSON S2**
```json
{
  "rows": int,
  "cols": int,
  "total_mines": int,
  "board": [[cell]],         // may be present, may be all -1 if image only
  "board_image_pgm": "train_v2/board_*.pgm"  // optional relative or absolute path
}
```
If `board_image_pgm` present, engine must open PGM and decode board state — **PGM is authoritative ground truth**. The JSON `board` field may be present but can be all `-1` placeholder (several train_v2 inputs have all-hidden JSON boards whose PGM is authoritative and differs from board). When both present with differing values, image overrides board. In training, some pairs have board equal to decoded image, others have board all-hidden and only PGM gives clues — deduce mapping from PGM pixels to cell types. Verifier will test image-only inputs.

**PGM Format P2 plain**
```
P2
cols rows
255
pixel0 pixel1 ...
```
Each pixel corresponds to one board cell (rows x cols). Gray value mapping to cell type must be deduced from train_v2 examples - do not hardcode guessed ranges. Train includes boundary cases that uniquely pin every hidden constant via sweep verification (only one threshold assignment matches all 8). For example, train contains images where a single-pixel difference flips hidden↔flag and 4↔5 - deduce which value maps to which type by comparing PGM pixels to paired JSON boards.

You must deduce this mapping from train_v2 images + board JSON. Sweep all other thresholds fails at least one train pair.

**Output JSON S2**
```json
{
  "safe": [[r,c],...],
  "flags": [[r,c],...],
  "best_tile": [r,c] | null,
  "probabilities": {"r,c": float} // optional
}
```
- `safe`,`flags` same deterministic closure as S1 (preserve)
- If you emit `probabilities`, include it only when deterministic closure yields no safe tiles, remaining hidden candidates exist, and at least one valid placement exists. When `safe` is non-empty, omit `probabilities`. Keys are `"r,c"` strings and values are JSON numbers.
- `best_tile`:
  - If safe non-empty → `best_tile = safe[0]` (first sorted safe) → preservation contract
  - Else if remaining hidden non-empty → compute exact mine probability via exhaustive enumeration of all placements consistent with all numbered clues + global total_mines budget
- `remaining_mines = total_mines - input_flags - deduced_flags`
- If input flags plus deduced flags exceed `total_mines`, the board is invalid: return empty `safe`, empty `flags`, and `best_tile: null`.
- `hidden_remain = -1 cells not safe/flag`
- Enumerate all combos `hidden_remain choose remaining_mines` that satisfy every revealed number (flagged+placed == number)
  - For each hidden cell, `P(mine) = count placements where cell is mine / total placements` using Fraction exact rational
  - Pick minimal probability, tie break row asc col asc
  - If no consistent placement (invalid board) or no hidden → null
- Canonical encoding: outputs checked with `sort_keys=True, separators=(',',':')` canonical JSON and sorted row-col order for safe/flags/best.

**Preservation contract (multiturn core) — behavioral, not import string**
S2 output `safe` and `flags` must exactly equal S1 output (behavioral preservation) when S2-specific fields equal S1-compatible values:
- board_image_pgm absent or decodes to same board as S1 board (or board all -1 placeholder)
- total_mines same, board content same after PGM decode
- deterministic safe exists (so best = first safe) OR no safe needed consistent

Verified behaviorally via hidden preservation tests. Reuse via import of S1's `deterministic_closure` is recommended for modularity; behavioral equality is the contract.

When `board_image_pgm` is present with an all-hidden JSON board, PGM is authoritative and the JSON board is only a placeholder.

Hidden PGM tests are generated from globally consistent Minesweeper boards. If a parsed board has no global mine placement consistent with the numbered clues, preserve deterministic safe/flags when they are within the `total_mines` budget and set `best_tile` to `null`.

**What you must do**
1. Read all 8 train_v2 pairs plus compare to v1. All 8 must match exactly.
2. Deduce: PGM parsing gray→cell mapping via sweep (only one threshold set matches all 8; train includes single-pixel-difference images flipping hidden↔flag and number↔number), image overrides board, invalid budgets return empty safe/flags and `best_tile: null`, deterministic closure same as S1, probabilistic enumeration exact Fraction not float sampling, minimal risk selection tie row col.
3. Extend Step1 engine. S2 must equal S1 under the preservation contract.
4. Test against train_v2 exactly - must match including boundary boards.
5. Keep S2 imports S1 logic via modular funcs; engine file still exists after S2; no hardcode of expected boards; no reading of `/tests`.

**Hints for deduction**
- Some train_v2 images differ by 1 gray level but decode to different cell types - find threshold via comparing PGM pixel values to paired JSON boards. Sweep other thresholds fails.
- One board has single-pixel hidden vs flag difference near low gray values and another near mid gray where 4 vs 5 flips - only one assignment matches all.
- Tie break: when multiple tiles share minimal mine probability (e.g., 2x2 all hidden total 1), best is lowest row then col, not input file order.
- Global coupling: clue restricts mine to subset of hidden, far cells prob 0 minimal → best is far cell, not neighbor of clue. Proves whole board coupled via total_mines.
- Preservation: board with deterministic safe exists → best = safe[0]
- Invalid: flag count > total → empty output no retention

**Stdlib only, no PIL, no numpy. Parse PGM plain P2 via open(). Use itertools.combinations + Fraction.**

**Anti-cheating checklist**
- Dockerfile 0 COPY ground-truth, only COPY project
- tests/_dgp.py outside build context
- test.sh greps _dgp|test_outputs zero reward, chmod go-rwx /tests, setpriv agent_runner, EXIT trap cleanup
