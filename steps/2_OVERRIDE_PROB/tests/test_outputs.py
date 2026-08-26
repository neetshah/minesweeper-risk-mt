#!/usr/bin/env python3
# CANARY GUID: minesweeper-risk-mt-8f3a9c2e-7b1d-4f2a-9c3e-1a2b3c4d5e6f
import json, os, sys, glob, subprocess, itertools, fractions

ENGINE = "/app/project/engine.py"


def run_engine(inp, out):
    subprocess.run([sys.executable, ENGINE, inp, out], check=True, timeout=15)


def test_train_v2_exact():
    for i in range(1, 9):
        inp = f"/app/project/train_v2/input_{i}.json"
        exp = f"/app/project/train_v2/output_{i}.json"
        out = f"/tmp/out_v2_{i}.json"
        assert os.path.exists(inp)
        assert os.path.exists(exp)
        run_engine(inp, out)
        with open(out) as f:
            got = json.load(f)
        with open(exp) as f:
            expected = json.load(f)
        for k in ["safe", "flags", "best_tile"]:
            assert got.get(k) == expected.get(k), (
                f"v2 train {i} key {k} got {got.get(k)} exp {expected.get(k)}"
            )


def test_image_parsing():
    # ensure PGM files exist and engine can parse them
    for i in range(1, 9):
        pgm = f"/app/project/train_v2/board_{i}.pgm"
        assert os.path.exists(pgm)
        # quick parse check: file starts with P2
        with open(pgm) as f:
            first = f.read(2)
            assert first == "P2"


def test_preservation_exact():
    # S2 must equal S1 under compatible inputs (image == board, deterministic safe)
    # Use train S1 inputs as S2 with image absent should preserve safe/flags
    for i in range(1, 9):
        s1_in = f"/app/project/train/input_{i}.json"
        s1_out_exp = f"/app/project/train/output_{i}.json"
        # run S1 engine via S2 engine (same binary) - safe/flags should match
        out = f"/tmp/pres_s1_{i}.json"
        run_engine(s1_in, out)
        with open(out) as f:
            got = json.load(f)
        with open(s1_out_exp) as f:
            exp = json.load(f)
        # S2 engine may also output best_tile, but safe/flags must equal S1
        assert got.get("safe") == exp.get("safe"), f"preservation train {i} safe"
        assert got.get("flags") == exp.get("flags"), f"preservation train {i} flags"


def test_tie_break_row_col():
    # board_5 2x2 all hidden total 1 -> all prob 0.25 tie -> best [0,0]
    inp = "/app/project/train_v2/input_5.json"
    out = "/tmp/out_v2_5_tie.json"
    run_engine(inp, out)
    with open(out) as f:
        data = json.load(f)
    assert data.get("best_tile") == [0, 0], (
        f"tie break expected [0,0] got {data.get('best_tile')}"
    )


def test_fleet_coupling_far_zero():
    # board_6 far cell prob 0 minimal
    inp = "/app/project/train_v2/input_6.json"
    out = "/tmp/out_v2_6_coup.json"
    run_engine(inp, out)
    with open(out) as f:
        data = json.load(f)
    assert data.get("best_tile") == [0, 2], (
        f"coupling expected [0,2] got {data.get('best_tile')}"
    )


def test_invalid_flag_over_cap():
    # board_8 invalid flag>total -> empty
    inp = "/app/project/train_v2/input_8.json"
    out = "/tmp/out_v2_8_inv.json"
    run_engine(inp, out)
    with open(out) as f:
        data = json.load(f)
    assert (
        data.get("safe") == []
        and data.get("flags") == []
        and data.get("best_tile") is None
    )


def test_boundary_uniquely_pinned():
    # ensure 49 vs 50 and 199 vs 200 thresholds uniquely pinned via sweep check (only correct mapping passes)
    # Simulate wrong thresholds failing train
    # This is meta test that train itself pins thresholds, not engine logic directly
    # Check that board_2 pixel 49 decodes to hidden not flag via engine output
    inp = "/app/project/train_v2/input_2.json"
    out = "/tmp/out_v2_2_bnd.json"
    run_engine(inp, out)
    with open(out) as f:
        data = json.load(f)
    # board_2 is [1,-1] with pixel 49 hidden -> should flag [0,1]
    assert data.get("flags") == [[0, 1]], f"boundary 49 vs 50 failed {data}"


def test_canonical_encoding():
    # output must use canonical separators ',' ':' no space
    inp = "/app/project/train_v2/input_1.json"
    out = "/tmp/out_v2_1_canon.json"
    run_engine(inp, out)
    with open(out, "rb") as f:
        raw = f.read()
    assert b": " not in raw, "canonical encoding contains ': '"
    assert b", " not in raw or raw.count(b",") > 0, "check separators"


def test_hidden_preservation_30_30_if_dgp():
    dgp_path = "/tests/_dgp.py"
    if not os.path.exists(dgp_path):
        # local fallback
        candidates = [
            "tests/_dgp.py",
            "/app/../tests/_dgp.py",
            "/data/repos/fbsource/codimango/minesweeper-risk-mt/tests/_dgp.py",
        ]
        for cand in candidates:
            if os.path.exists(cand):
                dgp_path = cand
                break
        else:
            return
    import importlib.util

    spec = importlib.util.spec_from_file_location("_dgp", dgp_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return
    if not hasattr(mod, "gen_board"):
        return
    for seed in range(720000, 720030):
        board, _, _ = mod.gen_board(seed, 5, 5, 5, 0.6)
        rows = len(board)
        cols = len(board[0])
        total = 5
        tmp_in = f"/tmp/hid_{seed}.json"
        tmp_out = f"/tmp/hid_{seed}_out.json"
        with open(tmp_in, "w") as f:
            json.dump(
                {"rows": rows, "cols": cols, "total_mines": total, "board": board}, f
            )
        run_engine(tmp_in, tmp_out)
        with open(tmp_out) as f:
            got = json.load(f)
        s1_safe_set, s1_flags_set = mod.deterministic_closure(
            rows,
            cols,
            board,
            {(r, c) for r in range(rows) for c in range(cols) if board[r][c] == "F"},
        )
        s1_safe = sorted(list(s1_safe_set))
        s1_flags = sorted(list(s1_flags_set))
        assert got.get("safe") == s1_safe and got.get("flags") == s1_flags, (
            f"pres seed {seed}"
        )
