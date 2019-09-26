---
title: "HASDEL"
date: 2013-04-01
draft: false
work: true
tools:
- name: "Python"
  url: "https://www.python.org/"
- name: "ANTLR"
  url: "https://www.antlr.org/"
- name: "GTK"
  url: "https://www.gtk.org/"
resources:
- src: "screeny.png"
  title: "Computing the probability of a failure"
---

When I was a research assistant at [MOVES](https://moves.rwth-aachen.de), I was involved in the [HASDEL](http://www.compass-toolset.org/projects/hasdel/) project.
This was an ESA project, aiming to provide [RAMS](https://en.wikipedia.org/wiki/RAMS) analyses tailored to the specific needs of launcher systems.
Since this was a successor of the [COMPASS](http://www.compass-toolset.org/projects/compass/) project, the original COMPASS toolset had to be extended.

In COMPASS, the system specification is written in the [SLIM](http://www.compass-toolset.org/projects/compass/about/#slim-language) language.
I was mainly responsible for adapting the SLIM compiler front and middle end, to support the language extensions proposed for HASDEL.
In line with this, I also handled arising change requests concerning the <abbr title="Graphical User Interface">GUI</abbr>, and automated the creation of a minimal Linux image for showcasing HASDEL.