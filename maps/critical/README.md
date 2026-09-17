# Critical Maps

Unlike `hard/` and `challenger/`, which are about raw scale and
difficulty, this folder isolates the specific rule interactions from
the subject that are easiest to get subtly wrong. Each map is small
and focused on exactly one mechanic, so a wrong turn count or an
invalid simulation state points straight at the bug.

## Maps

- `01_restricted_gate_contention.txt` - two roomy staging zones both
  feed a single restricted zone. Tests that capacity for a restricted
  (2-turn, forced-arrival) zone is reserved in advance and shared
  correctly across every connection that leads into it.
- `02_conveyor_chain.txt` - a single-file tunnel of capacity-1 zones.
  Tests the "moving out frees capacity the same turn" rule, which is
  the difference between an efficient convoy and needlessly doubling
  the turn count.
- `03_link_vs_zone_capacity.txt` - a choke route where the connection
  capacity, not the zone capacity, is the real bottleneck, run in
  parallel with an independently capped bypass route. Tests that both
  capacity types are tracked (and that drones get distributed across
  both routes).
- `04_symmetric_deadlock_risk.txt` - two symmetric arms funnel into one
  restricted zone via two separate connections. Tests that destination
  capacity is checked jointly across all incoming connections for a
  turn, not per connection in isolation.

## Why these matter

The mandatory part of the subject explicitly requires "avoidance of
path conflicts and deadlocks" and tracking "zone capacity constraints
(max_drones) and connection capacity (max_link_capacity)" together.
These four maps are the smallest reproductions we could build of the
situations where that's actually hard: forced multi-turn commitments,
same-turn capacity hand-offs, and destination contention from multiple
directions at once. If your algorithm produces a valid, reasonably
short simulation on all four, it is very likely handling those rules
correctly in general, not just by accident on the bigger maps.
