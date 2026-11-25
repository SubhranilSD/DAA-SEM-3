# Performance and validation notes

## Validation

The deterministic self-check passed four assertions: deadline ordering, a known optimal knapsack selection, a closed route, and Dijkstra distance plus path reconstruction. The 60-parcel dataset also produced a feasible selection at or below the capacity of 100 and a depot-to-depot route through every chosen destination.

The small demonstration plan selects P-102, P-107, P-103, and P-101: 18/18 capacity units and value 153. Its nearest-neighbor route is `DEPOT → MARKET → EAST → NORTH → RIVER → DEPOT`, with distance 23.858 coordinate units.

## Runtime snapshot

Recorded on the bundled Python runtime during project assembly. Times are milliseconds and will vary by machine. Full per-run data is in `benchmark.csv`; the plotted version is `runtime_chart.svg`.

| Component | Input sizes | Observed time range |
| --- | --- | ---: |
| Merge sort | 100–2,000 parcels | 0.234–6.962 ms |
| Built-in sort reference | 100–2,000 parcels | 0.028–0.582 ms |
| Knapsack DP | 10–50 parcels; capacity 100–400 | 0.221–4.518 ms |
| Dijkstra, one source | 20–120 vertices | 0.041–1.224 ms |
| Nearest-neighbor tour | 20–120 vertices | 0.641–128.889 ms |

The built-in sort is much faster in this Python implementation, while the explicit merge sort keeps the algorithm visible for the assignment. Route time grows fastest because the simple implementation computes shortest paths from every candidate origin. A next iteration could cache only required pairwise paths or use a faster all-pairs strategy for dense graphs, and a deadline-aware planner could include travel and service time in feasibility.

## Reproducibility

`python courier_planner.py --self-check` runs the assertions. `python courier_planner.py --benchmark` regenerates the CSV and SVG using a fixed random seed for benchmark input. Wall-clock times are naturally not fixed.
