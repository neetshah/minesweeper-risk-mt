#!/bin/bash
# CANARY GUID: minesweeper-risk-mt-8f3a9c2e-7b1d-4f2a-9c3e-1a2b3c4d5e6f
set -e
PROJECT_DIR=/app/project
mkdir -p $PROJECT_DIR
cat > $PROJECT_DIR/engine.py << 'PY'
#!/usr/bin/env python3
import sys, json

def neighbors(r,c,rows,cols):
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr==0 and dc==0:
                continue
            nr, nc = r+dr, c+dc
            if 0<=nr<rows and 0<=nc<cols:
                yield nr,nc

def deterministic_closure(rows, cols, board, pre_flags):
    safe=set()
    flags=set()
    changed=True
    while changed:
        changed=False
        for r in range(rows):
            for c in range(cols):
                v=board[r][c]
                if not isinstance(v,int) or v<0 or v>8:
                    continue
                flagged=0
                hidden=[]
                for nr,nc in neighbors(r,c,rows,cols):
                    if (nr,nc) in pre_flags or (nr,nc) in flags:
                        flagged+=1
                    else:
                        b=board[nr][nc]
                        if b==-1 and (nr,nc) not in safe:
                            hidden.append((nr,nc))
                need=v-flagged
                if need==0 and hidden:
                    for h in hidden:
                        if h not in safe:
                            safe.add(h)
                            changed=True
                elif need==len(hidden) and need>0:
                    for h in hidden:
                        if h not in flags:
                            flags.add(h)
                            changed=True
    return safe, flags

def main():
    if len(sys.argv)!=3:
        print("usage: engine.py INPUT OUTPUT", file=sys.stderr)
        sys.exit(2)
    inp=sys.argv[1]
    outp=sys.argv[2]
    with open(inp) as f:
        data=json.load(f)
    rows=data["rows"]; cols=data["cols"]; total=data["total_mines"]; board=data["board"]
    pre_flags={(r,c) for r in range(rows) for c in range(cols) if board[r][c]=="F"}
    if len(pre_flags)>total:
        res={"safe":[],"flags":[]}
        with open(outp,"w") as out:
            json.dump(res,out, sort_keys=True, separators=(',',':'))
        return
    safe, flags = deterministic_closure(rows, cols, board, pre_flags)
    res={"safe":[list(x) for x in sorted(safe)],"flags":[list(x) for x in sorted(flags)]}
    with open(outp,"w") as out:
        json.dump(res,out, sort_keys=True, separators=(',',':'))

if __name__=="__main__":
    main()
PY
chmod +x $PROJECT_DIR/engine.py
echo "Step1 engine built"
