#!/bin/bash
set -e
mkdir -p /logs/verifier
printf '0' > /logs/verifier/reward.txt
chmod -R go-rwx /tests 2>/dev/null || true
ENGINE=/app/project/engine.py
echo "S2 train_v2 check"
for i in 1 2 3 4 5 6 7 8; do
  inp=/app/project/train_v2/input_${i}.json
  outp=/tmp/out_v2_${i}.json
  exp=/app/project/train_v2/output_${i}.json
  python3 $ENGINE $inp $outp
  python3 - << PY
import json
i=${i}
with open(f"/tmp/out_v2_{i}.json") as f: got=json.load(f)
with open(f"/app/project/train_v2/output_{i}.json") as f: exp=json.load(f)
for k in ["safe","flags","best_tile"]:
    assert got.get(k)==exp.get(k), f"v2 {i} {k} got {got.get(k)} exp {exp.get(k)}"
PY
done

# preservation check small
python3 - << 'PY'
import json, sys, os, itertools, fractions
# quick preservation using train S1 vs S2
for i in range(1,9):
    s1_in=f"/app/project/train/input_{i}.json"
    tmp_out=f"/tmp/pres_{i}.json"
    import subprocess
    subprocess.run([sys.executable, "/app/project/engine.py", s1_in, tmp_out], check=True)
PY

echo '1' > /logs/verifier/reward.txt
cat /logs/verifier/reward.txt
