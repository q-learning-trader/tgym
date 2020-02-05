# -*- coding:utf-8 -*-
import random

import gym
import numpy as np

from tgym.logger import logger
from tgym.portfolio import Portfolio


class MultiVolEnv(gym.Env):
    """
    多支股票平均分仓日内买卖
    action: [scaled_sell_price, scaled_sell_percent,
    scaled_buy_price, scaled_buy_percent]*n, 所有取值[-1, 1], 价格对应[-0.1, 0.1],
    即: 出价较前一交易日的涨跌幅. percent对应[0, 1], 表示仓位占比.
    n: 是股票的个数
    对每支股票, 先以sell_price 卖出目标仓位, 再以 buy_price 买进目标仓位
    NOTE(wen): 实际交易时，可能与模拟环境存在差异
        1. 先到最高价，然后再到最低价：与模拟环境一致
        2. 先到最低价，再到最高价，这里出价有两种情况
            有现金，则按最低价买进，与模拟环境一致
            无现金(满仓)，模拟环境可以成交，实盘交易时的成交状态不一定可以成交
    """

    def __init__(self, market=None, investment=100000.0, look_back_days=10):
        """
        investment: 初始资金
        look_back_days: 向前取数据的天数
        """
        self.market = market
        # 股票数量
        self.n = len(market.codes)
        self.action_space = 2 * self.n
        self.codes = market.codes
        self.start = market.start
        self.end = market.end
        self.look_back_days = look_back_days
        self.investment = investment
        # 输入数据: 去除不复权数据 和复权因子
        self.input_size = len(market.codes_history[self.codes[0]].iloc[0]) - 10
        # 每一天放入obs中的数据起始位置
        self.input_start_index = 10
        # 开市日期列表
        self.dates = self.get_open_dates()
        # 记录一个回合的收益序列
        self.returns = []

    def get_open_dates(self):
        dates = []
        for code in self.codes:
            dates.extend(self.market.codes_history[code].index.tolist())
        dates = list(set(dates))
        dates.sort()
        return dates

    def _init_current_time_id(self):
        return self.look_back_days

    def get_init_portfolio_obss(self):
        # 初始持仓 状态
        one_day = np.array([0, 0])
        one_obs = np.array([one_day] * self.look_back_days)
        obss = [one_obs] * self.n
        return obss

    def get_init_obss(self):
        """
        obs 由两部分组成: 市场信息, 帐户信息(收益率, 持仓量)
        """
        obss = []
        portfolio_obss = self.get_init_portfolio_obss()
        for i in range(self.n):
            code = self.codes[i]
            equity_obs = self.market.codes_history[
                code].iloc[:self.look_back_days].values
            obs = np.concatenate((equity_obs, portfolio_obss[i]), axis=1)
            obss.append(obs)
        return obss

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
        self.obs = self.get_init_obss()
        self.portfolio_value_logs = []
        return self.obs

    def get_action_price(self, v_price, code):
        pre_close = self.market.get_pre_close_price(
            code, self.current_date)
        logger.debug("%s %s pre_close: %.2f" %
                     (self.current_date, code, pre_close))
        # scale [-1, 1] to [-0.1, 0.1]
        pct = v_price * 0.1
        price = round(pre_close * (1 + pct), 2)
        return price

    def get_action_target_pct(self, v_vol):
        # scale [-1, 1] to [0, 1]
        target_pct = v_vol * 0.5 + 0.5
        return target_pct

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

    def update_portfolio(self):
        pre_portfolio_value = self.portfolio_value
        self.market_value = 0
        self.daily_pnl = 0
        self.pnl = 0
        self.transaction_cost = 0
        self.all_transaction_cost = 0
        for p in self.portfolios:
            self.market_value += p.market_value
            self.daily_pnl += p.daily_pnl
            self.pnl += p.pnl
            self.transaction_cost += p.transaction_cost
            self.all_transaction_cost += p.all_transaction_cost
        self.total_pnl += self.pnl

        # 当日收益率 更新
        if pre_portfolio_value == 0:
            self.daily_return = 0
        else:
            self.daily_return = self.daily_pnl / pre_portfolio_value
        # update portfolio_value
        self.portfolio_value = self.market_value + self.cash
        self.portfolio_value_logs.append(self.portfolio_value)

    def update_reward(self):
        # NOTE(wen): 如果今天盈利，则reward=1, 否则reward=-1
        # reward决定算法的搜索方向, 建议设置为一个连续可导函数
        if self.daily_pnl <= 0:
            self.reward = -1
        else:
            self.reward = 1
        # 每一只股的reward
        for i in range(self.n):
            if self.portfolios[i].daily_pnl <= 0:
                self.rewards[i] = -1
            else:
                self.rewards[i] = 1

    def update_value_percent(self):
        if self.portfolio_value == 0:
            self.value_percent = 0.0
        else:
            self.value_percent = self.market_value / self.portfolio_value
        for i in range(self.n):
            self.portfolios[i].update_value_percent(self.portfolio_value)

    def do_action(self, action, pre_portfolio_value, only_update):
        """
        only_update: 仅更新Portfolio, 不做操作, 即:buy_and_hold策略
        """
        cash_change = 0
        # 更新拆分信息
        for i in range(self.n):
            code = self.codes[i]
            divide_rate = self.market.get_divide_rate(code, self.current_date)
            self.portfolios[i].update_before_trade(divide_rate)
        if not only_update:
            # 卖出
            for i in range(self.n):
                code = self.codes[i]
                act_i = action[4 * i: 4 * (i + 1)]
                sell_price = self.get_action_price(act_i[0], code)
                target_pct = self.get_action_target_pct(act_i[1])
                sell_cash_change, ok = self.sell(i, sell_price, target_pct)
                cash_change += sell_cash_change
            # 买进
            for i in range(self.n):
                code = self.codes[i]
                act_i = action[4 * i: 4 * (i + 1)]
                buy_price = self.get_action_price(act_i[2], code)
                target_pct = self.get_action_target_pct(act_i[3])
                buy_cash_change, ok = self.buy(i, buy_price, target_pct)
                cash_change += buy_cash_change

        logger.debug("do_action: time_id: %d, cash_change: %.1f" % (
            self.current_time_id, cash_change))

        # update
        for i in range(self.n):
            code = self.codes[i]
            close_price = self.market.get_close_price(code, self.current_date)
            self.portfolios[i].update_after_trade(
                close_price=close_price,
                cash_change=cash_change,
                pre_portfolio_value=pre_portfolio_value)

    def _next(self):
        obss = []
        for i in range(self.n):
            code = self.codes[i]
            equity_obs = self.market.codes_history[
                code].loc[self.current_date].values
            portfolio_obs = np.array([self.portfolios[i].daily_return,
                                      self.portfolios[i].value_percent])
            new_obs = np.concatenate((equity_obs, portfolio_obs), axis=0)
            obs = np.concatenate((self.obs[i][1:, :],
                                  np.array([new_obs])), axis=0)
            obss.append(obs)
        if not self.done:
            self.current_time_id += 1
            self.current_date = self.dates[self.current_time_id]
        self.pre_cash = self.cash
        return obss

    def step(self, action, only_update=False):
        """
        only_update为True时，表示buy_and_hold策略，可作为一种baseline策略
        """
        self.action = action
        self.info = {"orders": []}
        logger.debug("=" * 50 + "%s" % self.current_date + "=" * 50)
        logger.debug("current_time_id: %d, portfolio: %.1f" %
                     (self.current_time_id, self.portfolio_value))
        logger.debug("step action: %s" % str(action))

        # 到最后一天
        if self.current_date == self.dates[-1]:
            self.done = True

        pre_portfolio_value = self.portfolio_value
        self.do_action(action, pre_portfolio_value, only_update)
        self.update_portfolio()
        self.update_value_percent()
        self.obs = self._next()
        self.info = {
            "orders": self.info["orders"],
            "current_date": self.current_date,
            "portfolio_value": round(self.portfolio_value, 1),
            "daily_pnl": round(self.daily_pnl, 1),
            "reward": self.reward}
        return self.obs, self.reward, self.done, self.info, self.rewards

    def get_random_action(self):
        return [random.uniform(-1, 1) for i in range(self.n * 4)]
