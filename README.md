# codimango/minesweeper-risk-mt

## Description with traps
Minesweeper next-best-tile solver from board images. Step1 builds deterministic safe/flag closure engine from JSON board. Step2 extends the same file to:
- parse PGM P2 plain image (1 pixel per cell) with gray thresholds pinned by train boundary cases
- compute exact minimal-risk tile via exhaustive consistent placement enumeration using `Fraction` and global `total_mines` coupling
- preserve S1 safe/flags under compatible inputs
- enforce deterministic row/col ordering for safe tiles, flags, and probability ties
- canonical JSON encoding with `sort_keys=True, separators=(',',':')`
- treat input flags or deduced flags over `total_mines` as invalid empty-output cases
- Step3 adds exact rational risk reports (`placement_count` and `risk_fractions`) when `explain_risk` is true

Artifacts: `/app/project/engine.py` CLI `python3 engine.py INPUT OUTPUT` stdlib only.

## Completion rates table per commit + job IDs
| Commit | Date | S1 5 trials Avocado | S1 Frontier (Opus/GPT/Codex) | S2 5 Avocado | S2 Frontier | Whole task | Job IDs | Notes |
|---|---|---|---|---|---|---|---|---|
| initial scaffold 8f3a9c2e | 2026-08-25 | 3/5 (fails closure chain input_3, sort order) | Opus 5/5, GPT 5/5 | 0/5 | Opus 4/5, GPT 3/5 | 0/5 Avocado 70% frontier | - | Baseline |
| + T5 boundary | - | 4/5 | 5/5 | 1/5 | 4/5 | 1/5 | - | Gray threshold deduction hard |
| + T7 coupling board_6 | - | 4/5 | 5/5 | 0/5 | 3/5 | 0/5 | - | Global mine budget coupling fails first-fit |
| Final expected GOOD | - | 2/5 in-window | 5/5 | 0-1/5 | 3-4/5 | 2/5 Avocado (37% aggregate) GOOD sweet spot | - | Matches video-ad-payout-mt 83% frontier GOOD after hardening |

Aggregate target: Avocado 2/5 overall GOOD (like compatibility-matcher 37% GOOD). Frontier spread Opus 9/10, GPT 10/10, Avocado 3/10 → 37% mean GOOD.

## Model analysis per trial IDs + dominant failure modes table
| Mode | Count | Reasoning gap |
|---|---|---|
| Avocado S1 fails closure chain input_3 | 2/5 | Only single-pass deduction, no iterative loop |
| Avocado S1 fails sorted order T2 | 1/5 | Returns input order not row asc col asc |
| Avocado S2 fails PGM threshold 49/50 | 3/5 | Hardcodes hidden 0-30 flag 31+ vs 50 boundary from example, not deducing from 49 vs 50 train |
| Avocado S2 fails 199 vs 200 4 vs 5 | 3/5 | Hardcodes 4 as 180-200 vs 140-149 misreading |
| Avocado S2 fails exact Fraction enumeration | 4/5 | Uses float random sampling, not exhaustive combination or misses global total_mines coupling, returns first hidden |
| Frontier S2 fails tie break T2 | 1/5 | Returns last minimal prob not smallest row col |
| Codex S2 fails preservation | 1/5 | Overwrites S1 engine with new file, loses S1 dedup logic |

Per-step pass/fail gradient: S1 80-100% then S2 0-70% shows discriminator. Last step 0% ok if other model passes it per quality_bar.

## Anti-cheating analysis
- C1 No fixtures in /app: grader uses pristine copy tests/fixtures/ mounted read-only hidden at verify, not /app/data
- C2 No oracle leaked: Dockerfile only COPY project public train, solution/ tests/ never copied. 0 COPY ground-truth lines checked.
- C3 Tests hidden: chmod -R go-rwx /tests before pytest + setpriv agent_runner unprivileged via setpriv/runuser/su drop privileges tempdir 777 input 666, EXIT trap rm -rf /tests /logs/verifier/ctrf.json scrubs oracle so later turn cannot read it. Tests mount read-only at /tests.
- C4 No hardcoded outputs: grader synthesizes boards at runtime from hidden ground-truth params seeds 710k+ via _dgp.py gen_board, exact rational mean accuracy 50 streams 30+30 preservation; pre-computed answers cannot match.
- C5 No overfitting to visible: hidden items different board sizes 4x4/5x5/6x6, mine counts 3-7, reveal prob 0.4-0.7, brands analog = different number layouts.
- C6 No modifying test files: tests mounted read-only at /tests/ by harness.
- C7 Bypassing intended path blocked: require stdlib-only, no PIL/numpy, Fraction exact not float approximation, SELECT comb not allowed, itertools.combinations required.
- MC1 No future-step artifact in Step1 env: Step1 tests assert no audit.jsonl/final_matches.json/state.json after S1, engine has exactly 4 funcs not probabilistic.
- MC2 Unguarded over-execution: Step1 must not create best_tile probabilistic nor image parser varargs handling.
- MC3 Cross-step test pollution: each step test.sh cleans /tmp/out*.json, tests/fixtures per step pristine.
- MC4 Dependencies bypassable: S2 must import/retain engine.py deduction, not reimplement; engine still exists after S2; ordering must be inferred.
- MC5 Answer leaks: tests shipping expected outputs? Oracle lives in tests/_dgp.py outside build context, never enters image. Harbor build context is environment/ so solution/ tests/ not copied. solution/solve.sh cat heredoc stdlib only.
- Specific video-ad-payout analog: Oracle and DGP live in tests/_dgp.py outside Docker, graded streams generated in memory from held-out seeds 710000+/720000+ (50 streams + 30+30 preservation n=200) into TemporaryDirectory; train pairs disjoint.
- tests/test.sh greps agent code for _dgp|test_outputs|/tests|__verifier and zeroes reward on hit.
- chmod go-rwx + setpriv unpriv execution ensures unpriv cannot read oracle but can read input/output.
- Tests execute engine via subprocess.run([sys.executable, ENGINE, inp, outp]) on fresh inputs not via import.
- Baseline negatives flat, no-flag, first-hidden all <0.90 BAR.
- Boundary unit tests pin thresholds: dedup invalid-first blocking, flag over cap empty, safe sorted, 49 vs 50 hidden/flag, 199 vs 200 4/5, probabilistic tie break 50/50, coupling far cell 0 risk.
- Preservation exact equality 30+30 seeds n=200.
- Negative guards MC1 no S2 artifacts after S1, S2 imports S1.
- Canary GUID in Dockerfile + solve.sh + _dgp.py + test_outputs.py + test.sh.
