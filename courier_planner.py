"""Courier planning capstone: sorting, knapsack DP, Dijkstra, and route approximation."""
from __future__ import annotations
import argparse, csv, heapq, json, math, random, statistics, time
from pathlib import Path
from typing import Any


def merge_sort(items: list[dict[str, Any]], key):
    """Stable O(n log n) merge sort."""
    if len(items) < 2:
        return items[:]
    mid = len(items) // 2
    left, right = merge_sort(items[:mid], key), merge_sort(items[mid:], key)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]): out.append(left[i]); i += 1
        else: out.append(right[j]); j += 1
    return out + left[i:] + right[j:]


def prioritize(parcels):
    return merge_sort(parcels, lambda p: (p["deadline"], -p["priority"], p["id"]))


def knapsack(parcels, capacity):
    """0/1 knapsack DP. Returns chosen parcels and the full capacity DP row."""
    if capacity < 0: raise ValueError("capacity must be non-negative")
    if any(p["weight"] <= 0 for p in parcels): raise ValueError("parcel weights must be positive")
    # dp[i][c] is maximum value using first i parcels and capacity c.
    n = len(parcels)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, p in enumerate(parcels, 1):
        for c in range(capacity + 1):
            dp[i][c] = dp[i - 1][c]
            if p["weight"] <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - p["weight"]] + p["value"])
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            p = parcels[i - 1]; chosen.append(p); c -= p["weight"]
    chosen.reverse()
    return chosen, dp[n][capacity], dp


def build_graph(points, roads=None):
    """Create weighted undirected graph; default is a complete Euclidean graph."""
    ids = [p["id"] for p in points]
    coords = {p["id"]: (p["x"], p["y"]) for p in points}
    graph = {node: {} for node in ids}
    if roads:
        for a, b, weight in roads:
            if a not in graph or b not in graph or weight <= 0: raise ValueError("invalid road edge")
            graph[a][b] = graph[b][a] = float(weight)
    else:
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                graph[a][b] = graph[b][a] = math.dist(coords[a], coords[b])
    return graph


def dijkstra(graph, source):
    distances = {node: math.inf for node in graph}; previous = {node: None for node in graph}
    distances[source] = 0.0; queue = [(0.0, source)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances[node]: continue
        for neighbor, weight in graph[node].items():
            candidate = distance + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate; previous[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))
    return distances, previous


def path_to(previous, target):
    path, node = [], target
    while node is not None: path.append(node); node = previous[node]
    return list(reversed(path))


def nearest_neighbor_route(graph, depot, stops):
    """TSP approximation using shortest-path distances as metric edge costs."""
    remaining = set(stops); route = [depot]; total = 0.0; current = depot
    all_dist, all_prev = {}, {}
    for node in graph:
        all_dist[node], all_prev[node] = dijkstra(graph, node)
    legs = []
    while remaining:
        nxt = min(remaining, key=lambda node: (all_dist[current][node], node))
        d = all_dist[current][nxt]; legs.append({"from": current, "to": nxt, "distance": d, "path": path_to(all_prev[current], nxt)})
        total += d; route.append(nxt); remaining.remove(nxt); current = nxt
    if current != depot:
        d = all_dist[current][depot]; legs.append({"from": current, "to": depot, "distance": d, "path": path_to(all_prev[current], depot)})
        total += d; route.append(depot)
    return route, total, legs


def plan(data):
    parcels, capacity, depot = data["parcels"], data["capacity"], data["depot"]
    ordered = prioritize(parcels)
    selected, value, dp = knapsack(ordered, capacity)
    graph = build_graph(data["points"], data.get("roads"))
    stops = [p["destination"] for p in selected]
    if any(s not in graph for s in stops) or depot not in graph: raise ValueError("every destination and depot must exist in points")
    route, distance, legs = nearest_neighbor_route(graph, depot, stops)
    return {"priority_order": [{"id": p["id"], "deadline": p["deadline"], "priority": p["priority"]} for p in ordered],
            "capacity": capacity, "selected_parcels": [p["id"] for p in selected],
            "selected_weight": sum(p["weight"] for p in selected), "selected_value": value,
            "route": route, "route_distance": round(distance, 3),
            "legs": [{**leg, "distance": round(leg["distance"], 3)} for leg in legs],
            "dp_final_row": dp[-1]}


def benchmark(seed=17):
    rng = random.Random(seed); rows = []
    def record(component, size, fn):
        start = time.perf_counter(); fn(); elapsed = (time.perf_counter() - start) * 1000
        rows.append({"component": component, "size": size, "runtime_ms": round(elapsed, 4)})
    for n in (100, 500, 1000, 2000):
        items = [{"deadline": rng.randrange(1, 10000), "priority": rng.randrange(1, 10), "id": str(i)} for i in range(n)]
        record("merge_sort", n, lambda: prioritize(items))
        record("built_in_sort", n, lambda: sorted(items, key=lambda p:(p["deadline"],-p["priority"],p["id"])))
    for n, cap in ((10,100),(20,200),(35,300),(50,400)):
        items = [{"id": str(i), "weight": rng.randrange(1,30), "value": rng.randrange(1,100)} for i in range(n)]
        record("knapsack_dp", n, lambda: knapsack(items, cap))
    for n in (20,40,80,120):
        points = [{"id":str(i),"x":rng.random()*100,"y":rng.random()*100} for i in range(n)]
        graph = build_graph(points)
        record("dijkstra_single_source", n, lambda: dijkstra(graph,"0"))
        record("nearest_neighbor_tour", n, lambda: nearest_neighbor_route(graph,"0",[str(i) for i in range(1,n)]))
    return rows


def svg_chart(rows):
    # Dependency-free benchmark chart. One small-multiple plot per algorithm.
    components = list(dict.fromkeys(r["component"] for r in rows))
    colors = ["#1769aa", "#d97706", "#11805a", "#8b5cf6", "#dc4561"]
    width, height, panel_h = 900, 210 * len(components) + 55, 210
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="#ffffff"/>', '<style>text{font-family:Arial,sans-serif;fill:#243247}.title{font-size:22px;font-weight:bold}.label{font-size:13px}.axis{stroke:#94a3b8;stroke-width:1}.grid{stroke:#e2e8f0;stroke-width:1}</style>',
           '<text x="34" y="32" class="title">Courier planner benchmark · milliseconds (lower is better)</text>']
    for idx, comp in enumerate(components):
        subset = [r for r in rows if r["component"] == comp]; top = 55 + idx*panel_h
        maxv = max(r["runtime_ms"] for r in subset) or 1
        out.append(f'<text x="35" y="{top+18}" class="label" font-weight="bold">{comp}</text>')
        x0, y0, plotw, ploth = 90, top+32, 730, 130
        for tick in range(4):
            yy = y0 + ploth - tick*ploth/3
            out.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x0+plotw}" y2="{yy:.1f}" class="grid"/>')
            out.append(f'<text x="{x0-8}" y="{yy+4:.1f}" text-anchor="end" class="label">{maxv*tick/3:.2f}</text>')
        out.append(f'<line x1="{x0}" y1="{y0+ploth}" x2="{x0+plotw}" y2="{y0+ploth}" class="axis"/>')
        pts=[]
        for j,r in enumerate(subset):
            x=x0+j*plotw/max(1,len(subset)-1); y=y0+ploth-r["runtime_ms"]/maxv*ploth; pts.append(f'{x:.1f},{y:.1f}')
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{colors[idx%len(colors)]}"/><text x="{x:.1f}" y="{y0+ploth+20}" text-anchor="middle" class="label">{r["size"]}</text>')
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{colors[idx%len(colors)]}" stroke-width="2"/>')
    out.append('</svg>')
    return '\n'.join(out)


def self_check():
    sample={"capacity":7,"depot":"D","parcels":[
      {"id":"A","weight":3,"value":6,"deadline":2,"priority":2,"destination":"A"},
      {"id":"B","weight":4,"value":7,"deadline":1,"priority":1,"destination":"B"},
      {"id":"C","weight":2,"value":4,"deadline":3,"priority":3,"destination":"C"}],
      "points":[{"id":"D","x":0,"y":0},{"id":"A","x":1,"y":0},{"id":"B","x":2,"y":0},{"id":"C","x":0,"y":2}]}
    result=plan(sample)
    assert result["priority_order"][0]["id"] == "B"
    assert result["selected_value"] == 13 and set(result["selected_parcels"]) == {"A","B"}
    assert result["route"][0] == "D" and result["route"][-1] == "D"
    g={"D":{"X":2},"X":{"D":2,"Y":3},"Y":{"X":3}}
    dist,prev=dijkstra(g,"D"); assert dist["Y"] == 5 and path_to(prev,"Y")==["D","X","Y"]
    return {"status":"passed","checks":["deadline ordering","optimal 0/1 knapsack","closed delivery tour","Dijkstra shortest path and reconstruction"]}


def main():
    parser=argparse.ArgumentParser(description="Integrated courier parcel and route planner")
    parser.add_argument("--data",type=Path,default=Path(__file__).parent/"data"/"small.json")
    parser.add_argument("--capacity",type=int,help="override vehicle capacity")
    parser.add_argument("--benchmark",action="store_true",help="write CSV and SVG runtime evidence")
    parser.add_argument("--self-check",action="store_true",help="run deterministic correctness checks")
    parser.add_argument("--output",type=Path,help="write plan JSON to this path")
    args=parser.parse_args()
    if args.self_check: print(json.dumps(self_check(),indent=2))
    if not args.self_check or args.data:
        data=json.loads(args.data.read_text(encoding="utf-8"))
        if args.capacity is not None: data["capacity"]=args.capacity
        result=plan(data)
        rendered=json.dumps(result,indent=2)
        if args.output: args.output.write_text(rendered+"\n",encoding="utf-8")
        else: print(rendered)
    if args.benchmark:
        rows=benchmark(); evidence=Path(__file__).parent/"evidence"; evidence.mkdir(exist_ok=True)
        with (evidence/"benchmark.csv").open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=["component","size","runtime_ms"]); writer.writeheader(); writer.writerows(rows)
        (evidence/"runtime_chart.svg").write_text(svg_chart(rows),encoding="utf-8")
        print(f"Benchmark evidence written to {evidence}")

if __name__ == "__main__": main()
