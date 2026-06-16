# I/O Mode Templates

Pick the template matching the problem's input format. Copy into the `Input` phase of the standard skeleton.

## 2a. Single Test Case

```python
    input = sys.stdin.readline
    n = int(input())
    nums = list(map(int, input().split()))
    print(ans)
```

## 2b. Multi Test Case (first line = T)

```python
    input = sys.stdin.readline
    t = int(input())
    out = []
    for _ in range(t):
        n = int(input())
        nums = list(map(int, input().split()))
        out.append(str(process_one(n, nums)))
    print("\n".join(out))
```

## 2c. Line-by-Line Until EOF (unknown line count)

```python
    out = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        out.append(str(process_line(parts)))
    print("\n".join(out))
```

## 2d. First Line = n, Then n Lines of Data

```python
    input = sys.stdin.readline
    n = int(input())
    arr = [list(map(int, input().split())) for _ in range(n)]
    print(ans)
```

## 2e. Mixed: n, m on first line, then grid

```python
    input = sys.stdin.readline
    n, m = map(int, input().split())
    grid = [list(map(int, input().split())) for _ in range(n)]
    print(ans)
```
