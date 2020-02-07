# -*- coding:utf-8 -*-
from tgym.envs.average import AverageEnv
from tgym.envs.multi_vol import MultiVolEnv
from tgym.envs.simple import SimpleEnv


def make_env(scenario="", market=None, investment=100000.0, look_back_days=10):
    if scenario == "simple":
        return SimpleEnv(market, investment, look_back_days)
    elif scenario == "average":
        return AverageEnv(market, investment, look_back_days)
    elif scenario == "multi_vol":
        return MultiVolEnv(market, investment, look_back_days)
    else:
        raise "Not implement scenario %S" % scenario
