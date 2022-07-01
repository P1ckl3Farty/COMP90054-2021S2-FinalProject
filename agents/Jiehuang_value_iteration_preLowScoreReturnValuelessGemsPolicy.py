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
        self.noble = None
        self.bought_most_point_card = False

    def SelectAction(self, actions, game_state):
        policy = ValueIteration(game_state, 0.5, self.id, actions, self.priority_colors)
        policy.set_color_most_fre()
        self.priority_colors = policy.find_priority_colors2()
        policy.priority_colors = self.priority_colors
        self.turn += 1
        if 5 < game_state.agents[self.id].score < 10:
            self.point_bonus = 3
        if game_state.agents[self.id].score >= 10:
            self.point_bonus = 5
        next_action = policy.selection()
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
        self.noble = None

    def find_priority_colors2(self):
        rank_color = []
        priority_color = {}
        color_most_fre, card_color_most_fre, card_level3 = self.find_valuable_card({}, {}, {})

        noble_color_most_fre, min_needed_noble_gem = self.find_min_gems_needed_noble2()

        color_most_fre = sorted(color_most_fre.items(), key=lambda a: a[1], reverse=True)
        card_color_most_fre = sorted(card_color_most_fre.items(), key=lambda a: a[1], reverse=True)
        noble_needed_gems = sorted(noble_color_most_fre.items(), key=lambda a: a[1])
        for color in noble_needed_gems:
            if color[0] not in rank_color:
                rank_color.append(color[0])
        for color in color_most_fre:
            if color[0] not in rank_color:
                rank_color.append(color[0])
        for color in COLOURS.values():
            if color not in rank_color:
                rank_color.append(color)
        value = 4
        for i, color in enumerate(rank_color):
            if i == len(noble_color_most_fre):
                value -= 2
            if color in min_needed_noble_gem and sum(min_needed_noble_gem.values()) <= 2:
                priority_color[color] = 5 + self.point_bonus
            else:
                bonus = 0
                if len(self.game_state.agents[self.id].cards[color]) == 0:
                    bonus = 2
                priority_color[color] = value + bonus
        return priority_color

    def same_color_num_with_noble(self, card):
        same_color_num = 0
        same_color_noble = None
        for noble in self.game_state.board.nobles:
            if noble:
                num = 0
                for color in CARDS[card][1].keys():
                    if color in noble[1]:
                        num += 1
                if num > same_color_num:
                    same_color_num = num
                    same_color_noble = noble
        return same_color_num, same_color_noble

    def find_valuable_card(self, color_most_fre, card_color_most_fre, card_most_point):
        for color in COLOURS.values():
            color_most_fre[color] = 0
            card_color_most_fre[color] = 0
        for level in range(0, len(self.game_state.board.dealt)):
            for card in self.game_state.board.dealt[level]:
                # if level < 2:
                color_most_fre = dict(Counter(color_most_fre) + Counter(CARDS[card.code][1]))
                card_color_most_fre[CARDS[card.code][0]] += 1
                # else:
                card_most_point[card.code] = CARDS[card.code]

        for color in COLOURS.values():
            if color not in color_most_fre:
                color_most_fre[color] = 0
            if color not in card_color_most_fre:
                card_color_most_fre[color] = 0
        return color_most_fre, card_color_most_fre, card_most_point

    def find_min_gems_needed_noble(self):
        min_num = float("inf")
        min_needed_noble = None
        noble_color_most_fre = {}
        collected_card = self.bought_card_num(self.game_state)
        for noble in self.game_state.board.nobles:
            if noble:
                needed_card = sum(dict(Counter(noble[1]) - Counter(collected_card)).values())
                if needed_card < min_num:
                    min_needed_noble = noble
                    noble_color_most_fre = dict(Counter(noble[1]) - Counter(collected_card))
                    min_num = sum(dict(Counter(noble[1]) - Counter(collected_card)).values())
        return noble_color_most_fre, min_needed_noble

    def find_min_gems_needed_noble2(self):
        min_num = float("inf")
        min_needed_noble_gem = {}
        noble_color_most_fre = {}
        collected_card = self.bought_card_num(self.game_state)
        for noble in self.game_state.board.nobles:
            if noble:
                needed_card = dict(Counter(noble[1]) - Counter(collected_card))
                for color in needed_card:
                    if color not in noble_color_most_fre:
                        noble_color_most_fre[color] = needed_card[color]
                    else:
                        if needed_card[color] < noble_color_most_fre[color]:
                            noble_color_most_fre[color] = needed_card[color]
                if sum(needed_card.values()) < min_num:
                    min_needed_noble_gem = dict(Counter(noble[1]) - Counter(collected_card))
                    min_num = sum(dict(Counter(noble[1]) - Counter(collected_card)).values())
        return noble_color_most_fre, min_needed_noble_gem

    def set_priority_noble(self, noble):
        priority = {}
        collected_card = self.bought_card_num(self.game_state)
        noble_color_most_fre = dict(Counter(noble[1]) - Counter(collected_card))
        num = len(noble_color_most_fre)
        for color in COLOURS.values():
            if color not in noble_color_most_fre:
                noble_color_most_fre[color] = 0
        noble_color_most_fre = sorted(noble_color_most_fre.items(), key=lambda a: a[1], reverse=True)
        value = 4
        for i, color in enumerate(noble_color_most_fre):
            if i == num:
                value -= 2
            priority[color[0]] = value
        self.priority_colors = priority

    def set_color_most_fre(self):
        min_gems_left = sorted(self.game_state.board.gems.items(), key=lambda a: a[1])
        value = 5
        for color in min_gems_left:
            self.freq_colors[color[0]] = value
            value -= 1
        for color in COLOURS.values():
            if color not in self.freq_colors:
                self.freq_colors[color] = 0

    def get_reward(self, action, game_state):
        max_reward = -float("inf")
        max_reward_card = ""
        win_reward = 1
        if "collect" in action["type"]:
            for level in range(0, len(game_state.board.dealt)):
                for card in game_state.board.dealt[level]+game_state.agents[self.id].cards["yellow"]:
                    returned_useful_gem = 0
                    if len(action["returned_gems"]) > 0:
                        for gem in action["returned_gems"]:
                            if gem in CARDS[card.code][1]:
                                returned_useful_gem += 1
                    reward = self.useful_num_of_gems(action["collected_gems"], CARDS[card.code][1], game_state) - self.turns_to_buy_card(CARDS[card.code][1], action["collected_gems"], game_state) + self.priority_colors[CARDS[card.code][0]] + CARDS[card.code][3] * self.point_bonus - returned_useful_gem
                    if reward > max_reward:
                        max_reward = reward
                        max_reward_card = card.code
        elif "buy" in action["type"]:
            noble_reward = 0
            if (game_state.agents[self.id].score + CARDS[action["card"].code][3]) >= 15:
                win_reward = 10
            if action["noble"] is not None:
                noble_reward = 3
            max_reward = ((self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus + noble_reward + 1) * 2) * win_reward
        elif "reserve" in action["type"]:
            max_reward = 0
            card_num = self.bought_card_num(game_state)
            rest_cost = dict(Counter(CARDS[action["card"].code][1]) - Counter(card_num))
            board_gems = dict(Counter(game_state.board.gems))
            if len(rest_cost) == 1 and sum(rest_cost.values()) == 1 and CARDS[action["card"].code][3] > 0 and list(rest_cost.keys())[0] not in board_gems:
                max_reward = self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus * 2 + 1
            if self.splendorGameRule.resources_sufficient(game_state.agents[1 - self.id], CARDS[action["card"].code][1]) and CARDS[action["card"].code][3] >= 3:
                max_reward = 20
                if game_state.agents[1 - self.id].score < 15 and (game_state.agents[1 - self.id].score + CARDS[action["card"].code][3]) >= 15:
                    max_reward *= 100
        return action, max_reward_card, max_reward

    def useful_num_of_gems(self, selected, needed, game_state):
        rest_cost = dict(Counter(needed) - Counter(game_state.agents[self.id].gems) - Counter(self.bought_card_num(game_state)))
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
        if sum(dict(Counter(cost) - Counter(card_num)).values()) > 10 or sort_cost[1] > 2 or sum(dict(Counter(rest_cost) - Counter(board_gems)).values()) > 0:
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
        reserve_action = []
        action_num = 0
        for i in range(iteration):
            delta = 0.0
            q_values = {}
            for state in states:
                max_reward = -float("inf")
                max_reserve_reward = -float("inf")
                for action in self.splendorGameRule.getLegalActions(state, self.id):
                    state_copy = copy.deepcopy(state)
                    action_reward = self.get_reward(action, state_copy)
                    action_num += 1
                    if action_reward[2] > max_reward:
                        if "reserve" not in action["type"]:
                            max_reward_actions = [action_reward]
                            max_reward = action_reward[2]
                            max_reward_action = action_reward
                            next_state = self.splendorGameRule.generateSuccessor(state_copy, action, self.id)
                            q_values[next_state] = action_reward[2]
                        else:
                            if action_reward[2] > max_reserve_reward:
                                max_reserve_reward = action_reward[2]
                                reserve_action = [action_reward]
                            elif action_reward[2] == max_reserve_reward:
                                reserve_action.append(action_reward)
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
                max_reward_action = sorted(max_reward_actions, key=lambda a: a[2], reverse=True)[0]
            elif "buy" in max_reward_actions[0][0]["type"]:
                enemy_can_buy = []
                for action in max_reward_actions:
                    if "buy" in action[0]["type"] and CARDS[action[0]["card"].code][3] >= 1 and self.splendorGameRule.resources_sufficient(self.game_state.agents[1 - self.id], CARDS[action[0]["card"].code][1]):
                        enemy_can_buy.append(action)
                if len(enemy_can_buy) == 0:
                    max_reward_action = sorted(max_reward_actions, key=lambda a: CARDS[a[0]["card"].code][3], reverse=True)[0]
                else:
                    max_reward_action = sorted(enemy_can_buy, key=lambda a: CARDS[a[0]["card"].code][3], reverse=True)[0]
        if len(reserve_action) == 1:
            if reserve_action[0][2] > max_reward_action[2]:
                max_reward_action = reserve_action[0]

        return max_reward_action[0]

    def selection(self):
        return self.value_calculate()
