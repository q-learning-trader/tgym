# -*- coding:utf-8 -*-


from tgym.core import TEnv


class SimpleEnv(TEnv):
    """
    单支股票全量日内买卖
    action: [sell_price, buy_price]
    """

    def __init__(self):
        self.action_space = 2

    def reset(self):
        pass

    def step(self, action):
        pass
