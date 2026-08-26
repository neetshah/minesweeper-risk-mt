#!/usr/bin/env python3
# CANARY GUID: minesweeper-risk-mt-8f3a9c2e-7b1d-4f2a-9c3e-1a2b3c4d5e6f
import json, os, sys, glob, subprocess, pathlib, hashlib

ENGINE = "/app/project/engine.py"


def run_engine(inp_path, out_path):
    # drop privileges if agent_runner exists?
    cmd = [sys.executable, ENGINE, inp_path, out_path]
    # try setpriv fallback handled outside, but here run directly
    subprocess.run(cmd, check=True, timeout=10)


def test_train_exact_match():
    for i in range(1, 9):
        inp = f"/app/project/train/input_{i}.json"
        exp = f"/app/project/train/output_{i}.json"
        out = f"/tmp/out_{i}.json"
        assert os.path.exists(inp), f"missing {inp}"
        assert os.path.exists(exp)
        run_engine(inp, out)
        with open(out) as f:
            got = json.load(f)
        with open(exp) as f:
            expected = json.load(f)
        assert got.get("safe") == expected.get("safe"), (
            f"train {i} safe mismatch got {got.get('safe')} exp {expected.get('safe')}"
        )
        assert got.get("flags") == expected.get("flags"), f"train {i} flags mismatch"


def test_sorted_order():
    # safe and flags must be sorted row asc col asc
    for i in range(1, 9):
        out = f"/tmp/out_{i}.json"
        if not os.path.exists(out):
            inp = f"/app/project/train/input_{i}.json"
            run_engine(inp, out)
        with open(out) as f:
            data = json.load(f)
        safe = data.get("safe", [])
        flags = data.get("flags", [])
        assert safe == sorted(safe), f"safe not sorted in {i}"
        assert flags == sorted(flags), f"flags not sorted in {i}"


def test_no_s2_artifacts():
    # MC1: no audit.jsonl etc after S1
    assert not os.path.exists("/app/project/audit.jsonl")
    assert not os.path.exists("/app/project/final_matches.json")
    assert not os.path.exists("/app/project/state.json")


def test_anti_cheat_no_forbidden_imports():
    # C18: grep _dgp etc - should not be in agent code
    # This test will fail if agent cheats
    if os.path.exists(ENGINE):
        with open(ENGINE) as f:
            code = f.read()
        for pat in ["_dgp", "test_outputs", "/tests", "__verifier"]:
            assert pat not in code, f"forbidden pattern {pat} in engine"


def test_baseline_bar():
    # flat baseline should be <0.90 accuracy
    inputs = glob.glob("/app/project/train/input_*.json")
    acc = 0
    for inp in inputs:
        exp = inp.replace("input_", "output_")
        with open(exp) as f:
            expected = json.load(f)
        # flat baseline predicts empty
        pred = {"safe": [], "flags": []}
        if pred["safe"] == expected.get("safe") and pred["flags"] == expected.get(
            "flags"
        ):
            acc += 1
    ratio = acc / len(inputs) if inputs else 0
    assert ratio < 0.90, f"BAR flat baseline {ratio} >=0.90"


def test_hidden_dgp_oracle_if_present():
    # if _dgp.py present in /tests (hidden grading), test a few random boards preserve deterministic closure
    dgp_path = "/tests/_dgp.py"
    if not os.path.exists(dgp_path):
        # also check local tests/_dgp.py for local runs
        dgp_path = "/app/../tests/_dgp.py"
        if not os.path.exists(dgp_path):
            # try task root tests/_dgp.py
            dgp_path = "tests/_dgp.py"
            if not os.path.exists(dgp_path):
                return  # skip when not in hidden eval
    # import
    import importlib.util

    spec = importlib.util.spec_from_file_location("_dgp", dgp_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return
    # generate a couple boards using gen_board if available
    if hasattr(mod, "gen_board") and hasattr(mod, "solve_board"):
        for seed in [710000, 710001, 710002]:
            board, _, _ = mod.gen_board(seed, 4, 4, 3, 0.5)
            rows = len(board)
            cols = len(board[0])
            total = 3
            # write temp input
            tmp_in = f"/tmp/hidden_{seed}.json"
            tmp_out = f"/tmp/hidden_{seed}_out.json"
            with open(tmp_in, "w") as f:
                json.dump(
                    {"rows": rows, "cols": cols, "total_mines": total, "board": board},
                    f,
                )
            run_engine(tmp_in, tmp_out)
            with open(tmp_out) as f:
                got = json.load(f)
            # expected via oracle
            exp_safe, exp_flags, _, _ = mod.solve_board(rows, cols, total, board)
            # solve_board returns safe, flags, best, probs ; for S1 we only care safe/flags
            # exp_safe from solve_board is already sorted list? Our solve_board returns sorted lists
            # but deterministic_closure returns set
            # Ensure exact match for safe/flags (S1 part of S2)
            # For S1 engine, best not present, compare safe/flags only
            assert sorted(got.get("safe", [])) == sorted(exp_safe), (
                f"hidden seed {seed} safe mismatch"
            )
            assert sorted(got.get("flags", [])) == sorted(exp_flags), (
                f"hidden seed {seed} flags mismatch"
            )
