---
title: "Mastermind Solver"
date: 2024-11-08
draft: false
work: false
tools:
- name: "ClojureScript"
  url: "https://clojurescript.org/"
- name: "C++"
  url: "https://isocpp.org/"
- name: "Emscripten"
  url: "https://emscripten.org/"
- name: "kissat"
  url: "https://github.com/arminbiere/kissat"
resources:
- src: "initial_version.png"
  title: "Testing the example from the blog post"
---

I was curious to explore what [ClojureScript](https://clojurescript.org/) and [Reagent](https://github.com/reagent-project/reagent) are all about and used this opportunity to create [a web frontend](https://mastermind-solver.bohlender.pro) for [the SAT-based Mastermind solver from one of my posts](/blog/playing-hard-mastermind-games-with-a-sat-based-ai/).

All computation is kept client-side to avoid server costs.
I had to [port](https://github.com/bohlender/mastermind-solver) the approach to C/C++ and [kissat](https://github.com/arminbiere/kissat) to obtain a reasonably small and performant WASM library.
Ultimately, this library is what the thin ClojureScript frontend wraps.
