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

To this end, we intend the constraints to describe a circuit that is parameterised by the functions that its gates realise and the connections between these gates.
Without specifying what excatly the variables in the following formula refer to precisely, we conceptually want to solve:

$$\exists\mathit{gates}~\exists\mathit{wires}~\forall x_0,x_1,x_2\ldotp g(x_0, x_1, x_2)=circuit(x_0,x_1,x_2)$$

Allowing an arbitrary number of gates and arbitrary connections will result in an unnecessarily huge search space.
Instead, we restrict ourselves to a fixed number of gates, which we can increase incrementally, and only allow 
Two inputs...

The following schematic illustrates a choice (solid) of potential (dashed) connections for an example with only one output $g_0$ and one inner gate $f_3$.

{{< figure src="gfx/idea.svg" title="Example abstract syntax tree of an expression" width="200px" >}}

The variables $c_{gate, in1, in2}$ encode which 