# -*- coding:utf-8 -*-
import gym
import numpy as np

from tgym.logger import logger
from tgym.portfolio import Portfolio


class BaseEnv(gym.Env):
    def __init__(self, market=None, investment=100000.0, look_back_days=10,
                 used_infos=["equities_hfq_info", "indexs_info"]):
        """
        investment: 初始资金
        look_back_days: 向前取数据的天数
        """
        self.market = market
        # 股票数量
        self.n = len(market.codes)
        self.codes = market.codes
        self.start = market.start
        self.end = market.end
        self.look_back_days = look_back_days
        self.investment = investment
        # 输入数据: 个股信息 + 指数信息
        self.used_infos = used_infos
        self.market_info_size = self.get_market_info_size()
        # 开市日期列表
        self.dates = market.open_dates
        # 记录一个回合的收益序列
        self.returns = []

    def get_market_info_size(self):
        size = 0
        for info_name in self.used_infos:
            size += self.market.get_info_size(info_name)
        return size

    def _init_current_time_id(self):
        return self.look_back_days

    def get_market_info(self, date):
        info = []
        for info_name in self.used_infos:
            data = self.market.market_info[date][info_name]
            info.extend(data)
        return np.array(info)

    def sell(self, id, price, target_pct):
        # id: code id
        code = self.codes[id]
        logger.debug("sell %s, bid price: %.2f" % (code, price))
        ok, price = self.market.sell_check(
            code=code,
            datestr=self.current_date,
            bid_price=price)
        if ok:
            # 全仓卖出
            cash_change, price, vol = self.portfolios[
                id].order_target_percent(
                    percent=target_pct, price=price,
                    pre_portfolio_value=self.portfolio_value,
                    current_cash=self.cash)
            self.cash += cash_change
            if vol != 0:
                self.info["orders"].append(["sell", code,
                                            round(cash_change, 1),
                                            round(price, 2), vol])
            logger.debug("sell %s target_percent: 0, cash_change: %.3f" %
                         (code, cash_change))
            return cash_change, ok
        return 0, ok

    def buy(self, id, price, target_pct):
        # id: code id
        code = self.codes[id]
        logger.debug("buy %s, bid_price: %.2f" % (code, price))
        ok, price = self.market.buy_check(
            code=code,
            datestr=self.current_date,
            bid_price=price)
        pre_cash = self.cash
        if ok:
            # 分仓买进
            cash_change, price, vol = self.portfolios[id].order_target_percent(
                percent=target_pct, price=price,
                pre_portfolio_value=self.portfolio_value,
                current_cash=self.cash)
            self.cash += cash_change
            if vol != 0:
                self.info["orders"].append(["buy", code,
                                            round(cash_change, 1),
                                            round(price, 2), vol])
            logger.debug("buy %s cash: %.1f, cash_change: %1.f" %
                         (code, pre_cash, cash_change))
            return cash_change, ok
        return 0, ok

    def get_init_obs():
        raise NotImplementedError

    def reset(self):
        # 当前时间
        self.current_time_id = self._init_current_time_id()
        self.current_date = self.dates[self.current_time_id]
        self.done = False
        # 当日的回报
        self.reward = 0
        self.rewards = [0] * self.n
        # 累计回报
        self.total_reward = 0.0
        # 当日订单集合
        self.info = {"orders": []}
        # 总权益
        self.portfolio_value = self.investment
        # 初始资金
        self.starting_cash = self.investment
        # 可用资金
        self.cash = self.investment
        self.pre_cash = self.cash
        self.total_pnl = 0

        # 每只股的 portfolio
        self.portfolios = []
        for code in self.codes:
            self.portfolios.append(Portfolio(code=code))
        self.obs = self.get_init_obs()
        self.portfolio_value_logs = []
        return self.obs
