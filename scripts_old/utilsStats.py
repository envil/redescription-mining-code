from scipy.special import gammaln
from scipy.stats import binom
from numpy import exp
import pdb

def hypergeomPMF(k, M, n, N):
    tot, good = M, n
    bad = tot - good
    return exp(gammaln(good+1) - gammaln(good-k+1) - gammaln(k+1) + gammaln(bad+1) \
                              - gammaln(bad-N+k+1) - gammaln(N-k+1) - gammaln(tot+1) \
                              + gammaln(tot-N+1) + gammaln(N+1))
#same as the following but numerically more precise
#return comb(good,k) * comb(bad,N-k) / comb(tot,N)

def pValOver(kInter, nbRows, suppL, suppR):
    ## probability that two sets of these size have intersection equal or larger than kInter
    return sum([ hypergeomPMF(k, nbRows, suppL, suppR) for k in range(kInter, min(suppL, suppR)+1)])

def pValSupp(nbRows, supp, pr):
    ## probability that an itemset with marginal probability pr has support equal or larger than supp
    return 1-binom.cdf(supp-1, nbRows, pr) 

