# -*- coding:utf-8 -*-


import gym


class SimpleEnv(gym.Env):
    """
    单支股票全量日内买卖
    action: [sell_price, buy_price]
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
        self.portfolios = []

    def reset(self):
        # 当前时间
        self.current_time_id = self._init_current_time_id()
        self.current_date = self.dates[self.current_time_id]
        self.dones = [False] * self.agent_num
        # 当日的回报
        self.reward = 0
        # 当日每个agent 的回报
        self.rewards = [0.0] * self.agent_num
        # 累计回报
        self.total_reward = 0.0
        self.info = {"orders": []}
        starting_cash = self.invesment
        # 总权益
        self.portfolio_value = starting_cash
        # 初始资金
        self.starting_cash = starting_cash
        # 可用资金
        self.cash = starting_cash
        self.pre_cash = self.cash
        # 市值
        self.market_value = 0.0
        # 当日盈亏
        self.daily_pnl = 0.0
        # 累计盈亏, Profit and Loss
        self.pnl = 0.0
        # 当日收益率
        self.daily_return = 0.0
        # 当日交易费
        self.transaction_cost = 0.0
        # 累计交易费
        self.all_transaction_cost = 0.0
        # 获得该持仓的市场价值在股票投资组合价值中所占比例，取值范围[0, 1]
        self.value_percent = 0.0
        # 每只股的 portfolio
        self.portfolios = [Portfolio(
                code=self.codes[i]) for i in range(self.agent_num)]

        self.states = self.get_init_state()
        return self.states

    def step(self, action):
        pass
