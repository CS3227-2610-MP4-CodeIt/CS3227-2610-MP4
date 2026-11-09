"""Known-answer fixtures for the complexity model-selection probe.

Each case is a self-contained Python snippet whose Big-O time and auxiliary
space are known, so a probe can check whether a model's answer is correct, not
merely well-formed. `time_accept` / `space_accept` are the set of normalized
Big-O strings we treat as correct (models phrase the same complexity several
ways, e.g. "O(n)" vs "linear").

Normalization for matching strips spaces, lowercases, and removes "o(", ")",
"big-o", and "theta/θ" decoration before comparing against the accept set.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ComplexityCase:
    name: str
    code: str
    time_accept: tuple[str, ...]  # normalized acceptable time answers
    space_accept: tuple[str, ...]  # normalized acceptable auxiliary-space answers
    note: str


CASES: tuple[ComplexityCase, ...] = (
    ComplexityCase(
        name="constant-index",
        code="def first(xs):\n    return xs[0]\n",
        time_accept=("1",),
        space_accept=("1",),
        note="single index, no loop",
    ),
    ComplexityCase(
        name="linear-sum",
        code="def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n",
        time_accept=("n",),
        space_accept=("1",),
        note="one pass, scalar accumulator",
    ),
    ComplexityCase(
        name="quadratic-pairs",
        code=(
            "def pairs(xs):\n"
            "    out = []\n"
            "    for i in range(len(xs)):\n"
            "        for j in range(len(xs)):\n"
            "            out.append((xs[i], xs[j]))\n"
            "    return out\n"
        ),
        time_accept=("n^2", "n2", "n**2"),
        space_accept=("n^2", "n2", "n**2"),
        note="nested loops building n*n output",
    ),
    ComplexityCase(
        name="binary-search",
        code=(
            "def bsearch(xs, target):\n"
            "    lo, hi = 0, len(xs) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if xs[mid] == target:\n"
            "            return mid\n"
            "        if xs[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
        ),
        time_accept=("logn", "log(n)", "log2n"),
        space_accept=("1",),
        note="halving search space, iterative",
    ),
    ComplexityCase(
        name="merge-sort",
        code=(
            "def msort(xs):\n"
            "    if len(xs) <= 1:\n"
            "        return xs\n"
            "    mid = len(xs) // 2\n"
            "    left = msort(xs[:mid])\n"
            "    right = msort(xs[mid:])\n"
            "    out, i, j = [], 0, 0\n"
            "    while i < len(left) and j < len(right):\n"
            "        if left[i] <= right[j]:\n"
            "            out.append(left[i]); i += 1\n"
            "        else:\n"
            "            out.append(right[j]); j += 1\n"
            "    out.extend(left[i:]); out.extend(right[j:])\n"
            "    return out\n"
        ),
        time_accept=("nlogn", "nlog(n)", "nlog2n"),
        space_accept=("n",),
        note="divide and conquer merge sort",
    ),
    ComplexityCase(
        name="factorial-recursion",
        code=(
            "def fact(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    return n * fact(n - 1)\n"
        ),
        time_accept=("n",),
        space_accept=("n",),
        note="linear recursion depth -> O(n) call stack space",
    ),
    ComplexityCase(
        name="hashset-dedup",
        code=(
            "def dedup(xs):\n"
            "    seen = set()\n"
            "    out = []\n"
            "    for x in xs:\n"
            "        if x not in seen:\n"
            "            seen.add(x)\n"
            "            out.append(x)\n"
            "    return out\n"
        ),
        time_accept=("n",),
        space_accept=("n",),
        note="one pass, set + list grow with input",
    ),
)
