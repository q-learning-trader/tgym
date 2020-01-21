# -*- coding:utf-8 -*-

import gym
import numpy as np

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
            无现金(满仓)，模拟环境可以买卖，实盘交易时的成交状态就不一样
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
        one_day = np.array([self.daily_return,
                            self.value_percent])
        state = np.array([one_day] * self.look_back_days)
        return state

    def get_init_state(self):
        """
        state 由两部分组成: 市场信息, 帐户信息(收益率, 持仓量)
        """
        equity_state = self.market.codes_history[
            self.code].iloc[:, self.look_back_days]
        portfolio_state = self.get_init_portfolio_state()
        return np.concate((equity_state, portfolio_state), axis=1)

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
        self.portfolio_value = self.invesment
        # 初始资金
        self.starting_cash = self.invesment
        # 可用资金
        self.cash = self.invesment
        self.pre_cash = self.cash

        # 每只股的 portfolio
        self.portfolio = Portfolio(code=self.code)
        self.states = self.get_init_state()
        return self.states

    def _next_state(self):
        equity_state =
        portfolio_state =


    def step(self, action):
        pass
