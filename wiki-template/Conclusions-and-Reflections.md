## Challenges  
Challenges during the whole process are:
```angular2html
1. Understanding of the game.
2. The game initial state is random and we need to classfify states and design different policy to use.
3. How to decide the macro strategy: targeting on large points cards, small points cards or nobles?
4. How to re-design the strategy if the macro strategy is not proper.
5. Finding logical bugs and flaw in our agent.
6. How to improve our corner case strategy.
7. How to design features and their relationships of approximate Q learning.
```
## Conclusions and Learnings
After this project, we have a more advanced understanding of MDPs framework with the value iteration algorithm and the approximate
Q learning in the splendor game.

For the value iteration, we design and improve our strategy. From watching the replay with other agents, our agent becomes
smarter. The value iteration is quite easy to converge to the optimal state if the strategy designed properly. However, after trail offline, 
we also realised that this model cannot find the optimal action of several future rounds within time limit. And the strategy design is a 
time-consuming and challenge stuff.

For the approximate Q learning, it performed good as a baseline. It inspired us to consider nobles. We added this strategy
into the value iteration model and found it performed well. We also noticed it that with smarter counter player to train, we will get a 
better agent. Moreover, if we can design features more precisely, we will have a more completed technique.
