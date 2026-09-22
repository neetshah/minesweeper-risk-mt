# Task — Step2 Override to Probabilistic Best-Tile + PGM Image Parsing + Exact Risk Report (strongly dependent, example-driven)

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
  "board_image_pgm": "train_v2/board_*.pgm",  // optional relative or absolute path
  "explain_risk": true  // optional: include exact risk report (see below)
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
Each pixel corresponds to one board cell (rows x cols). Per the P2 spec, `#` comments may appear anywhere whitespace is allowed, including trailing on header and pixel lines — strip them before tokenizing. Gray value mapping to cell type must be deduced from train_v2 examples - do not hardcode guessed ranges. Train includes boundary cases that uniquely pin every hidden constant via sweep verification (only one threshold assignment matches all 8). For example, train contains images where a single-pixel difference flips hidden↔flag and 4↔5 - deduce which value maps to which type by comparing PGM pixels to paired JSON boards.

You must deduce this mapping from train_v2 images + board JSON. Sweep all other thresholds fails at least one train pair.

**Output JSON S2**
```json
{
  "safe": [[r,c],...],
  "flags": [[r,c],...],
  "best_tile": [r,c] | null,
  "placement_count": int,          // only when explain_risk true
  "risk_fractions": {"r,c": "n/d"} // only when explain_risk true
}
```
The output keys are exactly these — no additional keys in any mode. In plain
mode (no `explain_risk`) the output is exactly `safe`, `flags`, `best_tile`;
with `"explain_risk": true` it is exactly those three plus `placement_count`
and `risk_fractions`. Do not emit any other key (in particular, no
`probabilities` key).
- `safe`,`flags` same deterministic closure as S1 (preserve)
- `best_tile`:
  - If safe non-empty → `best_tile = safe[0]` (first sorted safe) → preservation contract
  - Else if remaining hidden non-empty → best_tile is the hidden cell with the
    exact lowest mine probability across all placements consistent with all
    numbered clues + global total_mines budget
- If input flags plus deduced flags exceed `total_mines`, the board is invalid: return empty `safe`, empty `flags`, and `best_tile: null`.
- Remaining hidden candidates are `-1` cells that are neither safe nor flags.
  Enumerate the placements that satisfy every revealed number; for each hidden
  cell, `P(mine)` is its mine count across placements over total placements,
  exactly (ties broken by row asc col asc). If no consistent placement
  (invalid board) or no hidden → null
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
   Read `/app/project/train_v3/` for the risk-report examples below.
2. Deduce the PGM gray→cell mapping from the 8 train_v2 pairs (all must match
   exactly, including boundary boards); keep invalid-budget behavior returning
   empty safe/flags and `best_tile: null`; keep deterministic closure as S1;
   select minimal risk with row-col tie-break.
3. Extend Step1 engine. S2 must equal S1 under the preservation contract.
4. Test against train_v2 and train_v3 exactly - must match including boundary boards.
5. Keep S2 imports S1 logic via modular funcs; engine file still exists after S2; no hardcode of expected boards; no reading of `/tests`.

**Hints for deduction**
- Some train_v2 images differ by 1 gray level but decode to different cell types - find threshold via comparing PGM pixel values to paired JSON boards. Sweep other thresholds fails.
- One board has single-pixel hidden vs flag difference near low gray values and another near mid gray where 4 vs 5 flips - only one assignment matches all.
- Tie break: when multiple tiles share minimal mine probability (e.g., 2x2 all hidden total 1), best is lowest row then col, not input file order.
- Global coupling: clue restricts mine to subset of hidden, far cells prob 0 minimal → best is far cell, not neighbor of clue. Proves whole board coupled via total_mines.
- Preservation: board with deterministic safe exists → best = safe[0]
- Invalid: flag count > total → empty output no retention

**Opt-in risk report (`explain_risk: true`)**

When input JSON contains `"explain_risk": true`, include two additional output
keys. All Step2 behavior (`safe`, `flags`, `best_tile`) is exactly unchanged.

- `placement_count` is the number of global mine placements consistent with all
  revealed clues, input flags, deduced flags, and `total_mines`.
- `risk_fractions` maps every remaining hidden candidate tile to its exact mine
  probability across those placements, encoded as a reduced rational string.
  Use `"0"` and `"1"` for whole numbers, `"n/d"` for proper fractions
  (`"1/3"`, never `"2/6"`).
- If deterministic safe tiles exist, `best_tile` is still the first safe tile
  and the risk report is empty: `placement_count: 0`, `risk_fractions: {}`.
- If input flags (plus deduced flags) exceed `total_mines`, return empty
  safe/flags, `best_tile: null`, `placement_count: 0`, `risk_fractions: {}`.
- If no globally consistent placement exists, keep in-budget deterministic
  safe/flags, set `best_tile: null`, `placement_count: 0`, `risk_fractions: {}`.
- Without `"explain_risk": true`, do not add `placement_count` or
  `risk_fractions`; Step2 output shape remains valid.
- If `board_image_pgm` is present, decode and solve that PGM board exactly as
  above, including when the JSON `board` is all hidden.

**Stdlib only, no PIL, no numpy. Parse PGM plain P2 via open(). Use itertools.combinations + Fraction.**

**Anti-cheating checklist**
- Dockerfile 0 COPY ground-truth, only COPY project
- tests/_dgp.py outside build context
- test.sh greps _dgp|test_outputs zero reward, chmod go-rwx /tests, setpriv agent_runner, EXIT trap cleanup
