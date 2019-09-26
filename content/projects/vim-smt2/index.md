---
title: "vim-smt2"
date: 2017-10-10
draft: false
work: false
tools:
- name: "Vim script"
  url: "https://en.wikipedia.org/wiki/Vim_(text_editor)"
- name: "SMT-LIB"
  url: "http://smtlib.cs.uiowa.edu/"
resources:
- src: "screeny.png"
  title: "Highlighting for Z3's extensions"
---

Although [SMT-LIB](http://smtlib.cs.uiowa.edu/) is the standard language supported by most [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) solvers, some of them introduce custom language extensions.
Such extensions may range from syntactical sugar to fine-grained control over the underlying solver-procedure.

Since I'm an avid user of [Z3](https://github.com/Z3Prover/z3), I started [vim-smt2](https://github.com/bohlender/vim-smt2) to have a plugin for the [Vim](https://github.com/vim/vim) editor that supports both the base SMT-LIB language and the extensions provided by Z3.
Besides the basic syntax highlighting I'm implementing convenient features, such as querying satisfiability or the solver's version, when I find myself repeatedly doing automatable tasks manually.