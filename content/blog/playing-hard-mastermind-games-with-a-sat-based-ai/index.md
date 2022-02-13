---
title: "Playing Hard Mastermind Games with a SAT-based AI"
date: 2020-03-08T16:12:02+01:00
publishDate: 2020-03-12
tags: ["SAT", "AI", "Puzzle"]
draft: false
math: true
images: []
videos: []
audio: []
---
Back in the day, [Mastermind](https://en.wikipedia.org/wiki/Mastermind_(board_game)) was a popular two player code-breaking game, and many [variations thereof](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations) still exist as both standalone games and puzzles within other games.
Although it is difficult for a human player to make *optimal guesses* of the secret code, or at least guesses that do not conflict with the provided clues, the setting is usually simple enough for an AI to find such candidates via explicit exploration of the [game tree](https://en.wikipedia.org/wiki/Game_tree).

However, such approaches become unfeasible when the number of possibilities for secret codes grows into the millions.
This post illustrates the problem with standard approaches, and how finding consistent candidates can be approached with [SAT](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) solving -- yielding an AI that can handle orders-of-magnitude harder Mastermind instances.
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
In every round, the *codebreaker* makes a guess, and receives a pair of numbers as feedback/clue from the codemaker:
1. The number of *full matches* states how many of the pegs coincide with the secret.
1. The number of *partial* or *symbol matches* states how many additional full matches can be achieved by reordering the pegs.

For example let $s$ be the secret from $(1)$ and $g=\textcolor{#a6e22e}{&#9679;}\textcolor{#f92672}{&#9679;&#9679;}\textcolor{#ae81ff}{&#9679;}$ be the codebreaker's guess.
The codemaker's feedback to that guess would be $(1, 1)$, since
* only one peg matches exactly (the green one in the first position)
* even though there are two pink pegs, only one of them can become a full match if put in the last position -- we can't put both there

The following code computes such feedback in two phases.
First, we get rid of all full matches from both the `guess` and `secret`, and then try to match the remaining symbols:
{{< highlight-file "mastermind.py" Python 14 28 >}}

### Example Playthrough
A full playthrough of classic Mastermind, i.e. with codes of length four, and six colours/symbols
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

This is in fact the log of an actual game played by the SAT-based AI that we will end up with in the end of the post.

The corresponding game loop amounts to few lines of code.
It requires a potential player or AI to be able to give a first guess at the beginning of the game (`initial_guess()`), and incorporate feedback for subsequent guesses (`make_guess(feedback)`):
{{< highlight-file "mastermind.py" Python 54 71 >}}

### Where's the Difficulty?
With four positions and six colours there are only $6^4=1\\,296$ possible combinations to choose from, so keeping the set of all combinations in memory and working with it is perfectly feasible when solving classic Mastermind instances.
However, there is nothing hindering us from using even longer sequences or introducing further colours.
The **code length** $|s|$ and **set of colours/symbols** $\Sigma$ are exactly the parameters that are typically varied to arrive at the different [variations of Mastermind](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations).

For example, *Grand Mastermind* keeps the secret length of the original but uses $25$ symbols ($5$ shapes, $5$ colours) which allows for $25^4=390\\,625$ different codes.
Overall, most Mastermind variants feature a number of combinations in this order of magnitude (thousands), rendering them amenable to analysis via methods that explicitly explore the game tree.
At the time of writing, [the Wikipedia page](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations) lists only one exception: *Mastermind Secret Search* uses $26$ letters as symbols to form words up to a length of six characters, which gives rise to $26^6=308\\,915\\,776$ possible secrets.

{{< note >}}
Keep in mind that Mastermind games are designed to be played by humans, and mostly feature reasonably small numbers of combinations.
To alleviate the difficulty of playing the variations with large numbers of combinations such games resort to additional constraints or more restrictive feedback.

*Mastermind Secret Search* limits the secret codes to valid words and provides separate feedback for each letter, stating whether the secret letter occurs earlier or later in the alphabet.
{{</ note >}}

But how to approach playing Mastermind variants with $6^{16}=2\\,821\\,109\\,907\\,456$ or more combinations without resorting to blind guessing?
Just to give you an idea: even iterating through all these combinations will take <q>forever</q> and is out of question for a game AI.
Therefore, even when not aiming for optimal play but merely reasonable guesses, explicit and enumerative methods without backtracking or learning from conflicts won't get us far.
However, they work well for most practical Mastermind variants and are a good place to start getting a feel for the problem domain.

## Explicit Approaches
In contrast to *symbolic* methods for search and reachability checking, which work with implicit representations of state sets, *explicit* methods actually construct each state (here: secret codes) separately and store each in an accessible form in memory.

{{< note >}}
I've found this [overview of Mastermind strategies](http://www.philos.rug.nl/~barteld/master.pdf) particularly helpful to get an understanding of the (explicit) standard approaches and their tradeoffs. 
{{</ note >}}

In the following implementations, we represent secrets as tuples of integers.
That is, the symbol set
$\Sigma=\\\{
    \textcolor{#272822}&#9679;,
    \textcolor{#f92672}&#9679;,
    \textcolor{#a6e22e}&#9679;,
    \textcolor{#f4bf75}&#9679;,
    \textcolor{#66d9ef}&#9679;,
    \textcolor{#ae81ff}&#9679;
\\\}$
is treated as $\Sigma=\\\{0,1,2,3,4,5\\\}$, and the secret $s=\textcolor{#a6e22e}&#9679;\textcolor{#272822}{&#9679;&#9679;}\textcolor{#f92672}{&#9679;}$ is just the tuple $s=(2,0,0,1)$ to us.
Given $|s|$ and $|\Sigma|$, we can now easily enumerate all possible secrets with Python's [`product`](https://docs.python.org/3.8/library/itertools.html#itertools.product) function:
{{< highlight-file "mastermind.py" Python 42 43 >}}

### Refinement of Consistent Candidates
The simplest approach to playing Mastermind is probably to iterate over `all_secrets()` and commit each element, since we must eventually encounter the code chosen by the codemaker.
However, this approach completely ignores the feedback received from the codemaker, and will obviously lead to many wasted rounds for the codebreaker.

The next best thing we can try is to avoid making guesses that are *inconsistent* with the accumulated feedback.
For this, we must merely check that whatever we assume `secret` to be, it generates the same feedback for the previous guesses as the actual secret.
For every guess-feedback pair from previous rounds the following function must return $\mathit{true}$:
{{< highlight-file "mastermind.py" Python 31 32 >}}

This is exactly the approach suggested by [Shapiro](https://doi.org/10.1145/1056635.1056637) in 1983, and a naïve implementation is provided with `ExplicitConsistentAi`:

{{< highlight-file "mastermind.py" Python 82 95 >}}

`self.candidates` stores all candidates that are consistent with the received feedback.
Prior to the first guess there is no feedback, so initially all possible secrets are consistent.
Although the implementation always returns the first element, there is nothing wrong with picking a different one.

Unless a guess happens to match the secret exactly, we will receive feedback $f$ that renders some elements of `self.candidates` inconsistent with $f$.
Therefore, after every round, such candidates and the last (wrong) guess are removed from `self.candidates`.

Although the approach does not result in optimal play, and many instances can be won in less turns, it is computationally cheap and solves a classic Mastermind instance in $5.765$ turns on average.
This is surprisingly [close to the theoretical minimum](http://www.philos.rug.nl/~barteld/master.pdf) of $4.34$ turns.

### Lazy Enumeration of Consistent Candidates
A downside of the above method is that it keeps a list of *all* consistent candidates in memory.
Since the number of possible secrets grows exponentially in the admissible length of secrets, this may already hinder us from solving slightly harder Mastermind variations, e.g. with $6^8$ possible secrets.

`LazyExplicitConsistentAi` is a more practical implementation of the previous approach.
It enumerates the consistent combinations but only needs one candidate to be explicitly present in memory at a time, which results in a small memory footprint:
{{< highlight-file "mastermind.py" Python 136 149 >}}

Unlike the previous approach, which incrementally refines the set of candidates w.r.t. the latest feedback, a lazily generated candidate is checked w.r.t. all of the received feedback:
{{< highlight-file "mastermind.py" Python 35 39 >}}

### Minimax-based Guessing
Since my original motivation for looking into the topic was to learn how to play the Mastermind games in [Mansions of Madness](https://en.wikipedia.org/wiki/Mansions_of_Madness) optimally, I feel like I should outline how to do this, too.
Even though the central topic of this post is the (symbolic) computation of consistent guesses for hard Mastermind instances.

Instead of just picking some consistent candidate, one can also analyse how promising the various candidates are and pick the <q>best</q> one -- depending on some heuristic or notion of quality.

The first and probably most popular way for picking a "good" candidate was suggested by [Knuth](https://www.cs.uni.edu/~wallingf/teaching/cs3530/resources/knuth-mastermind.pdf) in 1977.
The general idea is that the best guess should minimise the set of consistent candidates -- no matter the feedback.
By assuming the least helpful feedback to be returned for each guess, and picking the (not necessarily consistent) guess in this setting that will yield the smallest set of consistent candidates, Knuth effectively implements a shallow [Minimax](https://en.wikipedia.org/wiki/Minimax) rule.
While a tree-like illustration is most helpful for Minimax on longer games, I found the table-oriented argument from [the overview](http://www.philos.rug.nl/~barteld/master.pdf) to be more apt in the case of Mastermind.

Consider committing some candidate $c$ and, in turn, receiving some feedback $f$.
The following table illustrates the possible outcomes depending on the chosen $c$ and the codemaker's feedback $f$ for the very *first guess*:

|       | &nbsp;$(0,0,0,0)$&nbsp; | &nbsp;$(0,0,0,1)$&nbsp; | &nbsp;$(0,0,1,0)$&nbsp; | &nbsp;$(0,0,1,1)$&nbsp; | &nbsp;$\dots$&nbsp; |
| :---: | :---------------------: | :---------------------: | :---------------------: | :---------------------: | :-----------------: | 
|$(0,0)$| $625$                   | $256$                   | $256$                   | $256$                   | $\dots$             |
|$(0,1)$| $0$                     | $308$                   | $308$                   | $256$                   | $\dots$             |
|$(0,2)$| $0$                     | $61$                    | $61$                    | $96$                    | $\dots$             |
|$(0,3)$| $0$                     | $0$                     | $0$                     | $16$                    | $\dots$             |
|$(0,4)$| $0$                     | $0$                     | $0$                     | $1$                     | $\dots$             |
|$(1,0)$| $500$                   | $317$                   | $317$                   | $256$                   | $\dots$             |
|$(1,1)$| $0$                     | $156$                   | $156$                   | $208$                   | $\dots$             |
|$(1,2)$| $0$                     | $27$                    | $27$                    | $36$                    | $\dots$             |
|$(1,3)$| $0$                     | $0$                     | $0$                     | $0$                     | $\dots$             |
|$(2,0)$| $150$                   | $123$                   | $123$                   | $114$                   | $\dots$             |
|$(2,1)$| $0$                     | $24$                    | $24$                    | $32$                    | $\dots$             |
|$(2,2)$| $0$                     | $3$                     | $3$                     | $4$                     | $\dots$             |
|$(3,0)$| $20$                    | $20$                    | $20$                    | $20$                    | $\dots$             |
|$(4,0)$| $1$                     | $1$                     | $1$                     | $1$                     | $\dots$             |

For each possible guess, there is a column which states the sizes of the resulting sets of consistent candidates for each possible feedback.
To make it more clear, consider picking $c=(0,0,0,0)$ for the first guess.
The worst that could happen next would be receiving the feedback $(0,0)$, since this would still leave us with a set of $625$ candidates that are consistent with the feedback.
In contrast, the best feedback would clearly be $(4,0)$, as this would imply that our guess was equal to the secret code and we just won.

{{< note >}}
Due to symmetry and the lack of feedback, there is actually no need to enumerate *all* possible secrets for the first guess.
It is sufficient to consider $(0,0,0,0)$, $(0,0,0,1)$, $(0,0,1,1)$, $(0,0,1,2)$ and $(0,1,2,3)$ to cover all unique columns.
{{</ note >}}

To develop the idea further, finding the <q>best</q> guess amounts to constructing such a table, identifying the worst case of each column, and picking the column/candidate with the smallest worst case.
According to the provided table, *a* best initial guess would be $(0,0,1,1)$, which guarantees to bring the set of candidates down to a size of at most $256$.
`ExplicitMinimaxAi` implements this method to determine the best guess:
{{< highlight-file "mastermind.py" Python 98 133 >}}

Note that the best move may even be to gather further information and purposefully make a guess that is inconsistent with the received feedback.
However, if there is both a consistent and an inconsistent candidate that are <q>best</q>, one should of course prefer the consistent one -- it might match the secret after all.
That's why we also keep the inconsistent candidates (`self.not_candidate`) around.

The Minimax-based approach solves any classic Mastermind instance **within five guesses**, and needs $4.476$ rounds on average.
Unfortunately, the runtime complexity of this and similar methods that optimise rigorously is quadratic in the number of candidates.
Considering that even iterating over all possible secrets of a hard Mastermind instance takes too long for a game AI, aiming for optimal guesses is quite a stretch.

## SAT-based Approach
So far we've seen that the Minimax-based approach is well-suited for Mastermind instances with small numbers of possible secrets, and that the lazy enumeration of consistent candidates is not optimal, but cheaper to compute, and on average not much worse.
However, despite the small memory footprint, the core problem is that enumerative methods don't scale to larger Mastermind instances.

It would be nice if we could at manage to compute consistent candidates for the hard instances, but even this problem [is known](https://arxiv.org/abs/cs/0512049) to be [NP-complete](https://en.wikipedia.org/wiki/NP-complete).
Luckily, we can reduce the problem to another well-studied NP-complete problem -- the [Boolean satisfiability problem (SAT)](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) -- and leverage the highly-tuned solvers existing for it.

All we have to do is devise a logical characterisation of the candidates that are consistent with the feedback received so far and use a SAT solver to acquire such a candidate.
Let's see what kind of variables and constraints we need for this.

### Encoding the Symbol Mapping
Since we want to guess some secret $s$, we first of all need variables that indicate which symbol occurs at which position.
To this end, we introduce the Boolean variables:
$$s_{\mathit{pos},\mathit{sym}}$$
where $\mathit{pos}\in \\\{0,\dots,|s|-1\\\}, \mathit{sym}\in\Sigma$.

The intended semantics is that an assignment $s_{1,2}\mapsto\mathit{true}$ denotes symbol $2$ to be at index $1$ of $s$.
However, since there are no constraints yet, a solver might just as well choose $s_{1,2}$ and $s_{1,3}$ to be $\mathit{true}$, which suggests both $2$ and $3$ to be at index $1$ of the secret.

To characterise that each position of the tuple $s$ has **exactly one** symbol, we need add an according *cardinality constraint* for each position.
Assuming the classic Mastermind setting, i.e. $|s|=4$ and $|\Sigma|=6$, we add the constraints:

{{< math >}}
\begin{aligned}
s_{0,0} + s_{0,1} + s_{0,2} + s_{0,3} + s_{0,4} + s_{0,5} &= 1,\\
s_{1,0} + s_{1,1} + s_{1,2} + s_{1,3} + s_{1,4} + s_{1,5} &= 1,\\
s_{2,0} + s_{2,1} + s_{2,2} + s_{2,3} + s_{2,4} + s_{2,5} &= 1,\\
s_{3,0} + s_{3,1} + s_{3,2} + s_{3,3} + s_{3,4} + s_{3,5} &= 1\\
\end{aligned}
{{</ math >}}

If we were to query the satisfiability of our SAT instance now, we would get a satisfying assignment with four of the $s_{\mathit{pos},\mathit{sym}}$ variables set to $\mathit{true}$ -- one for each $\mathit{pos}$.

Using the Python bindings for [Z3](https://github.com/Z3Prover/z3/) -- a popular solver for SAT and [SMT](https://en.wikipedia.org/wiki/SMT_solver) instances -- the initialisation of `SymbolicConsistentAi` creates the discussed variables and constraints:
{{< highlight-file "mastermind.py" Python 152 164 >}}

### Encoding Full Matches
Initially, there is no feedback to constrain the set of consistent candidates, and picking a random candidate is unproblematic.
Any subsequent guess, however, should at least be consistent with the feedback accumulated up to that point.
To characterise such candidates, we next consider which constraints some feedback $f$ for a committed candidate $c$ imposes.

Consider the first part of the feedback: the number of full matches.
This is clearly another cardinality constraint, but this one does not constrain the $s_{\mathit{pos},\mathit{sym}}$ variables directly.
Instead we need some auxiliary variables
$$\mathit{fm}_\mathit{pos}$$
where $\mathit{pos}\in \\\{0,\dots,|s|-1\\\}$, to identify in which position we have a full match and count the number of matches.
These are the variables for which we create the constraint.
Assuming the classic Mastermind setting and some feedback $f=(2,1)$, we simply add:
$$\mathit{fm_0} + \mathit{fm_1} + \mathit{fm_2} + \mathit{fm_3} = 2$$

Although the $\mathit{fm}\_\mathit{pos}$ variables are now constrained, they are not related to any $s_{\mathit{pos},\mathit{sym}}$ yet.
Intuitively, a variable $\mathit{fm}_\mathit{pos}$ should be $\mathit{true}$, if and only if the symbol at index $\mathit{pos}$ of a committed candidate has the same symbol as the secret at index $\mathit{pos}$ -- that's what a full match is.
With this in mind, and assuming the candidate to have been $c=(3,2,0,1)$, the following constraints establish the missing link:

{{< math >}}
\begin{aligned}
s_{0,3} &= \mathit{fm}_0,\\
s_{1,2} &= \mathit{fm}_1,\\
s_{2,0} &= \mathit{fm}_2,\\
s_{3,1} &= \mathit{fm}_3
\end{aligned}
{{</ math >}}

The first part of `make_guess` mirrors the discussed idea, but introduces fresh variables $\mathit{fm}_\mathit{pos}$ in every iteration since the feedback of different rounds is unrelated:
{{< highlight-file "mastermind.py" Python 182 192 >}}

{{< note >}}
During development I actually used variables of the form $\mathit{fm}_{\mathit{pos},\mathit{round}}$ to simplify debugging.
Once done, it was just more readable to let Z3 pick fresh names for the variables instead of manually generating distinct names for each feedback's full match variables.
{{</ note >}}

### Encoding Symbol Matches
What remains is the creation of constraints which enforce consistency w.r.t. the second part of the feedback: the number of symbol matches.
Unlike the full match <q>flag</q> that we introduced for every position, a symbol match relates two positions -- one from the guess with one from the secret.
To this end, we introduce the Boolean variables:
$$\mathit{sm}_{\mathit{src},\mathit{dst}}$$
where $\mathit{src},\mathit{dst}\in \\\{0,\dots,|s|-1\\\}$.
A true literal $\mathit{sm}\_{2,3}$ shall denote that the symbol at index $2$ of the guess can be moved to index $3$ to achieve a full match.

With this in mind, we can easily construct an according cardinality constraint for some feedback $f=(2,1)$:
$$\mathit{sm}\_{0,1} +\mathit{sm}\_{0,2} + \dots + \mathit{sm}\_{3,2}  = 1$$
Note that no constraint should have a variable of the form $\mathit{sm}_{\mathit{pos},\mathit{pos}}$, as such a case would actually describe a full match -- not a symbol match.

{{< note >}}
One might think that it is also necessary to add a constraint which disallows cases like $\mathit{sm}\_{2,1}$ and $\mathit{sm}_{3,1}$ being $\mathit{true}$ at the same time.
After all, this would indicate that both symbols can become full matches if moved to the same position.

This is not wrong, but unnecessary since the following constraints already take care of that.
{{</ note >}}

To characterise the intended relation between the $\mathit{sm}\_{\mathit{src},\mathit{dst}}$ variables and the $\mathit{s}\_{\mathit{pos},\mathit{sym}}$ variables, we define a matching scheme that takes existing full matches into consideration and **prioritises low indices**.
A variable $\mathit{sm}\_{\mathit{src},\mathit{dst}}$ should be $\mathit{true}$, if and only if **all** of the following conditions are met:
* There is no full match at position $\mathit{src}$:
$$\neg \mathit{fm}\_\mathit{src}$$
* The symbol $\mathit{sym}$ at index $\mathit{src}$ of the guess is the same as the symbol at index $\mathit{dst}$ of the secret:
$$s_{\mathit{dst},\mathit{sym}}$$
* There is no full match at position $\mathit{dst}$:
$$\neg \mathit{fm}\_\mathit{dst}$$
* No smaller (higher priority) position has matched the symbol at $\mathit{dst}$:
$$\bigwedge_{\substack{0\leq\mathit{prev}<\mathit{src}\\\ \mathit{prev} \neq \mathit{dst}}} \neg \mathit{sm}_{\mathit{prev},\mathit{dst}}$$
* The symbol at index $\mathit{src}$ has not matched any symbol on a smaller (higher priority) position:
$$\bigwedge_{\substack{0\leq\mathit{prev}<\mathit{dst}\\\ \mathit{prev} \neq \mathit{src}}} \neg \mathit{sm}_{\mathit{src},\mathit{prev}}$$

The rest of the `make_guess` method -- started in the previous section -- implements the proposed encoding:
{{< highlight-file "mastermind.py" Python 194 223 >}}

Note that we treat the $\mathit{sm}\_{\mathit{src},\mathit{dst}}$ variables similar to the feedback-specific $\mathit{fm}\_\mathit{pos}$ variables: we introduce fresh ones for every feedback.

### Computing a Guess
We now have all the constraints together for the $s_{\mathit{pos},\mathit{sym}}$ variables to characterise the code sequences that are consistent with the received feedback.
To actually compute a guess, we just need to find an assignment that satisfies these constraints.
Luckily, we can delegate this task to a SAT solver.

To construct the guess, we identify the $s_{\mathit{pos},\mathit{sym}}$ variables that are set to $\mathit{true}$:
{{< highlight-file "mastermind.py" Python 166 180 >}}

That's all there is to it.
Feel free to experiment with [the provided implementation](mastermind.py) of the discussed methods.
Using the `SymbolicConsistentAi` you can now easily play Mastermind games with huge numbers of secret code combinations.
On average, it takes only $10.51$ guesses to find the secret within $2\\,821\\,109\\,907\\,456$ possible combinations of the classic Mastermind variant with codes of length $16$ (see experiments below).

## Experiments
For reference, I've run some experiments to measure the performance on an i7-7700K CPU, using Python 3.8 and Z3 v4.8.7.
The following table provides both a qualitative and quantitative comparison of the lazy enumeration AI and the SAT-based AI, with measurement cells formatted as <q>(Explicit / Symbolic)</q>:

| $\|s\|,\|\Sigma\|$&nbsp; | &nbsp;Games Played&nbsp; | &nbsp;Avg. Turns&nbsp; | &nbsp;Max. Turns&nbsp; | &nbsp;Avg. Game Time&nbsp; | 
| :--------: | :---------------------: | :--------------------: | :--------------------: | :------------------------: |
| 4, 6       | all 1&#8201;296         | 5.765 / 4.659          | 9 / 7                  | 2ms / 17ms                 |
| 5, 6       | all 7&#8201;776         | 6.218 / 5.100          | 11 / 8                 | 11ms / 34ms                |
| 6, 6       | all 46&#8201;656        | 6.735 / 5.572          | 12 / 9                 | 71ms / 60ms                |
| 7, 6       | 10&#8201;000            | 7.301 / 6.072          | 11 / 9                 | 466ms / 101ms              |
| 8, 6       | 1&#8201;000             | 7.874 / 6.560          | 12 / 10                | 3s / 161ms                 |
| 9, 6       | 10&#8201;000            | ? / 7.237              | ? / 11                 | ? / 263ms                  |
| 10, 6      | 10&#8201;000            | ? / 7.901              | ? / 12                 | ? / 413ms                  |
| 16, 6      | 1&#8201;000             | ? / 10.51              | ? / 15                 | ? / 6.6s                   |

{{< note >}}
Note that, due to the nondeterministic and heuristics-guided nature of SAT solving, the results may vary slightly for your setup.
{{</ note >}}

As to be expected, the lazy enumeration works well for Mastermind variants with small numbers of possible secrets but becomes unusably slow on harder instances.
Such measurements were aborted and are denoted by <q>?</q> in the table.
Furthermore, once the average game times went into the seconds, I switched from evaluating the performance for each possible secret to a fixed number of secrets that are evenly spaced over all possible combinations.
Accordingly, for those non-exhaustive runs, the measured maximal number of turns is not a guaranteed worst case for all instances.

Although both approaches implement the same idea, i.e. make guesses that are consistent with the feedback, the qualitative results differ.
This is because our implementation of Shapiro's idea picks the *smallest* consistent candidate but the SAT-based approach picks *some* consistent candidate.
The latter seems to be advantageous.

## Do Try This at Home!
As usual, there is a lot of room for further improvement and experimentation.
Here are some points you might want to explore on your own (easiest first):
* There are many low hanging fruits regarding performance improvements.
  Python is convenient for prototyping but its interpreted nature slows down the execution.
  Try alternative Python implementations like [Pypy](https://www.pypy.org/) to get a significant speedup of the explicit approaches for free, or port the approaches to [your favorite compiled language](https://dlang.org/).
  Furthermore, even though Z3 has tons of features and is a joy to use, I expect dedicated SAT solvers like [Lingeling](https://github.com/arminbiere/lingeling) to be even faster at solving the resulting constraints.
* Try to devise a SAT/SMT-based solver for a Mastermind variation with different forms of feedback.
  For example, [Number Mastermind](https://en.wikipedia.org/wiki/Mastermind_(board_game)#Variations) is played with numbers and the secret's sum is an additional clue.
* The proposed logical characterisation is just what seemed most straightforward to me.
  Try reformulating the encoding to achieve even better solver performance -- I might have overlooked a thing or two.
* Investigate whether it is feasible to implement the Minimax-style approach (or some other heuristic) symbolically.
  Depending on the chosen approach, it might help to look into [MAX-SAT](https://en.wikipedia.org/wiki/Maximum_satisfiability_problem) or [(approximate) model counting](https://www.msoos.org/2018/12/how-approximate-model-counting-works/).

{{< list-resources "{*.py}" >}}