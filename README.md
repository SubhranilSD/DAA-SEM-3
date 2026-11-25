# Courier Planning Capstone

A self-contained Python prototype for parcel prioritization, one-trip capacity planning, shortest-path calculations, and delivery-route approximation. It uses only the Python standard library.

## Run it

Python 3.10 or newer is recommended. From this folder:

```powershell
python courier_planner.py
python courier_planner.py --data data/large.json --output evidence/large_plan.json
python courier_planner.py --self-check
python courier_planner.py --benchmark
```

The default run prints a JSON delivery plan for `data/small.json`. `--capacity 20` overrides the vehicle capacity. `--benchmark` writes `evidence/benchmark.csv` and `evidence/runtime_chart.svg`.

## What the system does

1. **Prioritize parcels:** stable merge sort orders earlier deadlines first, then higher priority, then parcel ID for deterministic ties.
2. **Choose one trip’s parcels:** 0/1 knapsack dynamic programming maximizes total declared parcel value without exceeding vehicle capacity. The output includes the selected parcels, total weight/value, and final DP row.
3. **Build the delivery graph:** by default, locations form a complete undirected graph weighted by Euclidean distance. Input can instead supply explicit positive road edges.
4. **Plan the trip:** Dijkstra computes shortest-path distance and predecessor data. Nearest neighbor repeatedly chooses the closest unvisited selected destination, then returns to the depot. Each leg includes its reconstructed shortest path.

## Complexity and design notes

- Merge sort: `O(n log n)` time and `O(n)` auxiliary storage.
- Knapsack: `O(nC)` time and `O(nC)` storage, where `C` is integer capacity.
- Dijkstra with a binary heap: `O((V + E) log V)` time for a sparse graph; the default complete graph has `E = O(V²)`.
- Nearest-neighbor route: this implementation runs Dijkstra from each point used as a possible route origin, then selects the next stop. On the default dense graph this is roughly `O(V³ log V)` in the current straightforward implementation. It is a practical heuristic, not an optimal TSP solver.

## Assumptions and limitations

- Parcel weights, values, deadlines, priorities, and coordinates are synthetic input attributes. Values are the knapsack objective; priority only breaks deadline ties in the displayed sort order.
- The planner displays deadline order, but it does **not** promise delivery-by-deadline feasibility: no travel-time windows, service times, or deadline constraints are part of the knapsack objective.
- The nearest-neighbor tour is approximate and can be longer than an optimal tour. The graph distances are treated as symmetric and positive.
- Knapsack capacity and parcel weights are integer units. This is an educational prototype, not a live dispatch system.

## Included files

- `courier_planner.py` — integrated application and deterministic self-checks.
- `data/small.json` — eight-parcel demonstration dataset.
- `data/large.json` — seeded dataset with 60 parcels and 61 locations.
- `evidence/small_plan.json`, `evidence/large_plan.json` — captured sample outputs.
- `evidence/self_check.json` — correctness-check result.
- `evidence/benchmark.csv`, `evidence/runtime_chart.svg` — runtime measurements and chart.
- `evidence/performance_notes.md` — test scale, measured results, and interpretation.

## Reproduce the evidence

Run the commands above from this directory with Python available on `PATH`. The benchmark is a single local run using Python's `perf_counter`; timings vary with hardware and system load. It compares the custom merge sort with Python's built-in sort, scales the DP input, and measures Dijkstra and nearest-neighbor planning on generated complete graphs.
