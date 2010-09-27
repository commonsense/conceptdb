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

Representation
==============
New layout for reasons:

- reason id
- target (id) -- can be a real assertion or an external symbol, but *not*
  another reason
- list representing the conjunction
- polarity

