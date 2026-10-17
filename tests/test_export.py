"""Check the sharing boundary: unlisted artifacts cannot enter the export."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_public.py"
spec = importlib.util.spec_from_file_location("public_export", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_root = module.ROOT
        module.ROOT = self.root
        for name in module.FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic source placeholder")

    def tearDown(self):
        module.ROOT = self.old_root
        self.temp.cleanup()

    def test_excludes_unlisted_data_and_refuses_overwrite(self):
        for name in ["cookies.json", "data.db", "raw/players.csv", ".env", "reports/demo/observations.csv"]:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE_TEST_SENTINEL")
        destination = self.root / "export.zip"
        manifest = module.export(destination)
        with zipfile.ZipFile(destination) as archive:
            expected = {"scrapingress-public/" + name for name in module.FILES}
            expected.add("scrapingress-public/SHA256SUMS.json")
            self.assertEqual(set(archive.namelist()), expected)
            self.assertTrue(all(b"PRIVATE_TEST_SENTINEL" not in archive.read(n)
                                for n in archive.namelist()))
            self.assertEqual(json.loads(archive.read("scrapingress-public/SHA256SUMS.json")), manifest)
        with self.assertRaises(FileExistsError): module.export(destination)

    def test_refuses_symbolic_link_sources(self):
        name = module.FILES[0]
        source = self.root / name
        source.unlink()
        target = self.root / "private.txt"
        target.write_text("PRIVATE_TEST_SENTINEL")
        source.symlink_to(target)
        with self.assertRaises(ValueError): module.export(self.root / "export.zip")
        self.assertFalse((self.root / "export.zip").exists())
