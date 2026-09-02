# Minesweeper Risk MT - Project Overview
This directory contains public training data. Hidden grading uses fresh boards from held-out seeds.

## Training Data
`train/` covers deterministic JSON-board deduction. `train_v2/` adds PGM board decoding and best-tile selection. `train_v3/` adds exact rational risk reports.

## Engine path
Implement `/app/project/engine.py` CLI: `python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON`
Stdlib only, deterministic, sorted keys. Output is checked with canonical JSON `sort_keys=True, separators=(',',':')`.
