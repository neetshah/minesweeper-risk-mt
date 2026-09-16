#!/bin/bash
# Smoke test for the top-level golden (solution/solve.sh).
# Runs the golden on the inline-comment PGM contract (same behavior as
# test_hidden_pgm_inline_comments) plus the no-silent-fallback rule:
# a present-but-unparseable board_image_pgm must error, never solve JSON.
# No network, no docker, stdlib only. Safe to run in CI.
set -euo pipefail

TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Build the golden into a scratch project dir with fixtures beside it
# (threshold deduction scans dirname(engine)/train_v2, same as graded runs).
mkdir -p "$TMP/project/train_v2"
cp "$TASK_DIR/environment/project/train_v2/input_1.json" \
   "$TASK_DIR/environment/project/train_v2/board_1.pgm" \
   "$TMP/project/train_v2/"
sed 's|^PROJECT_DIR=/app/project|PROJECT_DIR='"$TMP"'/project|' \
    "$TASK_DIR/solution/solve.sh" > "$TMP/build_golden.sh"
bash "$TMP/build_golden.sh" > /dev/null
ENGINE="$TMP/project/engine.py"

pass=0
fail=0

# Case 1: trailing '#' comments on header and pixel lines must be stripped;
# PGM (all-zero 2x2) is authoritative over the JSON board (which alone would
# flag [0,1]), so the engine must output empty safe/flags with null best.
cat > "$TMP/decoy.pgm" <<'PGM'
P2 # image header
2 2 # dims
255 # maxval
110 110 # row0
110 110 # row1
PGM
cat > "$TMP/in1.json" <<'JSON'
{"rows": 2, "cols": 2, "total_mines": 1, "board": [[1, -1], [1, 1]], "board_image_pgm": "__PGM__"}
JSON
sed -i "s|__PGM__|$TMP/decoy.pgm|" "$TMP/in1.json"
python3 "$ENGINE" "$TMP/in1.json" "$TMP/out1.json"
expected='{"best_tile":null,"flags":[],"safe":[]}'
if [ "$(cat "$TMP/out1.json")" = "$expected" ]; then
    echo "PASS inline-comment PGM authoritative"
    pass=$((pass + 1))
else
    echo "FAIL inline-comment PGM authoritative: got $(cat "$TMP/out1.json") want $expected"
    fail=$((fail + 1))
fi

# Case 2: corrupt PGM with a valid JSON board must fail, not fall back.
echo "NOT A PGM AT ALL" > "$TMP/bad.pgm"
cat > "$TMP/in2.json" <<'JSON'
{"rows": 2, "cols": 2, "total_mines": 1, "board": [[1, -1], [1, 1]], "board_image_pgm": "__PGM__"}
JSON
sed -i "s|__PGM__|$TMP/bad.pgm|" "$TMP/in2.json"
if python3 "$ENGINE" "$TMP/in2.json" "$TMP/out2.json" 2>/dev/null; then
    echo "FAIL corrupt PGM: engine succeeded (silent JSON fallback)"
    fail=$((fail + 1))
else
    echo "PASS corrupt PGM errors (no silent fallback)"
    pass=$((pass + 1))
fi

echo "smoke: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
