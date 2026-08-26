# Minesweeper Risk MT — Two-turn Deterministic → Probabilistic Minimal-Risk

## Summary
Turn images of minesweeper boards + structured board JSON into next best tile to open.

- **Step1 Build Core:** Deterministic safe/flag engine from board JSON. 8 train pairs hide closure and ordering rules.
- **Step2 Extend Override:** Same file `/app/project/engine.py` now supports PGM P2 image board parsing (thresholds uniquely pinned by train boundary cases) + exact minimal-risk tile via exhaustive CSP enumeration with global `total_mines` coupling (fleet coupling T7), preserving every S1 rule.

**Artifact path:** `/app/project/engine.py`
**CLI:** `python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON` stdlib only, deterministic.

**What you know without reading train**
- Input is board rows/cols/total_mines + board 2D (-1 hidden, "F" flag, 0-8)
- S2 adds optional `board_image_pgm` P2 plain PGM path; when present image is ground truth
- Output S1 `{"safe":[[r,c]],"flags":[[r,c]]}` sorted row asc col asc
- Output S2 adds `best_tile` + optional probabilities, same safe/flags preserved
- Business rules hidden in `/app/project/train/` 8 pairs and `train_v2/` 8 pairs - no constants stated in prose, deduce via sweep

**Build→Extend shape**
- S1 deterministic closure iterative flag→safe until fixed point
- S2 adds image decoding (PGM 1px per cell, gray→cell mapping deduced) + minimal-risk exact enumeration via `Fraction` + preservation 30+30 seeds n=200 exact equality

**Traps T2,T3,T5,T6,T7**
- T2 deterministic order: safe sorted row col, best_tile minimal prob tie row col not file order
- T3 canonical JSON + hash chain: verifier recomputes SHA256 chain emission FLAGS→SAFE→BEST with `sort_keys=True, separators=(',',':')`
- T5 uniquely pinned constants via boundaries: train_v2 contains single-pixel difference images flipping hidden↔flag and 4↔5 - only one threshold assignment matches all 8
- T6 ordering dedup→validation→flag→safe→best: invalid flag>total returns empty no-retain, flag closure before safe
- T7 fleet coupling: global total_mines couples all hidden cells; far cell can have 0 risk while near clue cells 0.5 - best is far

## Completion Rates Expected
Per quality bar: per-step Avocado >=1 fail + >=1 frontier pass in 5 trials. Overall 2/5 Avocado sweet spot GOOD like compatibility-matcher 37%.
- S1: 80-100% frontier, Avocado may fail closure chain (input_3) or sorted order
- S2: 0-70% Avocado (needs image threshold deduction + Fraction enumeration + tie break), Opus 80% S1 70% whole

## Anti-cheating
Pristine fixtures tests/fixtures/ not /app/data, 0 COPY oracle, hidden 50+30 streams seeds 710k+, chmod go-rwx /tests + setpriv agent_runner, grep _dgp|test_outputs zero reward, baseline negatives <0.90 BAR, boundary unit tests, preservation exact, MC1 no S2 artifacts after S1, S2 imports S1.
