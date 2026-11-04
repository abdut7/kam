"""Lesson 24 reference solutions: stacks, queues, trees, graphs and heaps."""
import heapq
from collections import deque
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class TreeNode:
    """Binary tree node (provided, not an exercise)."""

    val: int
    left: "TreeNode | None" = None
    right: "TreeNode | None" = None


def is_valid_parentheses(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}  # closer -> opener
    stack: list[str] = []
    for ch in s:
        if ch in pairs:
            # Empty stack or wrong opener on top: invalid. Check emptiness before stack[-1].
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack  # leftover openers like "((" are invalid
    # Time O(n), space O(n).


def daily_temperatures(temps: list[int]) -> list[int]:
    answer = [0] * len(temps)
    stack: list[int] = []  # indices of days still waiting; their temps are non-increasing
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:  # strictly warmer resolves the waiting day
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer
    # Each index is pushed and popped at most once: time O(n), space O(n).


def kth_largest(nums: list[int], k: int) -> int:
    if not 1 <= k <= len(nums):
        raise ValueError(f"k must be between 1 and {len(nums)}, got {k}")
    heap: list[int] = []  # min-heap holding the k largest values seen so far
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)  # pop the smallest, push x, one O(log k) step
    return heap[0]
    # Time O(n log k), space O(k). One-liner: heapq.nlargest(k, nums)[-1]


def level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    levels: list[list[int]] = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):  # len is read once: exactly the nodes of this level
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        levels.append(level)
    return levels
    # Time O(n), space O(width of the widest level).


def num_islands(grid: list[list[int]]) -> int:
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            islands += 1
            seen.add((r, c))  # mark when enqueued, not when dequeued
            queue = deque([(r, c)])
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return islands
    # Time O(rows * cols), space O(rows * cols) for the visited set.


def course_order(num_courses: int, prerequisites: list[tuple[int, int]]) -> list[int] | None:
    graph: list[list[int]] = [[] for _ in range(num_courses)]  # prereq -> courses it unlocks
    indegree = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        indegree[course] += 1
    queue = deque(c for c in range(num_courses) if indegree[c] == 0)
    order: list[int] = []
    while queue:
        c = queue.popleft()
        order.append(c)
        for nxt in graph[c]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    # Courses stuck in a cycle never reach indegree 0, so they are missing from order.
    return order if len(order) == num_courses else None
    # Time O(V + E), space O(V + E).


def coin_change(coins: list[int], amount: int) -> int:
    coin_values = tuple(set(coins))  # duplicates in coins change nothing

    @lru_cache(maxsize=None)  # cache lives inside this call, so it never leaks between calls
    def fewest(remaining: int) -> float:
        if remaining == 0:
            return 0
        best = float("inf")
        for c in coin_values:
            if c <= remaining:
                best = min(best, fewest(remaining - c) + 1)
        return best

    result = fewest(amount)
    return -1 if result == float("inf") else int(result)
    # Time O(amount * len(coins)), space O(amount) for the cache and the call stack.
    # Recursion depth is up to amount / smallest coin, so for very large amounts
    # use the bottom-up table instead:
    #   dp = [0] + [inf] * amount
    #   for a in range(1, amount + 1):
    #       dp[a] = min((dp[a - c] + 1 for c in coins if c <= a), default=inf)
