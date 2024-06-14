from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)
import random
import numpy

doc = """
Testing version of the Goods Trading Game
"""
#NOTE: Currency per point: $1.00
#USING A TEST NUMBER OF 6 PLAYERS

class Constants(BaseConstants):
    name_in_url = 'testing_goods_trading'
    players_per_group = 2
    num_rounds = 20
    #This is the set of periods that start a new sequence
    periods = [1,4,13]
    goods = ['Red', 'Blue', 'Green']
    #Ensure these three numbers add up to the total number of players for the game
    #THESE NUMBERS GO RED, BLUE, GREEN (The order of the goods array)!!!
    num_production = [2,2,2]
    num_consumable = [3,2,1]
    show_table = False
    #prod_graph_height is for the CSS graph (good-graph)...
    #prod_graph_height = # pixels per unit of good
    prod_graph_height = 30

class Subsession(BaseSubsession):
    def period_end(self):
        for group in self.get_groups():
            group.period_end()

    #Randomly group players at start of EACH ROUND
    def creating_session(self):
        production_array = []
        consumable_array = []
        # Set each players' random good
        color_index = 0
        for color in Constants.num_production:
            index = 0
            while index < color:
                production_array.append(Constants.goods[color_index])
                index += 1
            color_index += 1
        color_index = 0
        for color in Constants.num_consumable:
            index = 0
            while index < color:
                consumable_array.append(Constants.goods[color_index])
                index += 1
            color_index += 1
        if len(self.get_players()) != len(production_array) or len(self.get_players()) != len(
                consumable_array):
            print('WARNING: array length mismatch! Players: ' + str(len(self.get_players())) + ', prod: ' + str(len(
                production_array)) + ', cons: ' + str(len(consumable_array)))

        random.shuffle(consumable_array)
        #player index
        index = 0
        if self.round_number == 1 or self.round_number in Constants.periods:
            random.shuffle(production_array)
        print(production_array)
        print(consumable_array)
        print(len(self.get_players()))
        for p in self.get_players():
            if self.round_number == 1 or self.round_number in Constants.periods:
                p.production_good = production_array[index]
            else:
                p.production_good = p.in_round(self.round_number - 1).production_good
            p.consumable_good = consumable_array[index]
            index += 1
        self.group_randomly()

        #Check if new sequence
        new_sequence = (self.round_number in Constants.periods)
        #Run loop two times... first set held good, then set others good
        for p in self.get_players():
            p.set_held_good(new_sequence)
        for p in self.get_players():
            p.set_others_good()


class Group(BaseGroup):
    def check_start_of_new_sequence(self):
       new_sequence = (self.round_number in Constants.periods)
       for p in self.get_players():
            p.set_held_good(new_sequence)

    #End of period, try the trade, then try to consume
    def period_end(self):
        p1 = self.get_players()[0]
        p2 = self.get_players()[1]

        #Get p1_good and p2_good for session array
        p1_good = 0
        p2_good = 0
        if p1.held_good == 'Red':
            p1_good = 0
        elif p1.held_good == 'Blue':
            p1_good = 1
        else:
            p1_good = 2
        if p2.held_good == 'Red':
            p2_good = 0
        elif p2.held_good == 'Blue':
            p2_good = 1
        else:
            p2_good = 2
        if (p1.held_good == p2.held_good) or (p1.held_good == p1.consumable_good) or (p2.held_good == p2.consumable_good):
            #Trade could not happen
            p1.trade_success = False
            p1.trade_possible = False
            p2.trade_success = False
            p2.trade_possible = False
        else:
            p1.trade_possible, p2.trade_possible = True, True
            if p1.trade_choice and p2.trade_choice:
                p1.trade_success, p2.trade_success = True, True
            else:
                p1.trade_success, p2.trade_success = False, False

        #Try to consume post-trade...
        p1.try_consume(p2)
        p2.try_consume(p1)

        #Establish results
        p1.set_others_consumption_results(p2.trade_choice, p2.consumed)
        p2.set_others_consumption_results(p1.trade_choice, p1.consumed)

    def get_prev_trading_activity(self):
        activity = [][4]
        index = 1
        while index < self.round_number:
            prev_self = self.in_round(index)
            activity.append(index, prev_self.held_good, prev_self.consumable_good, prev_self.others_good)
            index += 1
        return activity


class Player(BasePlayer):
    #For fields that the user will not fill out, and are simply for data-tracking purposes
    #Include the key blank=True
    production_good = models.StringField(initial='', blank=True)
    consumable_good = models.StringField(initial='', blank=True)
    held_good = models.StringField(initial='', blank=True)
    trade_choice = models.BooleanField(
        choices=[
            [True, 'Trade'],
            [False, 'Don\'t Trade'],
        ]
    )
    trade_success = models.BooleanField(initial=0, blank=True)
    trade_possible = models.BooleanField(initial=0,blank=True)
    consumed = models.BooleanField(initial=0,blank=True)
    others_good = models.StringField(initial='', blank=True)
    others_consumable = models.StringField(initial='', blank=True)
    other_consumed_good = models.BooleanField(initial=0,blank=True)
    other_offered_trade = models.BooleanField(initial=0,blank=True)

    #Start of a new period, set held good and get others' good
    def set_held_good(self, is_new_sequence):
        #Check just in case for round 1
        if is_new_sequence or self.round_number == 1:
            self.held_good = self.production_good
        else:
            if self.in_previous_rounds()[-1].consumed:
                self.held_good = self.production_good
            elif self.in_previous_rounds()[-1].trade_success:
                self.held_good = self.in_previous_rounds()[-1].others_good
            else:
                self.held_good = self.in_previous_rounds()[-1].held_good

        if self.held_good == self.consumable_good:
            self.trade_choice = 0

    def set_others_good(self):
        self.others_good = self.get_others_in_group()[0].held_good
        self.others_consumable = self.get_others_in_group()[0].consumable_good

    def set_others_consumption_results(self, offered_trade, consumed_good):
        self.other_consumed_good = consumed_good
        self.other_offered_trade = offered_trade


    def try_consume(self, other):
        #comparable good allows for comparison whether trade occurs or not...
        comp_good = self.held_good
        if self.trade_success:
            #Could have used self.others_good here instead of other.held_good... Only realized after I got the code working.
            comp_good = other.held_good
        if self.consumable_good == comp_good:
            self.consumed = True
            self.payoff += 1
            #self.held_good = ''
            self.held_good = self.production_good
        else:
            self.consumed = False


def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'round_number', 'id_in_group', 'production_good', 'consumable_good',
           'held_good', 'others_good', 'trade?', 'trade_possible', 'trade_success', 'consumed']
    for p in players:
        participant = p.participant
        session = p.session
        group = p.group
        yield [session.code, participant.code, p.round_number, p.id_in_group, p.production_good, p.consumable_good,
               p.held_good, p.others_good, p.trade_choice, p.trade_possible, p.trade_success, p.consumed]