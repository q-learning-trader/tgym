# -*- coding:utf-8 -*-

import gym


class TEnv(gym.Env):
    """
    Trade enviroment
    """

    def __init__(self):
        pass

    def reset(self):
        raise NotImplementedError

    def step(self, action):
        raise NotImplementedError
