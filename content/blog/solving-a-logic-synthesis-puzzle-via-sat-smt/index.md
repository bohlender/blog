---
title: "Solving a Logic Synthesis Puzzle via SAT/SMT"
date: 2019-11-30T22:54:10+01:00
publishDate: 2019-12-12
tags: ["SAT", "SMT", "Logic Synthesis", "Puzzle"]
draft: false
math: true
images: []
videos: []
audio: []
---
A few weeks ago, I was asked the following riddle:
<q>Design a logic circuit with three inputs and three outputs, such that the outputs are the inverted inputs. You may use arbitrary many AND and OR gates, but at most two NOT gates</q>.
Although the characterisation of this problem as an [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) instance is straightforward, I found it necessary to reduce it to [SAT](https://en.wikipedia.org/wiki/Satisfiability) and incorporate further assumptions to achieve reasonable performance.
This post illustrates said process, ranging from the original idea via a standard formulation of SAT-based logic synthesis to a problem-specific and more constrained instance.
<!--more-->
## Introduction
[Logic synthesis](https://en.wikipedia.org/wiki/Logic_synthesis) is the process of turning an abstract circuit description into a concrete design in terms of logic gates.
In the context of our riddle, the abstract description can be formalised as a set of goal functions which the circuit must realise:
{{< math >}}
\begin{aligned}
g_0(x_0,x_1,x_2) &=\neg x_0\\
g_1(x_0,x_1,x_2)&=\neg x_1\\
g_2(x_0,x_1,x_2)&=\neg x_2
\end{aligned}
{{</ math >}}
where $x_0,x_1,x_2$ are the circuit's Boolean inputs.

Instead of thinking of a solution ourselves, we want to characterise the problem in terms of constraints whose solution can be interpreted as a solution to the riddle.
To this end, we intend the constraints to describe a generic circuit that is parametrised by the _functions_ that its gates realise and the _connections_ between these gates.
{{< note >}}
Without loss of generality, we restrict ourselves to gates with two inputs.
Gates with larger [fan-in](https://en.wikipedia.org/wiki/Fan-in) can be constructed from these.
{{</ note >}}

The following schematic illustrates one choice of connections (solid) from the many potential wirings (dashed) for an example with only one output $g_0$ and one gate $f_3$.

{{< figure src="gfx/schematic_v1.svg" title="Generic 1-gate circuit" width="180px" >}}

If $g_0$ were $x_0 \wedge x_1$, choosing the highlighted wiring and $f_3$ as AND would be a desireable logic synthesis result.
That is, conceptually we want to solve something along these lines:

$$\tag{1}\forall x_0,x_1,x_2\ldotp g_0(x_0, x_1, x_2)=\mathit{circuit}(x_0,x_1,x_2)$$

where $\mathit{circuit}$ is defined by the choice of $f_3$ and the wiring.
{{< note >}}
As in the post on the [inverse square root hack](/blog/smt-based-optimisation-of-fast-inverse-square-root), logic synthesis can be understood as a **parameter synthesis** problem, too.
We are searching for a choice of parameters (gates and wiring) that make the system (circuit) compliant with some property for every input.
{{< /note >}}

Considering the generic circuit with one gate, $g_0$ can only be connected to the inputs $x_0, x_1, x_2$ or the gate's output $x_3$.
Depending on which inputs $f_3$ is connected to, its output $x_3$ will be given by $f_3(x_0,x_1), f_3(x_0,x_2)$ or $f_3(x_1,x_2)$.
Note that it is sufficient to consider the input combinations $f_3(x_j, x_k)$ for $1\leq j < k < 3$ since $f_3$ is unconstrained (yet) and can represent any binary operator on Booleans.

Allowing an arbitrary number of gates and arbitrary connections right from the start will result in an unnecessarily huge search space.
Instead, we restrict ourselves to a fixed number of gates which we can increase incrementally if the current number of gates turns out to be insufficient to synthesise the goal function $g_0$.
Without loss of generality, the inputs of a new gate $f_{n+1}$ may be connected to preceding gates (and inputs) $x_0,\dots,x_n$ but not the other way around, e.g. $x_4$ may not be an input of $f_3$.
This was the ad-hoc approach [my colleague](https://lukas-boersma.com/) and I figured should work, so I started implementing it.

## SMT-based Logic Synthesis
Looking at the schematic from the introduction, characterising the logic synthesis problem boils down to:

1. formulating how the outputs $g_i$ may be connected to the gates $x_0, \dots, x_n$, and
1. formulating how the gates may be interconnected.

To denote that a gate $g_i$ is connected to $x_j$ we use a variable $g_{i,j}$.
Similarly, we introduce variables $c_{i, j, k}$ to encode that $x_j$ is the first input of $f_i$ and $x_k$ the second one.
With this in mind, reconsidering the wiring from our schematic, only $g_{0,3}$ and $c_{3,0,1}$ should be $\mathit{true}$.

{{< figure src="gfx/schematic_v2.svg" title="Connection variables" width="240px" >}}

For the simple case of $n=1$ inner gates, a circuit can be synthesised if (and only if) the following is satisfiable:
{{< math >}}
\tag{2}
\begin{aligned}
\forall x_0,x_1,x_2~ \exists x_3\ldotp &~ (g_0(x_0,x_1,x_2) = x_0\\
\vee &~ g_0(x_0,x_1,x_2)= x_1\\
\vee &~ g_0(x_0,x_1,x_2)= x_2\\
\vee &~ \textcolor{a6e22e}{g_0}(x_0,x_1,x_2)= \textcolor{a6e22e}{x_3})\\
\wedge &~ (x_3=\textcolor{f92672}{f_3(x_0,x_1)}\\
\vee &~ x_3 = f_3(x_0,x_2)\\
\vee &~ x_3 = f_3(x_1,x_2))
\end{aligned}
{{</ math >}}

Here, the first part requires $g_0$ to be connected to at least one $x_i$, and the second part requires $f_3$ to be connected to some combination of inputs.
In contrast to $(1)$, we now express the circuit's overall semantics $\mathit{circuit}(x_0, x_1, x_2)$ in terms of the functions realised by its gates.
Increasing either the number of outputs or gates will merely add further conjuncts in the same vein.

However, this characterisation does not yet make use of the variables $g_{i,j}$ and $c_{i,j,k}$ to encode the chosen wiring.
To bind the intended semantics to these variables, we let the variables imply the corresponding options and require at least one of them to be $\mathit{true}$.
{{< note >}}
We do not explicitly require $g_0$ to be connected to exactly one $x_i$.
Although we can add this constraint it is not necessary.
For example, if the solver finds a satisfying assignment with both $g_{0,4}$ and $g_{0,5}$ set to $\mathit{true}$ then the values of $x_4$ and $x_5$ coincide for all inputs and $g_0$ can be connected to any.

This hints at redundancy and realisability of the circuit with fewer gates.
Most of the time the connection variables $g_{i,j}$ of an output $g_i$ cannot be $\mathit{true}$ at the same time.
The same reasoning applies to the connection variables $c_{i,j,k}$ of gates.
{{< /note >}}
This yields an [equisatisfiable](https://en.wikipedia.org/wiki/Equisatisfiability) constraint:
{{< math >}}
\tag{3}
\begin{aligned}
\forall x_0,x_1,x_2~ \exists x_3\ldotp &~ (g_{0,0}\rightarrow g_0(x_0,x_1,x_2) = x_0)\\
\wedge &~ (g_{0,1}\rightarrow g_0(x_0,x_1,x_2)= x_1)\\
\wedge &~ (g_{0,2}\rightarrow g_0(x_0,x_1,x_2)= x_2)\\
\wedge &~ (\textcolor{a6e22e}{g_{0,3}}\rightarrow g_0(x_0,x_1,x_2)= x_3)\\
\wedge &~ (g_{0,0} \vee g_{0,1} \vee g_{0,2} \vee \textcolor{a6e22e}{g_{0,3}})\\
\wedge &~ (\textcolor{f92672}{c_{3,0,1}}\rightarrow x_3 = f_3(x_0,x_1))\\
\wedge &~ (c_{3,0,2}\rightarrow x_3 = f_3(x_0,x_2))\\
\wedge &~ (c_{3,1,2}\rightarrow x_3 = f_3(x_1,x_2))\\
\wedge &~ (\textcolor{f92672}{c_{3,0,1}} \vee c_{3,0,2} \vee c_{3,1,2})
\end{aligned}
{{</ math >}}

If there is an interpretation that satisfies $(2)$, then it can be extended to an interpretation that satisfies $(3)$ by picking appropriate values for $g_{i,j}$ and $c_{i,j,k}$ and vice versa.

Conceptually, **that's all there is to characterising a generic logic synthesis** problem in [first-order logic](https://en.wikipedia.org/wiki/First-order_logic).
However, to solve the introductory riddle we still have to restrict the functions $f_i$ to AND, OR and at most two NOTs.

Restricting the $f_i$ to AND, OR and NOT amounts to constraining each $f_i$ to these operators' truth tables, i.e. also assert for each $f_i$:
{{< math >}}
\begin{aligned}
    &(\neg f_i(0,0) \wedge \neg f_i(0, 1) \wedge \neg f_i(1,0) \wedge f_i(1, 1))\\
    \vee~ & (\neg f_i(0,0) \wedge f_i(0, 1) \wedge f_i(1,0) \wedge f_i(1, 1))\\
    \vee~ & (f_i(0,0) \wedge \neg f_i(0, 1) = f_i(1,0) \wedge \neg f_i(1, 1))\\
\end{aligned}
{{</ math >}}
{{< note >}}
We use $0$ and $1$ instead of $\mathit{false}$ and $\mathit{true}$ to improve readability.
Of course the constants must be truth values and not integers.
{{</ note >}}

Here, the first line is only satisfied by an AND, the second line is only satisfied by an OR, and the last line is only satisfied by a NOT on the first or second input.
This characterisation of NOT is needed since all of our $f_i$ have two parameters.

Having restricted the functions to the allowed gates, we can also limit the number of NOTs by means of [cardinality constraints](http://theory.stanford.edu/~nikolaj/programmingz3.html#sec-cardinality-constraints):
{{< math >}}
\begin{aligned}
    & (f_3(0,0) \wedge \neg f_3(0, 1) = f_3(1,0) \wedge \neg f_3(1, 1))\\
    +~& (f_4(0,0) \wedge \neg f_4(0, 1) = f_4(1,0) \wedge \neg f_4(1, 1))\\
    &~ \vdots\\
    +~& (f_n(0,0) \wedge \neg f_n(0, 1) = f_n(1,0) \wedge \neg f_n(1, 1))\\
    \leq~& 2
\end{aligned}
{{</ math >}}
essentially constraining how many $f_i$ may be interpreted as NOTs.

### Implementation
Using the Python bindings of [Z3](https://github.com/Z3Prover/z3/), an implementation of this approach for arbitrary numbers of inputs, outputs and inner gates spans only [few lines of code](gen_smt2.py).

Functions over argument lists allow for an easy specification of the wanted outputs:
{{< highlight-file "gen_smt2.py" Python 62 66 >}}

Providing the number of inputs and inner gates to consider, we can create the corresponding variables $x_i$ and their uninterpreted functions $f_i:\mathbb{B}^2\rightarrow\mathbb{B}$ as follows: 
{{< highlight-file "gen_smt2.py" Python 41 46 >}}

The characterisation of possible output connections strongly follows the scheme shown in $(3)$.
We create variables $g_{i,j}$ for the potential connection of $g_i$ and each $x_j$, and let them imply that $g_0(\mathit{inputs})=x_j$.
It is also asserted that at least one $g_{i,j}$ for each $g_i$ must be $\mathit{true}$:
{{< highlight-file "gen_smt2.py" Python 4 13 >}}

The characterisation of possible gate connections is very similar.
The enumeration of relevant input combinations can be achieved comfortably via [`itertools.combinations`](https://docs.python.org/3.8/library/itertools.html?itertools.combinations#itertools.combinations):
{{< highlight-file "gen_smt2.py" Python 15 25 >}}

Finally, the code for the riddle-specific additional constraints of $f_i$ closely resembles the constraints shown in the end of the previous section:
{{< highlight-file "gen_smt2.py" Python 27 38 >}}

All that remains is simplifying these constraints and acquiring their [SMT-LIB representation](http://smtlib.cs.uiowa.edu/papers/smt-lib-reference-v2.6-r2017-07-18.pdf) -- the common exchange format for SMT solvers:
{{< highlight-file "gen_smt2.py" Python 49 54 >}}

{{< note >}}
Note that we could easily let Z3 solve the instance right away via `s.check()`.
I just prefer benchmarking the once generated SMT instances instead of regenerating them in every run.
{{</ note >}}

The resulting characterisation works great for synthesis of smaller circuits, such as a full adder built from just ANDs, ORs and at most two NOTs:
{{< highlight-file "gen_smt2.py" Python 58 61 >}}

Feel free to experiment with [the implementation](gen_smt2.py), feed the generated instances into SMT solvers and interpret the found solutions before continuing with the SAT-based approach.
I've attached the full adder synthesis [SMT instance](full_adder.smt2) to this post, so you don't have run the generator.
The solution I get describes the following circuit:
{{< figure src="gfx/full_adder.svg" title="Visualisation of synthesised full adder" width="350px" >}}

Nevertheless, the quantifiers, uninterpreted functions and cardinality constraints render the instance arising from the introductory puzzle too difficult to be solved within several days.
Therefore, in the next section, we reduce the characterisation to [propositional logic](https://en.wikipedia.org/wiki/Propositional_calculus), trading off the complexity of our constraints against a larger instance, and end up with a standard approach for SAT-based logic synthesis.
While the SMT-based synthesis of a full adder may take a few seconds, the [corresponding SAT instance](full_adder.cnf) will be [solvable in milliseconds](full_adder.log).

## SAT-based Logic Synthesis
To make our problem approachable via SAT solving, we must reformulate the constraints to be free of quantifiers and uninterpreted functions.
The cardinality constraints are less of a problem since (i) many SAT solvers support them, and (ii) Z3 can also reduce them to propositional logic for us.
{{< note >}}
Strictly speaking, non-logical symbols like <q>=</q> are not part of propositional logic either but are easily reduced to it.
As with the cardinality constraints, Z3 does this automatically for us.
{{</ note >}}

### Eliminating the Existential Quantifier
The first step of this reduction is understanding the $\exists$-quantified gate outputs as functions of the $\forall$-quantified circuit inputs.
Clearly, the gates' outputs depend on the current inputs.
With this in mind, our example constraint $(3)$ can be rewritten as follows:
{{< math >}}
\tag{4}
\begin{aligned}
\forall x_0,x_1,x_2\ldotp &~ (g_{0,0}\rightarrow g_0(x_0,x_1,x_2) = x_0)\\
\wedge &~ (g_{0,1}\rightarrow g_0(x_0,x_1,x_2)= x_1)\\
\wedge &~ (g_{0,2}\rightarrow g_0(x_0,x_1,x_2)= x_2)\\
\wedge &~ (g_{0,3}\rightarrow g_0(x_0,x_1,x_2)= x_3(x_0,x_1,x_2))\\
\wedge &~ (g_{0,0} \vee g_{0,1} \vee g_{0,2} \vee g_{0,3})\\
\wedge &~ (c_{3,0,1}\rightarrow x_3(x_0,x_1,x_2) = f_3(x_0,x_1))\\
\wedge &~ (c_{3,0,2}\rightarrow x_3(x_0,x_1,x_2) = f_3(x_0,x_2))\\
\wedge &~ (c_{3,1,2}\rightarrow x_3(x_0,x_1,x_2) = f_3(x_1,x_2))\\
\wedge &~ (c_{3,0,1} \vee c_{3,0,2} \vee c_{3,1,2})
\end{aligned}
{{</ math >}}

One detail that is easily overlooked is that the inner gates' inputs are not guaranteed to be constants, such as $x_0,x_1$ and $x_2$, but may be function evaluations.
For example, if we were to characterise a generic circuit with $n=2$ inner gates, the following clause would have to be used (among others):
$$\tag{5} c_{4,0,3} \rightarrow x_4(x_0,x_1,x_2) = f_4(x_0,x_3(x_0,x_1,x_2))$$

### Eliminating the Universal Quantifier
In next step we get rid of the $\forall$-quantifier.
Looking at how $\forall x$ is defined for a Boolean $x$:
$$ \forall x\ldotp \varphi := \varphi[\mathit{true}/x] \wedge \varphi[\mathit{false}/x]$$
it is easy to see that we can eliminate one variable at a time by cloning the expression $\varphi$ and substituting $x$ by $\mathit{true}$ in the first instance and by $\mathit{false}$ in the second one.
We effectively enumerate all the values the quantifier ranges over and conjunct the instantiated constraints.
{{< note >}}
Although every variable elimination doubles the number of constraints, and will clearly not scale to arbitrary numbers of inputs, it is fine for our purposes.
The puzzle features only three inputs so this quantifier elimination only increases the characterisation roughly by $2^3$.
{{</ note >}}

By eliminating the $\forall$-quantifier in $(4)$ like this, we end up with 
{{< math >}}
\tag{6}
\begin{aligned}
&
\begin{aligned}
    (g_{0,0} \rightarrow&~ g_0(0,0,0) = 0)\\
    \wedge&~ g_0(0,0,1) = 0)\\
    \wedge&~ g_0(0,1,0) = 0)\\
    \wedge&~ g_0(0,1,1) = 0)\\
    \wedge&~ g_0(1,0,0) = 1)\\
    \wedge&~ g_0(1,0,1) = 1)\\
    \wedge&~ g_0(1,1,0) = 1)\\
    \wedge&~ g_0(1,1,1) = 1))\\
\end{aligned}\\
\wedge~ & (g_{0,1} \rightarrow~ \dots )\\
\wedge~ & (g_{0,2} \rightarrow~ \dots )\\
\wedge~ & (g_{1,2} \rightarrow~ \dots )\\
\wedge~ & (g_{0,0} \vee g_{0,1} \vee g_{0,2} \vee g_{0,3})\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(0,0,0) = f_3(0,0))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(0,0,1) = f_3(0,0))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(0,1,0) = f_3(0,1))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(0,1,1) = f_3(0,1))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(1,0,0) = f_3(1,0))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(1,0,1) = f_3(1,0))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(1,1,0) = f_3(1,1))\\
\wedge~ & (c_{3,0,1} \rightarrow~ x_3(1,1,1) = f_3(1,1))\\
\wedge~ & (c_{3,0,2} \rightarrow~ \dots )\\
\wedge~ & (c_{3,1,2} \rightarrow~ \dots )\\
\wedge~ &(c_{3,0,1} \vee c_{3,0,2} \vee c_{3,1,2})
\end{aligned}
{{</ math >}}
where we again use $0$ and $1$ to denote $\mathit{false}$ and $\mathit{true}$, respectively.
Note that we could as well have encoded the implications of $c_{3,0,1}$ in a single clause (similar to $g_{0,0}$).
However, the illustrated encoding will make the upcoming elimination of uninterpreted functions more readable.

Although likely clear, I want to stress that if we had a more complex clause like $(5)$, it would be expanded into the following clauses:
{{< math >}}
\begin{aligned}
    &~(c_{4,0,3} \rightarrow x_4(0,0,0) = f_4(0,x_3(0,0,0)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(0,0,1) = f_4(0,x_3(0,0,1)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(0,1,0) = f_4(0,x_3(0,1,0)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(0,1,1) = f_4(0,x_3(0,1,1)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(1,0,0) = f_4(1,x_3(1,0,0)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(1,0,1) = f_4(1,x_3(1,0,1)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(1,1,0) = f_4(1,x_3(1,1,0)))\\
    \wedge&~ (c_{4,0,3} \rightarrow x_4(1,1,1) = f_4(1,x_3(1,1,1)))
\end{aligned}
{{</ math >}}

### Eliminating Uninterpreted Functions
The last step of the reduction is the elimination of the uninterpreted functions $f_i$ and the corresponding $x_i$.
Since we're dealing with functions over Booleans, we can simply introduce a variable for each entry of a function's truth table, and encode the semantics in terms of these entries.
{{< note >}}
Note that the goal functions $g_i$ are not uninterpreted but known and evaluated during construction of the constraints.
{{</ note >}}

For example, a gate $f_4:\mathbb{B}^2\rightarrow \mathbb{B}$ can be encoded by an assignment to the four variables
$$ f_{4,(0,0)}, f_{4,(0,1)}, f_{4,(1,0)}, f_{4,(1,1)} $$
each of which represents an entry of $f_4$'s truth table.
Similarly, a function $x_i:\mathbb{B}^3\rightarrow \mathbb{B}$ will be blasted into $2^3$ variables $x_{i,(0,0,0)}, \dots, x_{i,(1,1,1)}$ to refer to the value of $x_i$ for different inputs.

Since the elimination of all uninterpreted functions from $(6)$ would take too much space, I will illustrate the approach on a single but generic clause:
$$ c_{i,j,k} \rightarrow x_i(0,0,0) = f_i(x_j(0,0,0),x_k(0,0,0)) $$

If $x_j$ and $x_k$ are picked as the inputs of $f_i$, this constraint requires $f_i$ to relate the truth values of these inputs with the gate's output $x_i$, for a given circuit input $(0,0,0)$.
To get rid of $f_i$ but express the same semantics with the new variables, we explicitly enumerate all $2^3$ possible combinations of input and output values of the gate, and require the corresponding $f_{i,(0,0)},\dots,f_{i,(1,1)}$ to be consistent with them:

{{< math >}}
\begin{aligned}
    &~ (c_{i,j,k} \wedge \neg x_{i,(0,0,0)} \wedge \neg x_{j,(0,0,0)} \wedge \neg x_{k,(0,0,0)} \rightarrow \neg f_{4,(0,0)})\\
    \wedge &~ (c_{i,j,k} \wedge \neg x_{i,(0,0,0)} \wedge \neg x_{j,(0,0,0)} \wedge x_{k,(0,0,0)} \rightarrow \neg f_{4,(0,1)})\\
    \wedge &~ (c_{i,j,k} \wedge \neg x_{i,(0,0,0)} \wedge x_{j,(0,0,0)} \wedge \neg x_{k,(0,0,0)} \rightarrow \neg f_{4,(1,0)})\\
    \wedge &~ (c_{i,j,k} \wedge \neg x_{i,(0,0,0)} \wedge x_{j,(0,0,0)} \wedge x_{k,(0,0,0)} \rightarrow \neg f_{4,(1,1)})\\
    \wedge &~ (c_{i,j,k} \wedge x_{i,(0,0,0)} \wedge \neg x_{j,(0,0,0)} \wedge \neg x_{k,(0,0,0)} \rightarrow f_{4,(0,0)})\\
    \wedge &~ (c_{i,j,k} \wedge x_{i,(0,0,0)} \wedge \neg x_{j,(0,0,0)} \wedge x_{k,(0,0,0)} \rightarrow f_{4,(0,1)})\\
    \wedge &~ (c_{i,j,k} \wedge x_{i,(0,0,0)} \wedge x_{j,(0,0,0)} \wedge \neg x_{k,(0,0,0)} \rightarrow f_{4,(1,0)})\\
    \wedge &~ (c_{i,j,k} \wedge x_{i,(0,0,0)} \wedge x_{j,(0,0,0)} \wedge x_{k,(0,0,0)} \rightarrow f_{4,(1,1)})\\
\end{aligned}
{{</ math >}}

Applying this transformation to the clauses from $(6)$ leaves us with a SAT instance that is equivalent to a [standard formulation](https://people.eecs.berkeley.edu/~alanmi/publications/2018/date18_exact.pdf) of SAT-based logic synthesis.

### Implementation
Since [the implementation](gen_sat.py) is mostly a refinement of the SMT instance generator, I will only touch on some aspects and refer to the implementation if something is unclear.

The biggest difference to the SMT-based characterisation is that we introduced variables $x_{i,(0,0,0)},\dots,x_{i,(1,1,1)}$ and $f_{i,(0,0),\dots,f_{i,(1,1)}}$ to refer to the values of $x_i$ and $f_i$ for every possible input.
Accordingly, the implementation now uses lists of lists for indexing all the variants of $x_i$ and $f_i$:
{{< highlight-file "gen_sat.py" Python 53 63 >}}

Due to this indexing of variables, the restriction of $f_i$ had to be adapted slightly:
{{< highlight-file "gen_sat.py" Python 40 42 >}}

Besides the indexing, the implementation implements the very same reduction to SAT that has been sketched above and maintains the general structure of the SMT-oriented implementation.
What needs mention though is how to export the constraints in the [DIMACS](https://www.domagoj-babic.com/uploads/ResearchProjects/Spear/dimacs-cnf.pdf) exchange format used by virtually all SAT solvers:
{{< highlight-file "gen_sat.py" Python 66 75 >}}

Z3 provides [tactics](http://theory.stanford.edu/~nikolaj/programmingz3.html#sec-tactics) that can be applied to a set of constraints.
By applying `card2bv`, all occurring cardinality constraints will be reduced to propositional logic.
The subsequent `tseitin-cnf` tactic brings the resulting constraints into [conjunctive normal form](https://en.wikipedia.org/wiki/Conjunctive_normal_form) (CNF) -- in fact they almost are in CNF already.
The resulting constraints are then be output in the DIMACS format.

Although a SAT-based characterisation is a lot larger than its SMT-base counterpart, it is less complex and is typically solved in orders-of-magnitude less time.
Feel free to experiment with [the implementation](gen_sat.py), or try to reconstruct the full adder circuit [shown above](gfx/full_adder.svg) from the [generated SAT instance](full_adder.cnf) and [the solution](full_adder.log) found by a SAT solver.

Still, the constraint that restricts the number of NOTs seems to make the SAT instance that characterises the introductory puzzle hard to solve.
The next section proposes two additional assumptions that are rather weak but sufficient to alleviate the combinatorial explosion, and make the constraints solvable in reasonable time.

## Solving the Puzzle
The constraints that we used so far did not make any assumptions that could disregard potential solutions to the puzzle, but merely formalised the provided information.
To make the combinatorial explosion more manageable, we will now also add some assumptions that are _likely_ to hold for the circuit, but may potentially disregard some solutions.

First of all, if the puzzle allows the use of at most two NOTs, almost certainly both NOTs are necessary.
It is also quite likely that if there is a solution, it can also be realised with both NOTs placed two gates apart, so the result of the first NOT can pass through all kinds of allowed gates (an AND and an OR) before reaching the last NOT.
So there must be some $i$, such that both $f_i$ and $f_{i+3}$ are NOT gates.

This is the first puzzle-specific assumption that distinguishes the implementation:
{{< highlight-file "gen_puzzle.py" Python 54 58 >}}

The second assumption is a lot weaker and concerns the connections of the outputs.
If there is a solution, it likely can be formulated so that the outputs are connected to the very last gates of the circuit.
In particular, $g_2$ can certainly be computed independently of $g_1$ and $g_0$.
We can enforce these connections via:
{{< highlight-file "gen_puzzle.py" Python 16 18 >}}

With these additional constraints, it took an old i5-4690 CPU [about 15min](puzzle.log) to solve the [corresponding SAT instance](puzzle.cnf) with **22 inner gates**.
The synthesised circuit looks as follows:
{{< figure src="gfx/puzzle.svg" title="Solution to puzzle" >}}
Since we only allow gates with fan-in 2, here, the NOT2 denotes a NOT on the second input.

## Do Try This at Home!
Although the SAT-based characterisation of logic synthesis turns out to be practical -- especially when the artificial constraint on the number of gates is dropped -- there is still room for improvement and experimentation.
Here are some ideas that you might want to explore on your own (easiest first):

* Instead of relying on an external solver to solve the generated constraints, use the API to invoke the check programmatically.
* Automate the interpretation of the solutions found by a solver as logic circuits and plot them via [DOT](https://en.wikipedia.org/wiki/DOT_(graph_description_language)).
* Extend the characterisation to allow some composite gates.
  For example, I found that the [expected solution](https://puzzling.stackexchange.com/questions/9438/invert-three-inputs-with-two-not-gates) has circuitry to decide whether more than one (or more than two) inputs are $\mathit{true}$.
  Requiring the synthesis to feature such blocks may speed up the synthesis of the puzzle's solution.
* Instead of characterising the circuit for a fixed number of gates, devise an incremental variant of SMT-based or SAT-based synthesis.
  It should be advantageous to have the solver reuse information established during checks with fewer gates.

If you manage to solve the riddle without the domain-specific assumptions, or have any ideas how to do this more efficiently with SAT/SMT solving, please let me know.
It might also be possible to solve this with the logic synthesis tools mentioned in [the paper](https://people.eecs.berkeley.edu/~alanmi/publications/2018/date18_exact.pdf) that discusses the practicability of the SAT-based encoding we ended up with.

{{< list-resources "{*.py,*.cnf,*.smt2,*.log}" >}}