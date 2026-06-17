# 导入系统模块，用于读取控制台输入
import sys
# 导入双端队列，BFS算法专用，队首弹出效率远高于普通列表
from collections import deque

# 定义四个移动方向：下、上、右、左 (行偏移, 列偏移)
# x 代表行，y 代表列；dx 改变行，dy 改变列
DIR4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def solve():
    """
    迷宫最短路径求解（BFS广度优先搜索）
    输入规则：
        第一行：两个整数 n m，分别代表迷宫的行数、列数
        第二行：四个整数 xs ys xt yt，代表起点、终点坐标（题目为 1 开始编号）
        后续 n 行：迷宫地图，. 代表可通行道路，# 代表墙壁
    输出规则：
        输出起点到终点的最短步数，无法到达则输出 -1
    """
    # 读取第一行输入，拆分并转为整数，获取迷宫行数n、列数m
    n, m = map(int, sys.stdin.readline().split())

    # 读取第二行输入，获取起点坐标(xs, ys)、终点坐标(xt, yt)
    xs, ys, xt, yt = map(int, sys.stdin.readline().split())

    # 坐标转换：题目是 1 起始坐标，Python列表是 0 起始索引，统一减1对齐
    xs -= 1
    ys -= 1
    xt -= 1
    yt -= 1

    # 初始化迷宫列表，存储整张地图
    grid = []
    # 循环读取 n 行迷宫数据
    for _ in range(n):
        # 读取一行内容，并去除首尾空格、换行符
        line = sys.stdin.readline().strip()
        # 将字符串转为字符列表，存入迷宫，方便后续按索引访问每个格子
        grid.append(list(line))

    # 步数记录数组：dist[x][y] 表示从起点走到 (x,y) 的最短步数
    # 初始值设为 -1，同时充当「未访问标记」，-1 = 该格子还未被遍历
    dist = [[-1] * m for _ in range(n)]

    # 创建BFS队列，存入待遍历的坐标，初始把起点入队
    q = deque([(xs, ys)])
    # 起点到自身的步数为 0
    dist[xs][ys] = 0

    # BFS主循环：队列不为空则持续遍历
    while q:
        # 弹出队首元素（当前正在处理的格子坐标）
        x, y = q.popleft()

        # 终止条件：当前坐标 == 终点坐标，输出最短步数并结束函数
        if x == xt and y == yt:
            print(dist[x][y])
            return

        # 遍历四个移动方向，探索相邻格子
        for dx, dy in DIR4:
            # 计算相邻格子的行、列坐标
            nx = x + dx
            ny = y + dy

            # 合法性判断（同时满足4个条件才可以通行）：
            # 1. 行坐标在合法范围 0~n-1 内（不越上下边界）
            # 2. 列坐标在合法范围 0~m-1 内（不越左右边界）
            # 3. 当前格子不是墙壁（. 代表可走）
            # 4. 该格子从未被访问（dist=-1），避免重复入队
            if 0 <= nx < n and 0 <= ny < m and grid[nx][ny] == "." and dist[nx][ny] == -1:
                # 新格子步数 = 当前格子步数 + 1
                dist[nx][ny] = dist[x][y] + 1
                # 将合法的新坐标加入队列，等待下一轮遍历
                q.append((nx, ny))

    # 队列遍历完毕仍未找到终点，说明终点被墙壁阻挡、无法到达
    print(-1)


# 程序入口：当前文件直接运行时，执行solve函数
if __name__ == "__main__":
    solve()