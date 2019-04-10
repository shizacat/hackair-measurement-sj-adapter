import asyncio
import unittest
from datetime import datetime, timezone

from lib.hackair_async import HackAIR


class Tests(unittest.TestCase):

    def setUp(self):
        self.obj = HackAIR("")

    # def tearDown(self):
    #     self.obj.close()

    def test__to_date(self):
        r = self.obj._to_date("2016-10-31T06:33:44.866Z")
        self.assertEqual(
            datetime(2016, 10, 31, 6, 33, 44, tzinfo=timezone.utc),
            r
        )

    def test__get_range_date(self):

        with self.subTest("1"):
            dts = datetime(2016, 10, 31, 6, 33, 44, tzinfo=timezone.utc)
            dte = datetime(2016, 10, 31, 7, 0, 0, tzinfo=timezone.utc)
            r = self.obj._get_range_date(dts, dte)
            self.assertEqual(r, [(dts, dte)])

        with self.subTest("1"):
            dts = datetime(2016, 10, 31, 6, 33, 44, tzinfo=timezone.utc)
            dte = datetime(2016, 10, 31, 9, 0, 0, tzinfo=timezone.utc)
            print(r)
            r = self.obj._get_range_date(dts, dte)
            self.assertEqual(
                r,
                [
                    (
                        datetime(2016, 10, 31, 6, 33, 44, tzinfo=timezone.utc),
                        datetime(2016, 10, 31, 7, 33, 44, tzinfo=timezone.utc)
                    ),
                    (
                        datetime(2016, 10, 31, 7, 33, 45, tzinfo=timezone.utc),
                        datetime(2016, 10, 31, 8, 33, 44, tzinfo=timezone.utc)
                    ),
                    (
                        datetime(2016, 10, 31, 8, 33, 45, tzinfo=timezone.utc),
                        datetime(2016, 10, 31, 9, 0, tzinfo=timezone.utc)
                    )
                ]
            )
