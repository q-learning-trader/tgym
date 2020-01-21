# -*- coding:utf-8 -*-

import logging
import os
import unittest

from market import Market

logging.root.setLevel(logging.ERROR)


class TestMarket(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        # NOTE: 需要在环境变量中设置 TUSHARE_TOKEN
        ts_token = os.getenv("TUSHARE_TOKEN")
        self.start = "20190101"
        self.end = "20200101"
        self.codes = ["000001.SZ"]
        self.indexs = ["000001.SH", "399001.SZ"]
        # self.indexs = []
        self.data_dir = "/tmp/tgym"
        self.m = Market(
            ts_token=ts_token,
            start=self.start,
            end=self.end,
            codes=self.codes,
            indexs=self.indexs,
            data_dir=self.data_dir)

    def test_init_codes_history(self):
        self.assertEqual(244, len(self.m.indexs_history["000001.SH"]))
        self.assertEqual(244, len(self.m.codes_history[self.codes[0]]))

    def test_is_suspended(self):
        self.assertTrue(self.m.is_suspended(code='000', datestr=''))
        self.assertTrue(self.m.is_suspended(code='000001.SZ', datestr=''))
        # 星期六
        self.assertTrue(self.m.is_suspended(code='000001.SZ',
                                            datestr='20191012'))
        self.assertFalse(self.m.is_suspended(code='000001.SZ',
                                             datestr='20191021'))


if __name__ == '__main__':
    unittest.main()
