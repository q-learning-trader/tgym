# -*- coding:utf-8 -*-
import logging
import os

import pandas as pd
import tushare as ts

logger = logging.getLogger()


class Market:
    """
    模拟市场，加载环境所需要的数据
    NOTE(wen):
        从多数实验可以发现，使用后复权的数据做为模型输入，性能更优， Market统一使用
        后复权数据做模型的输入, 而不复权的数据做买卖的判断
    indexs:
        000001.SH: 上证指数
        399001.SZ: 深证成指
        ...
    NOTE(wen): 使用tushare下载指数日线信息需要在tushare.pro帐户中有200积分
    data_dir: 存储数据文件的目录，以降低重复下载的频率
    """

    def __init__(self,
                 ts_token="",
                 start="20190101",
                 end="20200101",
                 codes=["000001.SZ"],
                 indexs=["000001.SH", "399001.SZ"],
                 data_dir="/tmp/tgym"):
        ts.set_token(ts_token)
        self.start = start
        self.end = end
        self.codes = codes
        self.indexs = indexs
        self.data_dir = data_dir

        self.init_codes_history()

    def get_code_history(self, code, adj=None):
        return ts.pro_bar(
            ts_code=code, adj=adj,
            start_date=self.start, end_date=self.end)

    def load_codes_history(self):
        self.codes_history = {}
        for code in self.codes:
            dir = os.path.join(self.data_dir, code)
            if not os.path.exists(dir):
                os.makedirs(dir)
            data_path = os.path.join(dir,
                                     self.start + "-" + self.end + ".csv")
            if os.path.exists(data_path):
                self.codes_history[code] = pd.read_csv(data_path)
            else:
                # 不复权
                df_bfq = self.get_code_history(code, adj=None)
                df_bfq = df_bfq.drop(columns=["ts_code"], axis=1)
                # 后复权
                df_hfq = self.get_code_history(code, adj="hfq")
                df_hfq = df_hfq.drop(columns=["ts_code"], axis=1)
                df = pd.merge(df_bfq, df_hfq,
                              on='trade_date', how='left',
                              suffixes=('', '_hfq'))
                # 拆分因子
                col_name = df.columns.tolist()
                col_name.insert(0, 'adj_factor')
                df = df.reindex(columns=col_name)
                df["adj_factor"] = df["close_hfq"] / df["close"]
                df = df.sort_values(by="trade_date", ascending=True)
                df = df.set_index("trade_date")
                df.to_csv(data_path)
                self.codes_history[code] = df

    def load_indexs_history(self):
        self.indexs_history = {}
        for code in self.indexs:
            dir = os.path.join(self.data_dir, "indexs", code)
            if not os.path.exists(dir):
                os.makedirs(dir)
            data_path = os.path.join(dir,
                                     self.start + "-" + self.end + ".csv")
            if os.path.exists(data_path):
                self.indexs_history[code] = pd.read_csv(data_path)
            else:
                # 不复权
                pro = ts.pro_api()
                df = pro.index_daily(ts_code=code,
                                     start_date=self.start,
                                     end_date=self.end)
                df = df.drop(columns=["ts_code"], axis=1)
                df = df.sort_values(by="trade_date", ascending=True)
                df = df.set_index("trade_date")
                df.to_csv(data_path)
                self.indexs_history[code] = df

    def init_codes_history(self):
        """
        self.codes_history: dict
        每条记录由两部分数据组成: 股票数据，指数数据
        股票数据包含:
            复权因子: adj_factor
            不复权OHLCV, ...
            后复权OHLCV, ...
        指数数据:
            指数1 OHLCV, ...
            指数2 OHLCV, ...
        例如: 当codes=["000001.SZ"], indexs=["000001.SH", "399001.SZ"] 时
        self.codes_history[].columns的值为:
        [u'adj_factor', u'open', u'high', u'low', u'close', u'pre_close',
        u'change', u'pct_chg', u'vol', u'amount', u'open_hfq', u'high_hfq',
        u'low_hfq', u'close_hfq', u'pre_close_hfq', u'change_hfq',
        u'pct_chg_hfq', u'vol_hfq', u'amount_hfq', u'close_1', u'open_1',
        u'high_1', u'low_1', u'pre_close_1', u'change_1', u'pct_chg_1',
        u'vol_1', u'amount_1', u'close_2', u'open_2', u'high_2', u'low_2',
        u'pre_close_2', u'change_2', u'pct_chg_2', u'vol_2', u'amount_2']
        """
        self.load_codes_history()
        self.load_indexs_history()
        for code in self.codes:
            if len(self.indexs) > 0:
                for i in range(len(self.indexs)):
                    index = self.indexs[i]
                    self.codes_history[code] = self.codes_history[code].merge(
                        self.indexs_history[index],
                        left_index=True, right_index=True,
                        sort=True,
                        suffixes=('', '_%d' % (i + 1))
                    )
                    drop_column = "trade_date_%d" % (i + 1)
                    if drop_column in self.codes_history[code].columns:
                        self.codes_history[code] = self.codes_history[
                            code].drop(columns=[drop_column], axis=1)

                self.codes_history[code] = self.codes_history[
                    code].sort_values(by="trade_date", ascending=True)
                if "trade_date" in self.codes_history[code].columns:
                    self.codes_history[code] = self.codes_history[
                        code].set_index("trade_date")
            # index int64 -> str
            self.codes_history[code].index = self.codes_history[
                code].index.astype(str, copy=False)

    def is_suspended(self, code='', datestr=''):
        # 是否停牌，是：返回 True, 否：返回 False
        if code not in self.codes_history:
            return True
        if datestr not in self.codes_history[code].index:
            return True
        return False

    def buy_check(self, code='', datestr='', bid_price=None):
        # 返回：OK, 成交价
        ok = False
        # 停牌
        if self.is_suspended(code, datestr):
            return ok, 0
        # 获取当天标的信息
        [open, high, low, pct_change] = self.codes_history[code].loc[
            datestr, ["open", "high", "low", "pct_chg"]]
        # 涨停封板, 无法买入
        if low == high and pct_change > self.top_pct_change:
            logger.debug(u"sell_check %s %s 涨停法买进" % (code, datestr))
            return ok, 0
        # 买入竞价低于最低价，不能成交
        if bid_price < low:
            return ok, 0
        # 买入竞价高于最低价， 可以成交
        if bid_price >= low:
            return True, min(bid_price, high)

    def sell_check(self, code='', datestr='', bid_price=None):
        # 返回：OK, 成交价
        ok = False
        # 停牌
        if self.is_suspended(code, datestr):
            return ok, 0
        # 获取当天标的信息
        [open, high, low, pct_change] = self.codes_history[code].loc[
            datestr, ["open", "high", "low", "pct_chg"]]
        # 跌停封板， 不能卖出
        if low == high and pct_change < -self.top_pct_change:
            logger.debug(u"sell_check %s %s 跌停无法卖出" % (code, datestr))
            return ok, 0
        # 卖出竞价高于最高价，不可以成交
        if bid_price > high:
            return ok, 0
        # 卖出竞价在最低最高价之间， 可以成交，按出价成交
        # NOTE: 这里卖出竞价低于最低价时，可以成交，按最低价成交
        if bid_price <= high:
            ok = True
            return ok, max(bid_price, low)

    def get_pre_close_price(self, code, datestr):
        if datestr in self.codes_history[code].index:
            return self.codes_history[code].loc[datestr]["pre_close"]
        # 如果当天停牌
        df = self.codes_history[code]
        df_ = df[df.index < datestr]
        return df_.iloc[-1]["pre_close"]

    def get_pre_adj_factor(self, code, datestr):
        df = self.codes_history[code]
        df_ = df[df.index < datestr]
        return df_.iloc[-1]["adj_factor"]

    def get_adj_factor(self, code, datestr):
        if self.is_suspended(code=code, datestr=datestr):
            return self.get_pre_adj_factor(code, datestr)
        else:
            return self.codes_history[code].loc[datestr]["adj_factor"]

    def get_divide_rate(self, code, datestr):
        pre_adj_factor = self.get_pre_adj_factor(code)
        current_adj_factor = self.get_adj_factor(code, datestr)
        return current_adj_factor / pre_adj_factor
