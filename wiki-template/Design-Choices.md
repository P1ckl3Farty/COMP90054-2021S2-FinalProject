# Design Choices

## General Comments

At the beginning, we used A start as a trail. However, we found this method is easy to reach the time limit. Thus, we did not pay much time to explore it and we turned to MDPs with value iteration and approximate Q learning. That is the reason why we do not introduce it in detail. We take most of our time to do research and watch replay with different counter agents to improve our strategy. We tried to develop both off-policy and on-policy models. Specifically, we focused more on the on-policy model: MDPs with the value iteration algorithm. From the "Large-Point" to "Naive Small-Point", and finally, "Smart Small-Point", our strategy become more generalized and powerful as the strategy evolute. The main purpose of the off-policy algorithm approximate Q learning is to give us more inspirations on strategy design.

In summary, we choose MDPs with the value iteration algorithm as the final agent to join the match. The final strategy is the "Smart Small-Point".

## Comments per topic
**For the value iteration algorithm, final detailed strategies are as follows**:
```
a.  We have optimized strategy to decide choosing cards with small points to invite a noble or buy cards on the second dealt.
    1. We will calculate maximum overlapped colours of nobles each by each at the beginning. Only if no smaller than two colours in common we will choose noble strategy.
    2. For noble, we will choose to invite the one with the least cards needed.
b. The colours priority are calculated as:
    1. The colour has the least differences to invite the chosen noble.
    2. The needed colours for buying a target card on the second dealt.
    3. The colour needed by other two nobles.
    4. The most needed colours by all cards on board.
    5. The left colour.
c.  We will collect each colour gem at least one time in case that specific agent interrupt our agent.
d.  We also reserve cards if we can buy it at next round. But, only if there are no gems this card required on board and it has no less than 3 points will we reserve it.
e.  We add defense policy:
    1.  At the middle stage, we will reserve cards with no smaller than 3 points and it is the only card which the counter agent can get at its turn.
    2.  At the final stage, even if we can win this turn, the counter can win at its turn by buying and can only win by this card, we will reserve it in case that
        we have smaller check-out points to lose the game.
f.  For technique d of the "Naive Small-Point", we change to replace the rarest gems on board to the rarest gems in agent hands.
```
Our strategy has considered on choosing different tendencies according to the initial state of the board. During the
game, our agent will evaluate different rewards of an action and choose the highest one. This greedy choice will help us converge to 
near optimal decision path. And at the end of a game, we considered several corner cases in case that we lose the game when we take
the lead. It is the result from the continuous evolution of our strategies. As designers, it is enjoyable for us to discuss
and improve the strategy overall. We fell that splendor is a quite interesting game. However, we also realise that the value 
iteration is hard to design in games with large state space. Moreover, we also find it is hard to deign an agent which can 
thinks further within acceptable time.

**For the approximate Q learning, final detailed design of features are as follows**:

  1. For collecting gems, there are three types of feature for collecting gems:
    a. who can help to buy a card on board.
    b. to buy a reserved card. 
    c. if collect 1 or two gems, apply a punishment.

  2. For reserving cards, there are four types of feature for reserving a card:
    a. whose representing gem colour is required to buy the needed cards.
    b. who is needed when a wild is needed
    c. who is needed to invite a noble
    d. when passing the turn return a punishment

  3. For reserving cards, there are six types of feature for buying a card:
    a. who can gain points
    b. who can increase the needed gem colours
    c. whose colour is needed to invite a noble
    d. whose colour can buy a card on board.
    e. whose colour can buy a reserved card
    f. whose representing colours are needed during the path to invite a noble.

Since this method is a baseline and an inspiration model, our features are not deigned perfectly. The linear approximation is not precise. Our feature selection is also not optimal.
For example, in collecting gems feature collections, one problem is that we just treat all taking two gems as actions receiving punishment. 
However, sometimes taking two same gems is a good action. Such corner case is not considered as detailed as our method one did. 
Thus, one improvement can be modifying linear approximate function or using more complicated approximate functions or using neural network to calculate them. 
Another method is replacing approximate Q learning with Q learning and even deep Q learning.

We find this model does not need to care about strategy too much. It is off-policy. However, designer still need to have
a further understanding on game because features need to be designed based on game. During the development process, we find 
it is a totally different experience compared to the value iteration. 

## Offense and Defense Policy
In this section, we only discuss the value iteration algorithm with the "Smart Small-Point" strategy.
### Offense
The offense policies are the most in the strategy. They are:
```offense
a.  We have optimized strategy to decide choosing cards with small points to invite a noble or buy cards on the second dealt.
    1. We will calculate maximum overlapped colours of nobles each by each at the beginning. Only if no smaller than two colours in common we will choose noble strategy.
    2. For noble, we will choose to invite the one with the least cards needed.
b. The colours priority are calculated as:
    1. The colour has the least differences to invite the chosen noble.
    2. The needed colours for buying a target card on the second dealt.
    3. The colour needed by other two nobles.
    4. The most needed colours by all cards on board.
    5. The left colour.
c.  We will collect each colour gem at least one time in case that specific agent interrupt our agent.
d.  We also reserve cards if we can buy it at next round. But, only if there are no gems this card required on board and it has no less than 3 points will we reserve it.
e.  To save collect gems chance, we optimize the decision of gems. For example, if we find we have only three round to
    buy a card with 3 black 3 white and 2 blue gems at the opening. We will collect white, black and blue for two rounds.
    But for the last round, we will take white and black and other colours gems which is the rarest in agent hands.
```
### Defense
The defense policies are mainly achieved by reservation:
```angular2html
a.  At the middle stage, we will reserve cards with no smaller than 3 points and it is the only card which the counter agent can get at its turn.
b.  At the final stage, even if we can win this turn, the counter can win at its turn by buying and can only win by this card, we will reserve it in case that
    we have smaller check-out points to lose the game.
```
