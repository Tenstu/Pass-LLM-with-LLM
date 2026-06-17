# Exam Pattern Templates

campus recruitment exam highest-frequency patterns. Replace the Algorithm phase
in the standard skeleton with the matching template below.
See `SKILL.md` section 3 (Template Selection) for how to choose.

## 4a. Simulation + State Machine

**Trigger keywords**: simulation, state machine, toggle, alternating, state changes over time

```python
    # ============================================================
    # Algorithm: Simulation + state machine
    # ============================================================
    s = input().strip()
    ops = input().strip()

    state = False  # TODO: define states
    arr = list(s)

    for i, op in enumerate(ops):
        # TODO: determine pos = i % len(arr) or other rule
        # TODO: apply state-dependent transformation to arr[pos]
        # TODO: toggle state if needed
        pass

    ans = "".join(arr)
    print(ans)
```

**Complexity**: O(n) time, O(n) space.

## 4b. Simulation + Counter/Mapping

**Trigger keywords**: counter, frequency, mapping, count occurrences, tally, histogram

```python
    # ============================================================
    # Algorithm: Simulation + counter/mapping
    # ============================================================
    mapping = {}  # TODO: predefine mapping
    # e.g. mapping = {c: value for c, v in zip("0123456789", [...])}

    t = int(input())
    out = []
    for _ in range(t):
        s = input().strip()
        total = sum(mapping[c] for c in s)
        out.append(str(total))
    print("\n".join(out))
```

**Complexity**: O(total_length) time, O(1) space for fixed alphabet.

## 4c. Stack + GCD Merge

**Trigger keywords**: GCD, merge, stack, coprime, adjacent merge, 互质

```python
    # ============================================================
    # Algorithm: Stack + GCD merge
    # ============================================================
    n = int(input())
    nums = list(map(int, input().split()))

    st = []
    ans = 0
    for x in nums:
        st.append(x)
        while len(st) >= 2 and math.gcd(st[-1], st[-2]) == 1:
            # TODO: merge logic, update ans
            st.pop()
        # TODO: update ans from st[-1]

    # TODO: finalize ans
    print(ans)
```

**Complexity**: O(n) amortized time (each element pushed/popped at most once), O(n) space.

## 4d. String Modification (by Index)

**Trigger keywords**: modify string, replace character at position, q operations, update string

```python
    # ============================================================
    # Algorithm: String modification by index
    # ============================================================
    s = input().strip()
    q = int(input())
    chars = list(s)

    for _ in range(q):
        idx = int(input()) - 1  # 1-based to 0-based
        # TODO: read replacement value
        # TODO: chars[idx] = new_char

    ans = "".join(chars)
    print(ans)
```

**Complexity**: O(n + q) time, O(n) space.
**Pitfall**: input() returns string with trailing newline — use `.strip()` or index conversion carefully.

## 4e. Bracket Matching

**Trigger keywords**: bracket, parentheses, valid, balanced, matching pairs, 括号匹配

```python
    # ============================================================
    # Algorithm: Bracket matching
    # ============================================================
    s = input().strip()

    st = []
    pair = {')': '(', ']': '[', '}': '{'}
    valid = True
    for c in s:
        if c in "([{":
            st.append(c)
        elif c in ")]}":
            if not st or st[-1] != pair[c]:
                valid = False
                break
            st.pop()

    ans = "valid" if valid and not st else "invalid"
    print(ans)
```

**Complexity**: O(n) time, O(n) space.
**Pitfall**: must check both `valid` AND empty stack — unclosed opening brackets make it invalid too.

## 4f. Math Derivation + Formula

**Trigger keywords**: formula, arithmetic, GCD, prime factorization, modular arithmetic, count/sum derivation

```python
    # ============================================================
    # Algorithm: Math derivation + formula
    # ============================================================
    n = int(input())

    # TODO: derive the formula from the problem statement
    # Common: arithmetic series, GCD, prime factorization, modular arithmetic

    ans = 0  # TODO: replace with formula
    print(ans)
```

**Pitfall**: for large n, always check if O(n) loop TLEs — look for O(1) or O(log n) formula.
For modular arithmetic, apply `% MOD` at each step to avoid overflow.
