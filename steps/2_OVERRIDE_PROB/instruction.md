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
If `board_image_pgm` present, engine must open PGM and decode board state to override `board`. When both present, image is ground truth and equals board in training but verifier may test image-only.

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
  "probabilities": {"r,c": float} // optional, not checked but helpful
}
```
- `safe`,`flags` same deterministic closure as S1 (preserve)
- `best_tile`:
  - If safe non-empty → `best_tile = safe[0]` (first sorted safe) → preservation contract
  - Else if remaining hidden non-empty → compute exact mine probability via exhaustive enumeration of all placements consistent with all numbered clues + global total_mines budget (fleet coupling T7)
  - `remaining_mines = total_mines - input_flags - deduced_flags`
  - `hidden_remain = -1 cells not safe/flag`
  - Enumerate all combos `hidden_remain choose remaining_mines` that satisfy every revealed number (flagged+placed == number)
  - For each hidden cell, `P(mine) = count placements where cell is mine / total placements` using Fraction exact rational
  - Pick minimal probability, tie break row asc col asc (T2 deterministic order inference)
  - If no consistent placement (invalid board) or no hidden → null
- Canonical encoding: outputs checked with sorted lists, but audit hash chain also verifies emission order: flags sorted, then safe sorted, then best. Verifier recomputes SHA256 chain.

**Preservation contract (multiturn core)**
S2 output `safe` and `flags` must exactly equal S1 output when S2-specific fields equal S1-compatible values:
- board_image_pgm absent or decodes to same board as S1 board
- total_mines same, board same
- deterministic safe exists (so best = first safe) OR no safe needed consistent

Hidden tests: 30+30 seeds n=200 exact dict equality per seed, not mean, for preservation.

**What you must do**
1. Read all 8 train_v2 pairs plus compare to v1. All 8 must match exactly.
2. Deduce: PGM parsing gray→cell mapping via sweep (only one threshold set matches all 8; train includes single-pixel-difference images flipping hidden↔flag and number↔number), image overrides board, validation when flag count > total → return empty safe/flags/best null (no-retain analog like cross-invalid no zero-earner), deterministic closure same as S1, probabilistic enumeration exact Fraction not float sampling, minimal risk selection tie row col.
3. Extend Step1 engine. S2 must equal S1 under preservation contract - hidden tests exact equality per seed (30+30 seeds n=200).
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
