import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wait_daily_editorial import validate_date
class DateGuard(unittest.TestCase):
    def test_current(self):
        validate_date({'date':'2026-10-25','verified_on':'2026-10-25'},'2026-10-25')
    def test_stale_or_incomplete(self):
        for d in [{},{'date':'2026-10-24','verified_on':'2026-10-24'},{'date':'2026-10-25','verified_on':'2026-10-24'}]:
            with self.assertRaises(ValueError):validate_date(d,'2026-10-25')
