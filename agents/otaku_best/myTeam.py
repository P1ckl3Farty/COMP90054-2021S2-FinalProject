from template import Agent
from Splendor.splendor_model import SplendorGameRule
from Splendor.splendor_utils import CARDS, COLOURS
from collections import Counter
import copy


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.priority_colors = {}

    def SelectAction(self, actions, game_state):

        # initilize the value iteraion class
        policy = ValueIteration(game_state, 0.5, self.id, actions, self.priority_colors)

        # set the collected color most frequent priority each round
        policy.set_color_most_fre()

        # set the color priority each round
        self.priority_colors = policy.find_priority_colors()
        policy.priority_colors = self.priority_colors

        # when the point is greater than 5 and less than 8 , set the point_bonus and min_noble_bonus to 2
        if 5 <= game_state.agents[self.id].score < 8:
            policy.min_noble_bonus = 2
        if game_state.agents[self.id].score >= 8:
            policy.min_noble_bonus = 3
            policy.point_bonus = 2

        # select action
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
        self.buy_bonus = 1
        self.min_noble_bonus = 1
        self.noble_bonus = 1
        self.splendorGameRule = SplendorGameRule(len(game_state.agents))
        self.noble = None

    # measure the priority of the card for each color
    def find_priority_colors(self):
        rank_color = []
        priority_color = {}

        # find the valuable card
        color_most_fre, card_gem_needed, _ = self.find_valuable_card({}, {}, {})

        # find the noble color which need the least card and find the noble color with the most commonly occurs
        noble_color_most_fre, min_needed_noble_gem = self.find_min_gems_needed_noble()

        # find the most cover color which in any pair of noble
        max_noble_cover_num = self.noble_cover_color()

        # sort the color_most_fre and card_gem_needed from more to less
        # sort the noble_needed_gems from less to more
        color_most_fre = sorted(color_most_fre.items(), key=lambda a: a[1], reverse=True)
        card_gem_needed = sorted(card_gem_needed.items(), key=lambda a: a[1], reverse=True)
        noble_needed_gems = sorted(noble_color_most_fre.items(), key=lambda a: a[1])

        # set value to 5 and value_deduct to 1
        value_deduct = 1
        if len(max_noble_cover_num) >= 2:
            self.noble_bonus = 2
        else:
            self.noble_bonus = 1
        value = 5

        # first priority: the noble color which need the least card
        for color in min_needed_noble_gem.keys():
            if color not in rank_color:
                rank_color.append(color)

        # second priority: the noble color which cover most
        for color in max_noble_cover_num:
            if color not in rank_color:
                rank_color.append(color)

        # third priority: the point card which need the least card
        for color in card_gem_needed:
            if color[0] not in rank_color:
                rank_color.append(color[0])

        # forth priority: the other noble color
        for color in noble_needed_gems:
            if color[0] not in rank_color:
                rank_color.append(color[0])

        # fifth priority: the color with most occurs
        for color in color_most_fre:
            if color[0] not in rank_color:
                rank_color.append(color[0])
        for color in COLOURS.values():
            if color not in rank_color:
                rank_color.append(color)

        # assign priority value to each color
        for i, color in enumerate(rank_color):
            if i == len(min_needed_noble_gem) or i == (len(min_needed_noble_gem) + len(card_gem_needed)):
                value -= value_deduct
            if color in min_needed_noble_gem and sum(min_needed_noble_gem.values()) <= 2:
                priority_color[color] = value + 3 - sum(min_needed_noble_gem.values()) + self.noble_bonus + self.min_noble_bonus
            elif color in max_noble_cover_num and len(self.game_state.agents[self.id].cards[color]) < 1:
                priority_color[color] = value + self.noble_bonus + 1
            else:
                bonus = 0
                if len(self.game_state.agents[self.id].cards[color]) == 0:
                    bonus = 2
                priority_color[color] = value + bonus
            if color in noble_needed_gems:
                priority_color[color] += 1
        return priority_color

    # find the most cover color which in any pair of noble
    def noble_cover_color(self):
        max_cover_color = []
        for noble in self.game_state.board.nobles:
            for other_noble in self.game_state.board.nobles:
                if noble:
                    cover_color = []
                    if noble != other_noble:
                        for color in noble[1]:
                            if color in other_noble[1]:
                                cover_color.append(color)
                    if len(cover_color) > len(max_cover_color):
                        max_cover_color = cover_color
        return max_cover_color

    # find the valuable card
    # return most commonly color, most commonly color on card and the card with the most point
    def find_valuable_card(self, color_most_fre, card_gem_needed, card_most_point):
        need_gems = float("inf")
        collected_card = self.bought_card_num(self.game_state)
        for color in COLOURS.values():
            color_most_fre[color] = 0
        for level in range(0, len(self.game_state.board.dealt)):
            for card in self.game_state.board.dealt[level]:
                if level >= 1:
                    card_needed = dict(Counter(CARDS[card.code][1]) - Counter(collected_card) - Counter(self.game_state.agents[self.id].gems))
                    if sum(card_needed.values()) > 0:
                        if sum(card_needed.values()) < need_gems:
                            need_gems = sum(card_needed.values())
                            card_gem_needed = card_needed
                        elif sum(card_needed.values()) == need_gems and len(card_needed) > len(card_gem_needed):
                            card_gem_needed = card_needed
                color_most_fre = dict(Counter(color_most_fre) + Counter(CARDS[card.code][1]))
                card_most_point[card.code] = CARDS[card.code]

        for color in COLOURS.values():
            if color not in color_most_fre:
                color_most_fre[color] = 0
        return color_most_fre, card_gem_needed, card_most_point

    # find the noble color which need the least card and find the noble color with the most commonly occurs
    def find_min_gems_needed_noble(self):
        min_num = float("inf")
        min_needed_noble_gem = {}
        noble_color_most_fre = {}

        # find the bought card
        collected_card = self.bought_card_num(self.game_state)

        # iterate over the noble
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

    # set fre_color to the card_gem_needed and min_gems_left
    def set_color_most_fre(self):
        _, card_gem_needed, _ = self.find_valuable_card({}, {}, {})
        card_gem_needed = sorted(card_gem_needed.items(), key=lambda a: a[1], reverse=True)
        min_gems_left = sorted(self.game_state.agents[self.id].gems.items(), key=lambda a: a[1])
        value = 5
        for color in card_gem_needed:
            if color[0] != "yellow":
                self.freq_colors[color[0]] = value
                value -= 1
        for color in min_gems_left:
            if color[0] != "yellow" and color[0] not in self.freq_colors:
                self.freq_colors[color[0]] = value
                value -= 1
        for color in COLOURS.values():
            if color not in self.freq_colors:
                self.freq_colors[color] = 0

    # get the reward with the given action and state
    def get_reward(self, action, game_state):
        max_reward = -float("inf")
        max_reward_card = ""
        win_reward = 1

        # if the action type is "collect diff" or "collect same"
        if "collect" in action["type"]:

            # iterate over the card on the board and the reserved card
            for level in range(0, len(game_state.board.dealt)):
                for card in game_state.board.dealt[level]+game_state.agents[self.id].cards["yellow"]:

                    # returned_useful_gem counts the number of valuable gems returned
                    rest_cost = dict(Counter(CARDS[card.code][1]) - Counter(self.bought_card_num(game_state)))
                    returned_useful_gem = 0
                    if len(action["returned_gems"]) > 0:
                        for gem in action["returned_gems"]:
                            if gem in rest_cost:
                                returned_useful_gem += 1
                            if gem == "yellow":
                                returned_useful_gem += 10

                    # useful_num_of_gems() counts the number of valuable gems collected (The number of gems that match the color of the given card to be cost ）
                    # turns_to_buy_card() counts the the number of rounds it takes to buy the given card
                    # priority_colors is the prior value of each color (calculated each round)
                    # CARDS[card.code][3] is the point of the given card
                    # self.point_bonus is the bonus of the point
                    # self.collected_bonus is the bonus of the collection action
                    reward = self.useful_num_of_gems(action["collected_gems"], CARDS[card.code][1], game_state) - self.turns_to_buy_card(CARDS[card.code][1], action["collected_gems"], game_state) + self.priority_colors[CARDS[card.code][0]] + CARDS[card.code][3] * self.point_bonus - returned_useful_gem
                    if reward > max_reward:
                        max_reward = reward
                        max_reward_card = card.code

        # if the action type is "buy"
        elif "buy" in action["type"]:

            # if we bought the card and win, set the win_reward to 10
            noble_reward = 0
            if (game_state.agents[self.id].score + CARDS[action["card"].code][3]) >= 15:
                win_reward = 100
            if action["noble"] is not None:
                noble_reward = 3
            max_reward = ((self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus + noble_reward + self.buy_bonus) * 2) * win_reward

        # reserve the card which the enemy have enough gems to buy with more than 3 points
        elif "reserve" in action["type"]:
            max_reward = 1
            card_num = self.bought_card_num(game_state)
            rest_cost = dict(
                Counter(CARDS[action["card"].code][1]) - Counter(card_num) - Counter(game_state.agents[self.id].gems))
            board_gems = game_state.board.gems

            # reserve the card when we only need one gem to buy that card and the board did not have the gem
            if (sum(rest_cost.values()) - game_state.agents[self.id].gems["yellow"]) == 1 and CARDS[action["card"].code][3] >= 1 and board_gems[list(rest_cost.keys())[0]] == 0:
                returned_useful_gem = 0
                if len(action["returned_gems"]) > 0:
                    for gem in action["returned_gems"]:
                        if gem in CARDS[action["card"].code][1]:
                            returned_useful_gem += 1
                        if gem == "yellow":
                            returned_useful_gem += 10
                max_reward = self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus * 2 + 1 - returned_useful_gem

            # reserve the card if enemy can buy the card and the point is greater than 3
            if self.splendorGameRule.resources_sufficient(game_state.agents[1 - self.id], CARDS[action["card"].code][1]):
                if CARDS[action["card"].code][3] >= 3:
                    max_reward = 30
                if game_state.agents[1 - self.id].score < 15 and (game_state.agents[1 - self.id].score + CARDS[action["card"].code][3]) >= 15:
                    max_reward *= 50
        return action, max_reward_card, max_reward,

    # return the number of gems which in the given card
    def useful_num_of_gems(self, selected, needed, game_state):
        rest_cost = dict(Counter(needed) - Counter(game_state.agents[self.id].gems) - Counter(self.bought_card_num(game_state)))
        total = 0
        for color in selected.keys():
            if color in rest_cost:
                total += 1
        return total

    # return the number of round which can buy the given card
    def turns_to_buy_card(self, cost, selected, game_state):
        card_num = self.bought_card_num(game_state)
        rest_cost = dict(Counter(cost) - Counter(game_state.agents[self.id].gems) - Counter(selected) - Counter(card_num))
        board_gems = dict(Counter(game_state.board.gems) - Counter(selected))
        if len(rest_cost) == 0:
            return 0
        sort_cost = sorted(rest_cost.items(), key=lambda a: a[1], reverse=True)[0]
        if sum(dict(Counter(cost) - Counter(card_num)).values()) > 10 or sort_cost[1] > 2 or sum(dict(Counter(rest_cost) - Counter(board_gems)).values()) > 1:
            return sort_cost[1] * 10
        return sort_cost[1]

    # return the bought card dict
    def bought_card_num(self, game_state):
        card_num = {}
        bought_card = game_state.agents[self.id].cards
        for color in bought_card.keys():
            card_num[color] = len(bought_card[color])
        return card_num

    # Implmentation of value iteration
    def value_calculate(self, iteration = 1, theta = 0.001):
        # Initialise the state of the game, start with current game state
        states = [self.game_state]

        # Initialise the value function V for states
        values = {self.game_state: 0}
        max_reward_action = None
        max_reward_actions = []
        reserve_action = []

        # start iteration
        for i in range(iteration):
            delta = 1
            q_values = {}
            for state in states:
                max_reward = -float("inf")
                max_reserve_reward = -float("inf")

                # Calculate the value of Q(s,a)
                # Iterate over the actions of the selected state
                for action in self.splendorGameRule.getLegalActions(state, self.id):

                    # get the reward of each action with the selected state
                    state_copy = copy.deepcopy(state)
                    action_reward = self.get_reward(action, state_copy)

                    # if the reward of current action is greater than the max_reward
                    if action_reward[2] > max_reward:

                        # if the action is "collected gems" or "buy cards", store the action and update the value of Q(s,a)
                        if action["type"] != "reserve":
                            max_reward_actions = [action_reward]
                            max_reward = action_reward[2]
                            max_reward_action = action_reward
                            next_state = self.splendorGameRule.generateSuccessor(state_copy, action, self.id)
                            q_values[next_state] = action_reward[2]

                        # if the action is "reserve", store the action
                        else:
                            if action_reward[2] > max_reserve_reward:
                                max_reserve_reward = action_reward[2]
                                reserve_action = [action_reward]
                            elif action_reward[2] == max_reserve_reward:
                                reserve_action.append(action_reward)
                            q_values[self.game_state] = 0
                            if max_reward == None:
                                max_reward_action = action_reward

                    # if the reward is same as max_reward, store the action with the max_reward action
                    elif action_reward[2] == max_reward:
                        max_reward_actions.append(action_reward)

                # V(s) = max_a Q(s,a)
                maxQ = max(q_values.values())
                delta = max(delta, abs(values[state] - maxQ))
                values[state] = maxQ

            # terminate if the value function has converged
            if delta < theta:
                break

        # if more than 1 action with in max_reward_actions
        if len(max_reward_actions) > 1:

            # if the action is "collect_diff" and the action only choose 1 or 2 gems
            if max_reward_actions[0][0]["type"] == "collect_diff" and sum(max_reward_actions[0][0]["collected_gems"].values()) < 3:

                # find the most valuable gems for us and update the reward of the action
                same_reward_less_collect_gems = max_reward_actions[0]
                for i in range(1, len(max_reward_actions)):
                    if "collect" in max_reward_actions[i][0]["type"] and len(max_reward_actions[i][0]["collected_gems"]) > 1 :
                        redundant_gems = dict(Counter(max_reward_actions[i][0]["collected_gems"]) - Counter(same_reward_less_collect_gems[0]["collected_gems"]))
                        extra_reward = 0
                        for color in redundant_gems.keys():
                            extra_reward += self.freq_colors[color]
                        max_reward_actions[i] = (max_reward_actions[i][0], max_reward_actions[i][1], max_reward_actions[i][2] + extra_reward)

                # select the action with maximum reward
                max_reward_action = sorted(max_reward_actions, key=lambda a: a[2], reverse=True)[0]

            # if the action is "buy card"
            elif "buy" in max_reward_actions[0][0]["type"]:
                enemy_can_buy = []

                # prior to buy the card which the enemy also can buy
                for action in max_reward_actions:
                    if "buy" in action[0]["type"] and CARDS[action[0]["card"].code][3] >= 1 and self.splendorGameRule.resources_sufficient(self.game_state.agents[1 - self.id], CARDS[action[0]["card"].code][1]):
                        enemy_can_buy.append(action)
                if len(enemy_can_buy) == 0:
                    max_reward_action = sorted(max_reward_actions, key=lambda a: CARDS[a[0]["card"].code][3], reverse=True)[0]
                else:
                    max_reward_action = sorted(enemy_can_buy, key=lambda a: CARDS[a[0]["card"].code][3], reverse=True)[0]

        # reserve the card which the enemy have enough gems to buy with more than 3 points and only reserve when the enemy
        # only have one card with 3 points can buy
        if len(reserve_action) == 1:
            if reserve_action[0] is not None and reserve_action[0][2] > max_reward_action[2]:
                max_reward_action = reserve_action[0]
        elif len(reserve_action) > 1:
            if not self.splendorGameRule.resources_sufficient(self.game_state.agents[1 - self.id], CARDS[reserve_action[0][0]["card"].code][1]):
                if reserve_action[0][2] > max_reward_action[2]:
                    _, min_needed_noble_gem = self.find_min_gems_needed_noble()
                    for action in reserve_action:
                        if CARDS[action[0]["card"].code][0] in min_needed_noble_gem:
                            max_reward_action = action
        if max_reward_action is None:
            return random.choice(self.actions)

        return max_reward_action[0]

    def selection(self):
        return self.value_calculate()
