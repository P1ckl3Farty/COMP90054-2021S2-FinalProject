from template import Agent
import random
import heapq
import time
import numpy as np

"""
Current strategy:
1. Open strategy: first two turns to take gems with the top 3 amounts cards need to buy and
record the card with the highest score with the most optimal rank to buy. The third turn to reserve the card.
What is 'the highest score with the most optimal rank to buy' (the chosen card)?
A: Highest score, then the lowest cost, then the most need color is in 'the top 3 amounts cards need to buy'.
2. Middle-turn strategy: Try to take the color C needs the most to buy the chosen card.
How to choose? at the early stage, buy low point cards and its color is C. If reverse can reach the same goal,
i.e. the player with one less gem but have a wild. Return gems key should in NOWILDS rather than GEMS.
"""
# COLOURS = {'B':'black', 'r':'red', 'y':'yellow', 'g':'green', 'b':'blue', 'w':'white'}
GEMS = ['black', 'red', 'yellow', 'green', 'blue', 'white']
BUY = ['buy_available', 'buy_reserve']
COLLECT = ['collect_diff', 'collect_same']
NOBLE = 3
class PriorityQueue:
    """
    Source: Tutorial 02 of COMP90054
      Implements a priority queue data structure. Each inserted item
      has a priority associated with it and the client is usually interested
      in quick retrieval of the lowest-priority item in the queue. This
      data structure allows O(1) access to the lowest-priority item.
    """

    def __init__(self):
        self.heap = []
        self.count = 0


    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def isEmpty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        # If item already in priority queue with higher priority, update its priority and rebuild the heap.
        # If item already in priority queue with equal or lower priority, do nothing.
        # If item not in priority queue, do the same thing as self.push.
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)
        self.id = _id
        self.turn = 1

    def SelectAction(self, actions, game_state):
        start_time = time.time()
        my_agent = game_state.agents[self.id]
        pqueue = PriorityQueue()
        my_state, my_gem_cards, my_nobles = myAgent.get_agent_state(game_state, my_agent)
        for action in actions:
            if time.time() - start_time < 0.95:
                # Think within time
                pqueue.push(action, self.heuristic(my_state, my_gem_cards, my_nobles, action))
            else:
                # Out of time so return a random choice
                pqueue.push(random.choice(actions))
        self.turn += 1
        return pqueue.pop()  # reach time limit, pop the first item in priority queue.
    def get_agent_state(game_state, my_agent):
        state = [my_agent.score]
        gem_card = []
        nobles = []
        # Return gem array
        for gem in GEMS:
            if len(my_agent.cards[gem]) != 0:
                state.append(my_agent.gems[gem] + len(my_agent.cards[gem]))
                gem_card.append(len(my_agent.cards[gem]))
            else:
                state.append(my_agent.gems[gem])
                gem_card.append(0)
        # Return noble array
        for noble in game_state.board.nobles:
            temp = [NOBLE]
            for gem in GEMS:
                try:
                    color = noble[1][gem]
                except:
                    color = 0
                temp.append(color)
            nobles.append(temp)
        return state, gem_card, nobles

    def heuristic(self, my_state, my_gem_cards, nobles, action):
        max_mark = np.array([3] * 5)
        next_state, next_my_gem_cards = self.get_next_action(my_state, my_gem_cards,action)
        total_gems = sum(next_my_gem_cards[:-1])
        # Parameters for different turn stages
        open_factors = [1,1,0.05,0.25]
        middle_factors = [3, 0.5, 0.05, 0.5]
        end_factors = [4, 0.5, 0.05, 0.5]
        score = 15 - next_state[0]
        penalty = sum(max_mark - my_state[1:-1]) / (total_gems + 1)
        # Calculate cost negative rewards
        cost_distance = 0
        costs = (next_state - my_state)[1:]
        for cost in costs:
            if cost > 0:
                cost_distance -= cost
            else:
                cost_distance -= 1.5 * cost

        cost_distance = cost_distance / (total_gems + 1)
        penalty += next_my_gem_cards[-1] * 1.5
        # winning noble rewards
        noble_loss = 0
        for noble in nobles:
            total_nobles_distance = np.abs(sum(noble[1:] - next_my_gem_cards))
            noble_loss += total_nobles_distance * np.log2(total_gems + 1)
        heuristic_members = [score, cost_distance, noble_loss, penalty]
        if self.turn < 10:
            # Open stage heuristic value
            h_value = self.calc_h(open_factors, heuristic_members)
        elif self.turn < 20:
            # Middle stage heuristic value
            h_value = self.calc_h(middle_factors, heuristic_members)
        else:
            # End stage heuristic value
            h_value = self.calc_h(end_factors, heuristic_members)
        return h_value

    def calc_h(self, factors, members):
        h = 0
        for i in range(0,len(factors)-1):
            h += factors[i] * members[i]
        return h

    def get_next_action(self, my_state, my_gem_cards, action):
        # 7 actions:
        # two buy: buy_available and buy_reserve
        # two collect: collect_same and collect_diff
        # Reserve, pass and add noble points
        total_gems = []
        gem_card = [0, 0, 0, 0, 0, 0]
        if action['type'] in COLLECT:
            total_gems.append(0)
            for gem in GEMS:
                try:
                    temp = action['collected_gems'][gem]
                except:
                    temp = 0
                self.return_gems(action, total_gems, temp, gem)
        elif action['type'] in BUY:
            total_gems.append(action['card'].points)
            for gem in GEMS:
                temp = 0
                self.return_gems(action, total_gems, temp, gem)
            gem_card[GEMS.index(action['card'].colour)] = 1
        else:
            total_gems = [0, 0, 0, 0, 0, 0, 0]
            if action['type'] == 'reserve':
                total_gems[6] = 1
            else:
                return my_state + np.array(total_gems), my_gem_cards + np.array(gem_card)
        if action['noble'] != None:
            total_gems[0] += 3
        return my_state + np.array(total_gems), my_gem_cards + np.array(gem_card)

    def return_gems(self, action, total_gems,temp, code):
        try:
            temp -= action['returned_gems'][code]
        except:
            temp = temp
        total_gems.append(temp)
