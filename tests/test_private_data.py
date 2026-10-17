"""Private processing tested only with a tiny, fictional database fixture."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from scrapingress.private_data import load_private_events

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pseudonymize_database.py"
spec = importlib.util.spec_from_file_location("pseudonymizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PrivateDataTests(unittest.TestCase):
    def test_keyed_ids_preserve_rows_but_remove_original_names_and_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, archive = root / 'fixture.db', root / 'fixture.zip'
            with sqlite3.connect(source) as con:
                con.execute('CREATE TABLE plexts(id TEXT, player_name TEXT, timestamp INTEGER, portal_name TEXT, portal_latE6 INTEGER, portal_lngE6 INTEGER, text TEXT, portal_address TEXT)')
                rows = [('original1', 'FictionalSecretPlayer', 1704067200000, 'FictionalSecretSite', 1000000, 2000000, 'FictionalSecretMessage', 'FictionalSecretAddress'),
                        ('original2', 'FictionalSecretPlayer', 1704067200000, 'FictionalSecretSite', 1000000, 2000000, '', ''),
                        ('original3', None, 1704067300000, None, None, None, '', '')]
                con.executemany('INSERT INTO plexts VALUES (?,?,?,?,?,?,?,?)', rows)
            with zipfile.ZipFile(archive, 'w') as zipped:
                zipped.write(source, module.MEMBER)
            key = root / 'private.key'
            output = root / 'pseudonymised.db'
            result = module.pseudonymize(archive, output, key)
            self.assertEqual(result['rows_preserved'], 3)
            for secret in ['FictionalSecretPlayer', 'FictionalSecretSite', 'FictionalSecretMessage', 'FictionalSecretAddress', 'original1']:
                self.assertNotIn(secret.encode(), output.read_bytes())
            events, quality = load_private_events(output)
            self.assertEqual(len(events), 2)
            self.assertEqual(quality['excluded_incomplete_rows'], 1)
            self.assertEqual(events.player_id.nunique(), 1)
            self.assertEqual(events.event_id.nunique(), 2)
            self.assertEqual(events.latitude.iloc[0], 1.)
            other = root / 'other.db'
            module.pseudonymize(archive, other, key)
            events2, _ = load_private_events(other)
            self.assertEqual(events.player_id.tolist(), events2.player_id.tolist())
            other_key = b'X' * 32
            self.assertNotEqual(module.token(key.read_bytes(), 'player', 'same'), module.token(other_key, 'player', 'same'))
            self.assertNotEqual(module.token(key.read_bytes(), 'player', 'same'), module.token(key.read_bytes(), 'site', 'same'))
            with self.assertRaises(FileExistsError): module.pseudonymize(archive, output, key)
