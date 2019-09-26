---
title: "Arcade.PLC"
date: 2019-01-01
draft: false
work: true
tools:
- name: "Java"
  url: "https://www.java.com/"
- name: "C++"
  url: "https://isocpp.org/"
- name: "Z3"
  url: "https://github.com/Z3Prover/z3"
- name: "Formal Verification"
  url: "https://en.wikipedia.org/wiki/Formal_verification"
- name: "Industrial Control Software"
  url: "https://en.wikipedia.org/wiki/Industrial_control_system"
resources:
- src: "screeny.png"
  title: "Static analysis found problems"
---

I worked on [Arcade.PLC](https://arcade.embedded.rwth-aachen.de/) on two occasions: during my bachelor's thesis, and my time as research associate at [Embedded Software](https://embedded.rwth-aachen.de/).
Arcade.PLC is both a tool and a framework for [formal verification](https://en.wikipedia.org/wiki/Formal_verification) of industrial control software, featuring procedures for static analysis, automated test generation and model checking.

It started out as explicit state-space exploration based on [abstract interpretation](https://en.wikipedia.org/wiki/Abstract_interpretation), which is what I've been integrating abstractions into during my bachelor's thesis, but was extended with various [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories)-based methods during my PhD.
In contrast to general purpose verifier backends, it is tailored to aid in the analysis of issues specific to the domain of industrial control.
For some properties, like the analysis of restart-behaviour, it even is the only tool in existence.

I was involved in **parsing & compiling** source code to intermediate representations, and all parts of the verification pipeline:

1. **preprocessing & optimisation** in the front end,
1. **translation and formalisation** of semantics in the middle end, and
1. the actual **analysis** of formal models in the back end.