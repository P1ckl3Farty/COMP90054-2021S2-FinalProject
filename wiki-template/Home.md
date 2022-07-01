# UoM COMP90054 Contest Project

[Wiki link](https://github.com/COMP90054-2021S2/contest-otaku_best.wiki.git)

1. [Home and Introduction](Home.md)
2. [Design Choices (Offense/Defense)](Design-Choices.md)

    2.1 [MDPs with the value iteration](AI-Method-1.md)

    2.2 [Approximate Q learning](AI-Method-2.md)

3. [Evolution and Experiments](Evolution.md)
4. [Conclusions and Reflections](Conclusions-and-Reflections.md)


# Youtube presentation

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/cZVN7silTTQ/0.jpg)](https://www.youtube.com/watch?v=cZVN7silTTQ)


## Team Members

List here the full name, email, and student number for each member of the team:

* Boyang Zhang - Boyazhang1@student.unimelb.edu.au - 1184097
* Jiehuang Shi - jiehuangs@student.unimelb.edu.au - 980709
* Mo Zhou - mzzho2@student.unimelb.edu.au - 1212382

## Introductions
AI planning for autonomy is a popular topic in the computer science field. It has been widely used in auto-pilot, industry 
robot, games and even more advanced areas such as space exploration. With an AI agent, people hope to use this pre-coded or
trained program to give an optimal action under a specific state. After dozens of years research, people has developed many
smart techniques and algorithms such us Breadth First Search, Markov Decision Processes (MDPs), Q learning and multilayer perceptron.
A typical way to test how smart an agent is to put it in a game. From cheese games like cheese and Go to video games like 
StarCraft, League of Legends and NBA2K, games have become a perfect playground to test the AI. Splendor, as a board game 
with medium size of state space, is the playground of this project. The rule of the splendor can be found in [splendor](splendor.md).
In this project, we will mainly discuss MDPs with the value iteration and the approximate Q learning to develop a smart AI to play this game.
We will explore how strategy evolutions can help the agent become smarter with the aid of off-policy agent using approximate
Q learning. We will also discuss the disadvantages and advantages of each agent. And challenges will be introduced as well.

In this documentation, you can find specific explanation on techniques and their implementations in [MDPs with the value iteration](AI-Method-1.md)
and [Approximate Q learning](AI-Method-2.md). You can also find why we choose MDPs with the value iteration algorithm 
with the "Smart Small-Point" strategy in [Design Choices (Offense/Defense)](Design-Choices.md). 
If you have interests in the evolution of our agents and their results, please refer to [Evolution and Experiments](Evolution.md). 
Finally, you can have read our conclusions in [Conclusions and Reflections](Conclusions-and-Reflections.md)
## Useful links - Wiki features

This wiki uses the [Markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) syntax. 

1. The [MarkDown Demo tutorial](https://guides.github.com/features/mastering-markdown/) shows how various elements are rendered.
2. This 5min video shows how to use markdown for creating [issues](https://www.youtube.com/watch?v=TKJ4RdhyB5Y).
3. The [GitHub documentation](https://docs.gitlab.com/ee/user/project/wiki/) has more information about using a wiki.
4. This video shows how can you use [Project boards and issues](https://www.youtube.com/watch?v=nI5VdsVl0FM&list=PLYMgErMHWi1PRMTsHXote19b7f9F-JjmT&index=2&t=1s) to integrate agile methodologies for working in your team.
5. Documentation on [wikis](https://docs.github.com/en/github/building-a-strong-community/documenting-your-project-with-wikis) by github.




