# Invalid Maps

These maps are deliberately malformed or violate a rule from the
subject. They should never produce a simulation result - loading one
must fail with a clear, line-specific error message (per section
VII.4 of the subject: *"Any other parsing error must stop the program
and return a clear error message indicating the line and cause"*).

| File | Violation |
|---|---|
| `01_missing_nb_drones.txt` | `nb_drones` line missing |
| `02_undefined_zone_reference.txt` | connection points at a zone that was never declared |
| `03_duplicate_zone_name.txt` | two hubs share the same name |
| `04_invalid_zone_type.txt` | `zone=` value outside `normal`/`blocked`/`restricted`/`priority` |
| `05_unreachable_goal.txt` | no connection path reaches `end_hub` |
| `06_zero_capacity_zone.txt` | `max_drones=0` permanently blocks the only route |
| `07_zero_drones.txt` | `nb_drones: 0` (must be a positive integer) |
| `08_malformed_line.txt` | a line is missing the `key: value` syntax |
| `09_duplicate_connection.txt` | the same edge declared twice (`a-b` then `b-a`) |
| `10_dash_in_zone_name.txt` | a zone name contains a dash, which the connection syntax reserves as the separator |

## Current gap

As of this writing, `Config_Map.validation_after_creation()` in
`src/input_parsing.py` is still an unimplemented stub. We ran every
map in this folder through the current parser to check, and these
five currently parse "successfully" instead of being rejected:
`03_duplicate_zone_name.txt`, `05_unreachable_goal.txt`,
`06_zero_capacity_zone.txt`, `07_zero_drones.txt`, and
`09_duplicate_connection.txt`. They will either crash later, silently
misbehave, or "succeed" with an ill-defined result instead of failing
cleanly at parse time. Wiring these checks into
`validation_after_creation()` (or wherever the equivalent validation
ends up living) before evaluation is worth prioritizing, since the
subject explicitly requires a clear, line-and-cause error message for
every parsing failure and this will very likely come up during peer
review.
