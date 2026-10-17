# Data provenance

## Public demo: synthetic

`scrapingress-demo` generates fictional players, sites, timestamps and coordinates from a random seed. No source rows are copied or used to calibrate its parameters. Its results are not empirical findings about Ingress players or finance.

## Local analysis: pseudonymised real observations

The separate local workflow reads a derivative of the supplied source archive. Player, site and event IDs are replaced with keyed, domain-separated HMAC-SHA256 codes. Original usernames, portal names, addresses, free text and unused team fields are excluded.

All source rows, coordinates, timestamps and event multiplicity are retained in the derivative. The original archive is unchanged. A separate secret key makes the replacement stable without publishing a username lookup table.

**This is pseudonymisation, not anonymisation.** Time and location patterns can still be identifying. The database, key and real-data outputs remain local/private and are excluded from the source export. There is no public database/API or database upload in this project.

Game events may reference multiple sites at one instant. Those records are retained for activity/site analysis, but the real-data workflow does not treat them as ordered physical player locations or calculate routes from them. Incomplete records remain in the database and are explicitly counted when excluded from analysis.

Every new output directory includes its own `DATA_NOTICE.txt`, and `metrics.json` records which execution mode was used.
