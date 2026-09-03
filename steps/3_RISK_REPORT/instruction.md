# Task - Step3 Exact Risk Report

Extend the same `/app/project/engine.py` from Step2. The CLI is unchanged:
```
python3 /app/project/engine.py INPUT_JSON OUTPUT_JSON
```

Step3 preserves every Step1 and Step2 behavior. Add one opt-in reporting mode:
when input JSON contains `"explain_risk": true`, include these additional output
keys:

```json
{
  "placement_count": 0,
  "risk_fractions": {"r,c": "n/d"}
}
```

Rules:
- `safe`, `flags`, and `best_tile` are exactly the same as Step2.
- If `board_image_pgm` is present, decode and solve that PGM board exactly as
  Step2 did, including when the JSON `board` is all hidden.
- `placement_count` is the number of global mine placements consistent with all revealed clues, input flags, deduced flags, and `total_mines`.
- `risk_fractions` maps every remaining hidden candidate tile to its exact mine probability across those placements, encoded as a reduced rational string. Use `"0"` and `"1"` for whole numbers, and `"n/d"` for proper fractions.
- If deterministic safe tiles exist, `best_tile` is still the first safe tile and the risk report is empty: `placement_count: 0`, `risk_fractions: {}`.
- If input flags or input flags plus deduced flags exceed `total_mines`, return empty safe/flags, `best_tile: null`, `placement_count: 0`, and `risk_fractions: {}`.
- If no globally consistent placement exists after deterministic closure, keep in-budget deterministic safe/flags, set `best_tile: null`, `placement_count: 0`, and `risk_fractions: {}`.
- With `"explain_risk": true`, emit `risk_fractions` instead of the Step2 float `probabilities` key.
- Without `"explain_risk": true`, do not add `placement_count` or `risk_fractions`; Step2 output shape remains valid.

Output must be canonical JSON using `sort_keys=True, separators=(',',':')`.
Read `/app/project/train_v3/` for public examples.
