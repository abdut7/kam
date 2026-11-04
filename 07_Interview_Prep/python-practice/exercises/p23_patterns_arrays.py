"""Lesson 23: coding patterns for arrays, strings and hashing.

Implement each function, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p23_patterns_arrays.py
"""


def two_sum(nums: list[int], target: int) -> list[int]:
    """Return [i, j] with i < j and nums[i] + nums[j] == target, or [] if no pair exists.

    Pattern: hash map of value -> index, one pass. Assume at most one valid answer.
    Example: two_sum([2, 7, 11, 15], 9) == [0, 1]
    """
    raise NotImplementedError


def group_anagrams(words: list[str]) -> list[list[str]]:
    """Group words that are anagrams of each other.

    Groups appear in the order their first word appears; words keep input order inside a group.
    Pattern: dict (defaultdict(list)) keyed by a signature of the word.
    Example: group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
             == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]
    """
    raise NotImplementedError


def length_of_longest_substring(s: str) -> int:
    """Return the length of the longest substring of s with no repeated character.

    Pattern: variable sliding window plus a dict of last-seen positions.
    Example: length_of_longest_substring("abcabcbb") == 3  ("abc")
    """
    raise NotImplementedError


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequent values, most frequent first.

    If k is larger than the number of distinct values, return all of them.
    When counts tie, any order among the tied values is accepted.
    Pattern: Counter plus heapq.nlargest (or bucket sort for O(n)).
    Example: top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]
    """
    raise NotImplementedError


def product_except_self(nums: list[int]) -> list[int]:
    """Return a list where item i is the product of every value except nums[i].

    Do not use division (zeros make it wrong). Pattern: prefix and suffix products.
    Example: product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    """
    raise NotImplementedError


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping [start, end] intervals and return them sorted by start.

    Intervals that touch ([1, 4] and [4, 5]) count as overlapping.
    Do not modify the caller's lists. Pattern: sort with key, then one linear pass.
    Example: merge_intervals([[1, 3], [8, 10], [2, 6]]) == [[1, 6], [8, 10]]
    """
    raise NotImplementedError
