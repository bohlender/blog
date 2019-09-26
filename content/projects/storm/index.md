---
title: "Storm"
date: 2014-09-02
draft: false
work: true
tools:
- name: "C++"
  url: "https://isocpp.org/"
- name: "CUDD"
  url: "https://github.com/ivmai/cudd"
- name: "Z3"
  url: "https://github.com/Z3Prover/z3"
- name: "Probabilistic Model Checking"
  url: "https://en.wikipedia.org/wiki/Model_checking"
resources:
- src: "screeny.png"
  title: "Shared coin protocol checking"
---

In the context of my master's thesis I've worked on the [Storm](https://github.com/moves-rwth/storm) probabilistic [model checker](https://en.wikipedia.org/wiki/Model_checking).
In particular, I developed a fully symbolic variant of the partially explicit procedure used in [PASS](https://depend.cs.uni-saarland.de/tools/pass/) for probabilistic reachability checking of Markov decision processes. 

I used [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories)-solving to compute a [menu-based abstraction](http://d-nb.info/1009497642), and refine it in a counterexample-guided fashion.
The abstraction was stored in terms of <abbr title="multi-terminal binary decision diagrams">MTBDDs</abbr>, for which I developed both the actual symbolic value iteration and symbolic static analyses for preprocessing.