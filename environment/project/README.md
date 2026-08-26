# Minesweeper Risk MT - Project Overview
This directory contains public training data. Hidden grading uses fresh boards from held-out seeds 710k+.

## Notes for task authoring (do NOT include in final instruction.md)
Image mapping thresholds are pinned by train_v2 boundary PGMs. Do not leak exact gray ranges in task instruction - let model deduce from examples.

## Engine path
Implement `/app/project/engine.py` CLI: `python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON`
Stdlib only, deterministic, sorted keys. Output will be checked with canonical JSON `sort_keys=True, separators=(',',':')` for hash chain.

