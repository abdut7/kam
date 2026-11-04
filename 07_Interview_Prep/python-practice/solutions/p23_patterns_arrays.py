"""Lesson 23 reference solutions: arrays, strings and hashing patterns."""
import heapq
from collections import Counter, defaultdict


def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}  # value -> index where we saw it
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:  # check BEFORE storing x, so x never pairs with itself
            return [seen[need], i]
        seen[x] = i
    return []
    # Time O(n), space O(n).


def group_anagrams(words: list[str]) -> list[list[str]]:
    groups: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    for w in words:
        # Sorted letters as a tuple: hashable, equal for every anagram.
        groups[tuple(sorted(w))].append(w)
    # dicts keep insertion order, so groups come out in first-seen order.
    return list(groups.values())
    # Time O(n * L log L) for n words of length L, space O(n * L).


def length_of_longest_substring(s: str) -> int:
    last_seen: dict[str, int] = {}  # char -> last index
    left = best = 0
    for right, ch in enumerate(s):
        # Only jump left forward. Without the >= check, "abba" moves left backwards.
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best
    # Time O(n), space O(min(n, alphabet size)).


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    # nlargest keeps a heap of size k: O(n log k) instead of sorting all distinct values.
    return heapq.nlargest(k, counts, key=counts.__getitem__)
    # Equivalent: [x for x, _ in counts.most_common(k)]


def product_except_self(nums: list[int]) -> list[int]:
    n = len(nums)
    out = [1] * n
    prefix = 1
    for i in range(n):  # out[i] = product of everything left of i
        out[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in reversed(range(n)):  # multiply in everything right of i
        out[i] *= suffix
        suffix *= nums[i]
    return out
    # Time O(n), extra space O(1) besides the output list.


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])  # a NEW list, never the caller's list
    return merged
    # Time O(n log n) for the sort, space O(n) for the output.
