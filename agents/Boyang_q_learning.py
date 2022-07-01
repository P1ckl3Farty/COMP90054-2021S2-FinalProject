from template import Agent
import numpy as np

# 6 colours of gems
GEMS = ['red', 'green', 'blue', 'black', 'white', 'yellow']
# 5 colours of card cost
CARDS = ['red', 'green', 'blue', 'black', 'white']

# weight of collect gems
COLLECT_WEIGHT = [-12.728446025144223, -23.163681472671666, -189.79103776456236]
# weight of reserve card
RESERVE_WEIGHT = [-17.67807095277969, 14.252739995142973, 34.43312462959414, -97.20890051620175]
# weight of buy card
BUY_WEIGHT = [90.87240283688378, -23.78533288044105, -182.38297308338403,
              2.5321643901482034, -3.951076260276537, 19.790949539646203]


# get one players state
# score(1) gems(6) cards(5)
def get_player_input(game_state, agent_id):
    player_input = []

    agent = game_state.agents[agent_id]
    player_input.append(agent.score)

    for key in GEMS:
        player_input.append(agent.gems[key])
    for key in CARDS:
        player_input.append(len(agent.cards[key]))
    return np.array(player_input)


# get one player's reserved cards
# point(1) cost(5) colour(1)
def get_reserved_input(game_state, agent_id):
    reserved_input = []
    agent = game_state.agents[agent_id]

    for card in agent.cards['yellow']:
        temp = [card.points]
        for key in CARDS:
            try:
                temp.append(card.cost[key])
            except:
                temp.append(0)
        temp.append(card.colour)
        reserved_input.append(temp)

    return np.array(reserved_input)


# get nobles information
# score(1) cards(5)
def get_game_noble_input(game_state):
    nobel_input = []

    for noble in game_state.board.nobles:
        temp = [3]
        for key in CARDS:
            try:
                temp.append(noble[1][key])
            except:
                temp.append(0)
        nobel_input.append(temp)

    return np.array(nobel_input)


# get cards information
# point(1) cost(5) colour(1)
def get_game_card_input(game_state):
    card_input = []

    for i in range(3):
        for j in range(4):
            temp = []
            if game_state.board.dealt[i][j]:
                temp.append(game_state.board.dealt[i][j].points)
                for key in CARDS:
                    try:
                        temp.append(game_state.board.dealt[i][j].cost[key])
                    except:
                        temp.append(0)
                temp.append(game_state.board.dealt[i][j].colour)
                card_input.append(temp)

    return np.array(card_input)


# get a player's next state if he uses one action
# score(1) gems(6) cards(5)
def get_action_change(action):
    score_change = 0
    gem_change = []
    card_change = [0] * 6

    if action['type'] == 'collect_diff' or action['type'] == 'collect_same':
        for key in GEMS:
            try:
                temp = action['collected_gems'][key]
            except:
                temp = 0
            try:
                temp = temp - action['returned_gems'][key]
            except:
                temp = temp
            gem_change.append(temp)

    elif action['type'] == 'reserve':
        gem_change = [0, 0, 0, 0, 0, 1]

    elif action['type'] == 'buy_available' or action['type'] == 'buy_reserve':
        score_change = action['card'].points
        for key in GEMS:
            try:
                gem_change.append(-action['returned_gems'][key])
            except:
                gem_change.append(0)
        card_change[GEMS.index(action['card'].colour)] = 1

    if action['noble'] != None:
        score_change += 3

    return score_change, np.array(gem_change), np.array(card_change)


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.id = _id

    # calculate a player's ability to buy cards in view of purchased cards
    def get_buy_power(self, agent_state):
        buy_power = []
        for i in range(5):
            buy_power.append(agent_state[i + 1] + agent_state[i + 7])
        buy_power.append(agent_state[6])
        return buy_power

    # calculate the gap to buy cards
    def get_gap_to_buy(self, cards, agent_state):
        buy_power = self.get_buy_power(agent_state)
        gaps = []
        for card in cards:
            gap = [0] * 6
            for i in range(5):
                gap[i] = int(buy_power[i]) - int(card[i + 1])
            gap[5] = buy_power[5]
            gaps.append(gap)
        return gaps

    # get a player's next state if he uses one action
    def get_next_state(self, agent_state, agent_action):
        _, gem_change, _ = get_action_change(agent_action)
        agent_next_state = [agent_state[0]]
        for i in range(1, 7):
            agent_next_state.append(int(agent_state[i] + gem_change[i - 1]))
        for i in range(7, 12):
            agent_next_state.append(agent_state[i])
        return agent_next_state

    # calculate how many cards need this card
    def if_card_need(self, cards, action, my_state):
        colour_index = GEMS.index(action['card'].colour)
        count = 0
        for card in cards:
            gap = float(card[colour_index + 1]) - my_state[colour_index + 7] - my_state[colour_index + 1]
            if gap > 0:
                count += 1
        return count

    # calculate how many nobles need this card
    def if_noble_need(self, nobles, action, my_state):
        colour_index = GEMS.index(action['card'].colour)
        count = 0
        for noble in nobles:
            gap = float(noble[colour_index + 1]) - my_state[colour_index + 7]
            if gap > 0:
                count += 1
        return count

    # calculate the features of collecting gems
    # feature 1: the collection helps to close the gap to buy a card from board
    # feature 2: the collection helps to close the gap to buy a reserved card
    # feature 3: punishment of collecting less than 3 gems
    def get_gems_features(self, game_state, agent_id, action):
        features = [0] * 3

        my_state = get_player_input(game_state, agent_id)
        my_reserved = get_reserved_input(game_state, agent_id)

        game_cards = get_game_card_input(game_state)

        my_buy_card_gap = self.get_gap_to_buy(game_cards, my_state)
        my_buy_reserved_gap = self.get_gap_to_buy(my_reserved, my_state)

        def get_increase(gaps, next_gaps):
            increase = 0
            for i in range(len(gaps)):
                for j in range(6):
                    if gaps[i][j] < 0 and next_gaps[i][j] > gaps[i][j]:
                        increase += (next_gaps[i][j] - gaps[i][j]) / gaps[i][j]
            return increase

        next_state = self.get_next_state(my_state, action)

        my_next_buy_card_gap = self.get_gap_to_buy(game_cards, next_state)
        my_next_buy_reserved_gap = self.get_gap_to_buy(my_reserved, next_state)

        features[0] = get_increase(my_buy_card_gap, my_next_buy_card_gap)
        features[1] = get_increase(my_buy_reserved_gap, my_next_buy_reserved_gap)

        if action['type'] == 'collect_diff' and len(action['collected_gems']) < 3 or action['returned_gems']:
            features[2] = 1
        else:
            features[2] = 0

        return features

    # calculate the features of reserving a card
    # feature 1: reserve a need card
    # feature 2: need a yellow gem
    # feature 3: noble need
    # feature 4: punishment of not pick
    def get_reserved_features(self, game_state, agent_id, action):
        features = [0] * 4

        my_state = get_player_input(game_state, agent_id)
        my_reserved = get_reserved_input(game_state, agent_id)

        game_cards = get_game_card_input(game_state)
        game_nobles = get_game_noble_input(game_state)

        my_buy_card_gap = self.get_gap_to_buy(game_cards, my_state)
        my_buy_reserved_gap = self.get_gap_to_buy(my_reserved, my_state)

        features[0] = self.if_card_need(game_cards, action, my_state) + self.if_card_need(my_reserved, action, my_state)

        card_count = 0
        for gap in my_buy_card_gap:
            sum_gap = 0
            for i in range(6):
                if gap[i] < 0:
                    sum_gap += gap[i]
            if sum_gap == -1:
                card_count += 1
        for gap in my_buy_reserved_gap:
            sum_gap = 0
            for i in range(6):
                if gap[i] < 0:
                    sum_gap += gap[i]
            if sum_gap == -1:
                card_count += 1
        features[1] = card_count

        features[2] = self.if_noble_need(game_nobles, action, my_state)

        if not action["collected_gems"] or action['returned_gems']:
            features[3] = 1
        else:
            features[3] = 0
        return features

    # calculate the features of buying a card
    # feature 1: points
    # feature 2: gem needed
    # feature 3: get noble
    # feature 4: cards on board need
    # feature 5: reserved card need
    # feature 6: noble need
    def get_buy_features(self, game_state, agent_id, action):

        my_state = get_player_input(game_state, agent_id)
        my_reserved = get_reserved_input(game_state, agent_id)

        game_cards = get_game_card_input(game_state)
        game_nobles = get_game_noble_input(game_state)

        score, cost, gem_card_change = get_action_change(action)

        features = [0] * 6
        features[0] = score

        sum_change = sum(cost)
        features[1] = sum_change

        if action['noble'] != None:
            features[2] = 3
        else:
            features[2] = 0

        features[3] = self.if_card_need(game_cards, action, my_state)
        features[4] = self.if_card_need(my_reserved, action, my_state)
        features[5] = self.if_noble_need(game_nobles, action, my_state)

        return features

    # calculate q value
    def cal_q_value(self, feature, weight):
        if len(feature) != len(weight):
            return 0
        q_value = 0
        for i in range(len(feature)):
            q_value += feature[i] * weight[i]
        return q_value

    def SelectAction(self, actions, game_state):

        # load the trained weight
        collect_weight = COLLECT_WEIGHT
        reserve_weight = RESERVE_WEIGHT
        buy_weight = BUY_WEIGHT

        # if cannot find the best action, use the first action
        best_action = actions[0]
        best_value = 0

        for action in actions:
            if action['type'] == 'collect_diff' or action['type'] == 'collect_same':
                collect_feature = self.get_gems_features(game_state, self.id, action)
                q_value = self.cal_q_value(collect_feature, collect_weight)
                if q_value > best_value:
                    best_value = q_value
                    best_action = action

            elif action['type'] == 'reserve':
                reserve_feature = self.get_reserved_features(game_state, self.id, action)
                q_value = self.cal_q_value(reserve_feature, reserve_weight)
                if q_value > best_value:
                    best_value = q_value
                    best_action = action

            elif action['type'] == 'buy_reserve' or action['type'] == 'buy_available':
                buy_features = self.get_buy_features(game_state, self.id, action)
                q_value = self.cal_q_value(buy_features, buy_weight)
                if q_value > best_value:
                    best_value = q_value
                    best_action = action

            else:
                return action
        return best_action
