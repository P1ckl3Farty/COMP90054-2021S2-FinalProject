# AI Method 2 - Approximate Q Learning. 

Our second technique is the model-free based approximate Q Learning. 


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
We had tried A star algorithm offline with a simple heuristic function in different stage of the game. 
However, A star sometimes had to pass without taking any actions because it took too long to calculate the next action, especially after three to four turns. 
Our first technique is the model based value iteration algorithm. We decided to try another model free technique. 
As one of our members has the experience in approximate Q learning, we hoped to implement such technique as a wiser 
agent other than A star to improve our value iteration model. Because the model free technique may give us some 
inspiration beyond our policy.

Q learning, as an off-policy reinforcement learning algorithm, is famous for its optimal solution from current state to 
the future state by maximizing the rewards of all successive steps. It can find an optimal solution to any finite Markov
decision process (FMDP). However, this algorithm requires to record all possible predecessor states and their chosen actions influences 
on Q value. All of those Q values are stored in a Q table. This process is time-consuming. Since we only hope method two can give us some inspiration,
we decided to use approximate Q learning.

The approximate Q learning combines function approximation, a method to fitting complex problem with a simplified function, to reach close performance
as Q learning but with less time to train. The approximate function we use in the project is a linear one. There are three 
reasonable actions in the game: collecting gems, buying cards and reserving cards. Thus, we designed three collections of features.

  #### 1.For collecting gems, there are three types of feature for collecting gems:
    a. who can help to buy a card on board.
    b. to buy a reserved card. 
    c. if collect 1 or two gems, apply a punishment.

  #### 2.For reserving cards, there are four types of feature for reserving a card:
    a. whose representing gem colour is required to buy the needed cards.
    b. who is needed when a wild is needed
    c. who is needed to invite a noble
    d. when passing the turn return a punishment

  #### 3.For reserving cards, there are six types of feature for buying a card: 
    a. who can gain points
    b. who can increase the needed gem colours
    c. whose colour is needed to invite a noble
    d. whose colour can buy a card on board.
    e. whose colour can buy a reserved card
    f. whose representing colours are needed during the path to invite a noble.

With these feature collections, after traversing actions, the q value can be calculated. The action with the highest q value is the best action.


[Back to top](#table-of-contents)

### Application
Below blocks contain core code in this method.
#### 1. Feature collections:
```feature collection 1
##########################################
####Collecting gems feature collection####
##########################################
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
```
```feature collection 2
##########################################
####Reserving a card######################
##########################################
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
```
```feature collection 2
##########################################
####Buying a card########################
##########################################
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
```
#### 2. Calculate q value:
```calculate q value
##########################################
####calculate q value#####################
##########################################
    def cal_q_value(self, feature, weight):
        if len(feature) != len(weight):
            return 0
        q_value = 0
        for i in range(len(feature)):
            q_value += feature[i] * weight[i]
        return q_value
```
#### 3. Select actions:
```select actions
##########################################
####select actions########################
##########################################
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
```

For the training process, we firstly train it with the random agent and match with the value iteration agent. The winning rate
is 5%. After that, we train it with the value iteration and use the trained one to fight against it to find some insights. It did give
us an insight on expand our strategy to consider about nobles. And the best winning rate increased to 20%.

### Trade-offs  
#### *Advantages*  
The approximate Q learning has the following general advantages:
```Advantages
  a. It does not need coder to list an extremly large table.
  b. Features can share the same features.
  c. It can handle continous state spaces.
  d. As a model free technique, it has better generalization.
```

#### *Disadvantages*
```Disadvantages
  a. It requires manual feature selections.
  b. The linear function is not realistic in this game. Thus, this approximation is not precise.
```
[Back to top](#table-of-contents)

### Future improvements  
In the future, we will try a more exquisite design of features. The linear approximation is not precise. Our feature selection is also not optimal.
For example, in collecting gems feature collections, one problem is that we just treat all taking two gems as actions receiving punishment. 
However, sometimes taking two same gems is a good action. Such corner case is not considered as detailed as our method one did. 
Thus, one improvement can be modifying linear approximate function or using more complicated approximate functions or using neural network to calculate them. 
Another method is replacing approximate Q learning with Q learning and even deep Q learning. 
The approximate Q learning is easy to design but it loses powerful functionality of Q learning. 
With more powerful Q learning techniques, a better agent will be gotten.

[Back to top](#table-of-contents)
