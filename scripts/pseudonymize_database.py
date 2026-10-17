"""Create a LOCAL pseudonymised derivative. This does NOT anonymise locations."""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import tempfile
import zipfile

MEMBER = "scrapingress-main/flask-server/data.db"


def token(key, kind, value):
    if value is None or not str(value).strip():
        return None
    message = json.dumps([kind, str(value)], separators=(",", ":")).encode()
    return kind + "_" + hmac.new(key, message, hashlib.sha256).hexdigest()


def pseudonymize(archive, output, key_file):
    output, key_file = Path(output).resolve(), Path(key_file).resolve()
    if output.exists():
        raise FileExistsError("Refusing to overwrite a database.")
    if output == key_file:
        raise ValueError("Key and output must be separate files.")
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if key_file.exists():
        if key_file.is_symlink():
            raise ValueError("Key must not be a symlink.")
        key = key_file.read_bytes()
    else:
        key_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with os.fdopen(os.open(str(key_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as file:
            key = secrets.token_bytes(32)
            file.write(key)
    if len(key) != 32:
        raise ValueError("Expected a 32-byte pseudonymisation key.")
    os.chmod(key_file, 0o600)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        source = Path(temporary) / "original.db"
        with zipfile.ZipFile(archive) as zipped, zipped.open(MEMBER) as file, source.open("wb") as dest:
            shutil.copyfileobj(file, dest)
        os.chmod(source, 0o600)
        reader = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
        # A fresh database excludes free pages, text, addresses and old usernames.
        descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        writer = sqlite3.connect(output)
        try:
            writer.execute("""CREATE TABLE events (
                event_id TEXT PRIMARY KEY, player_id TEXT, timestamp INTEGER,
                site_id TEXT, latitude REAL, longitude REAL)""")
            cursor = reader.execute("""SELECT id, player_name, timestamp, portal_name,
                                     portal_latE6, portal_lngE6 FROM plexts""")
            count = 0
            while True:
                batch = cursor.fetchmany(5000)
                if not batch:
                    break
                transformed = []
                for event, player, timestamp, site, lat, lon in batch:
                    site_key = json.dumps([site, lat, lon], ensure_ascii=False) if site is not None or lat is not None else None
                    transformed.append((token(key, "event", event), token(key, "player", player),
                                        timestamp, token(key, "site", site_key),
                                        None if lat is None else lat / 1e6,
                                        None if lon is None else lon / 1e6))
                writer.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", transformed)
                count += len(transformed)
            writer.execute("CREATE INDEX player_time ON events(player_id, timestamp)")
            writer.commit()
            if writer.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Output database integrity check failed.")
        except Exception:
            writer.close()
            output.unlink(missing_ok=True)
            raise
        finally:
            reader.close()
            writer.close()
    metadata = {"classification": "PSEUDONYMISED, NOT ANONYMOUS. Keep local/private.",
                "rows_preserved": count, "identifiers": "keyed HMAC-SHA256, domain-separated",
                "removed": ["usernames", "portal names", "addresses", "free text", "teams", "original IDs"],
                "preserved": ["timestamps", "coordinates", "event multiplicity"],
                "timestamp_unit": "milliseconds since Unix epoch, UTC",
                "source_archive_unchanged": True}
    notice = output.with_suffix(".notice.json")
    with os.fdopen(os.open(str(notice), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as file:
        json.dump(metadata, file, indent=2)
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(pseudonymize(args.archive, args.output, args.key_file), indent=2))
