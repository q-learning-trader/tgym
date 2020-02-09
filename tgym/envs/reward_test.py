import unittest

from tgym.envs.reward import mean_squared_error


class TestReward(unittest.TestCase):
    def test_mean_squared_error(self):
        a = [2.0, 4.0]
        b = [1.0, 4.0]
        mse = mean_squared_error(a, b)
        self.assertEqual(0.125, mse)


if __name__ == '__main__':
    unittest.main()
