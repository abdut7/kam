from practice_target import load

m = load("p23_patterns_arrays")


def test_two_sum_basic():
    assert m.two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert m.two_sum([3, 2, 4], 6) == [1, 2]  # must not use index 0 twice


def test_two_sum_duplicates_and_negatives():
    assert m.two_sum([3, 3], 6) == [0, 1]
    assert m.two_sum([-1, -2, -3, -4, -5], -8) == [2, 4]


def test_two_sum_edge_cases():
    assert m.two_sum([], 5) == []
    assert m.two_sum([5], 10) == []
    assert m.two_sum([1, 2, 3], 100) == []


def test_group_anagrams_basic():
    words = ["eat", "tea", "tan", "ate", "nat", "bat"]
    assert m.group_anagrams(words) == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]


def test_group_anagrams_edge_cases():
    assert m.group_anagrams([]) == []
    assert m.group_anagrams([""]) == [[""]]
    assert m.group_anagrams(["a"]) == [["a"]]
    assert m.group_anagrams(["ab", "ba", "ab"]) == [["ab", "ba", "ab"]]  # duplicates kept


def test_group_anagrams_letter_counts_matter():
    # Same letters, different counts: not anagrams.
    assert m.group_anagrams(["aab", "abb"]) == [["aab"], ["abb"]]


def test_longest_substring_basic():
    assert m.length_of_longest_substring("abcabcbb") == 3
    assert m.length_of_longest_substring("pwwkew") == 3


def test_longest_substring_edge_cases():
    assert m.length_of_longest_substring("") == 0
    assert m.length_of_longest_substring("a") == 1
    assert m.length_of_longest_substring("bbbbb") == 1
    assert m.length_of_longest_substring(" ") == 1


def test_longest_substring_left_never_moves_back():
    assert m.length_of_longest_substring("abba") == 2
    assert m.length_of_longest_substring("tmmzuxt") == 5


def test_top_k_frequent_basic():
    assert m.top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2]
    assert m.top_k_frequent([4, 4, 4, 4, 5, 5, 5, 6, 6, 7], 3) == [4, 5, 6]


def test_top_k_frequent_edge_cases():
    assert m.top_k_frequent([], 3) == []
    assert m.top_k_frequent([9], 1) == [9]
    assert m.top_k_frequent([1, 2, 3], 0) == []


def test_top_k_frequent_ties_and_large_k():
    assert sorted(m.top_k_frequent([1, 2, 3, 3], 5)) == [1, 2, 3]
    result = m.top_k_frequent([5, 5, 6, 6, 7], 2)
    assert sorted(result) == [5, 6]  # 5 and 6 tie, either order is fine


def test_product_except_self_basic():
    assert m.product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert m.product_except_self([2, 2, 2]) == [4, 4, 4]


def test_product_except_self_zeros():
    assert m.product_except_self([1, 0, 3]) == [0, 3, 0]
    assert m.product_except_self([0, 0]) == [0, 0]
    assert m.product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]


def test_product_except_self_edge_cases():
    assert m.product_except_self([]) == []
    assert m.product_except_self([5]) == [1]


def test_merge_intervals_basic():
    assert m.merge_intervals([[1, 3], [8, 10], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert m.merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]  # touching intervals merge
    assert m.merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]  # nested


def test_merge_intervals_edge_cases():
    assert m.merge_intervals([]) == []
    assert m.merge_intervals([[5, 7]]) == [[5, 7]]
    assert m.merge_intervals([[1, 3], [1, 3]]) == [[1, 3]]  # duplicates


def test_merge_intervals_does_not_mutate_input():
    data = [[1, 3], [2, 6], [8, 10]]
    m.merge_intervals(data)
    assert data == [[1, 3], [2, 6], [8, 10]]
