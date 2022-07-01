from template import Agent
import random
from Splendor.splendor_model import SplendorGameRule
import time
from Splendor.splendor_utils import CARDS, COLOURS
from collections import Counter
import copy


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.priority_colors = {}
        self.most_point_card = None
        self.turn = 1

    def SelectAction(self, actions, game_state):
        policy = ValueIteration(game_state, 0.5, self.id, actions, self.priority_colors)
        policy.set_color_most_fre()
        if self.turn == 3:
            self.priority_colors, self.most_point_card, _, _ = policy.find_priority_colors()
            policy.priority_colors = self.priority_colors
            for action in actions:
                if "reserve" in action["type"] and action["card"].code == self.most_point_card[0]:
                    self.turn += 1
                    return action
        else:
            if len(self.priority_colors) == 0:
                self.priority_colors, self.most_point_card, _, _ = policy.find_priority_colors()
                policy.priority_colors = self.priority_colors
            self.turn += 1
            next_action = policy.selection()
            if  "buy" in next_action["type"] and next_action["card"].code == self.most_point_card[0]:
                _, card_color_most_freq, _, = policy.find_valueable_card({}, {}, {})
                value = 3
                card_color_most_freq = sorted(card_color_most_freq.items(), key=lambda a: a[1], reverse=True)
                for i  in range(len(card_color_most_freq)):
                    if i == 1 or i == 2 or i == 4:
                        value -= 1
                    self.priority_colors[card_color_most_freq[i][0]] = value
                policy.point_bonus = 3
                policy.priority_colors = self.priority_colors
            return next_action


class ValueIteration():

    def __init__(self, game_state, discount_rate, id, actions, priority_colors):
        self.game_state = game_state
        self.discount_rate = discount_rate
        self.id = id
        self.actions = actions
        self.priority_colors = priority_colors
        self.freq_colors = {}
        self.point_bonus = 1
        self.splendorGameRule = SplendorGameRule(len(game_state.agents))

    def find_priority_colors(self):
        color_most_fre = {}
        card_color_most_fre = {}
        card_most_point = {}
        rank_color = []
        priority_color = {}

        color_most_fre, card_color_most_fre, card_most_point = self.find_valueable_card(color_most_fre, card_color_most_fre, card_most_point)

        card_most_point = sorted(card_most_point.items(), key=lambda a: a[1][3], reverse=True)
        color_most_fre = sorted(color_most_fre.items(), key=lambda a: a[1], reverse=True)
        card_color_most_fre = sorted(card_color_most_fre.items(), key=lambda a: a[1], reverse=True)
        color_most_point = sorted(card_most_point[0][1][1].items(), key=lambda a: a[1], reverse=True)
        for color in color_most_point:
            rank_color.append(color[0])
        for color in card_color_most_fre:
            if color[0] not in rank_color:
                rank_color.append(color[0])
        for color in COLOURS.values():
            if color not in rank_color:
                rank_color.append(color)
        value = 4
        for i, color in enumerate(rank_color):
            if i == 1 or i == 2 or i == 4:
                value -= 1
            priority_color[color] = value
        return priority_color, card_most_point[0], color_most_fre, card_color_most_fre

    def find_valueable_card(self, color_most_fre, card_color_most_fre, card_most_point):
        for color in COLOURS.values():
            color_most_fre[color] = 0
            card_color_most_fre[color] = 0
        for level in range(0, len(self.game_state.board.dealt)):
            for card in self.game_state.board.dealt[level]:
                if level < 2:
                    color_most_fre = dict(Counter(color_most_fre) + Counter(CARDS[card.code][1]))
                    card_color_most_fre[CARDS[card.code][0]] += 1
                else:
                    card_most_point[card.code] = CARDS[card.code]
        for color in COLOURS.values():
            if color not in color_most_fre:
                color_most_fre[color] = 0
            if color not in card_color_most_fre:
                card_color_most_fre[color] = 0
        return color_most_fre, card_color_most_fre, card_most_point

    def set_color_most_fre(self):
        color_most_fre, _, _ = self.find_valueable_card({}, {}, {})
        value = 4
        for i, color in enumerate(color_most_fre):
            if i == 1 or i == 2 or i == 4:
                value -= 1
            self.freq_colors[color] = value

    def get_reward(self, action, game_state):
        max_reward = -float("inf")
        max_reward_card = ""
        if "collect" in action["type"]:
            for level in range(0, len(game_state.board.dealt)):
                for card in game_state.board.dealt[level]+game_state.agents[self.id].cards["yellow"]:
                    reward = self.useful_num_of_gems(action["collected_gems"], CARDS[card.code][1], game_state) - self.turns_to_buy_card(CARDS[card.code][1], action["collected_gems"], game_state) + self.priority_colors[CARDS[card.code][0]] + CARDS[card.code][3] * self.point_bonus
                    if reward > max_reward:
                        max_reward = reward
                        max_reward_card = card.code
        elif "buy" in action["type"]:
            golden = 0
            if "yellow" in action["returned_gems"]:
                golden = action["returned_gems"]["yellow"]
            max_reward = (self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus) * 2 + 1 - golden
        elif "reserve" in action["type"]:
            turns_to_buy = self.turns_to_buy_card(CARDS[action["card"].code][1], action["collected_gems"], game_state)
            if 0 < turns_to_buy <= 2:
                max_reward = self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus + 1
        return action, max_reward_card, max_reward

    def useful_num_of_gems(self, selected, needed, game_state):
        rest_cost = dict(Counter(needed) - Counter(game_state.agents[self.id].gems))
        total = sum(rest_cost.values())
        if total == 0:
            return total
        return total - sum(dict(Counter(rest_cost) - Counter(selected)).values())

    def turns_to_buy_card(self, cost, selected, game_state):
        card_num = self.bought_card_num(game_state)
        rest_cost = dict(Counter(cost) - Counter(game_state.agents[self.id].gems) - Counter(selected) - Counter(card_num))
        board_gems = dict(Counter(game_state.board.gems) - Counter(selected))
        if len(rest_cost) == 0:
            return 0
        sort_cost = sorted(rest_cost.items(), key=lambda a: a[1], reverse=True)[0]
        if sum(dict(Counter(cost) - Counter(card_num)).values()) > 10 or sum(dict(Counter(rest_cost) - Counter(board_gems)).values()) > 1:
            return sort_cost[1] * 10
        return sort_cost[1]

    def bought_card_num(self, game_state):
        card_num = {}
        bought_card = game_state.agents[self.id].cards
        for color in bought_card.keys():
            card_num[color] = len(bought_card[color])
        return card_num

    def value_calculate(self, iteration = 1, theta = 0.001):
        states = [self.game_state]
        values = {self.game_state: 0}
        max_reward_action = None
        max_reward_actions = []
        for i in range(iteration):
            delta = 0.0
            q_values = {}
            for state in states:
                max_reward = -float("inf")
                for action in self.splendorGameRule.getLegalActions(state, self.id):
                    state_copy = copy.deepcopy(state)
                    action_reward = self.get_reward(action, state_copy)
                    if action_reward[2] > 2:
                        if action_reward[2] > max_reward:
                            max_reward_actions = [action_reward]
                            max_reward = action_reward[2]
                            max_reward_action = action_reward[0]
                            next_state = self.splendorGameRule.generateSuccessor(state_copy, action, self.id)
                            q_values[next_state] = action_reward[2]
                        elif action_reward[2] == max_reward:
                            max_reward_actions.append(action_reward)
                maxQ = max(q_values.values())
                delta = max(delta, abs(values[state] - maxQ))
                values[state] = maxQ
            if delta < theta:
                break
        if len(max_reward_actions) > 1:
            if max_reward_actions[0][0]["type"] == "collect_diff" and sum(max_reward_actions[0][0]["collected_gems"].values()) < 3:
                same_reward_less_collect_gems = max_reward_actions[0]
                for i in range(1, len(max_reward_actions)):
                    if max_reward_actions[i][1] == same_reward_less_collect_gems[1]:
                        redundant_gems = dict(Counter(max_reward_actions[i][0]["collected_gems"]) - Counter(same_reward_less_collect_gems[0]["collected_gems"]))
                        extra_reward = 0
                        for color in redundant_gems.keys():
                            extra_reward += self.freq_colors[color]
                        max_reward_actions[i] = (max_reward_actions[i][0], max_reward_actions[i][1], max_reward_actions[i][2] + extra_reward)
                max_reward_action = sorted(max_reward_actions, key=lambda a: a[2], reverse=True)[0][0]
            elif "buy" in max_reward_actions[0][0]["type"]:
                max_reward_action = sorted(max_reward_actions, key=lambda a: CARDS[a[0]["card"].code][3], reverse=True)[0][0]
        return max_reward_action

    def selection(self):
        return self.value_calculate()
