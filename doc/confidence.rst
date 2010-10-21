==============================================
Finding an efficient way to compute confidence
==============================================

Confidence calculations are messy but very localized computations on a
graph. MapReduce takes messy, localized computations and makes it efficient to
compute them globally. Can we use MapReduce to compute confidence scores?

PageRank
========
PageRank is the first eigenvector of the transition matrix of a graph. It
represents the probability of ending up at a particular node after an
arbitrarily-long random walk.

It can be efficiently computed with MapReduce. That's largely the point.

If we can make confidence scores into a random walk, then we can use PageRank
and MapReduce to compute confidence scores. Woot.

Calculating AND/OR justifications
---------------------------------
This would work if there were never any negations:

First, assign every reason its conjunctive score.

- Map: Iterate through the scores table. Find all conjunctions that contain
  each scored object. Emit (that conjunction ID, score).
- Reduce: Multiply. Save results into the reason table if possible.

Then, re-assign scores as the disjunction of reason scores.

- Map: Iterate through the reason table. Emit (target, score).
- Reduce: 1 - multiply.

    # applied to previous results
    m1 = function() {
      db.reasons.findAll({'factors': this}).forEach(
        function(doc) {
          emit(doc._id, this.score);
        }
      )
    }

    r1 = function(k, vals) {
      var prod = 1.0;
      for (var v in vals) prod *= v;
      return prod;
    }

    m2 = function() {
      emit(this.target, this.score);
    }
      
    r2 = function(k, vals) {
      var prod = 1.0;
      for (var v in vals) prod *= (1-v);
      return 1-prod;
    }

Bayesian justification updates
------------------------------
The situation is: you've got *n* reasons to believe something is true or false.
However, each of those reasons has a probability that it's lying to you, in
addition to a weight w(r).

The assertion we're choosing whether to believe will itself become a reason.

So, a probability of 0.5 represents the complete lack of information. This is
unrelated to the probability of the described event actually happening in the
world.

The posterior probability of an assertion, then, comes entirely from comparing
the evidence that it is true or false and normalizing them to add up to 1.
The probability that the evidence is true is:

    P(a) \propto \Prod_{r} P(r)^{w(r)}

And the evidence that it is false is:

    P(~a) \propto \Prod_{r} (1 - P(r))^{w(r)}

We can transform these values from probability into *net information*:

    I(x) := \lg(P(x) / (1 - P(x)))

To invert this:

    2^{I(y)} = P(y) / (1 - P(y))
    2^{I(y)} - P(y) * 2^{I(y)} = P(y)
    2^{I(y)} = (2^{I(y)} + 1) P(y)
    P(y) = 2^{I(y)} / (2^{I(y)} + 1)

And then the *actual posterior probability* can be calculated from these
values:

    I(a) = \Sum_{r} I(r) * w(r)

If this is to work, nothing can convey infinite information. Not even root.

Conjunctions
------------
The probability that a conjunctive statement is informative is...?

One vaguely-justified way: We're trying to use the statements to make a yes/no
decision. Each statement either transmits the right information, or it flips
the bit. In this case, two wrongs do make a right.

    I(a) = lg (P(r1) P(r2) + (1 - P(r1))(1 - P(r2))) / 
              (P(r1)(1 - P(r2)) + (1 - P(r1))(P(r2)))
         = lg (2 P(r1) P(r2) + (1 - P(r1) - P(r2))) /
              (P(r1) + P(r2) - 2 P(r1)P(r2) )
         = -lg (x/(1-x)), where x = P(r1) + P(r2) - 2 P(r1)P(r2)
    
    -I(a) is the net information of r1 XOR r2. Maybe there's a way to compute
    that.

Can we do this in information space instead of probability space?

Or we can just take things sufficiently close to 1 and treat them as the
identity.

Or...
=====
This all points to the "analog intuition" model (analog.txt).

This model even allows trust to propagate *without* a root.

Representation
==============
New layout for reasons:

- reason id
- target (id) -- can be a real assertion or an external symbol, but *not*
  another reason
- list representing the conjunction
- polarity

Incremental updates
===================

    A ---> B        A <= A, B, E
    A ---> E        B <= A, B, -C, D
    B -/-> C        C <= -B, C, D
    B ---> D        D <= B, C, D, E
    D ---> C        E <= A, D, E
    E ---> D

    A       B       C       D       E
    0       1       0       0       0
    1/3     1/4     -1/3    1/4     0
    7/36    7/24    etc.

This converges to the first eigenvector. woot. But: DAMMIT CONJUNCTIONS

okay. We have a matrix A of assertions => conjunctions. (c x a)
A' = inverse assertions => conjunctions, so it's mostly infinite.
And we have a matrix B of conjunctions => assertions. (a x c)
a is the current weight on assertions, b is the weight on conjunctions.

    a <= B * 1/(A * 1/a)

    b = 1/(A * 1/a)
    b[i] = 1/(A[i] * 1/a)
         = parallel of (A[i], a)


let % be the inverse-vector by matrix operation. Then:

    a <= B % (A % a)

This may have eigenvector-like properties. In fact, it damn well better.
