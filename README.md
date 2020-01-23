# tgym

基于[OpenAI Gym](https://gym.openai.com/)的程序化交易环境模拟器,

旨在为沪深A股基于增强学习的交易算法提供方便使用, 接近真实市场的交易环境

撮合规则: 基于最高，最低价成交, 对交易量不作限制

## 安装指南

支持: python 2.7, python 3.5+, 推荐使用 python3.7

**依赖**

[gym](https://github.com/openai/gym) [tushare](https://github.com/waditu/tushare)

```
pip install gym
pip install tushare
```

**安装**

```
git clone https://github.com/iminders/tgym
cd tgym
pip install -r requirements.txt
pip install -e .
```

## 使用

[Tushare token获取](https://tushare.pro/register?reg=124861)

设置 tushare token:

```
export TUSHARE_TOKEN=YOUR_TOKEN
```

Examples

实现        | 场景                                 | 使用例子
--------- | ---------------------------------- | ---------------------------------
simple.py | 单支股票， action=[v_sell, v_buy], 先卖再买 | `python tgym/envs/simple_test.py`
