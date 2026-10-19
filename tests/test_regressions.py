import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deadair = load_module("deadair", "skills/yt-edit/deadair.py")
chapters = load_module("chapters", "skills/yt-chapters/chapters.py")
retention = load_module("retention", "skills/yt-retention/retention.py")


class DeadAirRegressionTests(unittest.TestCase):
    def load_json(self, value):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as f:
            json.dump(value, f)
            path = f.name
        try:
            return deadair.load(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_json_list_of_segments_is_supported(self):
        result = self.load_json([
            {"start": 0, "end": 1, "text": "Hello"}
        ])
        self.assertEqual(result, [(0.0, 1.0, "Hello")])

    def test_json_object_with_segments_is_supported(self):
        result = self.load_json({
            "segments": [{"start": 0, "end": 1, "text": "Hello"}]
        })
        self.assertEqual(result, [(0.0, 1.0, "Hello")])


    def test_overlapping_cuts_are_counted_only_once(self):
        cuts = [
            {"start": 1, "end": 4},
            {"start": 3, "end": 6},
            {"start": 8, "end": 10},
        ]
        self.assertAlmostEqual(deadair.total_removed(cuts), 7.0)

    def test_empty_cuts_remove_zero_seconds(self):
        self.assertEqual(deadair.total_removed([]), 0.0)


class ChapterRegressionTests(unittest.TestCase):
    def test_draft_title_breaks_frequency_ties_alphabetically(self):
        text = "alpha bravo alpha bravo"
        self.assertEqual(chapters.draft_title(text), "Alpha Bravo")



    def test_zero_timestamp_uses_youtube_format(self):
        self.assertEqual(chapters.mmss(0), "00:00")


    def test_target_without_value_returns_clear_error(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, str(ROOT / "skills/yt-chapters/chapters.py"), "transcricao de teste", "--target"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

class RetentionAxisRegressionTests(unittest.TestCase):
    def test_explicit_seconds_axis_handles_values_below_100(self):
        self.assertFalse(retention.is_percent_axis([0, 10, 20, 30], "seconds"))

    def test_explicit_percent_axis_is_respected(self):
        self.assertTrue(retention.is_percent_axis([0, 10, 20, 30], "percent"))

    def test_auto_preserves_existing_detection(self):
        self.assertTrue(retention.is_percent_axis([0, 50, 100], "auto"))
        self.assertFalse(retention.is_percent_axis([0, 50, 120], "auto"))



class RetentionCliArgumentTests(unittest.TestCase):
    def run_cli(self, *args):
        import subprocess
        import sys

        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "skills/yt-retention/retention.py"),
                *args,
            ],
            capture_output=True,
            text=True,
        )

    def test_axis_without_value_returns_clear_error(self):
        result = self.run_cli("--axis")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_invalid_duration_returns_clear_error(self):
        result = self.run_cli("video.csv", "--duration", "abc")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_csv_filename_matching_duration_is_preserved(self):
        import csv
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "8"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for i in range(8):
                    writer.writerow([i * 10, 100 - i * 5])

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills/yt-retention/retention.py"),
                    "8", "--duration", "8", "--axis", "seconds", "--json",
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["points"], 8)


    def test_hook_leak_uses_last_point_in_opening_window(self):
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "retention.csv"
            points = [(0,100),(5,60),(10,90),(15,85),(20,80),(25,75),(30,70),(35,65)]
            with path.open("w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(points)
            result = self.run_cli(str(path), "--axis", "percent", "--json")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["hook_leak"], 10.0)




class DeadAirCliValidationTests(unittest.TestCase):
    def run_deadair(self, *args):
        import subprocess
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        return subprocess.run(
            [sys.executable, str(root / "skills/yt-edit/deadair.py"), *args],
            capture_output=True,
            text=True,
            cwd=root,
        )

    def test_missing_floor_value_returns_clear_error(self):
        result = self.run_deadair("--floor")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_non_numeric_floor_returns_clear_error(self):
        result = self.run_deadair("--floor", "abc")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_floor_values_return_clear_error(self):
        for value in ("NaN", "inf", "-inf", "0", "-1"):
            with self.subTest(value=value):
                result = self.run_deadair("--floor", value)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Erro:", result.stderr + result.stdout)
                self.assertNotIn("Traceback", result.stderr)

    def test_malformed_json_returns_clear_error(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "broken.json"
            source.write_text("{json inválido", encoding="utf-8")
            result = self.run_deadair(str(source), "--json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)


class SwipeCliValidationTests(unittest.TestCase):
    def test_missing_min_value_returns_clear_error(self):
        import subprocess
        import sys

        script = ROOT / "skills/yt-viral/swipe.py"
        result = subprocess.run(
            [sys.executable, str(script), "arquivo.json", "--min"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_min_values_return_clear_error(self):
        import subprocess
        import sys

        script = ROOT / "skills/yt-viral/swipe.py"
        for value in ("abc", "-1", "nan", "inf"):
            with self.subTest(value=value):
                result = subprocess.run(
                    [sys.executable, str(script), "arquivo.json", "--min", value],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("Erro:", result.stderr + result.stdout)
                self.assertNotIn("Traceback", result.stderr)


class TitleCliValidationTests(unittest.TestCase):
    def run_title(self, *args):
        import subprocess
        import sys

        script = ROOT / "skills/yt-package/title.py"
        return subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
        )

    def test_title_without_value_returns_clear_error(self):
        result = self.run_title("--title")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_thumb_without_value_returns_clear_error(self):
        result = self.run_title("--thumb")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Erro:", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
