#!/usr/bin/env python3
# CANARY GUID: minesweeper-risk-mt-8f3a9c2e-7b1d-4f2a-9c3e-1a2b3c4d5e6f
"""
Oracle and DGP for hidden grading - outside Docker build context per C2.
Generates boards from held-out seeds 710000+ (50 streams) + 30+30 preservation n=200.
Uses same deterministic_closure + exact enumeration as reference.
"""

import random, json, fractions, itertools, os, hashlib
from pathlib import Path


def neighbors(r, c, rows, cols):
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc


def deterministic_closure(rows, cols, board, pre_flags):
    safe = set()
    flags = set()
    changed = True
    while changed:
        changed = False
        for r in range(rows):
            for c in range(cols):
                v = board[r][c]
                if not isinstance(v, int) or v < 0 or v > 8:
                    continue
                flagged = 0
                hidden = []
                for nr, nc in neighbors(r, c, rows, cols):
                    if (nr, nc) in pre_flags or (nr, nc) in flags:
                        flagged += 1
                    else:
                        b = board[nr][nc]
                        if b == -1 and (nr, nc) not in safe:
                            hidden.append((nr, nc))
                need = v - flagged
                if need == 0 and hidden:
                    for h in hidden:
                        if h not in safe:
                            safe.add(h)
                            changed = True
                elif need == len(hidden) and need > 0:
                    for h in hidden:
                        if h not in flags:
                            flags.add(h)
                            changed = True
    return safe, flags


def solve_board(rows, cols, total, board):
    pre_flags = {(r, c) for r in range(rows) for c in range(cols) if board[r][c] == "F"}
    if len(pre_flags) > total:
        return [], [], None, {}
    safe, flags = deterministic_closure(rows, cols, board, pre_flags)
    all_flags = pre_flags | flags
    remaining = total - len(all_flags)
    hidden_remain = [
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if board[r][c] == -1 and (r, c) not in safe and (r, c) not in all_flags
    ]
    if safe:
        best = sorted(safe)[0]
        return sorted(safe), sorted(flags), list(best), {}
    if not hidden_remain:
        return sorted(safe), sorted(flags), None, {}
    if remaining < 0 or remaining > len(hidden_remain):
        return sorted(safe), sorted(flags), None, {}
    revealed = [
        (r, c, board[r][c])
        for r in range(rows)
        for c in range(cols)
        if isinstance(board[r][c], int) and 0 <= board[r][c] <= 8
    ]
    valid = []
    for combo in itertools.combinations(hidden_remain, remaining):
        cs = set(combo)
        ok = True
        for r, c, v in revealed:
            cnt = sum(
                1
                for nr, nc in neighbors(r, c, rows, cols)
                if (nr, nc) in all_flags or (nr, nc) in cs
            )
            if cnt != v:
                ok = False
                break
        if ok:
            valid.append(cs)
    if not valid:
        return sorted(safe), sorted(flags), None, {}
    totalPlac = len(valid)
    prob_counts = {h: 0 for h in hidden_remain}
    for vp in valid:
        for h in vp:
            prob_counts[h] += 1
    probs = {
        f"{r},{c}": float(fractions.Fraction(prob_counts[(r, c)], totalPlac))
        for r, c in hidden_remain
    }
    min_prob = min(prob_counts[h] / totalPlac for h in hidden_remain)
    cands = [h for h in hidden_remain if prob_counts[h] / totalPlac == min_prob]
    best = sorted(cands)[0]
    return sorted(safe), sorted(flags), list(best), probs


def gen_board(seed, rows=5, cols=5, mines=5, reveal_prob=0.5):
    random.seed(seed)
    # place mines
    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    mine_cells = set(random.sample(all_cells, mines))
    # build full numbers
    full = [[0] * cols for _ in range(rows)]
    for r, c in all_cells:
        if (r, c) in mine_cells:
            full[r][c] = "M"
        else:
            cnt = sum(
                1 for nr, nc in neighbors(r, c, rows, cols) if (nr, nc) in mine_cells
            )
            full[r][c] = cnt
    # hide
    board = [[-1] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if random.random() < reveal_prob and full[r][c] != "M":
                board[r][c] = full[r][c]
            else:
                board[r][c] = -1
    # ensure at least one number revealed
    has_number = False
    for rr in range(rows):
        for cc in range(cols):
            if isinstance(board[rr][cc], int):
                has_number = True
                break
        if has_number:
            break
    if not has_number:
        # reveal a random safe
        candidates = [
            (r, c) for r in range(rows) for c in range(cols) if full[r][c] != "M"
        ]
        if candidates:
            r, c = random.choice(candidates)
            board[r][c] = full[r][c]
    return board, full, mine_cells


def canonical_json(obj):
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def hash_chain(prev_hash, obj):
    data = canonical_json(obj)
    h = (
        hashlib.sha256(prev_hash.encode() + data).hexdigest()
        if isinstance(prev_hash, str)
        else hashlib.sha256(data).hexdigest()
    )
    return h


# hidden generation demo
if __name__ == "__main__":
    # generate 50 hidden S1 boards seed 710000+
    for i, seed in enumerate(range(710000, 710050)):
        rows, cols, ms = 5, 5, 5
        board, _, _ = gen_board(seed, rows, cols, ms, 0.5)
        safe, flags, _, _ = solve_board(rows, cols, ms, board)[
            :4
        ]  # Actually solve_board returns safe flags best probs but we need s1 only
        # safe flags for S1
        print(f"seed {seed} safe {len(safe)} flags {len(flags)}")
    # preservation 30+30 n=200
    for seed in range(720000, 720030):
        board, _, _ = gen_board(seed, 5, 5, 5, 0.5)
        s1_safe, s1_flags = (
            deterministic_closure(
                5,
                5,
                board,
                {(r, c) for r in range(5) for c in range(5) if board[r][c] == "F"},
            )
            if True
            else (set(), set())
        )
        # preservation exact equality tested elsewhere
