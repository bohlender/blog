---
title: "SMT-based Reasoning About the Fast Inverse Square Root"
date: 2019-09-12T09:31:28+02:00
tags: ["SMT", "SMT-LIB", "Software Verification"]
draft: false
math: true
images: []
videos: []
audio: []
---
While there is a [mathematical explanation](https://web.archive.org/web/20160308091758/http://www.daxia.com/bibis/upload/406Fast_Inverse_Square_Root.pdf) for the choice of `0x5F3759DF` in the [famous bit-level hack](https://en.wikipedia.org/wiki/Fast_inverse_square_root) for approximating the multiplicative inverse of the square root of a 32-bit floating-point number, it is not immediately clear to what extent the reasoning is really applicable in the context of machine data types and their peculiarities.
This post illustrates how this, and related aspects, can be investigated with [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories)-based reasoning about the actual implementation.
<!--more-->
## Introduction
Computing the "inverse" square root $1/\sqrt{x}$ is a common operation in 3D computer graphics since it occurs naturally during [vector normalisation](https://en.wikipedia.org/wiki/Unit_vector).
However, in the '90s, its precise computation was computationally expensive, and high numbers of such computations in every frame of a real-time graphics application could lead to stuttering and dropping of the framerate.
With this in mind, it is not surprising that the "fast inverse square root" is often associated with [Quake III Arena](https://en.wikipedia.org/wiki/Quake_III_Arena) -- a multiplayer-player focussed first-person shooter from 1999 that made use of this approximation to avoid the computational cost of the real thing, without losing "too much" precision.

While Quake did not invent the approximation, the publishing of its source code brought many developers into contact with this technique.
And although modern CPUs provide native support for approximating $1/\sqrt{x}$ quickly -- rendering the approximation mostly irrelevant nowadays -- the general approach taken in this post is still applicable to many modern day questions.

{{< note >}}
With the introduction of [SSE](https://en.wikipedia.org/wiki/Streaming_SIMD_Extensions), every x86_64 CPU since the Pentium III features a native instruction for computing $\sqrt{x}$ and its reciprocal via `SQRTSS` and `RSQRTSS`, respectively.

More recent extensions, such as [AVX-512](https://en.wikipedia.org/wiki/AVX-512), provide even better approximations w.r.t. the relative error, and also support 64-bit floats.
{{< /note >}}

### The Fast Inverse Square Root
The following C code is a condensed version of the [approximation used in Quake](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/q_math.c#L552).
It boils down to treating the float as a 32-bit integer, and performing the trickery shown in line 3.
The result could be returned after line 4, but adding a subsequent iteration of [Newton's method](https://en.wikipedia.org/wiki/Newton%27s_method) improves the precision significantly, while being computationally cheap.

{{< highlight c "linenos=table" >}}
float Q_rsqrt(float f) {
	int32_t b = *(int32_t*)&f;
	b = 0x5f3759df - (b >> 1); // The actual bit-level hack
	float res = *(float*)&b;

    // Run one iteration of Newton's method to improve precision
	float fHalf = f * 0.5f;
	return res * (1.5f - (fHalf * res * res));
}
{{< /highlight >}}

When presented with such a bit-level hack, one cannot help but wonder whether it really does what it is supposed to do in all cases.
As you will see, we do not have to understand the approximation's inner workings to assess its correctness, but merely be able to formalise it.
To this end, let us first look at how to express the expected behaviour of `Q_rsqrt`.

### Correctness of an Approximation
To asses the quality of an approximation, the employed measure should incorporate the discrepancy between the exact value $f(x)$ and its approximation $\hat{f}(x)$, that is, be based on the [absolute error](https://en.wikipedia.org/wiki/Approximation_error) $\epsilon(x) = |f(x) - \hat{f}(x)|$.
Depending on the context, various measures come into question, and it is often not obvious what the most sensible choice is.
However, a clear disadvantage of sticking with the absolute error is that it ignores the magnitude of the exact value.

For example consider finding that some approximation yields $\epsilon(42) = 1000$.
Without knowing the magnitude this may sound like a big error, but might actually be off by just 1% if $f(42) = 100000$.
For this reason, it is often advantageous to use the [relative error](https://en.wikipedia.org/wiki/Approximation_error)
$$\eta(x) = \frac{\epsilon(x)}{|f(x)|} = \left|1-\frac{\hat{f}(x)}{f(x)}\right|,$$
which takes the magnitude into consideration.
In the context of Quake, the quality of the approximation should not fluctuate but keep the relative error reasonably small for all inputs.
Therefore it is [common](https://web.archive.org/web/20160308091758/http://www.daxia.com/bibis/upload/406Fast_Inverse_Square_Root.pdf) to analyse the fast inverse square root  w.r.t. the **maximum relative error** it may cause.
The smaller this value is, the better the approximation is considered to be.

{{< note >}}
Depending on the context, it might be more reasonable to use the [least squares](https://en.wikipedia.org/wiki/Least_squares) criterion -- a standard tool in regression analysis.

[J. Kadlec](http://rrrola.wz.cz/inv_sqrt.html) has experimented with both measures in the context of `Q_rsqrt`, and provides accordingly optimised alternatives to `0x5f3759df`.
{{< /note >}}

Accordingly, correctness of an approximation can be specified as the requirement that $\eta(x)$ stays below a "sufficiently" small value for all inputs $x$.
Of course, the definition of when an error is negligible is governed by the context the approximation is used in.
For this post, let `Q_rsqrt` be correct if it achieves a maximum relative error of less than 1%:

{{< math >}}
\tag{1}\begin{aligned}
\eta(x) &= \left|1-\frac{\mathit{Q\_rsqrt}(x)}{\frac{1}{\sqrt{x}}}\right|\\
&= |1-\mathit{Q\_rsqrt}(x)\cdot\sqrt{x}| \\
&< 0.01
\end{aligned}
{{< /math >}}

## Logical Characterisation of Program Semantics
Instead of investigating the property of interest through testing, or exhaustive exploration of possible in- and outputs, symbolic verification is based on characterising semantics in terms of constraints in [first-order logic](https://en.wikipedia.org/wiki/First-order_logic), and reasoning about their satisfiability.

Just as $x^2+y^2 = 1$ characterises all points on the [unit circle](https://en.wikipedia.org/wiki/Unit_circle), we will establish constraints to characterise all realisable executions of `Q_rsqrt` -- the essential difference to our use-case being that program variables are ultimately just fixed-size bit vectors, while $x,y\in \mathbb{R}$.
A percise characterisation of program semantics has to take all the peculiarities of machine represented numbers into account, such as overflows, rounding errors and exceptions.

The actual heavy lifting, that is checking the constraints' satisfiability, is typically accomplished with an [SMT](https://en.wikipedia.org/wiki/Satisfiability_modulo_theories) solver.
Providing a proper characterisation of program semantics and properties of interest is up to us.
Luckily the [SMT-LIB](http://smtlib.cs.uiowa.edu/) standard provides a common language and interface that most SMT solvers are compliant with.
In particular, it specifies the types and operations relevant for software verification.

In the following we characterise both $\eta(x)$ and `Q_rsqrt` in SMT-LIB, using [this brute force search for the maximum relative error](maxRelErr.c) as a reference for the functions' expected outputs.
The characterisation is standard so feel free to skip it if you're just interested in finding out whether SMT solvers can handle the arising floating-point and bit vector constraints.

### Characterising the Relative Error
To start with a simple function, consider the following implementation of $\eta$ taken from our reference implementation.
Just as in $(1)$, it computes $\eta(x)$ from $\sqrt x$ and $\mathit{Q\\_rsqrt}(x)$.
{{< highlight-file "maxRelErr.c" c 29 31 >}}

This already looks pretty much like a constraint that relates inputs and outputs, but what is wrong with something along the lines of

$$\tag{2} \mathit{relErr} = |1 - \mathit{fFast}\cdot\mathit{fSqrt}|,$$

where $\mathit{relErr},\mathit{fFast},\mathit{fSqrt}\in\mathbb{F}_{32}$ (32-bit floats)?

While the general idea is sensible, going directly from source to characterisation bypasses the compiler.
As a result, subtleties like type promotion and architecture-specifics may be missing in the characterisation, e.g. the target architecture might not be using 32-bit floats.

To capture program semantics faithfully, but avoid dealing with assembly and tons of opcodes, many verifiers are based on [intermediate representations](https://en.wikipedia.org/wiki/Intermediate_representation) (IRs).
In the context of verification these will typically be higher level than machine-specific assembly, and use a reduced set of instructions, but have fixed semantics and be devoid of syntactic sugar.
Such decoupling of progamming languages and IRs, that all reasoning is actually based on, also enables verifiers to implicitly support several programming languages if these can be compiled to the one IR supported by the verifier.
[LLVM IR](https://llvm.org/docs/LangRef.html) is probably the most prominent one, and the one we will use here.
[Clang](https://clang.llvm.org/) can be used to compile our example to LLVM IR:

{{< highlight-file "maxRelErr.ll" llvm 28 33 >}}

Given this representation, all potential subtleties become explicit.
The function expects two 32-bit floats, denoted by %0 and %1, and returns a 32-bit floating-point number, too.
There is no branching of control flow, making the characterisation pretty straight forward:

{{< highlight-file "invsqrt.smt2" Scheme 27 38 >}}

While this post is not a tutorial on the [SMT-LIB language](http://smtlib.cs.uiowa.edu/papers/smt-lib-reference-v2.6-r2017-07-18.pdf), it should still be pretty easy to get the general idea and intuition.
For the most part, the characterisation boils down to expressing the LLVM IR in terms of [symbolic expressions](https://en.wikipedia.org/wiki/S-expression) written in [prefix notation](https://en.wikipedia.org/wiki/Polish_notation).

{{< note >}}
For an interactive introduction to the SMT-LIB language I recommend the [Z3 tutorial](https://rise4fun.com/Z3/tutorial/guide).
[Z3](https://github.com/Z3Prover/z3/) is a feature-packed, MIT licensed and SMT-LIB compliant SMT solver.
Besides supporting the SMT-LIB language it also features non-standard extensions, such as the `eval` command, which improve various aspects of working with SMT-LIB.

For example prior to SMT-LIB v2.6, `(declare-const f Float32)` was Z3's syntactic sugar for `(declare-fun x () Float32)`.
This handy command stresses the fact that 0-ary functions are just constants, and has made it into the standard.
{{< /note >}}

`relErr` is the logical characterisation of the eponymous function, using the same names for intermediate values as the LLVM IR.
As in the IR, the symbols `%0` to `%5` only exist within the scope of the function, and the returned value `%5` is just an alias for `(fp.abs %4)`.
In contrast to the handwaving in $(2)$, SMT-LIB is explicit about the operations and disinguishes between `fp.abs` and `abs`, for floats and integers, respectively.
The language is also aware of the fact that floats cannot represent every real number precisely, which is why `fp.mul`, and many other operations, require the underlying rounding mode to be specified.
Our example's IR does not make use of specific rounding modes, which is why we use the default [rounding to nearest](https://en.wikipedia.org/wiki/Floating-point_arithmetic#Rounding_modes) (RNE), where ties round to the nearest even digit.
This is also the reason why the verbosity in the auxiliary (0-ary) function `f1.0` is needed, just to specify a IEEE 754 compliant `1.0f`.

### Characterising the Fast Inverse Square Root
Similar to the relative error function, `Q_rsqrt` features no branching of control flow but is merely a sequence of instructions.
To be able to experiment with different constants in the hack later, we introduce an identifier `magic` that exists outside of the function.

{{< highlight-file "maxRelErr.c" c 17 27 >}}

Compiling this to LLVM IR yields the following for both 32 and 64-bit targets:

{{< highlight-file "maxRelErr.ll" llvm 14 25 >}}

This example illustrates another advantage of characterising an IR over directly translating the source code.
In contrast to many operations on real numbers, floating-point operations are [not associative](https://en.wikipedia.org/wiki/Floating-point_arithmetic#Accuracy_problems), but the IR makes the order, in which subexpressions will be evaluated on the target architecture, explicit.

As with `relErr`, the characterisation of `Q_rsqrt` is essentialy a reformulation of the returned value `%10` in terms of the operations specified in SMT-LIB.
As before, we introduce auxiliary functions `f0.5` and `f1.5` to keep the notation of these float constants short and readable.

{{< highlight-file "invsqrt.smt2" Scheme 1 25 >}}

Two points may need further clarification though:

{{< note >}}
Just like LLVM IR, SMT-LIB does not distinguish between signed and unsigned bit vectors.
Instead, operations whose semantics depends on the signedness come in two flavours, e.g. both `bvugt` and `bvsgt` express "greater than".
{{< /note >}}

1. The `magic` constant is declared as a 32-bit integer that exists in global scope.
Unlike in the source code, its value is currently unconstrained but will be restricted later, depending on the property of interest.
1. The characterised `Q_rsqrt` seems slightly off: for some reason it has two inputs, and the cast of the input float to a 32-bit integer is missing.
The reason is that [there is no _function_](http://smtlib.cs.uiowa.edu/theories-FloatingPoint.shtml) for converting floats to their IEEE 754 binary format, e.g. `NaN` has multiple representations.
Therefore we feed both the float `%0%` and its bit vector representation `%2` into `Q_rsqrt`, and will assert this relation for every call site.

## Checking Properties of Interest
Having defined both functions, we can start checking the satisfiability of constraints that involve them.
Although we are pretty sure that our logical characterisation is correct, we may have mixed things up or introduced typos.
It is a good idea to first test whether it performs the same computations as the [reference implementation](maxRelErr.c):

```zsh
arch: 64-bit
magic: 0x5F3759DF
worst: 0x016EB3C0 (0.000000000000)
fSqrt: 0x20773327 (0.000000000000)
fFast: 0x5E84530F (4767490664373944320.000000000000)
maxRelErr: 0x3AE5B000 (0.0017523765563964844)
```

To this end, we assert that `magic` should be the original constant `0x5F3759DF`, and that `b` is the bit vector representation of the float `f`.
The naïve reference implementation finds the **input `0x016EB3C0`** (interpreted as float) to cause a relative error of `0x3AE5B000`, so we experiment with `b` taking this value:

{{< highlight-file "invsqrt.smt2" Scheme 43 50 >}}

Feeding these constraints into an SMT solver, such as [Z3](https://github.com/Z3Prover/z3/), will return that they are indeed satisfiable.
To determine whether the characterised functions actually compute the expected values, we could also have added the following assertions (prior to `check-sat`):

```Scheme
(assert (= f ((_ to_fp 8 24) #x016EB3C0))) ; f = (float)0x016EB3C0
(assert (=                                 ; fSqrt = (float)0x20773327
    (fp.sqrt RNE f)				 
    ((_ to_fp 8 24) #x20773327)
))
(assert (=                                 ; fFast = (float)0x5E84530F
    (Q_rsqrt f b)
    ((_ to_fp 8 24) #x5E84530F)
))
(assert (=                                 ; relErr = (float)0x3AE5B000
    (relErr (fp.sqrt RNE f) (Q_rsqrt f b))
    ((_ to_fp 8 24) #x3AE5B000)
))
```

However, all these assertions do is evaluate whether applying various functions to the values picked by the solver for `f` and `b` yields the expected values.
Instead of adding these unnecessary assertions, making it harder for the solver to find a solution, it is more appropriate to use Z3's `eval` command, to do these evaluations _after_ `check-sat`:

```Scheme
(eval (= f ((_ to_fp 8 24) #x016EB3C0))) ; f = (float)0x016EB3C0
(eval (=                                 ; fSqrt = (float)0x20773327
    (fp.sqrt RNE f)				 
    ((_ to_fp 8 24) #x20773327)
))
(eval (=                                 ; fFast = (float)0x5E84530F
    (Q_rsqrt f b)
    ((_ to_fp 8 24) #x5E84530F)
))
(eval (=                                 ; relErr = (float)0x3AE5B000
    (relErr (fp.sqrt RNE f) (Q_rsqrt f b))
    ((_ to_fp 8 24) #x3AE5B000)
))
```
Using this variant in [our characterisation](invsqrt.smt2), instead of the additional assertions, a solution is found immediately.
The computed **values do indeed match those of the executable**:

{{< highlight-file "invsqrt.log" zsh 1 17 >}}

### Checking Correctness
Having confirmed that there is nothing obviously wrong with our characterisation, we can now investigate the properties we are actually interested in.

We already established in the introduction that correctness of an approximation can be specified by constraining the maximum relative error.
To prove that the relative error never exceeds 1% for any float, we leave the input to `Q_rsqrt` **unconstrained**, and check whether it is possible for `relErr` to return anything greater than 0.01.

{{< highlight-file "invsqrt.smt2" Scheme 85 96 >}}

Here the solver returns `sat`, finding that picking infinity (`#x7f800000`) as input results in a greater relative error.
Indeed, the hack turns out to not be applicable to all floating point numbers.

To find out whether it will work "correctly" for the remaining inputs, we can additionally require the input to be **not infinite**:

{{< highlight-file "invsqrt.smt2" Scheme 105 106 >}}

However, the solver returns `sat` again, finding that picking zero (`0x00000000`) as input results in a greater relative error, too.
Granted, this is a rather special input, so what about restricting the input to be **not zero** either?

{{< highlight-file "invsqrt.smt2" Scheme 115 116 >}}

Again, the solver finds the constraints to be satisfiable.
It turns out that picking a [subnormal](https://en.wikipedia.org/wiki/Denormal_number) input (`#x00000001`) can result in a relative error above 1%, too.
When also requiring the input to **not be subnormal**, the SMT solver finally determines the resulting set of constraints to be unsatisfiable:

{{< highlight-file "invsqrt.smt2" Scheme 125 126 >}}

Since normal floats are not zero, infinite, or subnormal, the unsatisfiability of the accumulated set of constraints **proves that for all normal floats**, the predicate `relErr(..) > 0.01` is not satisfiable.

### Can the Result be NaN?
Why do I state the result in such an indirect way, instead of just saying that we have proof of correctness for all normal floats?
Because there is still a minor issue with the previous result.
While we have indeed proven that the result of `relErr` can not exceed 0.01, the result may potentially not even be a number (`NaN`).
Since `NaN` is neither greater nor less than 1%, even an implementation of `Q_rsqrt` that always returns `NaN` will satisfy our current specification of correctness.

The authors of Quake were aware of the issue, and had an [according check](https://github.com/id-Software/Quake-III-Arena/blob/dbe4ddb10315479fc00086f08e25d968b4b43c49/code/game/q_math.c#L568) in place.
To determine whether `NaN` can ever be returned by `relErr` for a normal float, we simplify the previously accumulated constraints to just `(fp.isNormal f)` and assert `fp.isNaN` for the result of `relErr`:

{{< highlight-file "invsqrt.smt2" Scheme 134 145 >}}

The result is sobering.
The constraints are trivially satisfiable by any normal, negative floating-point number.
After all, we are not approximating an arbitrary function $f(x)$ but $1/\sqrt x$, and the square root for negative numbers is not defined -- at least not for floats.
This should really have been part of our correctness criterion from the start.

{{< note >}}
Knowing that $\sqrt x$ is not defined for negative $x$, we restrict the analysis to non-negative floats, such that `relErr` never returns `NaN`.
However, even if $f(x)$ were an arbitrary function, we could have achieved the same by simply asserting `relErr` to not be `NaN`.
{{< /note >}}

With the assertion `(not (fp.isNegative f))` added, `relErr` cannot return `NaN` anymore, and the previous proof that `relErr(..) > 0.01` is never satisfied becomes a proper proof of correctness.
The following constraints are not satisfiable, proving **within seconds** that for all normal, non-negative floats **the relative error never exceeds 1%**.

```Scheme
(assert (= magic #x5F3759DF))     ; original magic number

(declare-const f Float32)         ; input float
(declare-const b (_ BitVec 32))   ; input float's bitvector representation (asserted below)
(assert (= ((_ to_fp 8 24) b) f)) ; %3 = bitcast float %0 to i32 // originally in Q_rsqrt

(assert (fp.isNormal f))          ; only consider normal floats
(assert (not (fp.isNegative f ))) ; only consider non-negative floats

(assert (fp.gt                    ; can relErr exceed 0.01?
    (relErr (fp.sqrt RNE f) (Q_rsqrt f b))
    ((_ to_fp 8 24) RNE 0.01)
))
(check-sat)
```

### Bounding the Maximum Relative Error
Having established that the fast inverse square root really works for normal, non-negative floats, it would be nice to have a tighter bound on the relative error.
The maximum relative error might be significantly lower than 1%.

With the current set of constraints, SMT solving can take the role of an [oracle](https://en.wikipedia.org/wiki/Oracle_machine) for checking whether the maximum relative error is below some bound, and be used to **refine this bound iteratively**, e.g. via binary search.
While the solver returns `sat`, the maximum relative error is greater than the currently assumed bound, and a greater bound must be picked.
However, if the solver returns `unsat`, the bound can be decreased.

{{< note >}}
Z3 is not just an SMT solver but can also solve [optimisation problems over SMT formulas](https://rise4fun.com/Z3/tutorial/optimization).
Unfortunately this machinery does not support floating-point constraints, which is why we do the minimisation manually.
{{< /note >}}

A possible refinement sequence is evaluated in [`invsqrt.smt2`](invsqrt.smt2), outputting the following:

{{< highlight-file "invsqrt.log" zsh 45 80 >}}

Unlike the previous constraints, these checks take a while (**hours**), but eventually **prove the maximum relative error to be `0x3AE5B000`** (~0.00175237).
This matches the results of our [brute force search](maxRelErr.c).

### In Search of Better Magic
While we could analyse some interesting properties of the implementation with SMT solving, it didn't really pay off in this particular case, as the [naïve enumeration](maxRelErr.c) of all possible inputs and outputs takes just a few seconds.
It is when the problem space grows, and exhaustive testing becomes unfeasible, that formal verification starts to pay off.
One such task is finding a better `magic` constant, which reduces the maximum relative error even further.

When approaching this without any insight into the problem, finding the best constant boils down to computing the maximum relative error achieved by each of the $2^{32}$ possible constants.
The evaluation of each constant, in turn, requires checking the relative error resulting from each of the $2^{32}$ possible input floats.
Overall, exhaustive testing would involve $2^{32}\cdot 2^{32}$ computations of the relative error and is clearly not feasible.

{{< note >}}
An exhaustive exploration of the maximum relative error resulting from each of the $2^{32}$ constants in question **can be made feasible** by exploiting peculiarities of $\eta(x)$.
In particular, the computation of the maximum relative error for a given `magic` can be sped up, as it is sufficient to compute the error for $x\in[1,4)$ only -- the [error wraps around](http://rrrola.wz.cz/inv_sqrt.html).
{{< /note >}}

To approach this with SMT, we first of all need a way of checking whether a `magic` constant exists that yields a maximum relative error below a given bound.
The actual minimisation of the bound can then be achieved as above, by using the check as an oracle and refining the bound iteratively.
More formally, we are primarily interested in solving

$$ \underset{\mathit{magic}}{\exists}\, \underset{x\geq 0}{\forall}\, \mathit{normal}(x) \rightarrow \eta(x) < 0.001752,$$

that is finding a `magic` constant which returns a smaller maximum relative error than the original constant `0x5F3759DF` does for normal, non-negative inputs.
Such a search for parameters that make a system adhere to certain constraints is known as **parameter synthesis**.
Although dedicated techniques for solving such problems exist, they are out of the scope of this post.
We, instead, follow the conceptually simpler approach of letting the SMT solver deal with the alternating quantifiers on its own.

Since all [free constants](https://en.wikipedia.org/wiki/Free_variables_and_bound_variables) that occur in an SMT instance are implicitly existentially quantified, the SMT-LIB characterisation of the upper constraint only involves an explicit `forall` quantifier:

{{< highlight-file "invsqrt.smt2" Scheme 243 258 >}}

Using these constraints, and the initial bound 0.001752, Z3 will output the following for the refinement sequence chosen in our [SMT-LIB script](invsqrt.smt2):

{{< highlight-file "invsqrt.log" zsh 82 >}}

Solving these instances takes about **two days** on an i5-4210M, but Z3 eventually determines that the `magic` constant `0x5f375a81` achieves a maximum relative error of `0x3ae58c00` (~0.0017513).
Furthermore, we find that **no constant can achieve an even lower maximum relative error**.

## Do Try This at Home!
Having read this far, and understood how to get from source code to a logical characterisation of the semantics and various properties, you should be able to investigate related issues on you own.
The following ideas come to mind (easiest first):

* Find out whether the optimised `magic` constant is unique, or there are others that achieve the same maximum relative error.
* Quake uses [another hack](https://github.com/id-Software/Quake-III-Arena/blob/dbe4ddb10315479fc00086f08e25d968b4b43c49/code/game/q_math.c#L574) for computing the absolute value of a floating-point number.
  Come up with a reasonable specification of correctness, and (dis-)prove it with SMT-based reasoning.
* Try analysing the considered properties with [CBMC](http://www.cprover.org/cbmc/), [ESBMC](http://esbmc.org/) or [LLBMC](http://llbmc.org/).
* In machine learning, replacing floats with [bfloat16](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format) seems to be all the rage.
  Come up with a fast inverse square root and proof of correctness for those, or adapt what we have so far to doubles.
* Use a [less restrictive variant](http://rrrola.wz.cz/inv_sqrt.html) of the hack, where _three_ parameters are open to tweaking.
  Try to find optimal values for those.
* Instead of using SMT-LIB and hardcoding a potential refinement, try to implement the iterative refinement properly by using the [API of an SMT solver](https://github.com/Z3Prover/z3#z3-bindings) directly.
* Tweak the characterisation to let the solver not only choose the `magic` constant but also a (bounded) number of instructions from a fixed set.
  Does the solver come up with the same instructions that were used in the original hack, or does an even better hack exist?

{{< list-resources "{*.smt2,*.c,*.ll,*.log}" >}}