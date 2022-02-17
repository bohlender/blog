---
title: "Solving the \"Seven Segment Search\" Puzzle with Z3"
date: 2022-01-22T15:06:54+01:00
publishDate: 2022-02-13
tags: ["SMT", "Puzzle", "Advent of Code"]
draft: false
math: true
images: []
videos: []
audio: []
---
This week I stumbled upon [someone wondering](https://www.reddit.com/r/adventofcode/comments/rbwnh5/2021_day_8_can_it_be_solved_as_a_constraint/) whether the **second part** of the recent [Advent of Code puzzle "Seven Segment Search"](https://adventofcode.com/2021/day/8) can be expressed as a constraint satisfaction problem.
As attested by the replies: yes, it can.
However, I think the question deserves a more extensive discussion than just a few comments in a thread.
This post tries to provide a more instructive answer and raise awareness for the tradeoffs or solver misuses some solutions put up with.

I assume that the reader is familiar with mathematical notation and
- just struggles to express the posed problem in a formal, declarative way, _or_
- is interested in seeing how the [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) solver [Z3](https://github.com/Z3Prover/z3/) can be used to express and solve the problem in several logics.
It takes only few steps to get from a quantifier-laden high-level formulation to what is effectively [propositional logic](https://en.wikipedia.org/wiki/Propositional_logic).
<!--more-->
## The Problem Statement
A functioning [seven-segment display](https://en.wikipedia.org/wiki/Seven-segment_display) is supposed to represent digits as follows:

{{<figure src="gfx/display_good.svg" title="Random digits on a functioning display" width="450">}}

By associating each segment with a character, we can clearly describe which segments are supposed to light up for each digit:

{{<highlight-file "aoc08.py" Python 4 15>}}

The crux of the [Seven Segment Search](https://adventofcode.com/2021/day/8) puzzle is that we are faced with a seven-segment display whose wiring got mixed up.
As a result, instead of turning on segments `c` and `f` to display a 1, our display may turn on segments `a` and `b` instead.
We don't get to see how the wrong wiring looks like though.
All we can observe is a sequence of patterns and our task is to make sense of it.
That is, to find out which digit each pattern represents:

{{<figure src="gfx/display_broken.svg" title="Random digits on a malfunctioning display" width="450">}}

Once we've figured out how to map the observable patterns to the digits they were originally intended to represent, we can use this knowledge to read the number shown on a four-digit seven-segment display that uses the very same wiring:

{{<figure src="gfx/display_4digit.svg" title="How 5353 shows up on the malfunctioning display" width="450">}}

The decoded number 5353 is the solution to this problem instance.
However, [Advent of Code](https://adventofcode.com) is about programming, so -- to make people solve the puzzle programmatically -- there are actually 200 independent instances that need to be solved and their 4-digit numbers summed up.

### Puzzle Input File
The [puzzle input file](input.txt) consists of 200 lines -- each of which encodes an independent problem instance.
The **first part** of a line describes the ten (unordered) patterns that can be observed on the malfunctioning seven-segment display.
The **second part** represents the four-digit seven-segment display that needs be decoded.
The above problem instance is in fact [the original introductory example](https://adventofcode.com/2021/day/8).
It may appear as follows in the input file:
```txt
acedgfb cdfbe gcdfa fbcad dab cefabd cdfgeb eafb cagedb ab | cdfeb fcadb cdfeb cdbaf
```

## Formalising a Problem Instance
If you give it some thought, it is easy to come up with efficient [procedures to solve](https://www.reddit.com/r/adventofcode/comments/rbj87a/2021_day_8_solutions/) any problem instance of this puzzle by exploiting domain-specifics like the patterns' numbers of segments.
For example, since `1` is the only digit that is displayed by exactly two segments, any observed pattern with just two lit segments must be representing it as well.
However, in general, such procedures may require significant alterations and re-analysis of puzzle aspects to exploit even if seemingly small variations are introduced.

Declarative approaches, which merely rely on a description of _what_ a solution to a problem is, rather than _how_ to find it, tend to be less prone to this.
Therefore, instead of investing in a solution procedure tailored to a specific problem from the start, it may be sensible to first express the problem in a declarative formalism for which generic solvers exist.
If, at some point, the tradeoff between flexibility and performance becomes problematic, one can still look into designing a problem-specific, imperative procedure.

{{<note>}}
This is similar to a common approach for solving math word problems.

Instead of coming up with clever solution steps that exploit problem-specifics it is often easier to translate the problem into a system of equations.
This system can then be solved by some generic procedure that doesn't even know what the equations characterise.
{{</note>}}

In the following, we will use [first-order logic](https://en.wikipedia.org/wiki/First_order_logic) to express the puzzle in a formal, declarative way.
This is a reasonably high-level logic which allows us to conveniently express the relations between the problem's entities, and is amenable to automated theorem proving.

### Characterisation in First-Order Logic
Let us start by formalising the thing we know: **how each digit maps to a set of segments on a (functioning) seven-segment display**.
In first-order logic sets are characterised by predicates.
For example, if the domain of discourse is $\mathbb{Z}$, predicate $\mathit{neg}(x) := x<0$ chracterises the set of negative integers.
Accordingly, to characterise the segments of each digit $d$, we could define 10 predicates $\mathit{segment}_d(s)$.
However, it is probably more convenient to let *one* binary predicate
{{<math>}}
\mathit{digitSegment}:\underset{\overbrace{\\{0,1,2,3,4,5,6,7,8,9\\}}}{\mathit{Digit}}\times \underset{\overbrace{\\{a,b,c,d,e,f,g\\}}}{\mathit{Segment}}
{{</math>}}
characterise the digit's segments.
That is, require the following to hold
{{<math>}}
\tag{1}\mathit{digitSegment}(d,s) \iff s \text{ is a segment of } d
{{</math>}}
for all digits $d$ and segments $s$.

We'd like to have a similar characterisation of the **mapping of digits to segments on the broken seven-segment display**, but that can't be stated directly as it depends on the (unknown) [permutation](https://en.wikipedia.org/wiki/Permutation) of segments, or wires, if you will.
Therefore, to first model the permutation, we introduce an uninterpreted function
{{<math>}}
\mathit{Perm}:\mathit{Segment}\to\mathit{Segment}
{{</math>}}
but restrict the possible interpretations of $\mathit{Perm}$ to permutations only.
This is achieved by requiring the function to be bijective:
{{<math>}}
\tag{2}\forall s,s'\in\mathit{Segment}\ldotp s = s' \iff \mathit{Perm}(s) = \mathit{Perm}(s')
{{</math>}}

{{<note>}}
In contrast to the predicate $\mathit{digitSegment}$, whose [extension](https://en.wikipedia.org/wiki/Extension_(predicate_logic)) is provided, $\mathit{Perm}$ is an *uninterpreted* symbol.
We follow the convention of logic programming literature and capitalise uninterpreted symbols.
{{</note>}}

Based on that we can now characterise the permuted digit segments
{{<math>}}
\mathit{PermDigitSegment}:\mathit{Digit}\times \mathit{Segment}
{{</math>}}
by specifying that $\mathit{Perm}(s)$ must be a permuted segment of $d$ iff $s$ is a segment of $d$ on the functioning display:
{{<math>}}
\tag{3}\mathit{PermDigitSegment}(d,\mathit{Perm}(s)) \iff \mathit{digitSegment}(d,s)
{{</math>}}

{{<note id="stepwise-composition">}}
Alternatively, it may help to think of the relation as follows.
If $s$ is a segment of $d$ on the functioning display, and $\mathit{Perm}$ maps $s$ to some $s'$, then $s'$ must be a segment of $d$ on the malfunctioning display, i.e.
{{<math>}}
\begin{aligned}
& \mathit{digitSegment}(d,s)\wedge \mathit{Perm}(s) = s'\\\
\rightarrow & \mathit{PermDigitSegment(d,s')}
\end{aligned}
{{</math>}}
for all $s,s'\in\mathit{Segment},d\in\mathit{Digit}$.
{{</note>}}

Note that so far we've only formalised aspects that are common to all problem instances.
Even the permutation $\mathit{Perm}$, which differs from instance to instance, could be introduced without referring to instance-specific details.

What distinguishes an instance are the ten **patterns that can be observed on the (malfunctioning) display**, i.e. the first part of each line of the input file.
Just as $\mathit{digitSegment}$ characterises the segments behind each possible digit, the idea here is to introduce a predicate
{{<math>}}
\mathit{patternSegment}: \underset{\overbrace{\\{0,1,2,3,4,5,6,7,8,9\\}}}{\mathit{Index}} \times \mathit{Segment}
{{</math>}}
to characterise the segments behind each of the ten observable patterns.
That is, assert for all indices $i$ and segments $s$ that
{{<math>}}
\tag{4}\mathit{patternSegment}(i,s) \iff s \text{ is a segment of the $i$-th pattern}.
{{</math>}}

{{<note>}}
Even though the domains $\mathit{Digit}$ and $\mathit{Index}$ seem to be equal they model different things.
They happen to use the same symbols but their types just don't match.
Accordingly, a $0\in\mathit{Digit}$ is uncomparable to a $0\in\mathit{Index}$.

However, which domains are needed in a formalisation primarily derives from our understanding of the problem.
Had our mental model of a problem instance been different, e.g. if the sequence of observed patterns would be interpreted as a first guess at the mapping from digits to segments, it would have been warranted to use
{{<math>}}
\mathit{patternSegment}: \mathit{Digit} \times \mathit{Segment}
{{</math>}}
here, too.
{{</note>}}

The only thing that remains to be formalised is the **relation between the observed patterns and the other "objects"**.
That's the actual puzzle.
What we know from the puzzle description is that each of the observable patterns matches the permuted segments of some digit.
Therefore, there must be a "decoding function"
{{<math>}}
\mathit{Idx2dig}: \mathit{Index} \to \mathit{Digit}
{{</math>}}
which maps each observed pattern -- more precisely its index $i$ -- in such a way to a digit $d$ that the permuted segments of $d$ correspond to the observed pattern.
Similar to $(3)$, we can constrain $\mathit{Idx2dig}$ to behave like this
by specifying that $s$ must be a permuted segment of digit $\mathit{Idx2dig}(i)$ iff $s$ is a segment of the $i$-th observed pattern
{{<math>}}
\tag{5}\mathit{PermDigitSegment}(\mathit{Idx2dig}(i),s) \iff \mathit{patternSegment}(i,s)
{{</math>}}
for all indices $i$ and segments $s$.

### The Characterisation at a Glance
Overall, we end up with the following constraints
{{<math>}}
\begin{aligned}
\mathit{digitSegment}(d,s) &\iff s \text{ is a segment of } d\\
s = s' &\iff \mathit{Perm}(s) = \mathit{Perm}(s')\\
\mathit{PermDigitSegment}(d,\mathit{Perm}(s)) &\iff \mathit{digitSegment}(d,s)\\
\mathit{patternSegment}(i,s) &\iff s \text{ is a segment of the $i$-th pattern}\\
\mathit{PermDigitSegment}(\mathit{Idx2dig}(i),s) &\iff \mathit{patternSegment}(i,s)
\end{aligned}
{{</math>}}
for all $d\in\mathit{Digit}$, $s,s'\in\mathit{Segment}$, and indices $i\in\mathit{Index}$.

If we now manage to find an interpretation of the uninterpreted symbols that satisfies all these constraints, the particular puzzle instance will be solved.
We can then simply use $\mathit{Idx2dig}$ to map the patterns on the malfunctioning four-digit seven-segment display back to digits, or use $\mathit{Perm}$ to undo the permutation of segments.

## Solving the Puzzle via Z3
While there are many solvers, formalisms, and technologies that we can leverage to obtain a satisfying interpretation of the above constraints, this post illustrates how to do it with the [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) solver [Z3](https://github.com/Z3Prover/z3/).
More precisely, with its [Python bindings](https://z3prover.github.io/api/html/namespacez3py.html).

### Domains
To express the above predicates we first have to introduce the domains, or `Sort`s, our values will be from.
Finite domains of unrelated values can be created via `EnumSort`, and that's exactly the kind of values we're dealing with in the puzzle.
Since we will also need to convert between these values and their Python counterparts -- `int` for digits and indices, and `str` for segments -- we accompany each domain with corresponding mappings: 

{{<highlight-file "aoc08.py" Python 17 30>}}

{{<note>}}
If you find introducing an `IndexSort` and related definitions unnecessary, feel free to alias `DigitSort` and its definitions instead, i.e. let `IndexSort = DigitSort` etc.
{{</note>}}

Of course it is possible to use `IntSort` and `StringSort` to model digits, indices and segments instead of introducing dedicated finite domains, and some of the [suggested approaches](https://www.reddit.com/r/adventofcode/comments/rbwnh5/2021_day_8_can_it_be_solved_as_a_constraint/) do resort to this.
However, when doing so one must be aware of the implications.

For example, to exploit problem-specifics, one of the posted solutions features integer addition in its constraints.
The result of this is that the characterisation ends up in a more complex fragment of first-order logic than necessary -- in [quantifier-free linear integer arithmetic (QF_LIA)](http://smtlib.cs.uiowa.edu/logics.shtml).
This, in turn, forces SMT solvers to employ more complex techniques than necessary to solve the puzzle.
However, if higher-level modelling better captures the semantics of the problem, it may pay off to use a more expressive (sub-)logic -- even if reduction to a less expressive one is possible.
One should just **be careful to not add such complexity inadvertently**.
Otherwise, one can quickly end up expressing a decidable problem in terms of an [undecidable](https://en.wikipedia.org/wiki/Undecidable_problem) one.

{{<note>}}
The [solution](aoc08.py) outlined by this post features three exchangeable encodings.
This lets you see for yourself how a logic impacts modelling convenience, size of the characterisation, and solver performance.
{{</note>}}

### Solving the Puzzle Incrementally
To solve the overall puzzle, we have to solve the 200 independent problem instances described in the [input file](input.txt) and combine their solutions.
Although it is possible to construct and solve the instances' constraints independently, as most of the [suggested solutions](https://www.reddit.com/r/adventofcode/comments/rbwnh5/2021_day_8_can_it_be_solved_as_a_constraint/) do, it is more efficient to avoid starting from scratch 200 times.
Closer inspection of constraints $(1)--(5)$ shows that the instances' formalisations only differ in $(4)$, i.e. the definition of $\mathit{patternSegment}$.
Therefore, a simple way to avoid starting from scratch is by first adding the core constraints $(1)--(3),(5)$ to the solver's stack of constraints and then iteratively checking satisfiability with each of the 200 variants of $(4)$ swapped in at the top of the stack.

{{<note>}}
Besides the possibility of using [push/pop](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-scopes) to check satisfiability of assertions in an incremental way, there is also [solving under assumptions](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-assumptions).
The latter is [more incremental](https://github.com/Z3Prover/z3/issues/1152#issuecomment-317625799) since <q>learned clauses that don't contain the assumptions are thus independent of them and can be reused in the next SAT call. This is different from push/pop where all learned clauses under a push are removed.</q>
{{</note>}}

The following encoding-agnostic procedure implements the suggested approach.
It uses the scope management operations [`push` and `pop`](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-scopes) to replace the definition of $\mathit{patternSegment}$ between satisfiability checks.
When a satisfying interpretation -- a so called model -- is found, we can inspect it to learn how the observed patterns map to digits:

{{<highlight-file "aoc08.py" Python 53 72>}}

The procedure is encoding-agnostic, in the sense that it only expects the characterisation code to implement the following self-explanatory interface:

{{<highlight-file "aoc08.py" Python 33 50>}}

{{<note>}}
Implementations of `PuzzleEncoder` should strive to return the most specific (sub-)logic the produced encoding is in.
The more specific it is, the more likely 
<q>[it may possible to apply specialized and more efficient satisfiability techniques](https://smtlib.cs.uiowa.edu/logics.shtml)</q>.
{{</note>}}

As you can hopefully see, using an SMT solver incrementally is pretty straight forward in the context of this puzzle.
Although we've just started, our SMT-based puzzle solver is almost finished already.
It merely remains to provide a concrete implementation of `PuzzleEncoder`.

### High-level Encoding
The most obvious solution is to just use the means Z3 provides to express the characterisation we came up with [above](#the-characterisation-at-a-glance).

It is handy to keep the symbols that we use in our encoding around, e.g. to reference them in the encoding functions, or to look up their interpretation later.
Therefore, we declare these symbols as members of the encoder.
What may catch you by surprise is that, following the [SMT-LIB standard](http://smtlib.cs.uiowa.edu/language.shtml), there is no special way to create a predicate in Z3.
Instead, predicates are understood as functions with a Boolean result:

{{<highlight-file "aoc08.py" Python 75 86>}}

{{<note>}}
Be careful to not confuse `self.idx2dig` with the `idx2dig` from `solve_puzzle`.
The former is a Z3 [function declaration](https://z3prover.github.io/api/html/classz3py_1_1_func_decl_ref.html).
The latter is a Python list of integers that gives us more convenient access to the found interpretation of $\mathit{Idx2dig}$.
{{</note>}}

Besides the standard [logics](https://smtlib.cs.uiowa.edu/logics.shtml) Z3 supports several others.
However, instead of guesswork, I find it the easiest to just look up the [strings](https://github.com/Z3Prover/z3/blob/81e94b21541280cb7fbc3426419ed6c3a8f24dd4/src/solver/smt_logics.cpp) that map to supported (sub-)logics.

With the Python bindings, the expressions that represent our core constraints look very similar to the original ones.
What stands out is that, in contrast to our formalisation, the variables we quantify over must be created beforehand.
Furthermore, in code, the right-hand side of $(1)$ is a bit less readable than the <q>$s \text{ is a segment of }d$</q> (cf. lines 96-98):

{{<highlight-file "aoc08.py" Python 88 117>}}

{{<note>}}
A pitfall of the Python bindings is that, unlike `==`, the Boolean operators `and` and `or` are not overloaded.
`And` and `Or` must be used instead.
{{</note>}}

Since the constraints $(1)$ and $(4)$ have the same form, `encode_variant` looks a lot like lines 91--98 from `encode_core`:

{{<highlight-file "aoc08.py" Python 119 131>}}

When our constraints are determined to be satisfiable, the returned model contains -- among other things -- the information how $\mathit{Idx2dig}$ maps indices to digits.
Since only the encoder needs to know how exactly the encoding works, i.e. `solve_puzzle` shouldn't have to deal with the declared symbols, `interpret` looks up in the model what each input is mapped to and returns the findings as a plain list of integers.
The integer at index $i$ denotes the digit encoded by the $i$-th observed pattern:

{{<highlight-file "aoc08.py" Python 133 134>}}

At this point you can give [our puzzle solver](aoc08.py) a try.
Just make sure to pass an instance of `HighLevelEncoder` to `solve_puzzle`.
This naïve solution isn't exactly fast, taking roughly 30s, but comping up with it didn't require much thought beyond [the original formalisation](#formalising-a-problem-instance).
Let's see whether this can be improved by switching to a less expressive (sub-)logic.

### Mid-level Encoding
Although quantifiers facilitate concise characterisation they are also a source of complexity -- especially in the context of small finite domains.
Therefore, in the next step, we will bring our constraints into a quantifier-free fragment of first-order logic.

Dropping the quantifiers does not entail any changes to the declared symbols, but the new encoder should communicate that the constraints it produces are free of quantifiers:

{{<highlight-file "aoc08.py" Python 137 148>}}

The approach to get rid of a forall quantifier is simple: just **explicitly enumerate the values and assert the nested constraint for each**.
This leaves us with an increased number of constraints but spares Z3 the necessity of dealing with quantifiers:

{{<highlight-file "aoc08.py" Python 150 172>}}

Aside from the substitution of quantification by iteration, the code is effectively the same as in our [first encoder](#high-level-encoding).
I find this version to be even more readable that the previous one, mostly because it is so easy to express <q>$s \text{ is a segment of }d$</q> for a concrete pair $(d,s)$.

The rest of the encoder does not provide any new insights and is only shown for the sake of completeness:

{{<highlight-file "aoc08.py" Python 174 185>}}

Now, try running `solve_puzzle` with this new encoder.
It turns out that moving to a quantifier-free fragment of first-order logic reduces the runtime significantly (to ~6s).
One might wonder whether going even lower will yield similar performance gains.

### Low-level Encoding
Similar to quantifiers, uninterpreted functions introduce some complexity but do not add any expressivity that is essential to our characterisation.
If our constraints were free of both quantifiers and uninterpreted functions they'd be effectively propositional.
In fact, Z3 wouldn't even reach for SMT procedures but directly employ its [SAT solver](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-sat-core).

{{<note>}}
The constraints are "effectively" propositional since enumeration data types and equality are not really in propositional logic but trivially reduced to it.
Essentially, it is possible to encode the $k=|D|$ distinct values of a finite domain $D$ in propositional logic by means of $\lceil\log_2(k)\rceil$ Boolean variables.
{{</note>}}

Now, how do we get rid of the uninterpreted functions?
Since all of our functions have finite domains, it is possible to introduce symbolic values to **replace each possible function application** in our constraints.
That is, for each function and input, we introduce a variable to denote the result.
This of course impacts the symbols we declare. 
For example, where we previously used an uninterpreted function
{{<math>}}
\mathit{digitSegment}:\mathit{Digit}\times\mathit{Segment}\to\mathbb{B}
{{</math>}}
to represent the predicate $\mathit{digitSegment}:\mathit{Digit}\times\mathit{Segment}$, we now have a Boolean variable for each pair $(d,s)\in\mathit{Digit}\times\mathit{Segment}$:

{{<highlight-file "aoc08.py" Python 188 199>}}

{{<note>}}
Be careful to not mistake the variable names for function applications.
I just like naming the variables like the function applications they replace.
{{</note>}}

We can now use the freshly introduced variables within our constraints, in place of the original function applications.
This does complicate constraints where we previously had nested function applications, such as $(3)$ and $(5)$.
Here, the idea is similar to the [alternative formulation](#stepwise-composition) of $(3)$: we constrain the result of the outer function application depending on the result of the nested function application.
However, without uninterpreted functions, some constraint simplification opportunities may become more obvious, too.
Since the domain and value range of $\mathit{perm}$ are equal the bijectivity constraint can be simplified to "distinct applications of $\mathit{perm}$ return distinct segments":

{{<highlight-file "aoc08.py" Python 201 224>}}

As with the previous encodings, the rest of the code holds no surprises and is merely listed for the sake of completeness:

{{<highlight-file "aoc08.py" Python 226 237>}}

This is where we stop tweaking the encoding.
You will find that running `solve_puzzle` with an instance of `LowLevelEncoder` again reduces the runtime significantly (to ~1s).

## Do Try This at Home
Interestingly, if the `LowLevelEncoder` is used, each `check` in `solve_puzzle` takes only about 500µs.
So why does `solve_puzzle` take 1s? That's an order of magnitude longer than 200 times 500µs!
Well, running a profiler shows that most time is wasted in the bindings -- specifically in `ExprRef.__eq__`.

There are several things you can do to squeeze out better execution times:
* Now that you've seen how to express the constraints with the Python bindings, give the [bindings for C++](https://z3prover.github.io/api/html/namespacez3.html) -- or some other language with less overhead than Python -- a try.
* Avoid recreating the constraints for each variant.
  They have the same form anyway.
  Instead, try to come up with a way to leverage [solving under assumptions](https://theory.stanford.edu/~nikolaj/programmingz3.html#sec-assumptions), i.e. delete `encode_variant` and rather communicate the observed patterns by passing appropriate assumptions to the `check` function.
* Alternatively, instead of solving each of the 200 problem instances separately, try to combine them all into a single set of constraints.
  A single invocation of `check` shall suffice to solve the complete puzzle.
* Assuming you do implement the above suggestion, try feeding the constraints to a dedicated SAT solver for another performance gain.
  Have a look at [this section](/blog/generating-crosswords-with-sat-smt/#cnf-export) from a previous post, if you need some guidance on how to do this.

{{<list-resources "{*.py,*.txt}">}}