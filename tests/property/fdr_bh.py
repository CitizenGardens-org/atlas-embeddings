def benjamini_hochberg(pvals, q=0.05):
    n = len(pvals)
    ps = sorted((p, i) for i, p in enumerate(pvals))
    thresh = 0.0
    k = -1
    for rank, (p, i) in enumerate(ps, start=1):
        t = (rank / n) * q
        if p <= t:
            k = rank
            thresh = t
    reject = [False] * n
    if k >= 1:
        cutoff = ps[k - 1][0]
        for p, i in ps:
            reject[i] = p <= cutoff
    return reject, thresh
