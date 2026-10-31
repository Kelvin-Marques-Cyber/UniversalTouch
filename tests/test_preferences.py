import tempfile
from pathlib import Path
import unittest

from universal_touch.preferences import Preferences


class PreferenceTests(unittest.TestCase):
    def test_first_run_requires_tutorial_until_accepted_then_persists(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'settings.json'
            prefs = Preferences(path)
            self.assertFalse(prefs.tutorial_seen)
            prefs.accept_tutorial()
            self.assertTrue(Preferences(path).tutorial_seen)

    def test_corrupted_settings_do_not_skip_tutorial_or_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'settings.json'
            for invalid in ['broken','[]','null','{"tutorial_seen":"false"}']:
                path.write_text(invalid)
                self.assertFalse(Preferences(path).tutorial_seen)
