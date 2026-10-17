# Local pseudonymised-data workflow

This workflow is local and offline. The source-code archive excludes all databases, keys and real-data results. Replacing names does not anonymise timestamps and locations.

## 1. Create a separate derivative

From the project directory, with the environment active:

```bash
python scripts/pseudonymize_database.py \
  --archive ../scrapingress-main.zip \
  --output ../.scrapingress-private/events-pseudonymised.db \
  --key-file ../.scrapingress-private/pseudonymisation.key
```

The converter extracts the source SQLite file into a temporary local directory, opens it read-only, creates a fresh reduced-schema database and deletes the temporary copy. It never changes the source archive. A fresh database avoids retaining old text or deleted pages from the source.

Identifiers use HMAC-SHA256 with a random 32-byte key and separate event/player/site domains. A reused key gives stable IDs; a different key gives different IDs. Neither the key nor an identity lookup table is included in the export. Replacement codes are not a promise of anonymity.

The derivative has columns `event_id`, `player_id`, `timestamp` (Unix milliseconds), `site_id`, `latitude`, `longitude`. Original names, addresses, text and teams are not copied. All source rows and event multiplicity are retained. Files are created with local owner-only permissions where the filesystem supports them. Existing output databases are not overwritten.

## 2. Analyse activity privately

```bash
python scripts/analyse_private.py \
  --database ../.scrapingress-private/events-pseudonymised.db \
  --output ../.scrapingress-private/analysis \
  --repetitions 10 --sensitivity
```

The loader opens SQLite read-only. Incomplete records are excluded from analysis and counted, but remain in the derivative database. Distinct simultaneous events with distinct IDs remain distinct. Multiple simultaneous event sites are explicitly allowed for activity counts; path features are excluded because they would require an invented physical ordering. The private run uses seven activity features instead of the synthetic demo's eight features.

`--sensitivity` adds session-gap and scaling comparisons. It can be omitted for a shorter diagnostic run. The repetition count is recorded; three repetitions are only a smoke check, not a precise stability estimate.

## Sharing boundary

The explicit source export contains the converter, loader and analysis code, but no database, original records, key, mapping, private player profiles or real-data plot. No GitHub upload or HTTP endpoint is performed. Publishable findings require a separate decision about what the aggregates reveal; individual pseudonymised traces must not be described as anonymous.
