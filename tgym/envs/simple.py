# -*- coding:utf-8 -*-

import random

import gym
import numpy as np

from tgym.logger import logger
from tgym.portfolio import Portfolio


class SimpleEnv(gym.Env):
    """
    单支股票全量日内买卖, T0
    action: [scaled_sell_price, scaled_buy_price], 取值[-1, 1], 对应[-0.1, 0.1]
    先以sell_price 卖出, 再以 buy_price 买进
    NOTE(wen): 实际交易时，可能与模拟环境存在差异
        1. 先到最高价，然后再到最低价：与模拟环境一致
        2. 先到最低价，再到最高价，这里出价有两种情况
            有现金，则按最低价买进，与模拟环境一致
            无现金(满仓)，模拟环境可以成交，实盘交易时的成交状态不一定可以成交
    """

    def __init__(self, market, investment=100000.0, look_back_days=10):
        """
        investment: 初始资金
        look_back_days: 向前取数据的天数
        """
        self.market = market
        # Agent 数量
        self.n = 1
        self.action_space = 2
        self.code = market.codes[0]
        self.start = market.start
        self.end = market.end
        self.look_back_days = look_back_days
        self.investment = investment
        # 输入数据: 去除不复权数据 和复权因子
        self.input_size = len(market.codes_history[self.code].iloc[0]) - 10
        # 每一天放入state中的数据起始位置
        self.input_start_index = 10
        # 开市日期列表
        self.dates = market.codes_history[self.code].index.tolist()
        # 记录一个回合的收益序列
        self.returns = []

    def _init_current_time_id(self):
        return self.look_back_days

    def get_init_portfolio_state(self):
        # 初始持仓信息
        one_day = np.array([self.portfolio.daily_return,
                            self.portfolio.value_percent])
        state = np.array([one_day] * self.look_back_days)
        return state

    def get_init_state(self):
        """
        state 由两部分组成: 市场信息, 帐户信息(收益率, 持仓量)
        """
        equity_state = self.market.codes_history[
            self.code].iloc[:self.look_back_days].values
        portfolio_state = self.get_init_portfolio_state()
        return np.concatenate((equity_state, portfolio_state), axis=1)

    def reset(self):
        # 当前时间
        self.current_time_id = self._init_current_time_id()
        self.current_date = self.dates[self.current_time_id]
        self.dones = False
        # 当日的回报
        self.reward = 0
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

        # 每只股的 portfolio
        self.portfolio = Portfolio(code=self.code)
        self.state = self.get_init_state()
        return self.state

    def get_action_price(self, action):
        pre_close = self.market.get_pre_close_price(
            self.code, self.current_date)
        [v_sell, v_buy] = action
        # scale [-1, 1] to [-0.1, 0.1]
        pct_sell, pct_buy = v_sell * 0.1, v_buy * 0.1
        sell_price = round(pre_close * (1 + pct_sell), 2)
        buy_price = round(pre_close * (1 + pct_buy))
        return sell_price, buy_price

    def do_action(self, action, pre_portfolio_value, only_update):
        sell_price, buy_price = self.get_action_price(action)
        divide_rate = self.market.get_divide_rate(self.code, self.current_date)
        self.portfolio.update_before_trade(divide_rate)
        if not only_update:
            sell_cash_change, ok = self.sell(sell_price)
            buy_cash_change, ok = self.buy(buy_price)
            cash_change = buy_cash_change + sell_cash_change
            logger.debug("do_action: time_id: %d, %s, cash_change: %.1f" % (
                self.current_time_id, self.code, cash_change))

        close_price = self.market.get_close_price(self.code, self.current_date)
        self.portfolio.update_after_trade(
            close_price=close_price,
            cash_change=cash_change,
            pre_portfolio_value=pre_portfolio_value)

    def _next_state(self):
        equity_state = self.market.codes_history[self.code][self.current_date]
        portfolio_state = [self.portfolio.daily_return,
                           self.portfolio.value_percent]
        new_state = np.concatenate((equity_state, portfolio_state), axis=1)
        state = np.concatenate((self.state[1:, :], new_state), axis=0)
        self.current_time_id += 1
        self.current_date = self.dates[self.current_time_id]
        self.pre_cash = self.cash
        return state

    def step(self, action, only_update=False):
        """
        only_update为True时，表示buy_and_hold策略，可用于baseline策略
        """
        self.action = action
        self.info = {"orders": []}
        logger.debug("=" * 50 + "%s" % self.current_date + "=" * 50)
        logger.debug("current_time_id: %d" % self.current_time_id)
        logger.debug("step actions: %s" % str(action))

        # 到最后一天
        if self.current_date == self.end:
            self.done = True

        pre_portfolio_value = self.portfolio_value
        self.do_action(action, pre_portfolio_value, only_update)
        self.update_portfolio()
        self.update_value_percent()
        # 更新停牌信息，state中包含停牌信息
        self.update_is_suspended()
        self.state = self._next_state()
        self.info = {
            "orders": self.info["orders"],
            "current_date": self.current_date,
            "portfolio_value": round(self.portfolio_value, 1),
            "daily_pnl": round(self.daily_pnl, 1),
            "reward": self.reward}
        return self.state, self.reward, self.done, self.info

    def get_random_action(self):
        return [random.uniform(-1, 1), random.uniform(-1, 1)]
