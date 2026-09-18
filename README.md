*This project has been created as part of the 42 curriculum by jawosylu.*

# Fly-In

Autonomous multi-drone routing and turn-by-turn simulation, with a live
Pygame visualization.

## Description

Fly-In is a drone routing and simulation system. Given a map of connected
zones (a graph) with a single start and end hub, it computes a path for
every drone, then runs a turn-by-turn simulation that moves all drones from
the start to the end zone while respecting:

- **Zone occupancy limits** (`max_drones`), with the start and end zones
  exempt from the limit.
- **Connection capacity limits** (`max_link_capacity`).
- **Zone-type movement costs**: `normal`/`priority` zones cost 1 turn,
  `restricted` zones cost 2 turns (and cannot be waited on mid-transit),
  `blocked` zones cannot be entered at all.

The goal is to deliver every drone in as few simulation turns as possible.
The project is written entirely from scratch in Python — no graph library
(`networkx`, `graphlib`, ...) is used — and is fully object-oriented and
type-safe (`mypy --strict`, `flake8`).

The simulation can be watched live in a Pygame window, or (without a map
argument) explored through an in-app menu that lets you pick one of the
bundled example maps.

## Screenshots

| Intro | Menu |
| :--: | :--: |
| ![Intro screen](docs/screenshots/intro.png) | ![Menu screen](docs/screenshots/menu.png) |

| Map selection | Live simulation |
| :--: | :--: |
| ![Map selection screen](docs/screenshots/map_selection.png) | ![Simulation screen](docs/screenshots/drone_screen.png) |

The simulation screenshot above shows `maps/medium/03_priority_puzzle.txt`
mid-run: drones (the small X-shaped sprites) in transit between zones, live
`occupancy/capacity` labels under `fast_junction` and `merge_point`, the
red `restricted` zones on the slow upper path, and the running turn log in
the bottom-right panel.

## Project structure

```
src/
├── __main__.py               # CLI entry point: wires every stage together
├── argparsing.py             # --map command-line flag
├── input_parsing.py          # Map file parser + pydantic Zone/Connection models
├── pathfinding_algorithm.py  # Graph (Map) + Dijkstra shortest paths
├── route_planner.py          # Congestion-aware path assignment (1 path/drone)
├── drone_factory.py          # Drone state machine + fleet construction
├── simulation_engine.py      # Turn-by-turn Scheduler enforcing all constraints
├── visual_representation.py  # Pygame scenes: intro, menu, map select, sim view
└── visual/                   # Reusable Pygame building blocks
    ├── background.py         #   parallax scrolling background
    ├── particle.py           #   snowfall particle system
    ├── drone.py               #   animated drone sprite
    └── basescene.py           #   Scene/BaseScene interface shared by every screen
```

Data flows from a map file to an on-screen simulation in one direction —
each stage only depends on the plain data produced by the previous one, not
on how it was computed:

```mermaid
flowchart LR
    F["Map file (.txt)"] --> P["input_parsing\nConfig_Map / Zone / Connection"]
    P --> G["pathfinding_algorithm\nMap + Graph (Dijkstra)"]
    G --> R["route_planner\nRoutePlanner (1 path / drone)"]
    R --> D["drone_factory\nDroneFactory -> Drone[]"]
    D --> S["simulation_engine\nScheduler"]
    S --> V["visual_representation\nVisualizer (Pygame)"]
    S --> T["Turn log\n(D&lt;id&gt;-&lt;zone&gt; ...)"]
```

## Instructions

The project uses [uv](https://docs.astral.sh/uv/) to manage its virtual
environment and dependencies, and exposes everything through the `Makefile`:

```sh
make install      # uv sync — create the venv and install dependencies
make run           # uv run python -m src
make debug         # run the main script under pdb
make clean         # remove __pycache__ and .mypy_cache
make fclean        # clean + remove the virtual environment
make lint          # flake8 . && mypy . <required flags>
make lint-strict    # flake8 . && mypy . --strict
```

Running `make run` without any flags opens the interactive Pygame menu,
where a map can be chosen from the list. A specific map can also be loaded
directly on the command line:

```sh
uv run python -m src --map ./maps/easy/01_linear_path.txt
```

Controls in the simulation view:

- `Space` — pause / unpause the simulation.
- `Right arrow` — while paused, advance a single turn.
- `R` or the **Retry** button — restart the simulation from turn 0.
- `Esc` — quit.
- `E` — once the simulation has finished, return to the menu.

Map files follow the format described in the project subject
(`nb_drones`, `start_hub`, `end_hub`, `hub`, `connection` lines with
optional `[key=value]` metadata). Example maps of increasing difficulty are
provided under [maps/](maps/), documented in [maps/README.md](maps/README.md).

## Algorithm choices and implementation strategy

The routing/simulation pipeline is split into independent stages, each in
its own module:

1. **Parsing** ([src/input_parsing.py](src/input_parsing.py)) reads the map
   file line by line into a raw key/value structure, then validates it into
   typed `pydantic` models (`Zone`, `Connection`). Any structural or
   semantic error (unknown key, invalid zone type, malformed metadata, ...)
   raises `InputParsingError` and aborts with a clear message.

2. **Graph** ([src/pathfinding_algorithm.py](src/pathfinding_algorithm.py))
   builds an adjacency-list graph (`Map`) from the parsed zones and
   connections, skipping `blocked` zones entirely so they can never be
   entered. Connections that touch a blocked zone are dropped from the graph
   (a blocked zone is valid, just inaccessible), while connections to a zone
   that is not defined at all are an error. If no route from start to end
   remains, a clear "no valid path" error is raised.
   `Graph.shortest_distance` implements **Dijkstra's algorithm**
   from scratch (using `heapq`) with a pluggable edge-weight function,
   defaulting to the destination zone's movement cost.

3. **Route planning** ([src/route_planner.py](src/route_planner.py))
   assigns one shortest path per drone. Instead of giving every drone the
   same globally-shortest path (which would funnel every drone through the
   same bottleneck), `RoutePlanner` runs Dijkstra once per drone with a
   **congestion-aware weight function**: each zone/connection already
   reserved by a previously-routed drone adds a penalty proportional to
   `load / capacity`, and `priority` zones get a small bias to be preferred
   when a tie needs breaking. This naturally spreads drones across disjoint
   or parallel paths without needing a full multi-commodity-flow solver.

4. **Simulation** ([src/simulation_engine.py](src/simulation_engine.py))
   is a turn-based `Scheduler`. Each turn runs the same four steps:

   ```mermaid
   flowchart TD
       A["1. Land completed transits\n(restricted-zone arrivals)"] --> B["2. Sort movable drones\n(longest-blocked first, then\nshortest remaining path)"]
       B --> C{"3. Repeat until nothing changes:\ncan a drone enter its next zone\n(zone + link capacity free)?"}
       C -- "yes" --> D["Move / start transit\nrecord D&lt;id&gt;-&lt;target&gt;"]
       C -- "no" --> E["mark_blocked()\nretry next turn"]
       D --> F{"4. Any move happened\nthis turn?"}
       E --> F
       F -- "no, or turn cap reached" --> G["raise SchedulerDeadlockError"]
       F -- "yes, drones remain" --> A
       F -- "all drones delivered" --> H["done"]
   ```

   Drones that cannot move immediately are retried within the same turn
   until no more drone can advance. This lets a drone move into a zone that
   another drone leaves in that very turn (as the subject requires),
   regardless of the order the drones are processed in. A turn cap
   (`longest path + zones × drones`) bounds the simulation; if a
   turn produces no movement at all, or the cap is exceeded,
   `SchedulerDeadlockError` is raised with the state of every stuck drone.

5. **Drone bookkeeping** ([src/drone_factory.py](src/drone_factory.py))
   models each drone as a small state machine, keeping the simulation
   engine focused on scheduling rather than per-drone state:

   ```mermaid
   stateDiagram-v2
       [*] --> delivered: empty path (already at end)
       [*] --> can_move: has a path
       can_move --> can_move: move() into a normal/priority zone
       can_move --> on_way: start_transit() into a restricted zone
       on_way --> can_move: complete_transit(), path remains
       on_way --> delivered: complete_transit(), path empty
       can_move --> delivered: move(), path empty
   ```

**Complexity**: each `Dijkstra` run is `O((V + E) log V)`; route planning
runs it once per drone, so path assignment is `O(D · (V + E) log V)` for
`D` drones. The simulation itself is `O(T · D log D)` for `T` turns
(dominated by sorting movable drones each turn). Paths are computed once
up front and then simply consumed turn by turn — no re-planning happens
during the simulation, keeping memory usage at `O(V + E + D)` for the
graph and drone paths.

## Performance

Turns needed by this implementation compared with the reference targets of
the subject (fewer is better; every map is solved in well under a second):

| Map | Drones | Turns | Target |
| --- | --- | --- | --- |
| easy / linear path | 2 | 4 | ≤ 6 |
| easy / simple fork | 3 | 5 | ≤ 6 |
| easy / basic capacity | 4 | 6 | ≤ 8 |
| medium / dead end trap | 5 | 8 | ≤ 15 |
| medium / circular loop | 6 | 20 | ≤ 20 |
| medium / priority puzzle | 4 | 8 | ≤ 12 |
| hard / maze nightmare | 8 | 18 | ≤ 45 |
| hard / capacity hell | 12 | 23 | ≤ 60 |
| hard / ultimate challenge | 15 | 31 | ≤ 35 |
| challenger / impossible dream (optional) | 25 | 66 | record: 45 |

All mandatory targets are met. The optional challenger map is solved
correctly but does not beat the reference record.

## Visual representation

The Pygame front end ([src/visual_representation.py](src/visual_representation.py)
and [src/visual/](src/visual/)) is built as a small stack of `Scene`s, each
sharing a parallax scrolling background and a snowfall particle system for
a consistent look. `Visualizer.run` keeps a `list[Scene]` and always draws
its top ([src/visual_representation.py](src/visual_representation.py)):

```mermaid
flowchart LR
    Intro["IntroScreen\n(splash)"] -->|key / click| Menu["Menu\nstart / back / quit"]
    Menu -->|start, no CLI map| MapSel["MapSelection\npick a bundled map"]
    Menu -->|start, CLI map given| Drone["DroneScreen\nlive simulation"]
    MapSel -->|map chosen| Drone
    Drone -->|finished, press E| Menu
```

The simulation view (`DroneScreen`) is the core visualization:

- The network is laid out by scaling each zone's raw `(x, y)` coordinates
  to fit the window, then drawing every connection as a line and every
  zone as a tinted icon (tinted with the zone's configured `color`).
- Each zone displays its live `occupancy / capacity`, and each
  capacity-limited connection displays its live `usage / capacity`,
  making it easy to see where drones are queuing up (visible under
  `fast_junction` and `merge_point` in the screenshot above).
- Drones are drawn as an animated sprite that smoothly interpolates
  between the previous and next zone position over the turn interval,
  so multi-drone movement stays readable instead of jumping instantly.
- A scrolling log panel prints the raw per-turn move list (the same
  format used for the textual simulation output), letting the exact
  `D<id>-<zone>` output be cross-checked against what is drawn.
- The turn counter, pause state and step-by-step controls (`Space`,
  `Right arrow`) let a reviewer freeze the simulation and inspect any
  single turn in detail. A **Retry** button (or `R`) restarts the run from
  turn 0 with a freshly planned simulation.

This turns the abstract turn log into an at-a-glance view of congestion,
capacity usage and drone progress, which was the main goal of the visual
requirement in the subject.

## Resources

- [Dijkstra's algorithm — Introduction to Algorithms (CLRS)](https://mitpress.mit.edu/9780262046305/introduction-to-algorithms/) — reference for the shortest-path implementation in `Graph.shortest_distance`.
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html) — used for the priority queue in Dijkstra.
- [Pydantic documentation](https://docs.pydantic.dev/) — used to validate and type the parsed `Zone`/`Connection` models.
- [Pygame documentation](https://www.pyga.me/docs/) — used for the visual representation.
- [mypy documentation](https://mypy.readthedocs.io/) — used to reach `mypy --strict` compliance.

### AI usage

AI (an LLM-based coding assistant) was used for two distinct parts of this
project:

- **Pathfinding and scheduling**: as a discussion and debugging partner
  while designing `RoutePlanner`'s congestion-aware Dijkstra weighting and
  the `Scheduler`'s turn-based capacity/deadlock handling — explaining
  algorithmic trade-offs and helping track down scheduling bugs. The
  resulting design was reviewed and is understood by the author.
- **Type safety and documentation**: bringing the whole `src/` tree into
  compliance with `mypy --strict` (adding precise type hints, replacing
  unsound `Optional` attribute access with explicit assertions/guards,
  fixing a dead-code branch in `Visualizer.run`'s scene stack) and writing
  the PEP 257 docstrings for every module, class and function, plus this
  README (including the diagrams and screenshots, the latter rendered
  offscreen from the real Pygame scenes).
