import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "skills/yt-chapters/chapters.py",
    "skills/yt-edit/deadair.py",
    "skills/yt-package/title.py",
    "skills/yt-retention/retention.py",
    "skills/yt-script/hookscore.py",
    "skills/yt-viral/swipe.py",
]


class CliHelpTests(unittest.TestCase):
    def test_help_exits_successfully_for_every_script(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(ROOT / script), "--help"],
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{script} não aceitou --help.\n"
                    f"Saída: {result.stdout}\nErro: {result.stderr}",
                )
                self.assertTrue(
                    result.stdout.strip() or result.stderr.strip(),
                    f"{script} não exibiu nenhuma ajuda.",
                )


if __name__ == "__main__":
    unittest.main()
