"""
滑动窗口 + 频率计数 练习题
"""
import sys


# ============================================================
# 可匹配子段计数（滑动窗口 + 频率计数）
# 模式：滑动窗口 + 哈希映射 | I/O：多组测试用例
# ============================================================

def solve_matchable_subarray():
    """
    输入格式：
        第一行：t（测试用例组数）
        每组：一行 n m k；一行 a 数组；一行 b 数组
    输出格式：
        每组输出一行：满足条件的子段数量

    核心思路：
        match(c) = Σ_x min(cnt_x(c), cnt_x(b))
        窗口滑出 v 时：若 cnt_a[v] == cnt_b[v]，match -= 1
        窗口滑入 v 时：若 cnt_a[v] == cnt_b[v] - 1，match += 1
    """
    input = sys.stdin.readline

    t = int(input())
    out = []

    for _ in range(t):
        n, m, k = map(int, input().split())
        a = list(map(int, input().split()))
        b = list(map(int, input().split()))

        # ============================================================
        # Preprocess：统计 b 的频率，初始化第一个窗口的频率和匹配度
        # ============================================================
        cnt_b = {}
        for v in b:
            cnt_b[v] = cnt_b.get(v, 0) + 1

        cnt_a = {}                        # 窗口 [0, m-1] 的频率
        match = 0                         # 当前匹配度 Σ min(cnt_a[x], cnt_b[x])
        for v in a[:m]:
            cnt_a[v] = cnt_a.get(v, 0) + 1
            if v in cnt_b and cnt_a[v] <= cnt_b[v]:
                match += 1

        # ============================================================
        # Algorithm：滑动窗口，O(1) 增量更新匹配度
        # ============================================================
        ans = 1 if match >= k else 0      # 检查初始窗口

        for i in range(m, n):
            out_v = a[i - m]              # 滑出的元素
            in_v = a[i]                   # 滑入的元素

            # 滑出 out_v：先判断再减 [防错] 必须在减计数前判断
            if out_v in cnt_b and cnt_a[out_v] == cnt_b[out_v]:
                match -= 1               # [防错] 相等时减说明 min 刚好从 cnt_b 降到 cnt_b-1
            cnt_a[out_v] -= 1

            # 滑入 in_v：先加再判断 [防错] 必须在加计数后判断
            cnt_a[in_v] = cnt_a.get(in_v, 0) + 1
            if in_v in cnt_b and cnt_a[in_v] == cnt_b[in_v]:
                match += 1               # [防错] 相等时加说明 min 刚好从 cnt_b-1 升到 cnt_b

            if match >= k:
                ans += 1

        out.append(str(ans))

    # ============================================================
    # Output
    # ============================================================
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve_matchable_subarray()
