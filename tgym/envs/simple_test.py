# -*- coding:utf-8 -*-

import logging
import os
import unittest

from simple import SimpleEnv
from tgym.market import Market

logging.root.setLevel(logging.DEBUG)


class TestSimple(unittest.TestCase):
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
        self.invesment = 100000.0
        self.look_back_days = 10
        self.env = SimpleEnv(
            self.m,
            investment=self.invesment,
            look_back_days=self.look_back_days)

    def test_buy_and_hold(self):
        action = [0, 0]
        self.env.reset()
        state, reward, done, info = self.env.step(action, only_update=False)
        while not done:
            _, _, done, _ = self.env.step(action, only_update=True)


if __name__ == '__main__':
    unittest.main()
