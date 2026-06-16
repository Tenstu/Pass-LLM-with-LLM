# Algorithm Skeleton Templates

Replace the Algorithm phase in the standard skeleton with the matching template below.
See `SKILL.md` section 3 (Template Selection) for how to choose.

## 3a. BFS — Grid Shortest Path

**Trigger keywords**: shortest path, maze, grid, 0/1 matrix, reachable, min steps

```python
    # ============================================================
    # Algorithm: BFS grid shortest path
    # ============================================================
    xs, ys, xt, yt = map(int, input().split())
    xs -= 1; ys -= 1; xt -= 1; yt -= 1

    grid = [list(input().strip()) for _ in range(n)]

    dist = [[-1] * m for _ in range(n)]
    dist[xs][ys] = 0
    q = deque([(xs, ys)])

    while q:
        x, y = q.popleft()
        if x == xt and y == yt:
            break
        for dx, dy in DIR4:
            nx, ny = x + dx, y + dy
            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == "." and dist[nx][ny] == -1:
                dist[nx][ny] = dist[x][y] + 1
                q.append((nx, ny))

    ans = dist[xt][yt]
    print(ans if ans != -1 else -1)
```

**Complexity**: O(n*m) time, O(n*m) space.

## 3b. DFS — Iterative (Stack-Based)

**Trigger keywords**: connected components, traversal, graph, reachability, flood fill

```python
    # ============================================================
    # Algorithm: Iterative DFS
    # ============================================================
    n = int(input())
    m = int(input())
    graph = [[] for _ in range(n)]
    for _ in range(m):
        u, v = map(int, input().split())
        u -= 1; v -= 1
        graph[u].append(v)
        graph[v].append(u)

    seen = set()
    stack = [0]
    seen.add(0)
    while stack:
        u = stack.pop()
        for v in graph[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
```

**Complexity**: O(n + m) time, O(n) space.

## 3c. DSU (Union-Find)

**Trigger keywords**: merge, connected components, disjoint sets, union, connected query

```python
    # ============================================================
    # Algorithm: DSU
    # ============================================================
    n = int(input())

    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        return True

    m = int(input())
    for _ in range(m):
        a, b = map(int, input().split())
        a -= 1; b -= 1
        union(a, b)
```

**Complexity**: O(m * α(n)) time, O(n) space. Iterative find avoids Python recursion limit.

## 3d. Heap / Top-K

**Trigger keywords**: top K, largest K, smallest K, kth largest, priority queue

```python
    # ============================================================
    # Algorithm: Heap / Top-K
    # ============================================================
    n, k = map(int, input().split())
    nums = list(map(int, input().split()))

    heap = []
    for x in nums:
        if len(heap) < k:
            heappush(heap, x)
        elif x > heap[0]:
            heappop(heap)
            heappush(heap, x)

    ans = sorted(heap, reverse=True)
    print(ans)
```

**Complexity**: O(n log k) time, O(k) space.

## 3e. Dijkstra

**Trigger keywords**: weighted shortest path, min cost, min distance, Dijkstra, non-negative edges

```python
    # ============================================================
    # Algorithm: Dijkstra
    # ============================================================
    n = int(input())
    graph = [[] for _ in range(n)]
    m = int(input())
    for _ in range(m):
        u, v, w = map(int, input().split())
        u -= 1; v -= 1
        graph[u].append((v, w))
    start = int(input()) - 1

    INF = 10 ** 30
    dist = [INF] * n
    dist[start] = 0
    heap = [(0, start)]
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heappush(heap, (nd, v))
    ans = dist
    print(ans)
```

**Complexity**: O((n+m) log n) time, O(n+m) space.
**Pitfall**: stale heap entry — always skip with `if d != dist[u]: continue`.

## 3f. Prefix Sum

**Trigger keywords**: range sum, subarray sum, interval query, cumulative sum

```python
    # ============================================================
    # Algorithm: Prefix sum
    # ============================================================
    n = int(input())
    nums = list(map(int, input().split()))
    pre = [0]
    for x in nums:
        pre.append(pre[-1] + x)

    q = int(input())
    out = []
    for _ in range(q):
        l, r = map(int, input().split())
        out.append(str(pre[r] - pre[l]))
    print("\n".join(out))
```

**Complexity**: O(n+q) time, O(n) space.
**Pitfall**: confirm query uses 0-based or 1-based indexing — prefix array is 1-based internally.

## 3g. Sliding Window (max/min variant)

**Trigger keywords**: subarray, window, max/min of length k, fixed-length window

```python
    # ============================================================
    # Algorithm: Sliding window
    # ============================================================
    n, k = map(int, input().split())
    nums = list(map(int, input().split()))

    cur = sum(nums[:k])
    ans = cur
    for i in range(k, n):
        cur += nums[i] - nums[i - k]
        ans = max(ans, cur)
    print(ans)
```

**Complexity**: O(n) time, O(1) space (fixed window).
**Pitfall**: for variable-length window, use a deque for monotonic max/min; this template is for fixed-length sum only.

## 3h. Binary Search

**Trigger keywords**: find minimum/maximum satisfying condition, boundary, monotonic function, answer in range

```python
    # ============================================================
    # Algorithm: Binary search
    # ============================================================
    n = int(input())
    a = list(map(int, input().split()))
    a.sort()

    def lower_bound(x):
        l, r = 0, n
        while l < r:
            m = (l + r) // 2
            if a[m] >= x:
                r = m
            else:
                l = m + 1
        return l

    def upper_bound(x):
        l, r = 0, n
        while l < r:
            m = (l + r) // 2
            if a[m] > x:
                r = m
            else:
                l = m + 1
        return l

    def check(x):
        # return True/False based on whether x satisfies the condition
        return True

    lo, hi = 0, 10 ** 9
    while lo < hi:
        mid = (lo + hi) // 2
        if check(mid):
            hi = mid
        else:
            lo = mid + 1
    ans = lo
    print(ans)
```

**Complexity**: O(n log n + check * log(range)). Lower/upper bound are O(log n) each.
**Pitfall**: `lo < hi` is half-open interval; `mid = (lo + hi) // 2` with `lo = mid + 1` avoids infinite loop.
