import numpy as np, heapq, json, math, itertools, random

mask = np.load("street-mask2.npy")
H, W = mask.shape
S = 3
gh, gw = H//S, W//S
grid = np.zeros((gh, gw), bool)
for gy in range(gh):
    for gx in range(gw):
        grid[gy, gx] = mask[gy*S:gy*S+S, gx*S:gx*S+S].any()
print("grid nodes:", int(grid.sum()))

NBR = [(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414),(-1,1,1.414),(1,-1,1.414),(1,1,1.414)]
def dijkstra(start, goal, penalty=None):
    dist = {start: 0.0}; prev = {}; pq = [(0.0, start)]
    while pq:
        d, cur = heapq.heappop(pq)
        if cur == goal: break
        if d > dist.get(cur, 1e18): continue
        cy, cx = cur
        for dy, dx, c in NBR:
            ny, nx = cy+dy, cx+dx
            if 0 <= ny < gh and 0 <= nx < gw and grid[ny, nx]:
                nd = d + c * (penalty[ny, nx] if penalty is not None else 1.0)
                if nd < dist.get((ny, nx), 1e18):
                    dist[(ny, nx)] = nd; prev[(ny, nx)] = cur; heapq.heappush(pq, (nd, (ny, nx)))
    if goal not in prev and goal != start: return None
    p = [goal]
    while p[-1] != start: p.append(prev[p[-1]])
    return p[::-1]

def plen(p): return sum(math.hypot(a[0]-b[0], a[1]-b[1]) for a, b in zip(p, p[1:]))

def simplify(pts, eps=1.6):
    if len(pts) < 3: return pts
    def dp(lo, hi, keep):
        ax, ay = pts[lo]; bx, by = pts[hi]; mx, mi = -1, -1
        for i in range(lo+1, hi):
            dx, dy = bx-ax, by-ay; L = math.hypot(dx, dy) or 1
            d = abs(dy*(pts[i][0]-ax) - dx*(pts[i][1]-ay)) / L
            if d > mx: mx, mi = d, i
        if mx > eps: dp(lo, mi, keep); keep.add(mi); dp(mi, hi, keep)
    keep = {0, len(pts)-1}; dp(0, len(pts)-1, keep)
    return [pts[i] for i in sorted(keep)]

def snap(y, x):
    best, bd = None, 1e9
    for yy in range(max(0,y-10), min(gh,y+10)):
        for xx in range(max(0,x-10), min(gw,x+10)):
            if grid[yy, xx]:
                d = (yy-y)**2 + (xx-x)**2
                if d < bd: bd, best = d, (yy, xx)
    return best

random.seed(20260803)
cand = [(x, y) for x in range(120, 1180, 85) for y in range(120, 1460, 100)]
pts = [snap(y//S, x//S) for x, y in cand]
pts = [p for p in pts if p]
random.shuffle(pts)

# (diffLo, diffHi, key, penalty, radius, manLo, manHi, minDiag) - man in grid units (x3 = px)
# added lenHi: cap on the SHORT route's actual length (grid units) so trips read simply
BANDS = [(0.30, 0.60, 'E', 7.0, 4,  45, 105, 110, 150),
         (0.18, 0.32, 'M', 6.0, 5, 100, 200, 280, 330),
         (0.10, 0.18, 'H', 4.0, 5, 180, 300, 430, 560),
         (0.030, 0.10, 'X', 2.2, 4, 250, 430, 580, 10000)]
rounds = {b[2]: [] for b in BANDS}
tried = 0
pairs = list(itertools.combinations(range(len(pts)), 2))
random.shuffle(pairs)
for i, j in pairs:
    if all(len(rounds[k]) >= 7 for b in BANDS for k in [b[2]]): break
    if tried > 1600: break
    a1, a2 = pts[i], pts[j]
    man = abs(a1[0]-a2[0]) + abs(a1[1]-a2[1])
    need = [b for b in BANDS if len(rounds[b[2]]) < 7 and b[5] <= man <= b[6]]
    if not need: continue
    tried += 1
    p1 = dijkstra(a1, a2)
    if not p1: continue
    for lo, hi, k, PEN, R, mLo, mHi, minDiag, lenHi in need:
        pen = np.ones((gh, gw))
        for (py, px_) in p1[3:-3]:
            pen[max(0,py-R):py+R+1, max(0,px_-R):px_+R+1] = PEN
        p2 = dijkstra(a1, a2, pen)
        if not p2: continue
        q1, q2 = p1, p2
        m1, m2 = plen(q1), plen(q2)
        if m2 < m1: q1, q2, m1, m2 = q2, q1, m2, m1
        diff = (m2 - m1) / m1
        if m1 > lenHi: continue
        s1 = set(q1); shared = sum(1 for c in q2 if c in s1) / len(q2)
        if shared > (0.30 if k == 'E' else 0.40): continue
        if lo <= diff < hi:
            allp = q1 + q2
            dx = (max(p[1] for p in allp) - min(p[1] for p in allp)) * S
            dy = (max(p[0] for p in allp) - min(p[0] for p in allp)) * S
            if math.hypot(dx, dy) < minDiag: continue
            sa = [(int(x*S+S/2), int(y*S+S/2)) for y, x in simplify(q1)]
            sb = [(int(x*S+S/2), int(y*S+S/2)) for y, x in simplify(q2)]
            rounds[k].append({"short": sa, "long": sb, "lenShort": round(m1*S), "lenLong": round(m2*S), "diff": round(diff, 3)})
            break

print("tried:", tried, {k: len(v) for k, v in rounds.items()})
json.dump(rounds, open("routes-lib2.json", "w"))
