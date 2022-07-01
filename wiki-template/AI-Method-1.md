# AI Method 1 - Markov Decision Processes (MDPs) - Value iteration. 

Our first technique is the model-based based Markov Decision Processes with the value iteration algorithm. 


# Table of Contents
- [Governing Strategy Tree](#governing-strategy-tree)
  * [Motivation](#motivation)
  * [Application](#application)
  * [Trade-offs](#trade-offs)     
     - [Advantages](#advantages)
     - [Disadvantages](#disadvantages)
  * [Future improvements](#future-improvements)

## Governing Strategy Tree  

### Motivation  
At the start of the project, we have researched the game and decided to develop a model-based algorithm. 
Since Breadth First Search and A star have high possibility that exceed the time limit, we decided to 
use Markov Decision Processes with value iteration.

The MDPs implements the principle in mathematics, a discrete-time stochastic control process. In this framework, 
the decisions are making partly controlled by the decision maker but partly are random. At each turn, the process is in 
a state s. Next state will be chosen by the decision maker in a probability. There are two algorithms to solve 
problem under the MDP framework: policy iteration and value iteration.

To solve problems in MDPs framework, the value iteration algorithm will solve the Bellman equations iteratively untill 
the value V converge or almost converge to the optimal value function V<sup>*</sup> . For implementation, we have referred to 
the sample code provided in class. [link](https://gibberblot.github.io/rl-notes/single-agent/value-iteration.html)

About designing, we have a detailed illustration in the policy evolution in [Evolution](Evolution.md). Finally, our policy 
is: we will evaluate the noble on board. If their needed cards colours in common are two or more, we will pick one noble with
the least cards requirements as the target; If colours in common are one or less. We will tend to use picking cards with low to medium 
points strategy combining with inviting nobles strategy with lower weight. Specifically, at each round, we will evaluate
cards' colours priority at first. The cards' representing colours are sorted from the highest to the lowest as follows:
```
1. The colour has the least differences to invite the chosen noble.
2. The needed colours for buying a target card on the second dealt.
3. The colour needed by other two nobles.
4. The most needed colours by all cards on board.
5. The left colour.
```
Then we will calculate each action's reward and pick the most valuable one to execute. Specifically, we have "collect", 
"buy" and "reserve".

##### 1. "Collect"
```collect gems
1. Iterate all cards on board and reserved by the agent.
2. Calculate rewards after collecting gems:
  a. The number of gems that match the color of the given card to be cost
  b. the number of rounds it takes to buy the given card
  c. the prior value of each color (calculated each round)
  d. the point of the given card
  e. the bonus of the point (bonus: are gems which, after collected, can be used to purchase a card with the highest rewards)
  
  The final value of this turn Vc is: Vc = a - b + c + d * e

Note. The rule of collecting gems for corner cases: 
  a. For cards need three different colours to buy in next three rounds (the needed gems are in ratio of 3:3:2),
     at the last round to save one position to avoid taking unnecessary gems, we will replace the gem with the proportion of 
     2 / 8 with the most needed gems needed by cards.
  b. If agent's gems exceed 10, only gems with the lowest rewards will be returned
```

##### 2. "Buy"
```Buy cards
1. Calculate rewards of buying a card on:
  a. whether can invite a noble: returning 3; if not: returning 0
  b. the prior value of each color (calculated each round)
  c. the point of the given card
  d. the bonus of the point
  e. Buy bonus, this parameter is helping to make the agent concentrates on buying cards with no point at the early stage
     , which can be built up to buy cards with high points later. 
  f. Win reward, this parameter will perform an important role in the later stage to make the agent buy cards which can make
     points more than 15 directly.
  
  The final value is: Vb = a + b + c * d + 2 * e * f 
```

##### 3. "Reserve"
```reserve cards
1. Give the highest rewards if the agent reserve cards:
  a. which the counter agent buys and it is the only one that will let counter agent's points exceed 15, even if our agent can buy a card to win this round.
     This strategy can help up in case that the counter agent has an overall high score than ours at the end of 
     the last round.
  b. which can be bought in the next round with no less than 2 points but there are no needed gems on the board.
     (how do we know a card can be bought at the next round: max gems needed for buying this card minus our agents' all form
     of gems and wild is no exceed one)
  c. With no smaller than 3 points and it is the only card which the counter agent can get at its turn.
```

[Back to top](#table-of-contents)

### Application
Below blocks contain core code in this method.
```feature collection 1
##########################################
####The rewards calculator################
##########################################
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
                    returned_useful_gem = 0
                    if len(action["returned_gems"]) > 0:
                        for gem in action["returned_gems"]:
                            if gem in CARDS[card.code][1]:
                                returned_useful_gem += 1
                            if gem == "yellow":
                                returned_useful_gem += 10

                    # useful_num_of_gems() counts the number of valuable gems collected (The number of gems that match the color of the given card to be cost ）
                    # turns_to_buy_card() counts the the number of rounds it takes to buy the given card
                    # priority_colors is the prior value of each color (calculated each round)
                    # CARDS[card.code][3] is the point of the given card
                    # self.point_bonus is the bonus of the point
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
            max_reward = 0
            card_num = self.bought_card_num(game_state)
            rest_cost = dict(
                Counter(CARDS[action["card"].code][1]) - Counter(card_num) - Counter(game_state.agents[self.id].gems))
            board_gems = game_state.board.gems
            if (sum(rest_cost.values()) - game_state.agents[1 - self.id].gems["yellow"]) == 1 and CARDS[action["card"].code][3] >= 2 and board_gems[list(rest_cost.keys())[0]] == 0:
                returned_useful_gem = 0
                if len(action["returned_gems"]) > 0:
                    for gem in action["returned_gems"]:
                        if gem in CARDS[action["card"].code][1]:
                            returned_useful_gem += 1
                        if gem == "yellow":
                            returned_useful_gem += 10
                max_reward = self.priority_colors[CARDS[action["card"].code][0]] + CARDS[action["card"].code][3] * self.point_bonus * 2 + 1 - returned_useful_gem
            if self.splendorGameRule.resources_sufficient(game_state.agents[1 - self.id], CARDS[action["card"].code][1]) and CARDS[action["card"].code][3] >= 3:
                max_reward = 30
                if game_state.agents[1 - self.id].score < 15 and (game_state.agents[1 - self.id].score + CARDS[action["card"].code][3]) >= 15:
                    max_reward *= 10
        return action, max_reward_card, max_reward

```
```Value iteration algorithm
##########################################
####Value iteration algorithm#############
##########################################
    def value_calculate(self, iteration = 1, theta = 0.001):
        # Initialise the state of the game, start with current game state
        states = [self.game_state]

        # Initialise the value function V for states
        values = {self.game_state: 0}
        max_reward_action = None
        max_reward_actions = []
        reserve_action = []

        # start iteration 293-338 value iteration
        for i in range(iteration):
            delta = 0.0
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
                        if "reserve" not in action["type"]:
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
                    if max_reward_actions[i][1] == same_reward_less_collect_gems[1]:
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

        # reserve the card which the enemy have enough gems to buy with more than 3 points and only resrve when the enemy
        # only have one card with 3 points can buy
        if len(reserve_action) == 1:
            if reserve_action[0][2] > max_reward_action[2]:
                max_reward_action = reserve_action[0]

        return max_reward_action[0]
```
### Trade-offs  
#### *Advantages*  
The MDPs with value iteration algorithm has the following advantages:
```Advantages
  a. This algorithm always converges to the optimal policy, especially for problems with small to medium size of state space.
  b. The value iteration can improve parameter in the iteration based on a strategy. If the strategy is smart enough, the convergence state 
    will be satisfying
```

Specifically, our strategy has been improved based on concluding lessons from the performance of the match replay with 
other teams. The improvement of our agent can be predicted. Each time after add more detailed new strategy into our agent, 
we can observe our score has increased. Our agent have a rank from 19 at the beginning to 2 at 3 o'clock on 10/17. And our 
rank is steady ranging within top 20.

#### *Disadvantages*
```Disadvantages
  a. This strategy requires developers to have a deep understanding in the game policies. It is harder to find the optimal 
    strategy for large size state space game. Without the optimal strategy, the convergence will not be optimal.
  b. It is based on strategy, thus, it does not have good generalized problem solving ability.
  c. This strategy only considered current or 1-2 future rounds' best actions. Local optimal addup may not be the global optimal.
  d. The think time will become obviously slow if our agent think too far from the current stage. 
```
[Back to top](#table-of-contents)

### Future improvements  
In the future we will continuously improve our strategy. Parameters can be optimized as well as the value calculation methods.
The optimization can also be made by considering more corner cases such as the last action.

[Back to top](#table-of-contents)
