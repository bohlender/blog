---
title: "Signal-Flow Analysis for MATLAB Simulink"
date: 2012-04-01
draft: false
headless: true
work: true
tools:
- name: "Java"
  url: "https://www.java.com/"
- name: "MATLAB Simulink"
  url: "https://www.mathworks.com/products/simulink.html"
- name: "Data-Flow Analysis"
  url: "https://en.wikipedia.org/wiki/Data-flow_analysis"
- name: "yFiles"
  url: "https://www.yworks.com/products/yfiles-for-java"
---

When I was a research assistant at [Embedded Software](https://embedded.rwth-aachen.de/), I was involved in a research project with Daimler AG.
With [MATLAB Simulink](https://www.mathworks.com/products/simulink.html) being a popular choice for the development of embedded software in the automotive domain, this project aimed to develop model-based analyses to aid developers of Simulink models.

Tracking a signal's (potential) flow manually, given the highly modular and hierarchical models, is prone to error. 
To simplify this, I adapted standard dataflow analyses for programs to this domain.
I was also responsible for visualising results of such analyses in both Simulink and external frameworks.