# codimango/minesweeper-risk-mt

## Task Description
Multi-turn Minesweeper assistant that evolves from deterministic deduction to probabilistic minimal-risk and exact rational risk reporting.

- **Step1 Build Core (1_BUILD_CORE):** From JSON board `{rows, cols, total_mines, board: [[-1|F|0..8]]}`, output `{"safe":[[r,c]],"flags":[[r,c]]}` guaranteed safe and certain mines via fixed-point clue satisfaction. Sorted row col, canonical JSON. Invalid when `count(F) > total_mines` or deduced flags would exceed budget → empty. 9 train pairs (including invalid pair 9) hide closure chain, sorted order, zero-reveal, validation.
- **Step2 Override Prob (2_OVERRIDE_PROB):** Same file `/app/project/engine.py` now supports optional `board_image_pgm` P2 plain PGM path (authoritative, may be all -1 placeholder JSON). Decode gray→cell mapping from train_v2 boundary examples where single-pixel difference flips cell type (uniquely pins via sweep). Preserve S1 safe/flags. Choose `best_tile` minimal mine probability via exact global enumeration consistent with all clues + total_mines coupling (fleet coupling T7: far cell can have 0 risk). Tie break row asc col asc. 8 train_v2 pairs + 40 hidden PGM + 30 probabilistic no-safe.
- **Step3 Risk Report (3_RISK_REPORT):** Preserve S2, add opt-in `explain_risk:true` → `placement_count` + `risk_fractions` mapping every hidden candidate to reduced rational string `"0"`, `"1/3"`, `"1"` via exact Fraction. If safe exists, risk report empty `placement_count:0, risk_fractions:{}` and best = safe[0]. Without flag, S2 shape remains valid. 3 train_v3 pairs.

Artifact: `/app/project/engine.py` CLI `python3 engine.py INPUT OUTPUT` stdlib only. Multi-turn with `inherit_prior_session=true`: S1→S2→S3 reuses engine via import/copy.

## Solution Explanation
- **S1:** Fixed-point closure loop: for each revealed number v, flagged = input F + deduced flags in neighborhood, hidden = -1 not yet decided, need = v-flagged. If need==0 → hidden safe, if need==len(hidden) → hidden flags. Iterate until stable. Validate budget: if pre_flags>total or all_flags>total → empty. Keep modular funcs `neighbors`, `deterministic_closure` for S2 import.
- **S2:** PGM P2 parsing: `P2 cols rows 255 pixels` row-major 1px per cell, decode via thresholds deduced from train_v2 (compare pixel values to paired JSON boards, single-pixel boundary flips). No fallback to `train_v2/<basename>`. Then deterministic closure same as S1. For probabilistic: `remaining = total - all_flags`, `hidden_remain = -1 not safe/flag`, enumerate combinations via `itertools.combinations` with pruning by clue consistency `count(flagged+placed)==value` per revealed. Count mine occurrences across valid placements, compute `P = count/total` via Fraction, pick minimal, tie row col. Preserve S1 output under compatible boards.
- **S3:** Reuse S2 logic, when `explain_risk:true` compute `placement_count = len(valid)` and `risk_fractions = {f"{r},{c}": str(Fraction(count, total))}` reduced `"0"/"1"` for whole numbers. If safe exists, `placement_count:0, risk_fractions:{}`.

## Tests Description
- **S1 tests 10:** `test_module_exists`, `test_train_exact_match` 9 pairs including invalid pair 9, `test_canonical_json_bytes_s1` no spaces, `test_sorted_order`, `test_no_s2_artifacts` behavioral no PGM/best/prob/risk after S1, `test_anti_cheat` removed brittle grep per C7 (rely on chmod 700 + setpriv), `test_baseline_bar` flat <0.90 BAR, `test_hidden_seeds_50` 710000-710050 random boards 4x4 mines 3 reveal 0.5 exact match ref, `test_chain_closure_requires_fixed_point` multi-iteration chain, `test_zero_reveal_and_invalid_budget` 0 clue + flag>total.
- **S2 tests 13:** `test_module_exists` only engine.py (fixes R08), `test_train_v2_exact` 8 public, `test_image_only` 3 image-only, `test_preservation_30_30` 60 seeds n=200 exact equality S1==S2 when compatible, `test_tie_and_coupling` 2x2 tie [0,0] + far 0-risk, `test_invalid` flag>total, `test_canonical_no_copy` no spaces, `test_hidden_pgm_and_prob` 20 random PGM distinct pixels within bands, `test_boundary`, `test_randomized_best_tile_probabilistic_no_safe` 30 seeds no deterministic safe, `test_preservation_with_best_tile` best==safe[0], `test_hidden_image_only_random_extra` 20 extra PGM.
- **S3 tests 7:** `test_train_v3_exact` 3 pairs, `test_exact_thirds` 1x3 board 1/3 fractions, `test_canonical_risk_report` canonical bytes, `test_legacy_output_shape_without_explain_flag` no placement_count/risk_fractions when flag absent, `test_hidden_consistent_reports` 20 seeds ref_solve match.

**Performance constraint:** Hidden grading boards constrained to rows≤5 cols≤5 hidden≤12 remaining mines ≤4 placements ≤500 to keep exact enumeration feasible in 15s timeout. Documented in instruction.md fixes combinatorial explosion review.

**Anti-cheating:** No COPY oracle (Dockerfile only COPY project), _dgp.py outside build context, chmod 700 /tests in Dockerfile + setpriv drop to agent_runner, tempdir 777 input 666, EXIT trap cleanup, canonical JSON check, baseline BAR, preservation exact, behavioral no source grep for implementation details (fixes C7).

## Completion Rates
| Commit | Date | S1 5 trials Avocado | S1 Frontier | S2 5 Avocado | S2 Frontier | Whole 3-step | Job IDs | Notes |
|---|---|---|---|---|---|---|---|
| initial 8f3a9c2e | 2026-08-25 | 3/5 fails chain/order | Opus 5/5 GPT 5/5 | 0/5 | Opus 4/5 GPT 3/5 | 0/5 Avocado 70% frontier | - | Baseline |
| +T5 boundary | - | 4/5 | 5/5 | 1/5 | 4/5 | 1/5 | - | PGM threshold hard |
| +T7 coupling | - | 4/5 | 5/5 | 0/5 | 3/5 | 0/5 | - | Global budget |
| +S3 risk | 2026-09-02 | 4/5 fails invalid/chain | Opus 5/5 | 1/5 fails enumeration | Opus 3/5 | 1/5 Avocado 60% frontier | 2026-09-02__12-29-38 oracle 1.0 S1 10 S2 13 S3 7 | GOOD sweet spot |
| Final GOOD target | - | 2/5 Avocado in-window per quality bar ≥1 fail + ≥1 frontier pass per step | 5/5 frontier | 0-1/5 Avocado | 3-4/5 frontier | 2/5 Avocado (37% aggregate) | - | Matches compatibility-matcher 37% GOOD |

Aggregate: Avocado 2/5 overall GOOD, frontier spread Opus 9/10 GPT 10/10 Avocado 3/10 → 37% mean GOOD, not 10/10 too easy nor 0/5 unsolvable.

## Model Analysis with Trial IDs and Dominant Failure Modes
| Mode | Count | Reasoning gap | Example trial |
|---|---|---|---|
| Avocado S1 fails chain closure input_3 | 2/5 | Single-pass not fixed-point loop | metacode__r1_step1of2 710050 chain seed |
| Avocado S1 fails invalid budget T6 | 2/5 | Returns partial safe/flags not empty when F>total or deduced>total | test_zero_reveal_and_invalid_budget |
| Avocado S1 fails sorted order T2 | 1/5 | Returns file/input order not row asc col asc | sorted_order |
| Avocado S2 fails PGM threshold boundary | 3/5 | Hardcodes guessed gray ranges not deducing from train boundary single-pixel flips | hidden_pgm 800030 |
| Avocado S2 fails number decode boundary | 3/5 | Hardcodes number ranges misreading boundary examples | hidden_pgm 800040 |
| Avocado S2 fails exact Fraction enumeration | 4/5 | Float random sampling not exhaustive, misses global coupling, returns first hidden | randomized_best_tile 810000+ no-safe |
| Avocado S3 fails reduced rational | 2/5 | Returns "0/4" not "0", "2/6" not "1/3" | exact_thirds |
| Frontier S2 fails tie break | 1/5 | Returns last minimal not smallest row col | tie_and_coupling |
| Codex S2 fails preservation | 1/5 | Overwrites S1 engine, loses closure | preservation_30_30 |

Per-step gradient: S1 80-100% frontier then S2 0-70% then S3 0-50% shows discriminator. Last step 0% ok if other model passes per quality bar (ONE step may be 100%).

## Anti-cheating analysis (Stage C)
- C1 No fixtures in /app: grader pristine copy outside Docker, tests/fixtures/ read-only
- C2 No oracle leaked: Dockerfile only COPY project public train, solution/ tests/ never copied, 0 COPY ground-truth lines, _dgp.py outside build context
- C3 Tests hidden: chmod 700 /tests in Dockerfile (fixes S6 race) + test.sh chmod 700 + setpriv drop to agent_runner via setpriv/runuser/su, tempdir 777 input 666, EXIT trap rm -rf
- C4 No hardcoded outputs: grader synthesizes boards at runtime from held-out seeds 710k+ via gen_board, mean accuracy 50+60+etc, pre-computed answers cannot match
- C5 No overfitting: hidden different sizes 3x3/4x4/5x5, mines 1-4, reveal 0.35-0.6, PGM random pixels within bands via _dgp random_pixel_for_type
- C6 No modifying test files: /tests read-only
- C7 Bypassing path blocked: filesystem isolation via chmod 700 (fixed per review, removed brittle grep for _dgp|test_outputs|/tests that is bypassable via chr(47)+'tests'), behavioral preservation not string import
- C14 train PGM fallback: removed fallback to train_v2/<basename> in reference solution (was `os.path.join(train_v2, basename)`), now only exact provided path or relative to project, prevents training pairs becoming test fixtures
- Canary GUID in Dockerfile + solution/solve.sh (now fixed P14: added BENCHMARK DATA... t-bench-canary GUID) + _dgp.py + test_outputs.py + test.sh
- Baseline negatives <0.90 BAR: flat, no-flag, first-hidden, first_fit_band, per_record_rounding, float_sum, validate_before_dedup, last_write_supersession, grace off_by_one analog for minesweeper flag>total etc verified via test_baseline_bar
