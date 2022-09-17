import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = Path('./data')
PLOTS_DIR = Path('./plots')

DATA_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


class CasinoSimulator:
    """
    Simulator of the bet approach assuming that you should double bet value if you loose to achieve profit
    in game in which change for the win is 50%.
    """

    def __init__(self, n_games, chosen_color, start_money, rate, first_game_money):
        """Parameters
        ---------------------------------------------
        :param n_games: Number of games to play. When ths number achieved game is finished after first win.
        :param chosen_color: Color for bet - black or red.
        :param start_money: Money the gamer has at the beginning.
        :param rate: Rate of return.
        :param first_game_money: Money to bet in first game.
        """
        self.chosen_color = chosen_color
        self.current_money = start_money
        self._n_games = n_games
        self._start_money = start_money
        self._rate = rate
        self._first_game_money = first_game_money

    @property
    def n_games(self):
        return self._n_games

    @property
    def start_money(self):
        return self._start_money

    @property
    def rate(self):
        return self._rate

    @property
    def first_game_money(self):
        return self._first_game_money

    def one_bet(self, color, won_money, one_game_money):
        """Provide results for one bet.

        :param color: Sampled color.
        :param won_money: Money won until current bet.
        :param one_game_money: Bet value in current game.
        :return: Money after bet, Bet value for next bet.
        """

        if color != self.chosen_color:
            won_money -= one_game_money
            one_game_money *= self._rate
        else:
            won_money += one_game_money
            one_game_money = self._first_game_money
        current_money = self._start_money + won_money

        return current_money, one_game_money

    def single_game_simulation(self, play_till_win=True):
        """One game simulation for one gamer.

        :param play_till_win: If True player finishes game when first win after minimum number of bets.
        :return: Money player have after game.
        """
        won_money = 0
        self.current_money = self._start_money
        one_game_money = self._first_game_money

        for i in range(self._n_games):
            color = np.random.choice(["black", "red"])
            self.current_money, one_game_money = self.one_bet(color, won_money, one_game_money)

            if self.current_money < 0:
                return 0

        if color != self.chosen_color and play_till_win:
            while color != self.chosen_color:
                color = np.random.choice(["black", "red"])
                self.current_money, one_game_money = self.one_bet(color, won_money, one_game_money)

        return self.current_money

    def game_simulation(self, n_gamers, play_till_win=True):
        """One game simulation for multiple gamers.

        :param play_till_win: If True player finishes game when first win after minimum number of bets.
        :return: Money players have after game.
        """
        won_money = []
        for i in range(n_gamers):
            won_money.append(self.single_game_simulation(play_till_win=play_till_win))

        return pd.Series(won_money) - self._start_money

    def loose_chance(self, n_gamers, play_till_win=True):
        """Chance of loosing money counted based on simulations.

        :param n_gamers: Number of players.
        :param play_till_win:  If True player finishes game when first win after minimum number of bets.
        :return:
        """

        won_money = self.game_simulation(n_gamers, play_till_win)

        return won_money[won_money < 0].shape[0] / won_money.shape[0]


def full_simulation(n_gamers, chosen_color, n_games_opt, first_game_money_opt, start_money, rate, play_till_win=True):
    """Simulate some options, provide statistics and provide histograms.

    :param n_gamers: Number of players.
    :param chosen_color: Color the players bet.
    :param n_games_opt: list with number of games to simulate.
    :param first_game_money_opt: List with starting money options to simulate.
    :param start_money: Money players has at the beginning.
    :param rate: Rate of return
    :param play_till_win:  If True player finishes game when first win after minimum number of bets.
    """

    df = pd.DataFrame()
    loose_chance = []
    for n_games, first_game_money in itertools.product(n_games_opt, first_game_money_opt):
        name = f"n_games_{n_games}_first_money_{first_game_money}"

        casino = CasinoSimulator(n_games, chosen_color, start_money, rate, first_game_money)
        result = casino.game_simulation(n_gamers, play_till_win=play_till_win)

        result.name = name
        df = df.append(result)
        loosers_perc = casino.loose_chance(n_gamers, play_till_win=True)
        loose_chance.append((name, loosers_perc))
    df = df.T
    stat_df = df.describe(percentiles=(0.1, 0.25, 0.5, 0.75, 0.85, 0.95, .99)).T
    loose_df = pd.DataFrame(loose_chance, columns=["game_type", "loose_chance"]).set_index("game_type")
    stat_df = stat_df.merge(loose_df, left_index=True, right_index=True).sort_values("50%")

    stat_df.to_excel(DATA_DIR / f"statistics_play_till_win_{play_till_win}.xlsx")
    print(stat_df)

    df.hist(figsize=(12, 8), bins=15)
    plt.savefig(PLOTS_DIR / f"hist_play_till_win_{play_till_win}.png")
    plt.show()


def main():
    # set variables

    n_gamers = 1000
    n_games_opt = [10, 30, 50]
    chosen_color = "black"
    start_money = 1000
    rate = 2
    first_game_money_opt = [20, 50, 100]

    for play_till_win in [True, False]:
        full_simulation(n_gamers, chosen_color, n_games_opt, first_game_money_opt, start_money, rate,
                        play_till_win=play_till_win)


if __name__ == '__main__':
    main()
