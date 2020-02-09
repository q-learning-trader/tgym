# -*- coding:utf-8 -*-
from tgym.envs.average import AverageEnv
from tgym.envs.multi_vol import MultiVolEnv
from tgym.envs.simple import SimpleEnv


def make_env(scenario, market, investment, look_back_days,
             used_infos, reward_fn):
    if scenario == "simple":
        return SimpleEnv(market, investment, look_back_days,
                         used_infos, reward_fn)
    elif scenario == "average":
        return AverageEnv(market, investment, look_back_days,
                          used_infos, reward_fn)
    elif scenario == "multi_vol":
        return MultiVolEnv(market, investment, look_back_days,
                           used_infos, reward_fn)
    else:
        raise "Not implement scenario %S" % scenario
