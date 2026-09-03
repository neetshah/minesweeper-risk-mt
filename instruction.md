# Minesweeper Risk MT - Deterministic, Probabilistic, Exact Risk

## Summary
Turn images of minesweeper boards + structured board JSON into next best tile to open.

- **Step1 Build Core:** Deterministic safe/flag engine from board JSON.
- **Step2 Extend Override:** Same file `/app/project/engine.py` supports PGM P2 image board parsing, exact minimal-risk tile selection via exhaustive mine-placement enumeration, and every Step1 rule.
- **Step3 Risk Report:** Preserve Step2 behavior and add exact rational risk reporting when input sets `explain_risk: true`.

**Artifact path:** `/app/project/engine.py`
**CLI:** `python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON` stdlib only, deterministic.

**What you know without reading train**
- Input is board rows/cols/total_mines + board 2D (-1 hidden, "F" flag, 0-8)
- S2 adds optional `board_image_pgm` P2 plain PGM path; when present image is ground truth
- Output S1 `{"safe":[[r,c]],"flags":[[r,c]]}` sorted row asc col asc
- Output S2 adds `best_tile` + optional probabilities, same safe/flags preserved
- Output S3 adds `placement_count` and `risk_fractions` only when `explain_risk` is true
- Business rules are shown by the pairs in `/app/project/train/`, `/app/project/train_v2/`, and `/app/project/train_v3`; deduce the missing image thresholds from those examples

**Build→Extend shape**
- S1 deterministic closure iterative flag→safe until fixed point
- S2 adds image decoding (PGM 1px per cell, gray→cell mapping deduced), minimal-risk exact enumeration via `Fraction`, and preservation of Step1 safe/flag results
- S3 exposes the same enumeration as reduced rational strings for auditability

**Important rules**
- Deterministic order: `safe` and `flags` sorted row/col; `best_tile` uses the lowest mine probability with row/col tie-break.
- Canonical JSON: verifier checks `sort_keys=True, separators=(',',':')` canonical encoding and sorted row/col order.
- PGM thresholds are pinned by boundary examples in `train_v2`; compare paired images and JSON boards instead of guessing ranges.
- Invalid boards return an empty result: if input flags or input flags plus deduced flags exceed `total_mines`, do not return partial safe/flag deductions.
- Global `total_mines` couples all hidden cells; a far cell can have 0 risk while near clue cells have higher risk.
- Risk reports use reduced rational strings such as `"0"`, `"1/3"`, and `"1"`.

**Artifact contract**
- Only required artifact is `/app/project/engine.py` — no sentinel files needed. Later steps inherit the previous step's engine.py via `inherit_prior_session=true`.

## Completion Rates Expected
- S1: 80-100% frontier, Avocado may fail closure chain (input_3) or sorted order
- S2: 0-70% Avocado (needs image threshold deduction + Fraction enumeration + tie break), Opus 80% S1 70% whole
- S3: exact risk fractions and canonical report output are intended to separate complete enumeration from float-only heuristics

## Anti-cheating
Hidden grading uses fresh generated boards, unprivileged subprocess execution, and checks against direct references to hidden verifier assets.
