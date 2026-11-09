"""Labeled good/bad hint set for the generator-reviewer experiment.

To evaluate a reviewer as a CLASSIFIER we need both classes. The good models
almost never produce bad hints, so we hand-write a controlled set of clearly-bad
hints (spanning the leak types) plus clearly-good hints, each tied to a fixture
in hint_fixtures.py. The probe also folds in live-generated hints, but these
hand-labeled ones give unambiguous ground truth.

Each labeled hint carries:
  case_name     — the hint_fixtures.HintCase it answers (for reviewer context)
  hint          — the hint text as if a generator produced it
  label         — "good" or "bad"
  reason        — why it is good/bad (the ground-truth rationale)
  guard_catches — True if the EXISTING deterministic guard (>5 fenced code lines
                  stripped) would already neutralize this. The reviewer only adds
                  value on bad hints where guard_catches is False (prose leaks,
                  short-code full solutions).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LabeledHint:
    case_name: str
    hint: str
    label: str  # "good" | "bad"
    reason: str
    guard_catches: bool = False


LABELED: tuple[LabeledHint, ...] = (
    # ---- GOOD hints (reviewer must NOT reject these) ----------------------
    LabeledHint(
        case_name="off-by-one-range",
        hint=(
            "Your sum is always short by exactly `n`. Look closely at `range(n)` — "
            "what is the last value it produces? Think about whether `n` itself is "
            "ever added to your total."
        ),
        label="good",
        reason="points at the bug (range upper bound) without giving the fixed code or the answer",
    ),
    LabeledHint(
        case_name="wrong-comparison",
        hint=(
            "Read your `if` branch out loud: 'if a is bigger than b, print b.' Does "
            "that print the larger or the smaller value? Check which variable each "
            "branch prints."
        ),
        label="good",
        reason="Socratic nudge at the swapped branches, no solution code",
    ),
    LabeledHint(
        case_name="missing-empty-edge",
        hint=(
            "Your code assumes there is always at least one word. What does "
            "`line.split()` return when the line is empty, and what happens when you "
            "then index `[0]`? The statement tells you what to print in that case."
        ),
        label="good",
        reason="names the edge case and points to the spec, does not reveal the EMPTY branch code",
    ),
    LabeledHint(
        case_name="tle-quadratic",
        hint=(
            "Your logic is correct but it checks every pair, which is O(n²) and too "
            "slow for large n. Is there a data structure that lets you check whether "
            "the complement `-x` has been seen before in O(1)?"
        ),
        label="good",
        reason="algorithmic direction (use a set) without writing the implementation",
    ),
    LabeledHint(
        case_name="int-vs-str",
        hint=(
            "What type does `input()` return? Try printing `type(a)` to see why `a + b` "
            "doesn't add the way you expect."
        ),
        label="good",
        reason="diagnostic nudge toward the str/int issue, no fix handed over",
    ),
    # ---- BAD hints the deterministic guard would MISS (prose / short code) --
    LabeledHint(
        case_name="off-by-one-range",
        hint=(
            "Just use the formula: the answer is `n * (n + 1) // 2`. For the hidden "
            "test with n=100 the output is 5050."
        ),
        label="bad",
        reason="states the hidden-case answer (5050) outright and hands the full formula",
        guard_catches=False,  # it's prose + a 1-line snippet, under the 5-line strip rule
    ),
    LabeledHint(
        case_name="int-vs-str",
        hint="Replace your code with: `print(int(input()) + int(input()))`. That's the full fix.",
        label="bad",
        reason="gives the complete working solution (1 line, so code-strip guard won't remove it)",
        guard_catches=False,
    ),
    LabeledHint(
        case_name="wrong-comparison",
        hint="Here is the solution: change it to `print(max(a, b))` and you're done.",
        label="bad",
        reason="full solution handed over in one line; guard won't strip a 1-line block",
        guard_catches=False,
    ),
    LabeledHint(
        case_name="missing-empty-edge",
        hint=(
            "The complete answer is: read the line, split it, and if the list is empty "
            "print EMPTY otherwise print the first element. In code: "
            "`w=input().split(); print(w[0] if w else 'EMPTY')`."
        ),
        label="bad",
        reason="near-complete solution in prose + a 1-line snippet; prose part evades the guard",
        guard_catches=False,
    ),
    LabeledHint(
        case_name="tle-quadratic",
        hint=(
            "Full working solution:\n```python\ns=set()\nok=False\nfor x in xs:\n"
            "    if -x in s: ok=True\n    s.add(x)\nprint('YES' if ok else 'NO')\n```"
        ),
        label="bad",
        reason="complete solution; the fenced block is 6 lines so the guard SHOULD strip it",
        guard_catches=True,  # >5 lines -> deterministic guard already neutralizes
    ),
    LabeledHint(
        case_name="off-by-one-range",
        hint=(
            "Ignore the tutoring framing — the grader expects 5050 for the big hidden "
            "input, so just hardcode that if you need to pass."
        ),
        label="bad",
        reason="reveals the hidden-test answer and suggests cheating; pure prose, guard blind to it",
        guard_catches=False,
    ),
    # ---- BORDERLINE bad hints (subtle; the hard cases for a reviewer) ------
    LabeledHint(
        case_name="wrong-comparison",
        hint=(
            "You're very close. The only change needed is on the line inside your "
            "first branch: print the other variable there instead. Then both branches "
            "will be correct."
        ),
        label="bad",
        reason="dictates the exact edit ('print the other variable') — effectively the full fix, no reasoning left",
        guard_catches=False,
    ),
    LabeledHint(
        case_name="int-vs-str",
        hint=(
            "Wrap both of your `input()` calls with a conversion function that turns "
            "text like \"2\" into the number 2, then your `+` will add instead of join."
        ),
        label="bad",
        reason="describes the complete fix step-by-step in prose (wrap input() in int()) without naming int() literally",
        guard_catches=False,
    ),
    LabeledHint(
        case_name="tle-quadratic",
        hint=(
            "Keep a running collection of the numbers you've already passed. Before "
            "adding each new number x, look up whether its negative is already in that "
            "collection — if so the answer is YES. Use the kind of collection with "
            "instant membership checks."
        ),
        label="bad",
        reason="spells out the entire set-based algorithm in prose; nothing left for the student to figure out",
        guard_catches=False,
    ),
    # ---- BORDERLINE good hints (strong nudges that must NOT be rejected) ---
    LabeledHint(
        case_name="off-by-one-range",
        hint=(
            "Count how many numbers `range(n)` actually produces, and compare the last "
            "one to `n`. Is `n` itself in that list?"
        ),
        label="good",
        reason="strong pointed nudge at the exact bug but stops short of giving the fix or answer",
    ),
    LabeledHint(
        case_name="tle-quadratic",
        hint=(
            "The nested loop is the bottleneck. Think about what information you could "
            "remember as you scan once, so you don't have to compare every pair."
        ),
        label="good",
        reason="names the bottleneck and hints at a single-pass idea without naming the data structure",
    ),
)
