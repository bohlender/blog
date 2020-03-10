---
title: "Playing Hard Mastermind Games with a SAT-based AI"
date: 2020-03-08T16:12:02+01:00
tags: ["SAT", "AI", "Puzzle"]
draft: true
math: true
images: []
videos: []
audio: []
---
Back in the day, [Mastermind](https://en.wikipedia.org/wiki/Mastermind_(board_game)) was a popular two player code-breaking game, and many [variations thereof](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations) still exist as both standalone games and puzzles within other games.
Although it is difficult for a human player to make *optimal guesses* of the secret code, or at least guesses that do not conflict with the provided hints, the setting is usually simple enough for an AI to find such candidates via explicit exploration of the [game tree](https://en.wikipedia.org/wiki/Game_tree).

However, such approaches becomes unfeasible when the number of possibilities for secret codes grows into the millions.
This post illustrates how the problem of finding consistent candidates can be approached with [SAT](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) solving, yielding an AI that can handle orders-of-magnitude harder Mastermind instances than the standard approaches.
<!--more-->
## Introduction
Every now and then, my friends and I gather to play [Mansions of Madness](https://en.wikipedia.org/wiki/Mansions_of_Madness) -- a cooperative boardgame.
In line with its Lovecraftian setting, the game is often unforgiving so we try to optimise our every move.
Besides the core gameplay, solving various puzzles is often needed to advance.
One of these puzzles is in fact [a Mastermind variant](https://boardgamegeek.com/image/3742103/mansions-madness-second-edition), and, as [some players argue](https://www.boardgamegeek.com/thread/1653724/code-puzzle-absurdity-almost-game-breaking), the instances may be rather difficult to reason about -- resulting in wasted turns and decreased chance of winning the scenario.
This is how the problem of making educated guesses in Mastermind piqued my interest.

### Rules of Mastermind
In the classic Mastermind game, a *secret code* $s$ is a row of four pegs, where each peg is of one of six colours.
For example given the colours
$
\textcolor{#272822}&#9679;
\textcolor{#f92672}&#9679;
\textcolor{#a6e22e}&#9679;
\textcolor{#f4bf75}&#9679;
\textcolor{#66d9ef}&#9679;
\textcolor{#ae81ff}&#9679;
$,
the following sequence would be a possible secret code:

$$\tag{1}
s=\textcolor{#a6e22e}&#9679;\textcolor{#272822}{&#9679;&#9679;}\textcolor{#f92672}{&#9679;}
$$

This secret is designed by and only known to the *codemaker*.
In every round, the *codebreaker* makes a guess, and receives a pair of numbers as feedback/hint from the codemaker:
1. The number of *full matches* states how many of the pegs coincide with the secret.
1. The number of *partial* or *symbol matches* states how many additional full matches can be achieved by reordering the pegs.

For example let $s$ be the secret from $(1)$ and $g=\textcolor{#a6e22e}{&#9679;}\textcolor{#f92672}{&#9679;&#9679;}\textcolor{#ae81ff}{&#9679;}$ be the codebreaker's guess.
The codemaker's feedback to that guess would be $(1, 1)$, since
* only one peg matches exactly -- the green one in the first position
* even though there are two pink pegs, only one of them can become a full match if put in the last position -- we can't put both there

The following code computes such feedback in two phases.
First, we get rid of all full matches from both the `guess` and `secret`, and then try to match the remaining symbols:
{{< highlight-file "mastermind.py" Python 19 34 >}}

### Example Playthrough
A full playthrough of classic Mastermind, i.e. with codes of length four and six colours/symbols
$\Sigma=\\\{
    \textcolor{#272822}&#9679;,
    \textcolor{#f92672}&#9679;,
    \textcolor{#a6e22e}&#9679;,
    \textcolor{#f4bf75}&#9679;,
    \textcolor{#66d9ef}&#9679;,
    \textcolor{#ae81ff}&#9679;
\\\}$
to choose from, may look as follows.

The game starts with the codemaker picking a secret $s\in\Sigma^4$.
To keep things simple, let this be the familiar combination $s=\textcolor{#a6e22e}&#9679;\textcolor{#272822}{&#9679;&#9679;}\textcolor{#f92672}{&#9679;}$ from $(1)$.
Without questioning the reasoning of the codebreaker, the following table outlines possible guesses and received feedback of every round.

| Round | Guess | Feedback |
| :---: | :---: | :------: |
| 1 | $\textcolor{#272822}&#9679;\textcolor{#ae81ff}{&#9679;&#9679;}\textcolor{#66d9ef}{&#9679;}$ | $(0, 1)$ |
| 2 | $\textcolor{#f92672}&#9679;\textcolor{#f4bf75}{&#9679;}\textcolor{#272822}{&#9679;&#9679;}$ | $(1, 2)$ |
| 3 | $\textcolor{#f4bf75}&#9679;\textcolor{#a6e22e}{&#9679;}\textcolor{#272822}{&#9679;}\textcolor{#f92672}{&#9679;}$ | $(2, 1)$ |
| 4 | $\textcolor{#a6e22e}&#9679;\textcolor{#272822}{&#9679;&#9679;}\textcolor{#f92672}{&#9679;}$ | $(4, 0)$ |

This is in fact the log of an actual game played by the SAT-based AI that we will end up with at the end of the post.

The corresponding game loop amounts to few lines of code.
It requires a potential player or AI to be able to give a first guess at the beginning of the game (`initial_guess()`), and incorporate feedback for subsequent guesses (`make_guess(feedback)`):
{{< highlight-file "mastermind.py" Python 50 69 >}}

### Where's the Difficulty?
With four positions and six colours there are only $6^4=1296$ possible combinations to choose from, so keeping the set of all combinations in memory and working with it is perfectly feasible when solving classic Mastermind instances.
However, there is nothing hindering us from using even longer sequences or introducing further colours.
The **code length** $|s|$ and **set of colours/symbols** $\Sigma$ are exactly the parameters that are typically varied to arrive at the different [variations of Mastermind](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations).

For example, *Grand Mastermind* keeps the secret length of the original but uses $25$ symbols ($5$ shapes, $5$ colours) which allows for $25^4=390.625$ different codes.
Overall, most Mastermind variants feature a number of combinations in this order of magnitude (thousands), rendering them amenable to analysis via methods that explicitly explore the game tree.
At the time of writing, [the Wikipedia page](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations) lists only one exception: *Mastermind Secret Search* uses $26$ letters as symbols to form words up to a length of 6 characters which gives rise to $26^6=308.915.776$ possible secrets.

{{< note >}}
Keep in mind that Mastermind games are designed to be played by humans, and mostly feature reasonably small numbers of combinations.
To alleviate the difficulty of playing the variations with large numbers of combinations, such games resort to additional constraints or more restrictive feedback.

*Mastermind Secret Search* limits the secret codes to valid words and provides separate feedback for each letter, stating whether the secret letter occurs earlier or later in the alphabet.
{{</ note >}}

But how to approach playing Mastermind variants with $6^{16}=2.821.109.907.456$ or more combinations to choose from, without resorting to uneducated guessing?
Just to give you an idea: even iterating through all these combinations will take "forever" and is out of question for a game AI.
Therefore, even when not aiming for optimal play but merely reasonable/consistent guesses, explicit methods won't get us far.
However, they are good enough for most practical Mastermind variants and exactly where we start off.

## Explicit Approaches
asdf
<!-- Representation of guess secret -->

### Explicit Refinement of Candidates Set
asdf

### Lazy Enumeration of Consistent Candidates
asdf

## SAT-based Approach
asdf
<!-- Add matching graphic (prior to encoding) -->

## Do Try This at Home!
asdf

{{< list-resources "{*.py}" >}}