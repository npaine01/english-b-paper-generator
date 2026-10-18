"""The selected school cover must survive editable Word export."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("export_docx", ROOT / "ui/docx.py")
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


class CoverExport(unittest.TestCase):
    def test_internal_cover_keeps_school_details_and_embeds_logo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "paper.docx"
            export.build({"kind":"reading", "cover":"internal", "target":40,
                          "coverDetails":{"exam":"Midterm Examination", "grade":"G11"},
                          "items":[]}, path)
            with zipfile.ZipFile(path) as z:
                root = ET.fromstring(z.read("word/document.xml"))
                text = "".join(root.itertext())
                self.assertIn("Midterm Examination", text)
                self.assertIn("G11", text)
                self.assertIn("试卷排版和影印负责", text)
                self.assertNotIn("Write your session number", text)
                self.assertIn("word/media/qdhs-logo.png", z.namelist())
                ET.fromstring(z.read("word/_rels/document.xml.rels"))


if __name__ == "__main__":
    unittest.main()
