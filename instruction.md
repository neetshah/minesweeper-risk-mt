# Minesweeper Risk MT - Deterministic, Probabilistic, Exact Risk

## Summary
Turn images of minesweeper boards + structured board JSON into next best tile to open, with exact rational audit.

- **Step1 Build Core:** From JSON board, output guaranteed safe cells and certain mines.
- **Step2 Extend Override + Risk Report:** Same file also decodes PGM P2 board images (authoritative when present), chooses minimal-risk hidden tile when no deterministic safe exists preserving S1, and adds exact rational risk fractions when `explain_risk:true`.

**Artifact path:** `/app/project/engine.py`
**CLI:** `python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON` stdlib only, deterministic.

**What you know without reading train**
- Input: rows, cols, total_mines, board 2D (-1 hidden, "F" flagged, 0-8 revealed)
- S2 adds optional `board_image_pgm` path to P2 PGM; when present it is authoritative ground truth (JSON board may be all -1 placeholder and differs from image, several train_v2 cases)
- S2 adds optional `explain_risk:true` boolean in input
- Output S1: `{"safe":[[r,c]],"flags":[[r,c]]}` sorted row then col
- Output S2 adds `best_tile` (or null) preserving S1 safe/flags, plus `placement_count` and `risk_fractions` only when `explain_risk` true, else S2 shape remains valid
- Examples in `/app/project/train/` (S1), `/app/project/train_v2/` (S2 PGM), `/app/project/train_v3/` (S2 risk) intentionally visible from start. S1 rules visible across train + train_v2. Train_v2 contains boundary PGM cases where single-pixel difference flips cell type, which via sweep uniquely determines gray→cell mapping.

**Behavioral contract (not algorithmic prescription):**

- **Invalid budget:** Board is invalid if flagged cells exceed global mine budget. Specifically, if input flagged count > total_mines, or input flagged + deduced certain mines would exceed total_mines, return empty result: S1 `{"safe":[],"flags":[]}`, S2 same safe/flags empty, `best_tile:null`, and when explain_risk true, `placement_count:0, risk_fractions:{}`. Do not return partial deductions. Demonstrated in train pair 9 and train_v2 output_7/8.

- **Deterministic safe/flag:** A hidden cell is guaranteed safe or certain mine only if it is so in every board consistent with revealed numbers and mine budget. When no such cell exists, return empty lists (valid board with no deterministic move). Ordering must be deterministic independent of input file order: row asc col asc.

- **Minimal risk (S2):** When no guaranteed safe exists, `best_tile` is the hidden cell with lowest probability of being a mine across all globally consistent mine placements that satisfy every numbered clue and total_mines. If multiple share same minimal probability, choose lowest row then col (not file order). E.g., 2x2 all hidden total 1 has 4 placements each 1/4 → best is [0,0]. If no consistent placement exists, keep in-budget deterministic safe/flags, best null. Far cell can have 0 risk while near clue cells higher, because global budget couples all hidden cells.

- **Output format:** Canonical JSON with sorted keys, no spaces (`{"flags":[],"safe":[[0,1]]}` not spaced), sorted row-col for safe/flags/best. S2 `risk_fractions` uses key `"r,c"` with value reduced rational string `"0"`, `"1/3"`, `"1"` sorted by key. Placement count and risk_fractions only appear when input `explain_risk:true`; otherwise S2 shape remains valid (S1 safe/flags + best_tile). If deterministic safe exists, risk report is empty `placement_count:0, risk_fractions:{}` and best is first sorted safe.

- **PGM images (S2) — runtime deduction required:** P2 plain PGM `P2 cols rows 255` pixels row-major, 1 pixel per cell. Mapping gray→cell type (-1 hidden, "F" flag, 0-8) not stated here — must be deduced from train_v2 pairs. Training set includes boundary cases where single-pixel difference flips type, uniquely pinning mapping via sweep. Crucially, **the deduced mapping must be derived at runtime by scanning `/app/project/train_v2/`** (e.g., reading input_*.json boards + paired PGM pixels to build thresholds) because hidden grading uses fresh random PGMs with same band structure, not just train_v2 files. Hardcoding pixel values without reading train_v2 will fail hidden image tests. Use exact provided PGM path only — no fallback to `train_v2/<basename>`.

- **Risk fractions (S2 explain_risk):** When `explain_risk:true`, `placement_count` is number of globally consistent placements, `risk_fractions` maps every remaining hidden candidate to exact reduced rational as string. Reduced means `"0"` not `"0/4"`, `"1"` not `"4/4"`, `"1/3"` not `"2/6"`. Without flag, do not emit placement_count/risk_fractions.

- **Preservation (behavioral, verified via hidden seeds):** S2 safe/flags must equal S1 output when board compatible (deterministic case), and S2 risk outputs must preserve S2 safe/flags/best_tile. Verified by 30+30 seeds n=200 exact equality per seed, not by string import grep. Reuse via import recommended but contract is behavioral.

**Build→Extend shape**
- S1 → S2 adds image decoding + minimal-risk selection + exact rational audit, with preservation

**Artifact contract**
- Only required artifact is `/app/project/engine.py` — no sentinel files. Later steps inherit previous via `inherit_prior_session=true`.

## Completion Rates Expected
- S1: 80-100% frontier, Avocado may fail chain or invalid handling
- S2: 0-70% Avocado (needs threshold deduction + minimal-risk reasoning + tie-break + exact fractions), Opus 80% S1 70% whole

## Performance and hidden board constraints (fixes combinatorial explosion Medium)
- Exact minimal risk requires enumerating placements consistent with all clues. Hidden grading boards go up to 6x6 with 7 mines (~30 hidden cells after deterministic closure, ~1.5M raw combinations, exact placement counts into the millions): unpruned generate-and-filter does not finish in the 15s subprocess budget. Agents must implement exact enumeration with early pruning via clue consistency (assign constrained cells first, abort any branch that over-satisfies a clue or leaves one unsatisfiable), not float sampling; pruned search completes in well under a second. This is documented behavioral constraint, not leaked in earlier versions.
- Train examples are small (2x2 to 4x4, 1-3 mines) and do not demonstrate grading scale. Hidden grading uses larger boards as specified above; exactness (best_tile, placement_count, reduced risk_fractions) is still required at that scale.

## Anti-cheating
- Hidden grading uses fresh generated boards from held-out seeds 710k+ (not just train fixtures), unprivileged subprocess (chmod 700 /tests in Dockerfile + setpriv drop), canonical encoding check. No broad source grep for implementation details — behavioral checks only via preservation 30+30 seeds exact equality.
