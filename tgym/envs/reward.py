# -*- coding:utf-8 -*-


def simple(daily_return, *args):
    if daily_return <= 0:
        return -1
    else:
        return 1


def daily_return(daily_return, *args):
    return daily_return


def daily_pnl_add_count_rate(daily_return, highs, lows,
                             closes, sell_prices, buy_prices):
    fail, success, profit_count, loss_count = 0, 0, 0
    for i in range(len(highs)):
        # 买
        if buy_prices[i] >= lows[i]:
            success += 1
            if buy_prices[i] <= closes[i]:
                profit_count += 1
            else:
                loss_count += 1
        else:
            fail += 1

        # 卖
        if sell_prices[i] <= highs[i]:
            success += 1
            if sell_prices[i] <= closes[i]:
                loss_count += 1
            else:
                profit_count += 1
        else:
            fail += 1

    success_rate = (success * 2) / (success + fail)
    profit_rate = (profit_count * 2) / (profit_count + loss_count)

    reward = daily_return + success_rate + profit_rate

    return reward


def get_reward_func(name="simple"):
    if name == "simple":
        return simple
    if name == "daily_return":
        return daily_return
    if name == "daily_pnl_add_count_rate":
        return daily_pnl_add_count_rate


def main():
    r_func = get_reward_func(name="simple")
    assert -1 == r_func(0)
    assert 1 == r_func(0.01)
    assert -1 == r_func(-0.01)


if __name__ == '__main__':
    main()
