# -*- coding:utf-8 -*-
import tgym.envs as envs


def make_env(scenario="", market=None, investment=100000.0, look_back_days=10):
    if scenario == "simple":
        return envs.simple.SimpleEnv(market, investment, look_back_days)
    elif scenario == "average":
        return envs.average.AverageEnv(market, investment, look_back_days)
    elif scenario == "multi_vol":
        return envs.multi_vol.MultiVolEnv(market, investment, look_back_days)
    else:
        raise "Not implement scenario %S" % scenario
