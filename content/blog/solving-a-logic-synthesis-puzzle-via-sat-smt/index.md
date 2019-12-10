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
In the context of our riddle, the abstract description boils down to realising the functions
{{< math >}}
\begin{aligned}
g_0(x_0,x_1,x_2) &=\neg x_0\\
g_1(x_0,x_1,x_2)&=\neg x_1\\
g_2(x_0,x_1,x_2)&=\neg x_2
\end{aligned}
{{</ math >}}
where $x_0,x_1,x_2$ are the circuit's Boolean inputs.

Instead of thinking of a solution ourselves, we want to characterise the problem in terms of constraints whose solution can be interpreted as a solution to the riddle.
To this end, we intend the constraints to describe a generic circuit that is parameterised by the functions that its gates realise, and the connections between these gates.
Without loss of generality we restrict ourselves to gates with two inputs -- gates with larger [fan-in](https://en.wikipedia.org/wiki/Fan-in) can be composed of these.

The following schematic illustrates a choice (solid) of potential (dashed) connections for an example with only one output $g_0$ and one gate $f_3$.

{{< figure src="gfx/schematic_v1.svg" title="Generic 1-gate circuit" width="180px" >}}

Considering such a generic circuit with one gate, $g_0$ can only be connected to $x_0, x_1, x_2$ or the gate's output $x_3=f_3(x_0,x_1,x_2)$.
If $g_0$ were $x_0 \wedge x_1$, choosing the highlighted wiring and $f_3$ as AND would be a desireable logic synthesis result.
That is, conceptually we want to solve:

$$\tag{1}\exists f_3 ~ \exists\mathit{wiring} ~ \forall x_0,x_1,x_2\ldotp g_0(x_0, x_1, x_2)=circuit(x_0,x_1,x_2)$$

{{< note >}}
As in the post on the [inverse square root hack](/blog/smt-based-optimisation-of-fast-inverse-square-root), the riddle is effectively a **parameter synthesis** problem.
We are searching for a choice of parameters (gates and wiring) that make the system (circuit) compliant with some property for every input.
{{< /note >}}

Allowing an arbitrary number of gates and arbitrary connections will result in an unnecessarily huge search space.
Instead, we restrict ourselves to a fixed number of gates which we can increase incrementally if we find the number of gates insufficient to synthesise the goal function $g_0$.
Without loss of generality, the inputs of a new gate $f_4$ may be connected to preceding gates (including inputs) $x_0,\dots,x_3$ but not the other way around, e.g. $x_4$ may not be an input of $f_3$.

## SMT-based Synthesis
Looking at the schematic from the introduction, characterising the logic synthesis problem boils down to

1. formulating how the outputs $g_i$ may be connected to the gates $x_0, \dots, x_n$, and
1. formulating how the gates may be interconnected.

To denote that a gate $g_i$ is connected to $x_j$ we use a variable $g_{i,j}$.
Similarly, we introduce variables $c_{i, j, k}$ to encode that $x_j$ is the first input of $f_i$ and $x_k$ the second one.
With this in mind, reconsidering the wiring from our schematic, only $g_{0,3}$ and $c_{3,0,1}$ should be $\mathit{true}$.

{{< figure src="gfx/schematic_v2.svg" title="Connection variables" width="240px" >}}

Since SMT solving checks for _existence_ of an assignment that satisfies the constraints, the $\exists$-quantifiers prior to the $\forall$ in equation $(1)$ are implicit and can be dropped.
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
To bind the intended semantics to these variables, we make them imply the corresponding options and require at least one of them to be $\mathit{true}$.
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


<!-- Although we could require exactly one connection... -->
