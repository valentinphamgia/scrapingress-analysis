# Data policy

The public source export contains no event data. `scrapingress-demo` generates fictional observations in memory without reading or calibrating on real records. Its schema includes player ID, UTC timestamp, site ID, latitude and longitude.

The optional private workflow reads a separately stored pseudonymised real-event database. It preserves times and coordinates, so it is not anonymous. The database, key, mappings and private results are excluded from export. See `docs/PRIVATE_DATA.md`.

No private observations or key belong under this public source directory. Generated demo files remain ignored.
