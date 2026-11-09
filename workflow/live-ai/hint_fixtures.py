"""Known-scenario fixtures for the hint model-selection and reliability probes.

Unlike complexity, a hint has no single "correct" string — quality is a human
judgment. So each fixture pins the things we CAN reason about:

  - a realistic question (title + statement + visible tests + a HIDDEN test)
  - buggy student code with a specific, known defect
  - the intended nudge (what a good hint should point at)
  - the hidden test's expected output (ground truth for answer-leak detection:
    a hint must never reveal `hidden_expected` or hand over a full solution)

The probe reuses the REAL pipeline (app.ai.hints tool loop + guards), so the
model reaches the question/code only through the get_question / get_code tools,
exactly as in production. Hidden tests are filtered out before the model sees
them; the fixtures still carry them so we can check the model never leaks them.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VisibleTest:
    stdin: str
    expected_stdout: str


@dataclass(frozen=True)
class HintCase:
    name: str
    title: str
    statement_md: str
    visible_tests: tuple[VisibleTest, ...]
    hidden_stdin: str
    hidden_expected: str  # ground truth the hint must NOT reveal
    student_code: str
    student_question: str | None
    defect: str  # the actual bug in student_code
    good_hint_points_at: str  # what a helpful hint should nudge toward
    full_solution: str  # a correct solution; a hint must NOT reproduce this wholesale
    # Only some fixtures have a "surprising" hidden answer worth leak-detecting.
    # Categorical outputs (YES/NO/EMPTY) are defined by the problem statement and
    # appear in any correct hint, so they are NOT leak signals. leak_token is the
    # value that, if revealed, genuinely hands over the hidden-case answer; None
    # means this fixture has no meaningful hidden-answer leak to detect.
    leak_token: str | None = None


CASES: tuple[HintCase, ...] = (
    HintCase(
        name="off-by-one-range",
        title="Sum 1..N",
        statement_md="Read an integer N on one line. Print the sum 1 + 2 + ... + N.",
        visible_tests=(VisibleTest("5\n", "15\n"), VisibleTest("1\n", "1\n")),
        hidden_stdin="100\n",
        hidden_expected="5050\n",
        student_code=(
            "n = int(input())\n"
            "total = 0\n"
            "for i in range(n):\n"  # bug: range(n) stops at n-1
            "    total += i\n"
            "print(total)\n"
        ),
        student_question="Why is my sum always a bit too small?",
        defect="range(n) iterates 0..n-1, so it misses N and starts at 0",
        good_hint_points_at="the loop bounds / that range(n) excludes n",
        full_solution="n=int(input());print(n*(n+1)//2)",
        leak_token="5050",  # the hidden answer for N=100; a hint revealing it hands over the result
    ),
    HintCase(
        name="wrong-comparison",
        title="Max of Two",
        statement_md="Read two integers a and b (one per line). Print the larger one.",
        visible_tests=(VisibleTest("3\n5\n", "5\n"), VisibleTest("9\n2\n", "9\n")),
        hidden_stdin="7\n7\n",
        hidden_expected="7\n",
        student_code=(
            "a = int(input())\n"
            "b = int(input())\n"
            "if a > b:\n"
            "    print(b)\n"  # bug: prints the smaller one
            "else:\n"
            "    print(a)\n"
        ),
        student_question=None,
        defect="branches are swapped: prints the smaller value, not the larger",
        good_hint_points_at="which branch prints which variable",
        full_solution="a=int(input());b=int(input());print(max(a,b))",
    ),
    HintCase(
        name="missing-empty-edge",
        title="First Word",
        statement_md=(
            "Read a line of space-separated words (the line may be empty). "
            "Print the first word, or print 'EMPTY' if there are no words."
        ),
        visible_tests=(VisibleTest("hello world\n", "hello\n"), VisibleTest("a b c\n", "a\n")),
        hidden_stdin="\n",
        hidden_expected="EMPTY\n",
        student_code=(
            "line = input()\n"
            "words = line.split()\n"
            "print(words[0])\n"  # bug: IndexError on empty input
        ),
        student_question="It crashes on some inputs but I don't know which.",
        defect="no handling for empty input: words[0] raises IndexError when words is empty",
        good_hint_points_at="the empty-input edge case / checking if words is non-empty",
        full_solution="w=input().split();print(w[0] if w else 'EMPTY')",
    ),
    HintCase(
        name="int-vs-str",
        title="Add Two",
        statement_md="Read two integers a and b (one per line) and print their sum.",
        visible_tests=(VisibleTest("2\n3\n", "5\n"), VisibleTest("10\n20\n", "30\n")),
        hidden_stdin="100\n250\n",
        hidden_expected="350\n",
        student_code=(
            "a = input()\n"
            "b = input()\n"
            "print(a + b)\n"  # bug: string concatenation, not integer addition
        ),
        student_question="For input 2 and 3 it prints 23 instead of 5?",
        defect="inputs are strings; a + b concatenates instead of adding integers",
        good_hint_points_at="converting input to int before adding",
        full_solution="print(int(input())+int(input()))",
        leak_token="350",  # the hidden answer for 100+250
    ),
    HintCase(
        name="tle-quadratic",
        title="Any Pair Sums To Zero",
        statement_md=(
            "Read N then N integers. Print 'YES' if any two distinct elements sum to 0, "
            "else 'NO'. N can be up to 200000."
        ),
        visible_tests=(VisibleTest("4\n1 -1 2 3\n", "YES\n"), VisibleTest("3\n1 2 3\n", "NO\n")),
        hidden_stdin="5\n4 5 6 7 8\n",
        hidden_expected="NO\n",
        student_code=(
            "n = int(input())\n"
            "xs = list(map(int, input().split()))\n"
            "found = False\n"
            "for i in range(n):\n"
            "    for j in range(n):\n"  # bug: O(n^2), TLE for large n
            "        if i != j and xs[i] + xs[j] == 0:\n"
            "            found = True\n"
            "print('YES' if found else 'NO')\n"
        ),
        student_question="It works on small cases but times out on the big ones.",
        defect="nested loops are O(n^2); times out for n up to 200000",
        good_hint_points_at="using a set for O(n) lookup instead of the nested loop",
        full_solution=(
            "n=int(input());xs=list(map(int,input().split()));s=set();ok=False\n"
            "for x in xs:\n    if -x in s: ok=True\n    s.add(x)\nprint('YES' if ok else 'NO')"
        ),
    ),
)
