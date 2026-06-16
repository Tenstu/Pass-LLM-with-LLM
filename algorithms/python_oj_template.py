"""
Python 3 ACM/OJ 答题模板。

使用说明:
1. 复制你需要的辅助函数。
2. 将 solve() 替换为题目逻辑。
3. 保持 stdin/stdout 简单且高效。

写作风格: 每行关键操作附带中文注释，解释"做了什么"和"为什么这样做"。
"""

# ============================================================
# 常用标准库导入
# ============================================================
# 双端队列：BFS 专用，队首弹出 O(1) 远快于普通列表 pop(0)
from collections import Counter, defaultdict, deque
# 最小堆：Dijkstra、TopK 等场景
from heapq import heappop, heappush
# 二分查找：bisect_left / bisect_right 替代手写二分
import bisect
# 数学函数：gcd、sqrt、ceil、floor、inf 等
import math
# 快速 I/O：stdin.buffer 比 input() 快数倍
import sys


# ============================================================
# 快速输入函数
# ============================================================

def read_all() -> str:
    """一次性读取全部 stdin 内容并解码为字符串。适用于整文件读入后 split 处理。"""
    return sys.stdin.buffer.read().decode()


def read_ints() -> list[int]:
    """读取一行输入，按空白字符分割后转为 int 列表。
    适用于：一行中有多个空格分隔的整数。
    示例: "3 1 4 1 5"  ->  [3, 1, 4, 1, 5]
    """
    return list(map(int, sys.stdin.buffer.readline().split()))


def ints_from_stdin() -> list[int]:
    """读取全部 stdin 内容，按空白字符分割后转为 int 列表。
    适用于：行数未知、或一次性读入所有数字更方便的场景。
    示例: "3\n1 2\n3 4 5"  ->  [3, 1, 2, 3, 4, 5]
    """
    return list(map(int, sys.stdin.buffer.read().split()))


# ============================================================
# 二分查找工具
# ============================================================

def lower_bound(a: list, x) -> int:
    """在有序数组 a 中找第一个 >= x 的元素下标（C++ lower_bound 等价）。
    返回值范围 [0, len(a)]。所有元素 < x 时返回 len(a)。
    时间复杂度 O(log n)。
    """
    l, r = 0, len(a)
    while l < r:
        m = (l + r) // 2
        if a[m] >= x:
            r = m       # a[m] 满足条件，记录答案，继续向左搜索更小的可行位置
        else:
            l = m + 1   # a[m] 不满足，排除左半部分
    return l


def upper_bound(a: list, x) -> int:
    """在有序数组 a 中找第一个 > x 的元素下标（C++ upper_bound 等价）。
    返回值范围 [0, len(a)]。
    可用于计算 x 出现次数: upper_bound(a, x) - lower_bound(a, x)
    时间复杂度 O(log n)。
    """
    l, r = 0, len(a)
    while l < r:
        m = (l + r) // 2
        if a[m] > x:
            r = m       # a[m] 满足条件，继续向左搜索
        else:
            l = m + 1   # a[m] <= x，排除左半部分
    return l


def binary_search_answer(lo: int, hi: int, check) -> int:
    """二分答案法：在 [lo, hi] 中找到第一个使 check(x) 为 True 的 x。
    要求 check(x) 单调: False, False, ..., True, True, ...
    最小化问题直接使用；最大化问题取反 check 条件即可。
    时间复杂度 O(log(hi - lo) * check时间)。
    """
    while lo < hi:
        mid = (lo + hi) // 2
        if check(mid):
            hi = mid       # mid 可行，尝试更小的值
        else:
            lo = mid + 1   # mid 不可行，需要更大的值
    return lo


# ============================================================
# 前缀和
# ============================================================

def prefix_sums(nums: list) -> list:
    """计算前缀和数组。pre[i] = nums[0] + ... + nums[i-1]，pre[0] = 0。
    返回长度 len(nums)+1 的数组，配合 range_sum() 实现 O(1) 子数组求和。
    示例: prefix_sums([1,3,5]) -> [0, 1, 4, 9]
    """
    pre = [0]
    for x in nums:
        pre.append(pre[-1] + x)
    return pre


def range_sum(pre: list, l: int, r: int) -> int:
    """基于前缀和数组 pre，计算 nums[l] + ... + nums[r-1]（左闭右开）。
    时间复杂度 O(1)。
    """
    return pre[r] - pre[l]


# ============================================================
# 滑动窗口
# ============================================================

def sliding_window_max_len(nums: list, limit: int) -> int:
    """滑动窗口模板：求满足条件的最长子数组长度。
    本例条件: 子数组元素之和 <= limit。
    修改 while 循环中的收缩条件和 cur 更新方式即可适配其他题型。
    时间复杂度 O(n)，每个元素最多进出窗口各一次。

    常见变体:
      - 子数组和 >= limit: 改 while 条件为 cur >= limit 时收缩
      - 子数组不同元素数 <= k: 用 Counter 维护窗口内元素种类
      - 子数组最大值-最小值 <= limit: 用单调队列
    """
    left = 0        # 窗口左边界
    cur = 0         # 当前窗口内的度量值（此处为元素之和）
    ans = 0         # 记录最优答案
    for right, x in enumerate(nums):
        cur += x    # 右端元素加入窗口
        # 当窗口不满足条件时，收缩左边界
        while left <= right and cur > limit:
            cur -= nums[left]   # 左端元素移出窗口
            left += 1
        # 此时窗口 [left, right] 满足条件，更新最优解
        ans = max(ans, right - left + 1)
    return ans


# ============================================================
# 图论 / 网格 BFS / DFS
# ============================================================

# 四方向移动: 下、上、右、左（行偏移, 列偏移）
# x=行, y=列；dx 改变行，dy 改变列
DIR4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]
# 八方向: 在四方向基础上加四个对角线方向
DIR8 = DIR4 + [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def bfs_grid(grid: list, starts: list) -> list:
    """网格多源 BFS：从多个起点同时扩展，求每个格子到最近起点的距离。
    参数:
      grid:   二维网格，list[str] 或 list[list]，例如 ["..#.", ".#..", "...."]
      starts: 起点坐标列表，例如 [(0,0), (2,3)]
    返回:
      dist: 二维距离矩阵，dist[r][c] = 从最近起点到 (r,c) 的最少步数
            -1 表示不可达
    时间复杂度 O(n*m)，每个格子最多入队一次。

    典型应用: 多源最短路径、腐烂的橘子(LeetCode 994)、到最近目标的距离
    """
    if not grid:
        return []
    n, m = len(grid), len(grid[0])
    dist = [[-1] * m for _ in range(n)]  # -1 = 未访问标记，同时存储最短步数
    q = deque()
    # 将所有起点加入队列，距离初始化为 0
    for r, c in starts:
        if 0 <= r < n and 0 <= c < m and dist[r][c] == -1:
            dist[r][c] = 0
            q.append((r, c))

    # 标准 BFS 扩展：队列不为空则持续遍历
    while q:
        r, c = q.popleft()  # 弹出队首（当前正在处理的格子）
        for dr, dc in DIR4:
            nr, nc = r + dr, c + dc  # 计算相邻格子坐标
            # 四条件同时满足才通行: ①不越上下边界 ②不越左右边界 ③未被访问过
            if 0 <= nr < n and 0 <= nc < m and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1  # 步数 = 当前步数 + 1
                q.append((nr, nc))              # 新坐标入队，等待下一轮遍历
    return dist


def dfs_iterative(graph: list, start: int) -> set:
    """迭代式 DFS（非递归，规避 Python 递归深度限制）。
    参数:
      graph: 邻接表，list[list[int]] 或 dict[int, list[int]]
      start: 起始节点编号
    返回:
      seen: 从 start 可达的所有节点集合
    时间复杂度 O(V + E)。

    典型应用: 连通分量遍历、可达性判断、拓扑排序(需修改为记录出栈顺序)
    """
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()  # 弹出栈顶（LIFO：深度优先）
        for v in graph[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


# ============================================================
# 并查集 (DSU / Union-Find)
# ============================================================

class DSU:
    """并查集：高效维护不相交集合的合并与查询。
    支持 find(x) 查找代表元素（带路径压缩）和 union(a,b) 合并集合（按大小启发式）。
    时间复杂度近似 O(α(n))，α 为反阿克曼函数，实际视为常数。

    典型应用: 图的连通性、Kruskal MST、动态连通、等价类合并

    使用示例:
      dsu = DSU(10)           # 初始化 10 个独立元素 (0~9)
      dsu.union(1, 2)         # 合并 1 和 2
      dsu.find(1) == dsu.find(2)  # True
      dsu.union(2, 3)         # 合并后 1,2,3,4 同集合
    """

    def __init__(self, n: int):
        """初始化 n 个元素，每个元素初始时是自己的父节点（独立集合）。"""
        self.parent = list(range(n))  # parent[i] = i 的父节点
        self.size = [1] * n           # size[i] = 以 i 为代表元素的集合大小

    def find(self, x: int) -> int:
        """查找 x 所属集合的代表元素（根节点）。
        路径压缩（隔代压缩）: 将 x 直接指向祖父节点，加速后续查询。
        """
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # 路径压缩：指向祖父
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """合并 a 和 b 所在的集合。按大小启发式：小树挂到大树。
        返回 True = 成功合并（原本不在同一集合），False = 已在同一集合。
        """
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False           # 已在同一集合，无需合并
        # 按大小合并：确保 ra 是较大集合的根
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra       # 小树 rb 挂到大树 ra 下
        self.size[ra] += self.size[rb]
        return True


# ============================================================
# 堆（优先队列）
# ============================================================

def top_k_largest(nums: list, k: int) -> list:
    """使用最小堆找出 nums 中最大的 k 个元素。
    维护一个大小为 k 的最小堆: 堆不满直接插入；堆满且 x > 堆顶时替换。
    最终堆中即最大的 k 个元素。
    时间复杂度 O(n log k)，空间复杂度 O(k)。
    返回从大到小排序的 k 个元素列表。
    """
    heap = []
    for x in nums:
        if len(heap) < k:
            heappush(heap, x)
        elif x > heap[0]:
            heappop(heap)
            heappush(heap, x)
    return sorted(heap, reverse=True)


# ============================================================
# 最短路径 - Dijkstra 算法
# ============================================================

def dijkstra(graph: list, start: int) -> list:
    """Dijkstra 单源最短路径（仅适用于非负权边）。
    参数:
      graph: 邻接表，graph[u] = [(v, weight), ...]，u->v 边权为 weight
      start: 起始节点编号
    返回:
      dist: 距离数组，dist[i] = start 到 i 的最短距离，不可达为 inf
    时间复杂度 O((V + E) log V)，使用二叉堆优化。

    注意: 边权必须 >= 0（有负权边请用 Bellman-Ford 或 SPFA）
    """
    n = len(graph)
    inf = 10**30                      # 足够大的数表示无穷远
    dist = [inf] * n
    dist[start] = 0
    heap = [(0, start)]               # (当前距离, 节点编号)
    while heap:
        d, u = heappop(heap)
        if d != dist[u]:
            continue                  # 跳过已过时的松弛记录（懒删除）
        for v, w in graph[u]:
            nd = d + w                # 经过 u 到达 v 的距离
            if nd < dist[v]:
                dist[v] = nd          # 松弛成功，更新最短距离
                heappush(heap, (nd, v))
    return dist


# ============================================================
# 主函数入口
# ============================================================

def solve():
    """
    替换为题目逻辑。

    常见输入格式:

    格式1 - 先读 n，再读数组:
        n = int(sys.stdin.buffer.readline())
        nums = read_ints()

    格式2 - 多组测试用例:
        t = int(sys.stdin.buffer.readline())
        out = []
        for _ in range(t):
            n, m = read_ints()
            # ... 处理每组数据 ...
            out.append(result)
        sys.stdout.write("\\n".join(map(str, out)))

    格式3 - 读入全部数据后处理:
        data = ints_from_stdin()
        n = data[0]
        nums = data[1:]
    """
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    # 示例占位代码: 输出读入的整数个数（实际提交时删除）
    nums = list(map(int, data))
    print(len(nums))


if __name__ == "__main__":
    solve()
