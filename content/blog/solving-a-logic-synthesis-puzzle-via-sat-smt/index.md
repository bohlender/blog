---
title: "Solving a Logic Synthesis Puzzle via SAT/SMT"
date: 2019-11-30T22:54:10+01:00
publishDate: 2019-12-10
tags: ["SAT", "SMT", "Logic Synthesis", "Puzzle"]
draft: true
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
Instead, we restrict ourselves to a fixed number of gates which we can increase incrementally as long as the current number of gates turns out to be insufficient to synthesise the goal function $g_0$.
Without loss of generality, the inputs of a new gate $f_{n+1}$ may be connected to preceding gates (and inputs) $x_0,\dots,x_n$ but not the other way around, e.g. $x_4$ may not be an input of $f_3$.

## SMT-based Synthesis
Looking at the schematic from the introduction, characterising the logic synthesis problem boils down to

1. formulating how the outputs $g_i$ may be connected to the gates $x_0, \dots, x_n$, and
1. formulating how the gates may be interconnected.

To denote that a gate $g_i$ is connected to $x_j$ we use a variable $g_{i,j}$.
Similarly, we introduce variables $c_{i, j, k}$ to encode that $x_j$ is the first input of $f_i$ and $x_k$ the second one.
With this in mind, reconsidering the wiring from our schematic, only $g_{0,3}$ and $c_{3,0,1}$ should be $\mathit{true}$.

{{< figure src="gfx/schematic_v2.svg" title="Connection variables" width="240px" >}}

Considering the simple case of $n=1$ inner gates, a circuit can be synthesised if (and only if) the following is satisfiable:

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

Here, the first part requires $g_0$ to be connected to at least one $x_i$, and the last part requires $f_3$ to be connected to some combination of inputs.
In contrast to $(1)$, we now express the circuit's overall semantics $\mathit{circuit}(x_0, x_1, x_2)$ in terms of the functions realised by its gates.
Increasing either the number of outputs or gates will merely add further conjuncts in the same vein.

However, this characterisation does not yet make use of the variables $g_{i,j}$ and $c_{i,j,k}$ for denoting the chosen wiring.
To bind the intended semantics to these variables, we let the variables imply the corresponding options and require at least one of them to be $\mathit{true}$.
{{< note >}}
We do not explicitly require $g_0$ to be connected to exactly one $x_i$.
Although we can add this constraint it is not necessary.
For example, if the solver finds a satisfying assignment with both $g_{0,4}$ and $g_{0,5}$ set to $\mathit{true}$ then the values of $x_4$ and $x_5$ coincide for all inputs and $g_0$ can be connected to any.

This hints at redundancy and realisability of the circuit with fewer gates.
Most of the time the connection variables $g_{i,j}$ of an ouput $g_i$ cannot be $\mathit{true}$ at the same time.
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

If this formula can be satisfied by picking appropriate values for $g_{i,j}$ and $c_{i,j,k}$ then $(2)$ must be satisfiable too.

Conceptually, **that's all there is to characterising a generic logic synthesis** problem in [first-order logic](https://en.wikipedia.org/wiki/First-order_logic).
However, to solve the introductory riddle we still have to restrict the functions $f_i$ to AND, OR and at most two NOTs.

Restricting the $f_i$ to AND, OR and NOT amounts to constraining each $f_i$ to one of the operators truth tables, i.e. also assert for each $f_i$:
{{< math >}}
\begin{aligned}
    &(\neg f_i(\mathit{false},\mathit{false}) \wedge \neg f_i(\mathit{false}, \mathit{true}) \wedge \neg f_i(\mathit{true},\mathit{false}) \wedge f_i(\mathit{true}, \mathit{true}))\\
    \vee~ & (\neg f_i(\mathit{false},\mathit{false}) \wedge f_i(\mathit{false}, \mathit{true}) \wedge f_i(\mathit{true},\mathit{false}) \wedge f_i(\mathit{true}, \mathit{true}))\\
    \vee~ & (\neg f_i(\mathit{false},\mathit{false}) \wedge \neg f_i(\mathit{false}, \mathit{true}) = f_i(\mathit{true},\mathit{false}) \wedge f_i(\mathit{true}, \mathit{true}))\\
\end{aligned}
{{</ math >}}
Here, the first line is only satisfied by an AND, the second line is only satisfied by an OR, and the last line is only satisfied by a NOT on the first or second input.
This characterisation of NOT is needed since all of our $f_i$ have two parameters.

Having restricted the functions to the allowed gates, we can also limit the number of NOTs by means of [cardinality constraints](http://theory.stanford.edu/~nikolaj/programmingz3.html#sec-cardinality-constraints):
{{< math >}}
\begin{aligned}
    & (\neg f_3(\mathit{false},\mathit{false}) \wedge \neg f_3(\mathit{false}, \mathit{true}) = f_3(\mathit{true},\mathit{false}) \wedge f_3(\mathit{true}, \mathit{true}))\\
    +~& (\neg f_4(\mathit{false},\mathit{false}) \wedge \neg f_4(\mathit{false}, \mathit{true}) = f_4(\mathit{true},\mathit{false}) \wedge f_4(\mathit{true}, \mathit{true}))\\
    & \vdots\\
    +~& (\neg f_n(\mathit{false},\mathit{false}) \wedge \neg f_n(\mathit{false}, \mathit{true}) = f_n(\mathit{true},\mathit{false}) \wedge f_n(\mathit{true}, \mathit{true}))\\
    \leq~& 2
\end{aligned}
{{</ math >}}
essentially constraining how many $f_i$ may be interpreted as NOTs.

### Implementation
Using the Python bindings of [Z3](https://github.com/Z3Prover/z3/) an implementation of this approach for arbitrary numbers of inputs, outputs and inner gates spans only [few lines of code](gen_smt2.py).

Functions over argument lists allow for an easy specification of the wanted outputs:
{{< highlight-file "gen_smt2.py" Python 63 67 >}}

Inputting the number of inputs and inner gates to consider, we can create the corresponding variables $x_i$ and their uninterpreted functions $f_i:\mathbb{B}^2\rightarrow\mathbb{B}$ as follows: 
{{< highlight-file "gen_smt2.py" Python 42 47 >}}

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
{{< highlight-file "gen_smt2.py" Python 50 55 >}}

{{< note >}}
Note that we could easily let Z3 solve the instance right away (via `s.check()`).
I just happen to prefer benchmarking the generated SMT instances.
{{</ note >}}

Although our implementation is fine and works great for synthesis of smaller circuits, such as a full adder, the quantifiers, uninterpreted functions and cardinality constraints render the instance arising from the introductory puzzle too difficult to be solved within several days.
Therefore, in the next section, we reduce the characterisation to propositional logic, trading off the complexity of our constraints against a larger instance, and end up with a standard approach for SAT-based logic synthesis.
<!-- TODO: Append full adder files -->

{{< list-resources "{*.py,*.log}" >}}