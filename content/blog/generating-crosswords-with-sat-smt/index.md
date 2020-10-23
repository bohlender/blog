---
title: "Generating Crosswords via SAT/SMT"
date: 2020-09-27T16:03:37+02:00
tags: ["SAT", "Puzzle"]
draft: true
math: true
images: ["gfx/12x12_q103.svg"]
videos: []
audio: []
---
Recently I got interested in designing personalised crosswords as a way to spice up photo book presents.
This made me realise how hard generating <q>high-quality</q> crosswords actually is.
Trying to create a crossword from a set of words -- or a subset thereof -- I checked out several tools but found all of them to be based on heuristics and yield rather sparse crosswords.

In line with the general theme of my previous posts, this one illustrates how we can leverage [SAT solving](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) to solve this problem.
In contrast to related approaches, which assume a fixed word placement and search for fitting words, we consider word placement as part of the problem and eventually end up with an integrated solution to generating crosswords of adjustable quality.
<!--more-->
## The Problem Statement
When designing a crossword puzzle on a specific theme or topic, one will likely start with **a set of words** (and clever clues) that fit the setting and a rough idea of **the crossword's dimensions**.
For example, when designing a crossword for a magazine, the page size will probably limit the crossword's width to less than 20 cells to keep the characters legible.

For the sake of exposition, assume that we want to design a square crossword of size 12 on the topic of (mostly retro) games and let the following be the words we came up with:

{{< highlight-file "crossword.py" Python 256 265 >}}

Clearly, we can't put all of them in a 12x12 grid.
Not only do they amount to more than 144 characters but there are also certain **rules regarding allowed word placement** in a crossword.
That is,
1. the words must be placed horizontally or vertically within the crossword grid,
1. the words may not be placed within each other,
1. each word may only be placed once,
1. every horizontal and vertical contiguous sequence of characters in the grid must correspond to a word placement,
1. the placed words must form a single [connected component](https://en.wikipedia.org/wiki/Connected_component_%28graph_theory%29).

{{< note >}}
We consider horizontal character sequences to be read from left to right, and vertical ones from top to bottom.
{{< /note >}}

Overall, the problem of crossword generation amounts to selecting the subset of words that allows for a placement which is compliant with the rules but also achieves some level of <q>quality</q>.
While <q>quality</q> may be subjective, the following is an <q>optimal</q> placement for the quality metric I chose:

{{< figure src="gfx/12x12_q103.svg" title="An optimal word placement" width="380px" >}}

To really appreciate the result, try to come up with a subset and placement of words that looks better to you or at least contains a similar number of words.
For reference, you can also give [existing tools](https://duckduckgo.com/?q=best+crossword+puzzle+generator) a try.

## Overview of SAT-based Problem Solving
Given a Boolean formula, a [SAT solver](https://en.wikipedia.org/wiki/SAT_solver) determines whether a variable assignment exists which makes the formula evaluate to $\mathit{true}$.
To leverage this functionality for problem solving the problem must be characterised in terms of a Boolean formula, such that a solution to the formula can be interpreted as a solution for the original problem.
This process is also reflected in the structure of our main function:

{{< highlight-file "crossword.py" Python 26 46 >}}

Given a set of words, a sensible crossword size, and a minimal value for the required <q>quality</q>, `encodeProblem` shall return the Boolean constraints that -- in conjunction -- characterise word placements which meet these criteria.
Furthermore, we need to know which variables in these formulas represent which placement.
This is the information that will be stored in `placement_vars` (cf. line 35).
It will be used to interpret the satisfying assignment, or *model*, if one exists (cf. line 43).

Don't be surprised that we use the Python bindings of the [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) solver [Z3](https://github.com/Z3Prover/z3), although the claim was that we will use SAT solving machinery.
Since the resulting constraints are expressed over finite domains -- as both the crossword grid and the words are finite -- they can easily be [translated to SAT instances](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-sat-core).
Furthermore, it is often advantageous to use dedicated SAT solvers for such instances, so -- besides solving the SMT instance with Z3 in line 41 -- we also export the problem in the standard [format for SAT solvers](http://www.satcompetition.org/2011/format-benchmarks2011.html) in line 38.

## Encoding the Problem
Before looking into how the constraints mentioned in [the problem statement](#the-problem-statement) can be expressed as propositional SAT, let's start by compiling the set of variables and constants that we will clearly need for the characterisation of our problem.

When talking about word placement, what we typically have in mind are a word's start coordinates and its orientation.
For example, in the generated [crossword shown above](#an-optimal-word-placement), the phrase <q>MYST</q> starts at $(x,y)=(0,0)$ and is oriented vertically.
Since there is only a finite number of possible placements, a simple way of encoding the placement of a word $w$ in terms of Boolean variables is by means of a variable
$$w_{x,y,o}$$
for each position $(x,y)$ within the grid and orientation $o\in\\{\mathit{horizontal},\mathit{vertical}\\}$.
We will use these placement variables in such a way that 
$w_{x,y,o}$ being assigned $\mathit{true}$ in the SAT solver's solution will indicate that $w$ should be placed at $(x,y)$ in orientation $o$.
{{< note >}}
Of course we could have used two bounded integers $w_x,w_y$ and a Boolean $w_o$ just as well to encode the attributes separately.
However, this would ultimately have complicated the use of a SAT solver and the interpretation of its solution.
{{< /note >}}

In addition to the placement, we also need a way to characterise the subset of words that is actually used in the solution.
Only the placement of those selected words will be constrained and make sense.
Since the choice whether a word shall be part of the crossword is Boolean, it suffices to introduce a variable
$$w_\mathit{selected}$$
for each word $w$.

The first lines of `encodeProblem` do just that:

{{< highlight-file "crossword.py" Python 50 61 >}}

We now have variables to symbolise the placement of a word and whether it is part of the crossword.
What we still need is a characterisation of the grid, i.e. which character is placed in which grid cell, so we can relate a word's placement with the state of the grid.

Before we can relate words and characters in grid cells, we have to characterise characters logically as well.
Instead of supporting a fixed set of characters, e.g. lowercase alphanumeric characters, and denoting each by a corresponding logical symbol, it suffices to only create a constant $c$ for each distinct character <q>c</q> in our set of words.
Note that, to denote empty grid cells, we also introduce a special <q>empty</q> character:

{{< highlight-file "crossword.py" Python 63 67 >}}

`char_sort` is the finite domain of all characters that occur in our words (plus the empty one).
Here, it is fine to use a finite domain instead of Booleans since we will not interpret the grid's characters but derive everything from the placement of words.
We essentially do not care if the automated translation to SAT makes this information harder to extract.

With `char_sort` at hand, we can represent the characters in the grid as an array of such `char_sort` variables:

{{< highlight-file "crossword.py" Python 69 71 >}}

### Word Placement
With the variable creation out of the way, let's see how we can express the first few rules from [the problem statement](#the-problem-statement) as constraints over these variables.

Depending on how and whether a word is placed, other characters must appear in the corresponding grid cells.
So to encode [rule (1)](#the-problem-statement), we can iterate over each word and placement within the grid bounds, and assert that the characters match.
For example, to cover the placement of <q>MYST</q> in the [introductory crossword](#an-optimal-word-placement), we need the following constraint:

{{< math >}}
\begin{aligned}
\mathit{MYST}_{0,0,\mathit{vertical}} \rightarrow &~ grid_{0,0}=M\\
\wedge &~ grid_{0,1}=Y\\
\wedge &~ grid_{0,2}=S\\
\wedge &~ grid_{0,3}=T
\end{aligned}
{{< /math >}}

Lines 91 to 94 take care of creating such constraints for horizontal placement, but the vertical placement can be handled analogously:
{{< highlight-file "crossword.py" Python 73 94 >}}

Note that the utility of `possible_placements` and `word_placement_vars` may not be obvious yet, but tracking all words' possible placements in a cell and all possible placement of a word will come in handy later.

Besides relating the placement and grid variables, we also have to ensure that words are not placed within each other (cf. [rule (2)](#the-problem-statement)).
This can be achieved by requiring the characters before and after each placed word to be empty (or out of grid bounds).
In the case of our running example, this amounts to

{{< math >}}
\begin{aligned}
\mathit{MYST}_{0,0,\mathit{vertical}} \rightarrow &~ \cancel{grid_{0,-1}=\mathit{empty}}\\
\wedge &~ grid_{0,4}=\mathit{empty}
\end{aligned}
{{< /math >}}

where the coordinates $(0,-1)$ lie outside the grid.

The corresponding constraints can be created right after the previous ones:
{{< highlight-file "crossword.py" Python 96 103 >}}

Now, each word's possible placement has been characterised and related to the grid's characters.
However, there is nothing stopping the SAT solver from picking two placements for the same word and violating [rule (3)](#the-problem-statement).
To account for this, we require at most one variable $w_{x,y,o}$ to be $\mathit{true}$ for each word $w$, while at least one of them should be if the word is selected for inclusion in the crossword, i.e. if $w_\mathit{selected}$ is $\mathit{true}$.

Considering our example word <q>MYST</q>, we have to add

{{< math >}}
\begin{aligned}
&~ \mathit{MYST}_{0,0,\mathit{horizontal}}\\
+ &~ \dots\\
+ &~ \mathit{MYST}_{8,11,\mathit{horizontal}}\\
+ &~ \mathit{MYST}_{0,0,\mathit{vertical}}\\
+ &~ \dots \\
+ &~ \mathit{MYST}_{11,8,\mathit{vertical}}\\
\leq &~ 1
\end{aligned}
{{< /math >}}
and
{{< math >}}
\begin{aligned}
\mathit{MYST}_\mathit{selected} \rightarrow &~ \mathit{MYST}_{0,0,\mathit{horizontal}}\\
\vee &~ \dots\\
\vee &~ \mathit{MYST}_{11,8,\mathit{vertical}}
\end{aligned}
{{< /math >}}

The following lines take care of creating such constraints for each word:
{{< highlight-file "crossword.py" Python 125 127 >}}

### Only Sequences of Words
If we were to use a SAT solver on the constraints accumulated so far, we may find that some grid cell variables are assigned seemingly random characters which do not even form a word.
This is to be expected, as there is no constraint to enforce that all character sequences must correspond to a word placement yet (cf.  [rule (4)](#the-problem-statement)).

A simple way to achieve this, is to require the start coordinates of each sequence to correspond to the coordinates of a word placement.
The following lines handle horizontal character sequences but vertical ones can be treated analogously:
{{< highlight-file "crossword.py" Python 129 136 >}}

### Connectedness
The last and most complex requirement is [rule (5)](#the-problem-statement), which demands the placed words to form a single crossword rather than several disjoint ones.
That is, understanding the placed words as vertices of an [undirected graph](https://en.wikipedia.org/wiki/Undirected_graph), which are connected if the words intersect, should result in a graph with only one [connected component](https://en.wikipedia.org/wiki/Connected_component_%28graph_theory%29).

The following figure illustrates the graph corresponding to our [introductory example](#an-optimal-word-placement):
{{< figure src="gfx/12x12_q101_edgeRelationOfWords.svg" title="Understanding words as vertices" width="380px" >}}

For a fixed graph, computing the components can be [done in linear time](https://en.wikipedia.org/wiki/Connected_component_(graph_theory)#Algorithms), and the connectedness is also easy to see in the above figure.
However, in our application, the graph is not fixed but parametrised by the solutions to the other constraints.
Therefore, we have to come up with a formula that characterises the connectedness of any word placement, i.e. it should be satisfiable if the encoded word placement forms a single component.

Since neither the subset of words that will be placed nor the intersections of these words are known beforehand, a Boolean encoding of the word intersection relation will have to introduce variables $\mathit{connected}_{w_1,w_2}$ for each pair of words $w_1, w_2$.
Even when avoiding symmetrical entries, the number of such variables will grow polynomially in the number of words that can potentially be placed.
This is problematic since even our example crossword of size 12 already features 51 words to choose from.

Alternatively, by understanding the grid cells as vertices of a graph where the edges connect neighbouring (non-empty) cells, we can get around this problem:
{{< note >}}
When talking about the neighbours of a cell at position $(x,y)$, we exclude the diagonal neighbours, i.e. we only refer to those at positions $(x, y-1)$, $(x, y+1)$, $(x-1, y)$ and $(x+1, y)$.
{{< /note >}}
{{< figure src="gfx/12x12_q101_edgeRelationOfCells.svg" title="Understanding cells as vertices" width="380px" >}}

Here, the edge relation grows linearly in the number of cells as every cell can at most be connected to four others.
The size of our word set has no impact.

From this perspective, the connectedness check amounts to proving that we can reach every placed character from every other placed character by some path over neighbouring (non-empty) cells.
In fact, it already suffices to show that **there is one cell that can be reached from all others**.

To approach the connectedness check in the suggested way, we first have to characterise a non-empty cell for which we will try to prove reachability from all others.
Since it is unknown where words will be placed, let's just pick the uppermost-leftmost non-empty cell as the <q>start cell</q> of the connected component.
We introduce the variables

$$\mathit{ccStart}\_y,\mathit{ccStart}_{x,y}$$

for all coordinates $(x,y)$ within the grid bounds, to identify the row and exact coordinates of the <q>start cell</q>.
Clearly, $\mathit{ccStart}_y$ must be $\mathit{true}$ for the first row that is not empty, i.e.

{{< math >}}
\begin{aligned}
\mathit{ccStart}_y =&~ \bigwedge_{0\leq x < \mathit{size}} \mathit{grid}_{x,y} \neq \mathit{empty}\\
\wedge&~ \bigwedge_{0\leq i < y} \neg \mathit{ccStart}_i
\end{aligned}
{{< /math >}}

and $\mathit{ccStart}_{x,y}$ must be $\mathit{true}$ for the first non-empty cell in that row, i.e.

{{< math >}}
\begin{aligned}
\mathit{ccStart}_{x,y} =&~ \mathit{ccStart}_y\\
\wedge&~ \mathit{grid}_{x,y} \neq \mathit{empty}\\
\wedge&~ \bigwedge_{0\leq i < x} \neg \mathit{ccStart}_{i,y}
\end{aligned}
{{< /math >}}

Lines 151 to 161 take care of creating such constraints:
{{< highlight-file "crossword.py" Python 145 179 >}}

It only remains to assert that all the other non-empty cells in the grid can reach the <q>start cell</q>.
Considering that the grid is square and its `size` is finite, all other non-empty cells must be reachable within $\mathit{size}^2$ steps.
{{< note >}}
Note that $\mathit{size}^2$ is not the tightest upper bound.
The example code actually uses a lower `maxDistance`, which is easy to come up with by assessing the longest possible paths in some example grids.
{{< /note >}}

To identify states that can reach the <q>start</q> of the connected component within $n$ steps (or less), we introduce the variables
$$\mathit{reach}_{i,x,y}$$
for each position $(x,y)$ and maximal distance $i\in[0,\mathit{maxDistance(size)}]$ to the start. 

Of course only the <q>start cell</q> can reach itself in zero steps, so we assert
$$\mathit{reach}_{0,x,y} = \mathit{ccStart}\_{x,y}$$
for all coordinates $(x,y)$ in the grid (cf. line 164).
Furthermore, we know that a cell can reach the <q>start</q> in $i$ steps only if an adjacent cell can do so in $i-1$ steps, i.e.

{{< math >}}
\begin{aligned}
\mathit{reach}_{i,x,y} \rightarrow &~ \mathit{grid}_{x,y}\neq \mathit{empty}\\
\wedge &~ (\mathit{reach}_{i-1,x,y}\vee\bigvee_{(nx,ny)} \mathit{reach}_{i-1,nx,ny})
\end{aligned}
{{< /math >}}

where $(nx,ny)$ are neighbours of $(x,y)$.
This is what the rest of the above listing takes care of, ultimately requiring in line 179 that all non-empty cells must reach the <q>start cell</q> within the `maxDistance` -- otherwise we'd have more than one connected component.

### Quality
At this point we've constructed all constraints that are needed to generate valid crosswords.
However, solving the constraints at this point will yield rather sobering results as even an empty crossword is a valid crossword -- we do not require anything but compliance with the rules yet.
It's time to introduce a quality criterion.

Quality is subjective, but I guess everyone agrees that a sparse crossword is worse than a tightly packed one.
Therefore, it may be reasonable to measure quality in terms of the number of words or characters put in the grid.
The problem I see with both approaches is that they do not reward crossing words, so I've settled for **the sum of the placed words' lengths**:
$$\sum_{w\in\mathit{words}} w_\mathit{selected}*\mathit{length}(w)$$
This effectively values every character in the grid as 1 but also counts each crossing as another 1.
With this metric, the [introductory crossword](#an-optimal-word-placement) achieves a quality of 104.

By requiring this sum to be greater or equal to a provided `minQuality`, we can force the SAT solver to only produce crosswords that meet our expectations:
{{< highlight-file "crossword.py" Python 181 183 >}}

That's all there is to it conceptually.
The [rest of the code](crossword.py) is just generic plumbing to feed the constraints `res` into [Z3](https://github.com/Z3Prover/z3) and interpret the returned assignment of Boolean values to our variables.

## CNF Export 
Although Z3 is feature-rich and state of the art, it nevertheless pays off to use a competitive SAT solver instead for our particular use-case.
I recommend sticking to SMT solving during development and switching to SAT solving for the more complex instances.
Z3 provides [tactics](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-tactics) to reduce the finite-domain SMT constraints to a SAT instance in [CNF](https://en.wikipedia.org/wiki/Conjunctive_normal_form), which can then be exported in the [standard format for SAT solvers](http://www.satcompetition.org/2011/format-benchmarks2011.html):
{{< highlight-file "crossword.py" Python 189 200 >}}

## Experiments
Now that we got the crossword generation pipeline up an running it is interesting to see how long it takes to assemble [the words from our example](#the-problem-statement) into crosswords of size 12 with varying quality requirements.
Following the proposed approach, I generated crosswords of increasing quality and measured the time needed to solve the SAT instances with various solvers.
Since not all steps of the SAT encoding and solving are fully deterministic, some repetitions are necessary to get a better overview of the solvers' average performance.
As implied in the previous section Z3 didn't perform too well on these instances and was therefore excluded from the evaluation.

{{< figure src="gfx/eval.svg" title="Solving time for varying SAT solvers and qualities" >}}

{{< note >}}
Note that the first two configurations -- [cadical](https://github.com/arminbiere/cadical/tree/c622a490ec3d9a1a1e998b08120c9b8d0b67a123) and [cryptominisat](https://github.com/msoos/cryptominisat/releases/tag/5.8.0) -- run single-threaded, while both [plingeling](https://github.com/arminbiere/lingeling/tree/7d5db72420b95ab356c98ca7f7a4681ed2c59c70) and [cryptominisat -t4](https://github.com/msoos/cryptominisat/releases/tag/5.8.0) use four worker threads on a i7-7700K CPU.
{{< /note >}}

As to be expected, the higher the quality requirements are the longer it takes to solve the corresponding SAT instance.
It is easy to see that computing an optimal word placement may be unfeasible in practice: the time investment ramps up significantly as we approach unsatisfiable quality requirements.
However, even the instances of quality 94 do already look pretty good and are solved by [plingeling](https://github.com/arminbiere/lingeling/tree/7d5db72420b95ab356c98ca7f7a4681ed2c59c70) within 188s on average.
Feel free to process [the measurements](eval.csv) on your own if you're interested in a specific figure.

## Do Try This at Home!
The presented solution works well for my use case but obviously leaves room for further improvements.
Instead of building infrastructure around the crossword generation, e.g. turning it into rich client application or a service, I'd rather point out some conceptual alleys worth exploring:
* What about non-square or hexagonal grids?
Adapting the encoding to other grids should be pretty easy to do.
* Experiment with other metrics of quality.
For example, the number of word crossings could make for an interesting metric.
* Instead of requiring a fixed minimal quality, iteratively increase the required quality until the resulting SAT instance becomes unsatisfiable.
This will leave you with a sequence of crosswords of increasing quality and [allow you to stop at any time](https://en.wikipedia.org/wiki/Anytime_algorithm) or wait for the optimal placement to be determined.
* As a follow-up to the previous point, refactor your solution to leverage [incremental SMT](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-incrementality) or [incremental SAT](https://satcompetition.github.io/2020/track_incremental.html) solving, such that the solver does not have to start from scratch when the quality requirements increase.
* By [transposing](https://en.wikipedia.org/wiki/Transpose) a crossword we get another valid crossword.
This symmetry increases the search space unnecessarily.
Can you come up with symmetry-breaking constraints to avoid wasting time on symmetrical word placements?
* Instead of selecting the best subset of words for a fixed grid size, one might potentially want to place all the provided words as compact as possible.
Adapt the encoding to optimise for the smallest grid size.
* I used a SAT/SMT backend to solve the crossword generation since this is what I'm most comfortable with.
However, I wonder whether discrete optimisation algorithms would work even better here.
Analogous to [SMT-LIB](http://smtlib.cs.uiowa.edu/) in the satisfiability community, there is [MiniZinc](https://www.minizinc.org/) to express discrete optimisation problems in a solver-independent way.
You could give it a try.

As usual, there are tons of alternatives to encode various aspects of the problem but it is unclear whether they pay off.
In any case, let me know if you find a better way to generate **personalised** crosswords that meet configurable quality criteria.

<!-- TODO: Update "optimal" solution graphic, once computed -->
<!-- Update formulas to latest example -->
<!-- TODO: Create proper visuals -->

{{< list-resources "{*.py,*.csv}" >}}