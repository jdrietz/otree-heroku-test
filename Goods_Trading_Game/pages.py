from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import time
import numpy

class GroupWaitPage(WaitPage):
    """Wait for partner to load into game"""
    after_all_players_arrive = 'check_start_of_new_sequence'


class Trade_Screen(Page):
    """Player: Choose whether or not to trade"""
    form_model = 'player'
    form_fields = ['trade_choice']

    def vars_for_template(self):
        player = self.player
        session = self.session
        all_players = self.subsession.get_players()
        # Session-wide trade stats
        tr = numpy.zeros((3, 3), dtype=numpy.int8)
        acc = numpy.zeros((3, 3), dtype=numpy.int8)
        for pl in all_players:
            my_good = 2
            other_good = 2
            if pl.held_good == "Red":
                my_good = 0
            elif pl.held_good == "Blue":
                my_good = 1
            if pl.others_good == "Red":
                other_good = 0
            elif pl.others_good == "Blue":
                other_good = 1
            tr[other_good][my_good] += 1
            try:
                if pl.trade_choice is not None:
                    acc[other_good][my_good] += pl.trade_choice
            except TypeError:
                #This is expected...trade_choice is None for current player always
                pass
        acc_rates = []
        index_1 = 0
        while index_1 < len(tr):
            index_2 = 0
            while index_2 < len(tr[index_1]):
                if index_1 != index_2:
                    if tr[index_1][index_2] == 0:
                        acc_rates.append(0)
                    else:
                        acc_rates.append(acc[index_1][index_2] / tr[index_1][index_2])
                index_2 += 1
            index_1 += 1
        can_consume = (player.consumable_good == player.held_good)
        return dict(
            num_players=session.num_participants,
            player_can_consume = can_consume,
            player_stats=player.in_previous_rounds(),
            trade_rb = tr[0,1],
            trade_rg = tr[0,2],
            trade_br = tr[1,0],
            trade_bg = tr[1,2],
            trade_gr = tr[2,0],
            trade_gb = tr[2,1],
            acc_rb = acc[0,1],
            acc_rg = acc[0, 2],
            acc_br = acc[1, 0],
            acc_bg = acc[1, 2],
            acc_gr = acc[2, 0],
            acc_gb = acc[2, 1],
            rate_rb = acc_rates[0],
            rate_rg=acc_rates[1],
            rate_br=acc_rates[2],
            rate_bg=acc_rates[3],
            rate_gr=acc_rates[4],
            rate_gb=acc_rates[5],
            showtable=Constants.show_table,
            num_red_prod=Constants.num_production[0],
            num_blue_prod=Constants.num_production[1],
            num_green_prod = Constants.num_production[2],
            num_red_cons=Constants.num_consumable[0],
            num_blue_cons=Constants.num_consumable[1],
            num_green_cons=Constants.num_consumable[2],
            tot_cons=(Constants.num_consumable[0]+Constants.num_consumable[1]+Constants.num_consumable[2]),
            red_perc=round(Constants.num_consumable[0]/(Constants.num_consumable[0]+Constants.num_consumable[1]+Constants.num_consumable[2])*100),
            blue_perc=round(Constants.num_consumable[1]/(Constants.num_consumable[0]+Constants.num_consumable[1]+Constants.num_consumable[2])*100),
            green_perc=round(Constants.num_consumable[2] / (Constants.num_consumable[0] + Constants.num_consumable[1] + Constants.num_consumable[2])*100),
            red_prod_height=Constants.num_production[0] * Constants.prod_graph_height,
            blue_prod_height=Constants.num_production[1] * Constants.prod_graph_height,
            green_prod_height=Constants.num_production[2] * Constants.prod_graph_height
        )


class ResultsWaitPage(WaitPage):
    """Wait for partner to select trade choice"""
    after_all_players_arrive = 'period_end'
    wait_for_all_groups = True


class Results(Page):
    """Only show results after ALL participants have submitted trade choice for this round"""
    """Force this page to be 10 seconds long..."""
    timeout_seconds = 10


page_sequence = [GroupWaitPage, Trade_Screen, ResultsWaitPage, Results]
