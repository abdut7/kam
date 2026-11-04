## Coding Patterns: Arrays, Strings & Hashing [Core]

> This section moves the biggest family of coding-round problems, arrays, strings and hash maps, into Python: the patterns (hash map lookup, two pointers, sliding window, prefix sums, sort then scan, binary search) and the standard-library tools that make each one short. The same moves show up in real FastAPI and AI backend code: deduplicating retrieved chunks by id with a set, counting labels or tokens with Counter, a sliding-window rate limiter, prefix sums over usage records for billing, bisect over sorted timestamps, and merging overlapping time ranges in a calendar or transcript feature. Most interviewers let you pick the language, and Python lets you spend the time on the idea instead of the boilerplate.

### Why it exists
Coding rounds test one skill above all: seeing that a brute-force O(n^2) scan can become O(n) or O(n log n) with the right pattern. The patterns are the same in every language, but Python ships the data structures as built-ins (dict, set, Counter, defaultdict, bisect, heapq, sorted with a key), so a solution is often half the length of the JavaScript version and has fewer index bugs. The cost is that short code can hide slow operations: `x in some_list` is O(n), slicing copies, and `list.pop(0)` shifts every element, so you must know what each call costs or your "one-liner" is quietly quadratic.

### In plain words
Think of a toolbox with a few labelled drawers. Most array and string problems ask one of four questions: "have I seen this before?" (a hash map or set), "can I squeeze in from both ends?" (two pointers), "what is inside this moving frame?" (a sliding window), or "what is the running total so far?" (prefix sums). Sorting first and binary search are a fifth drawer, for anything where order matters. Python has a ready-made tool in every drawer, so in the interview your job is picking the drawer, not building the tool.

### Walkthrough: Hash maps, sets and counting
1. **dict is your hash map**: average O(1) insert and lookup, and it keeps insertion order (guaranteed since 3.7). `in` checks keys, and `.get(k, default)` reads without raising KeyError. It replaces both the plain object and `Map` from JavaScript.

   ```python
   seen = {}                        # value -> first index
   for i, x in enumerate([4, 7, 4]):
       if x in seen:
           print("duplicate", x, "first at", seen[x])   # duplicate 4 first at 0
       else:
           seen[x] = i
   print(seen.get(99, -1))          # -1, no KeyError
   ```

2. **Keys must be hashable**: str, int, float, tuple and frozenset work; list, dict and set raise `TypeError: unhashable type: 'list'`. For a composite key use a tuple. In JavaScript a `Map` keys arrays by reference, so you would join them into a string; Python tuples hash and compare by value, so `(row, col)` is a perfect grid key.

   ```python
   visited = {(0, 1), (2, 3)}       # tuples hash by value
   print((0, 1) in visited)         # True
   print(tuple(sorted("tea")))      # ('a', 'e', 't'), same for "eat" and "ate"
   ```

3. **set for membership and dedup**: `in` on a set is O(1) on average, on a list it is O(n). Sets support `&` (intersection), `|` (union) and `-` (difference). Sets are unordered, so to dedupe while keeping order use `dict.fromkeys`.

   ```python
   ids = [3, 1, 3, 2, 1]
   print(len(set(ids)) != len(ids))     # True: there is a duplicate
   print(list(dict.fromkeys(ids)))      # [3, 1, 2], first-seen order kept
   a, b = {1, 2, 3}, {2, 3, 4}
   print(a & b, a | b, a - b)           # {2, 3} {1, 2, 3, 4} {1}
   ```

4. **Counter counts in one line**: `collections.Counter` is a dict subclass for counting. A missing key reads as 0 and is not inserted, `.most_common(k)` returns the top k pairs, and two Counters compare equal when every count matches, which is a one-line anagram check.

   ```python
   from collections import Counter
   c = Counter("banana")
   print(c)                         # Counter({'a': 3, 'n': 2, 'b': 1})
   print(c.most_common(2))          # [('a', 3), ('n', 2)]
   print(c["z"], "z" in c)          # 0 False
   print(Counter("listen") == Counter("silent"))   # True
   ```

5. **defaultdict for grouping**: `defaultdict(list)` creates an empty list the first time a key is touched, `defaultdict(int)` starts counts at 0. The trap: any `d[key]` read on a missing key inserts it, so test membership with `in` or `.get`, never by indexing.

   ```python
   from collections import defaultdict
   by_len = defaultdict(list)
   for w in ["hi", "yo", "hey"]:
       by_len[len(w)].append(w)     # no "if key not in d" boilerplate
   print(dict(by_len))              # {2: ['hi', 'yo'], 3: ['hey']}
   by_len[99]                       # only a read, but it inserts 99: []
   print(99 in by_len)              # True
   ```

### Walkthrough: Two pointers, sliding window and prefix sums
1. **Two pointers from both ends (sorted input)**: Python has no C-style `for (;;)` loop, so two moving indexes live in a `while`. Because the list is sorted, a sum that is too small can only grow by moving the left pointer, and one that is too big can only shrink by moving the right one. O(n) time, O(1) space.

   ```python
   def pair_sum_sorted(a: list[int], target: int) -> tuple[int, int] | None:
       i, j = 0, len(a) - 1
       while i < j:
           s = a[i] + a[j]
           if s == target:
               return i, j
           if s < target:
               i += 1                   # need a bigger sum
           else:
               j -= 1                   # need a smaller sum
       return None

   print(pair_sum_sorted([1, 3, 4, 6, 9], 10))   # (0, 4)
   ```

2. **Two pointers for palindromes and reversal**: `s == s[::-1]` is correct and readable but builds a reversed copy; the pointer version stops at the first mismatch. Tuple assignment moves both pointers (or swaps two items, `a[i], a[j] = a[j], a[i]`) without a temp variable, like JS destructuring.

   ```python
   def is_palindrome(s: str) -> bool:
       chars = [ch.lower() for ch in s if ch.isalnum()]
       i, j = 0, len(chars) - 1
       while i < j:
           if chars[i] != chars[j]:
               return False
           i, j = i + 1, j - 1
       return True

   print(is_palindrome("A man, a plan, a canal: Panama"))   # True
   ```

3. **Read and write pointers (in place)**: one pointer reads every item, the other marks where the next kept item goes. This is how you dedupe or filter a list in place with O(1) extra space.

   ```python
   def dedupe_sorted(a: list[int]) -> int:
       write = 0
       for read in range(len(a)):
           if read == 0 or a[read] != a[read - 1]:
               a[write] = a[read]
               write += 1
       return write                     # a[:write] holds the unique values

   nums = [1, 1, 2, 3, 3]
   k = dedupe_sorted(nums)
   print(nums[:k])                      # [1, 2, 3]
   ```

4. **Fixed-size window**: compute the first window once, then slide it by adding the item that enters and subtracting the item that leaves. The trap is writing `sum(nums[i:i + k])` inside the loop: the slice copies k items every step, so the "O(n)" loop is really O(n * k).

   ```python
   def max_window_sum(nums: list[int], k: int) -> int | None:
       if not 0 < k <= len(nums):
           return None
       window = best = sum(nums[:k])
       for i in range(k, len(nums)):
           window += nums[i] - nums[i - k]     # one in, one out
           best = max(best, window)
       return best

   print(max_window_sum([2, 1, 5, 1, 3, 2], 3))   # 9 (5 + 1 + 3)
   ```

5. **Variable-size window**: a `for` loop moves the right edge every step; an inner `while` moves the left edge to shrink the window. Each index enters and leaves once, so the nested loops are still O(n). This version relies on all values being positive (shrinking always lowers the sum); with negative numbers, use prefix sums instead.

   ```python
   def min_len_at_least(nums: list[int], target: int) -> int:
       left = total = 0
       best = float("inf")
       for right, x in enumerate(nums):
           total += x                          # grow to the right
           while total >= target:              # valid: record it, then shrink from the left
               best = min(best, right - left + 1)
               total -= nums[left]
               left += 1
       return 0 if best == float("inf") else best

   print(min_len_at_least([2, 3, 1, 2, 4, 3], 7))   # 2, the window [4, 3]
   ```

6. **Prefix sums**: `p[i]` is the sum of the first i items, so any range sum is `p[j] - p[i]` in O(1). `itertools.accumulate(nums, initial=0)` builds it (the `initial` argument needs 3.8+). Combined with a Counter of earlier prefixes, it counts subarrays that sum to k, and it works with negative numbers where a sliding window cannot.

   ```python
   from collections import Counter
   from itertools import accumulate

   nums = [3, 1, 4, 1, 5]
   p = list(accumulate(nums, initial=0))   # [0, 3, 4, 8, 9, 14]
   print(p[4] - p[1])                      # 6, the sum of nums[1:4]

   def count_subarrays_sum(nums: list[int], k: int) -> int:
       seen = Counter({0: 1})              # the empty prefix
       total = count = 0
       for x in nums:
           total += x
           count += seen[total - k]        # earlier prefixes that leave exactly k
           seen[total] += 1
       return count

   print(count_subarrays_sum([1, -1, 1, 1], 1))   # 5
   ```

### Walkthrough: Sorting with key, binary search and the time-saving built-ins
1. **sorted() returns a new list, .sort() returns None**: the classic bug is `nums = nums.sort()`, which leaves `nums` as None. Python compares numbers numerically by default, while JavaScript's `[10, 9, 1].sort()` returns `[1, 10, 9]` because it compares strings. Both Python sorts are Timsort: stable and O(n log n).

   ```python
   nums = [10, 9, 1]
   print(sorted(nums), nums)        # [1, 9, 10] [10, 9, 1]
   result = nums.sort()
   print(result, nums)              # None [1, 9, 10]
   ```

2. **A key function instead of a comparator**: Python's sort takes `key=`, a function called once per item, instead of a `(a, b)` comparator. A tuple key sorts by several fields in order, and negating a number flips one field to descending. `reverse=True` flips the whole sort, and `functools.cmp_to_key` exists for the rare pairwise rule.

   ```python
   users = [("ana", 31), ("bo", 25), ("cy", 31)]
   print(sorted(users, key=lambda u: u[1]))
   # [('bo', 25), ('ana', 31), ('cy', 31)]: stable, ties keep input order
   print(sorted(users, key=lambda u: (-u[1], u[0])))
   # [('ana', 31), ('cy', 31), ('bo', 25)]: age descending, then name
   print(sorted(["bb", "a", "ccc"], key=len, reverse=True))   # ['ccc', 'bb', 'a']
   ```

   The JavaScript equivalent of the second sort is `users.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))`.

3. **bisect for sorted lists**: `bisect_left(a, x)` is the first index whose value is at least x, `bisect_right(a, x)` the first index whose value is greater than x. Their difference counts occurrences, and `insort` inserts while keeping order (O(log n) to find the spot, O(n) to shift). The `key=` argument needs 3.10+.

   ```python
   from bisect import bisect_left, bisect_right, insort
   a = [1, 3, 3, 3, 7, 9]
   print(bisect_left(a, 3), bisect_right(a, 3))    # 1 4
   print(bisect_right(a, 7) - bisect_left(a, 3))   # 4 values in [3, 7]
   i = bisect_left(a, 5)
   print(i < len(a) and a[i] == 5)                 # False: 5 is not present
   insort(a, 5)
   print(a)                                        # [1, 3, 3, 3, 5, 7, 9]
   ```

4. **Hand-written binary search**: interviewers often ask you to write it. Use the half-open `[lo, hi)` template below, which returns the same index as `bisect_left` and never loops forever. Python ints never overflow, so `(lo + hi) // 2` is safe (Java and C++ need `lo + (hi - lo) / 2`). Replace `a[mid] < x` with any yes/no predicate and it becomes "binary search on the answer", for example the smallest capacity that ships everything in d days.

   ```python
   def lower_bound(a: list[int], x: int) -> int:
       """First index i with a[i] >= x, or len(a) if there is none."""
       lo, hi = 0, len(a)
       while lo < hi:
           mid = (lo + hi) // 2
           if a[mid] < x:
               lo = mid + 1             # the answer is right of mid
           else:
               hi = mid                 # mid itself might be the answer
       return lo

   print(lower_bound([1, 3, 3, 7], 3), lower_bound([1, 3, 3, 7], 8))   # 1 4
   ```

5. **The built-ins that save time**: these replace most hand-written loops in a coding round. `zip` stops at the shortest input (pass `strict=True`, 3.10+, to raise instead), `reversed` iterates backwards without copying, `min` and `max` take `key=` and `default=`, and `divmod` floors toward negative infinity, unlike JavaScript's `%`, which keeps the sign of the left operand.

   ```python
   import heapq
   nums = [5, 1, 8, 3]
   print(list(enumerate(nums, start=1)))           # [(1, 5), (2, 1), (3, 8), (4, 3)]
   print(list(zip("abc", [1, 2, 3])))              # [('a', 1), ('b', 2), ('c', 3)]
   print(list(reversed(nums)))                     # [3, 8, 1, 5]
   print(max(["kiwi", "fig", "banana"], key=len))  # banana
   print(min([], default=0))                       # 0 instead of ValueError
   print(sum(x * x for x in nums))                 # 99, no intermediate list
   print(divmod(17, 5), divmod(-7, 2))             # (3, 2) (-4, 1)
   print(heapq.nlargest(2, nums))                  # [8, 5], O(n log k)
   print(any(x > 7 for x in nums), all(x > 0 for x in nums))   # True True
   ```

6. **Know the hidden costs**: each of these lines is O(n) per call, so inside a loop they turn an O(n) idea into O(n^2). Build a set once for repeated membership tests, use `collections.deque` for removals at the front, and collect strings in a list and `"".join` them at the end.

   ```python
   big = list(range(100_000))
   print(99_999 in big)             # True, but it scanned the whole list
   big.pop(0)                       # shifts every remaining item
   part = big[:50_000]              # slicing copies 50,000 references
   words = ["a", "b", "c"]
   print("".join(words))            # 'abc': one pass, instead of += in a loop
   ```

### Concepts you must understand
- Read the pattern from the question: "pair, seen before, count, group" means dict or set; "sorted input, pair, palindrome" means two pointers; "contiguous subarray or substring with a condition" means a sliding window; "range sums or subarray sums with negatives" means prefix sums; "overlaps, closest, kth in order" means sort first; "find a position or the smallest valid value" means binary search.
- dict and set give average O(1) lookups only for hashable keys: use tuples (or frozenset) for composite keys, never lists.
- Counter reads a missing key as 0 without inserting it, while defaultdict inserts a default on any `d[key]` read, so test membership with `in`.
- A sliding window is only correct when moving the left edge always moves toward a valid window, which for sums means no negative numbers; otherwise use prefix sums plus a hash map.
- `sorted()` returns a new list and `.sort()` sorts in place and returns None; both are stable, which makes multi-field sorting with a tuple key reliable.
- `bisect_left` is the first index with a value at least x and `bisect_right` the first index with a value greater than x; `insort` still costs O(n) because the list shifts.
- Python ints never overflow, `//` floors toward negative infinity and `%` takes the sign of the divisor, so negative-number arithmetic differs from JavaScript.
- `x in list`, `list.pop(0)`, `list.insert(0, x)`, slicing and string `+=` in a loop are all O(n) per call; they are the usual cause of a "linear" Python solution timing out.
- Always state time and space, including the hash map: a one-pass dict solution is O(n) time and O(n) space, and the output list may or may not count, so say which.

| JavaScript | Python | Note |
| --- | --- | --- |
| `new Map()` or `{}` | `{}` or `dict()` | Insertion-ordered; keys must be hashable |
| `new Set(arr)` | `set(arr)` | O(1) average `in`, unordered |
| `map.get(k) ?? 0` | `d.get(k, 0)` or a `Counter` | Counter reads missing keys as 0 |
| `arr.sort((a, b) => a - b)` | `arr.sort()` or `sorted(arr)` | Python sorts numbers numerically by default |
| `arr.sort((a, b) => b.score - a.score)` | `sorted(arr, key=lambda x: -x.score)` | A key function, not a comparator |
| `arr.forEach((x, i) => ...)` | `for i, x in enumerate(arr):` | `enumerate(arr, start=1)` for 1-based |
| no built-in zip | `zip(a, b)` | Stops at the shortest; `strict=True` in 3.10+ |
| `Math.max(...arr)` | `max(arr, key=f, default=0)` | key and default are built in |
| `arr.reduce((s, x) => s + x, 0)` | `sum(arr)` | Takes a generator, no temporary list |
| `Math.trunc(a / b)` and `a % b` | `a // b`, `a % b`, `divmod(a, b)` | `-7 // 2` is -4 and `-7 % 2` is 1 in Python; -3 and -1 in JS |
| `arr.slice().reverse()` | `arr[::-1]` or `reversed(arr)` | `reversed` is lazy and copies nothing |
| hand-written binary search | `bisect.bisect_left(arr, x)` | `key=` needs 3.10+ |

### Q. In the first coding round you get: return the indices of the two numbers in `nums` that add up to `target`. Write it in Python in one pass.
**Short answer (45 seconds):** Brute force checks every pair, which is O(n^2). Instead I walk the list once with `enumerate` and keep a dict from value to index; for each x I look up `target - x` before storing x. A hit gives both indices, so it is O(n) time and O(n) space.

**Deeper explanation:**

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}            # value -> index
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:                 # look up BEFORE storing x
            return [seen[need], i]
        seen[x] = i
    return []

print(two_sum([2, 7, 11, 15], 9), two_sum([3, 3], 6))   # [0, 1] [0, 1]
```

The pattern is the hash map "have I seen the complement?": the inner loop of the brute force becomes an average O(1) dict lookup. The order inside the loop matters. Checking before storing stops an element from pairing with itself: with `[3, 2, 4]` and target 6, storing first would match 3 with itself and return `[0, 0]`. Duplicates work naturally: in `[3, 3]` the first 3 is stored at index 0 and the second 3 finds it. Empty or single-element input never reaches the inner `return`, so it falls through to `[]`; say out loud whether the interviewer wants `[]`, None or an exception.

Complexity: O(n) time, because each dict operation is O(1) on average, and O(n) extra space for the dict. If the input were already sorted, two pointers would give O(1) space. Sorting first costs O(n log n) and loses the original indices unless you sort the indices instead: `sorted(range(len(nums)), key=nums.__getitem__)`.

**Follow-ups they will ask:**
- The input is sorted. Can you use less memory?: two pointers from both ends, O(n) time and O(1) space.
- Return every pair, not just one?: keep a Counter of values seen so far and add `seen[need]` pairs at each step, or collect indices in a `defaultdict(list)`.
- Three numbers that sum to zero?: sort, fix one number, run two pointers on the rest and skip duplicate values, O(n^2).

**Mistakes to avoid:**
- Storing x before the lookup, which lets an element pair with itself.
- Calling `nums.index(need)` inside the loop: it is O(n) per call and quietly makes the solution O(n^2).
- Letting the function fall off the end: Python then returns None (like `undefined` in JS), which the caller may not expect.

### Q. Write a function that groups a list of words into anagram groups, keeping the groups in first-seen order.
**Short answer (45 seconds):** Anagrams share a signature, their sorted letters. I use a `defaultdict(list)` keyed by `tuple(sorted(word))`, append each word to its group, and return `list(groups.values())`. Because dicts keep insertion order, the groups come out in first-seen order with no extra work.

**Deeper explanation:**

```python
from collections import defaultdict

def group_anagrams(words: list[str]) -> list[list[str]]:
    groups: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    for w in words:
        groups[tuple(sorted(w))].append(w)   # same key for every anagram
    return list(groups.values())

print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))
# [['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]
```

The pattern is "group by a canonical key". `sorted("tea")` returns the list `['a', 'e', 't']`, which is unhashable, so it becomes a tuple (`"".join(sorted(w))` works too). For long words a letter-count key is O(L) instead of O(L log L):

```python
def signature(w: str) -> tuple[int, ...]:
    counts = [0] * 26                    # lowercase a-z only
    for ch in w:
        counts[ord(ch) - ord("a")] += 1
    return tuple(counts)
```

For arbitrary Unicode, `frozenset(Counter(w).items())` is a hashable count signature.

Edge cases: an empty list returns `[]`; `[""]` returns `[[""]]` because `tuple(sorted(""))` is `()`, a valid key; duplicate words such as `["ab", "ab"]` stay together in one group.

Complexity: for n words of length up to L, the sorted key costs O(n * L log L) time and the count key O(n * L). Space is O(n * L) for the keys and groups.

**Follow-ups they will ask:**
- Why not `frozenset(w)` as the key?: it drops counts, so "aab" and "abb" would land in the same group.
- Check whether just two strings are anagrams?: `Counter(a) == Counter(b)`, O(n), or `sorted(a) == sorted(b)`, O(n log n).
- Largest groups first?: `sorted(groups.values(), key=len, reverse=True)`; the sort is stable, so ties keep first-seen order.

**Mistakes to avoid:**
- Using `sorted(w)` directly as a dict key, which raises `TypeError: unhashable type: 'list'`.
- Using a set of letters as the key, which ignores how many times each letter appears.
- Returning `groups.values()` without `list()`: it is a live view object, not a list, and tests comparing to a list fail.

### Q. Write a function that returns the length of the longest substring without repeating characters. Your first version returns 3 for "abba" instead of 2. Find the bug and fix it.
**Short answer (45 seconds):** It is a variable sliding window with a dict of each character's last index. The bug is that the left edge jumps to `last[ch] + 1` even when that old position is already outside the window, so it moves backwards. The fix is to jump only when the repeat is inside the window, which keeps the solution O(n).

**Deeper explanation:** The buggy version:

```python
def longest_buggy(s: str) -> int:
    last, left, best = {}, 0, 0
    for right, ch in enumerate(s):
        if ch in last:
            left = last[ch] + 1          # BUG: can move left backwards
        last[ch] = right
        best = max(best, right - left + 1)
    return best
```

Trace "abba": at index 2 the second "b" moves left to 2. At index 3, "a" was last seen at 0, so left goes back to 1 and the window "bba" (length 3) is counted, although it repeats "b". The fix:

```python
def length_of_longest_substring(s: str) -> int:
    last: dict[str, int] = {}            # char -> last index seen
    left = best = 0
    for right, ch in enumerate(s):
        if last.get(ch, -1) >= left:     # the repeat is INSIDE the window
            left = last[ch] + 1
        last[ch] = right
        best = max(best, right - left + 1)
    return best
```

`left = max(left, last[ch] + 1)` is an equivalent fix. The pattern: the right edge grows the window every step, and the dict lets the left edge jump past the duplicate, always forward.

Edge cases: `""` returns 0 because the loop never runs, `"a"` returns 1 and `"bbbbb"` returns 1.

Complexity: O(n) time, since each index is visited once by `right` and `left` never moves back. Space is O(min(n, alphabet size)) for the dict.

**Follow-ups they will ask:**
- Return the substring itself?: also record `start = left` whenever `best` improves and return `s[start:start + best]`.
- Longest substring with at most k distinct characters?: keep a Counter of the window and shrink in a `while` loop while `len(counter) > k`, deleting keys whose count drops to 0.
- Can you do it with a set?: yes, remove `s[left]` and advance `left` in a `while` loop until `ch` is gone; still O(n), but it steps instead of jumping.

**Mistakes to avoid:**
- Trusting a stale dict entry from before the window: the "abba" bug.
- Rebuilding `set(s[left:right + 1])` on every step, which copies the window and makes it O(n^2).
- Off-by-one window length: it is `right - left + 1`, not `right - left`.

### Q. Write a function that returns the k most frequent elements of a list. The interviewer then asks you to beat O(n log n).
**Short answer (45 seconds):** Count with `Counter` in O(n), then take the top k with `heapq.nlargest`, which keeps a heap of size k: O(n + d log k) for d distinct values. To get strictly O(n), I bucket the values by their count, because a count can never exceed n, and read the buckets from the highest down.

**Deeper explanation:**

```python
import heapq
from collections import Counter

def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)                                       # O(n)
    return heapq.nlargest(k, counts, key=counts.__getitem__)    # O(d log k)

def top_k_bucket(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    buckets: list[list[int]] = [[] for _ in range(len(nums) + 1)]
    for value, c in counts.items():
        buckets[c].append(value)                 # index = frequency
    out: list[int] = []
    for c in range(len(nums), 0, -1):            # highest frequency first
        for value in buckets[c]:
            if len(out) == k:
                return out
            out.append(value)
    return out

print(top_k_frequent([1, 1, 1, 2, 2, 3], 2), top_k_bucket([1, 1, 1, 2, 2, 3], 2))   # [1, 2] [1, 2]
```

Iterating a Counter yields its keys, and `key=counts.__getitem__` ranks each key by its count. `counts.most_common(k)` is the same idea in one call and returns `(value, count)` pairs. For the buckets, write `[[] for _ in range(n + 1)]`: `[[]] * (n + 1)` creates n + 1 references to one shared list, so every value would land in every bucket.

Edge cases: an empty list or `k == 0` returns `[]`, and a k larger than the number of distinct values returns all of them.

Complexity: the heap version is O(n + d log k) time and O(d + k) space; the bucket version is O(n) time and O(n) space. In practice the heap version is the one to write first, then offer buckets when asked for linear time.

**Follow-ups they will ask:**
- How are ties ordered?: `nlargest` is stable, so tied values keep first-seen order; for a fixed rule use a key like `lambda v: (counts[v], -v)`.
- The stream is too big to count exactly in memory?: an approximate heavy-hitters sketch such as Count-Min Sketch or Misra-Gries, with a small heap of candidates.
- Top k retrieved chunks by score in a RAG service?: `heapq.nlargest(k, chunks, key=lambda c: c.score)`, no full sort.

**Mistakes to avoid:**
- Creating buckets with `[[]] * n`, which aliases one list.
- Calling `sorted(counts.items(), ...)` the O(n) solution: sorting d items is O(d log d).
- Forgetting that `most_common` returns pairs, then returning `[(1, 3), (2, 2)]` instead of `[1, 2]`.

### Q. Write product of array except self without using division, in O(n) time and O(1) extra space besides the output.
**Short answer (45 seconds):** The answer at i is the product of everything to the left of i times the product of everything to the right. One pass left to right writes the running prefix product into the output, and a second pass right to left multiplies in a running suffix product. No division, so zeros need no special case.

**Deeper explanation:**

```python
def product_except_self(nums: list[int]) -> list[int]:
    n = len(nums)
    out = [1] * n
    prefix = 1
    for i in range(n):                   # out[i] = product of nums[:i]
        out[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in reversed(range(n)):         # times the product of nums[i + 1:]
        out[i] *= suffix
        suffix *= nums[i]
    return out

print(product_except_self([1, 2, 3, 4]))   # [24, 12, 8, 6]
print(product_except_self([1, 0, 3]))      # [0, 3, 0]
```

The pattern is prefix and suffix accumulation, the multiplication twin of prefix sums. Trace `[1, 2, 3, 4]`: after the first pass `out` is `[1, 1, 2, 6]`; the second pass multiplies in suffixes 24, 12, 4 and 1 from the right, giving `[24, 12, 8, 6]`. `reversed(range(n))` walks backwards without building a list and avoids the off-by-one of `range(n - 1, -1, -1)`.

Why no division: `total // nums[i]` raises `ZeroDivisionError` on a zero, and with two zeros every answer is 0 anyway. Python ints are arbitrary precision, so large products stay exact (just slower); in JavaScript a Number loses precision past 2**53, which is worth one sentence in the interview.

Edge cases: `[]` returns `[]`, `[5]` returns `[1]` (the empty product), and duplicates need nothing special.

Complexity: O(n) time over two passes and O(1) extra space, because the output list does not count as extra; O(n) if your interviewer counts it.

**Follow-ups they will ask:**
- Division is allowed. Any trap?: count zeros first: two or more zeros make everything 0, exactly one zero means only that index gets the product of the rest.
- Why not `math.prod(nums[:i] + nums[i + 1:])` per index?: it copies and multiplies n items for every index, O(n^2).
- Range-sum queries on the same list?: build prefix sums once with `accumulate(nums, initial=0)` and answer each query in O(1).

**Mistakes to avoid:**
- Dividing the total product and crashing on zero.
- Writing the backward loop as `range(n, 0, -1)`, which starts out of range at n and never visits index 0.

### Q. This merge-intervals function returns the right answer, but after calling it the caller's own data has changed. Find the bug and fix it.
**Short answer (45 seconds):** It sorts the caller's list in place and appends the caller's inner lists into the result, then edits them while merging. Python passes object references, like JavaScript, so both changes leak out. I fix it with `sorted()` for a new outer list and by appending a fresh `[start, end]` for each new interval; the algorithm stays sort then linear scan.

**Deeper explanation:**

```python
def merge_buggy(intervals: list[list[int]]) -> list[list[int]]:
    intervals.sort()                         # BUG 1: reorders the caller's list
    merged = []
    for iv in intervals:
        if merged and iv[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], iv[1])   # BUG 2: edits a caller-owned list
        else:
            merged.append(iv)                # stores a reference, not a copy
    return merged

data = [[1, 3], [8, 10], [2, 6]]
merge_buggy(data)
print(data)    # [[1, 6], [2, 6], [8, 10]]: reordered, and [1, 3] became [1, 6]
```

The fix:

```python
def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if merged and start <= merged[-1][1]:    # overlaps or touches the last one
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])          # a new list that we own
    return merged
```

In a backend this corrupts shared state, such as a calendar service's cached busy slots. The pattern: after sorting by start, a new interval can only overlap the last merged one, so one pass is enough. `<=` merges touching intervals like `[1, 4]` and `[4, 5]`; use `<` if they should stay apart. `max` handles nested intervals such as `[1, 10]` followed by `[2, 3]`.

Edge cases: `[]` returns `[]`, a single interval comes back unchanged, and duplicates `[[1, 3], [1, 3]]` merge into `[[1, 3]]`.

Complexity: O(n log n) time for the sort and O(n) space for the sorted copy and the output.

**Follow-ups they will ask:**
- Insert one interval into an already merged, sorted list?: one linear pass that copies intervals before it, merges the overlapping ones and copies the rest, O(n).
- How many meeting rooms are needed?: sort by start and keep a min-heap of end times with `heapq`; the largest heap size is the answer.
- Would tuples help?: yes, tuples are immutable so this aliasing bug cannot happen; you build a new tuple when extending.

**Mistakes to avoid:**
- Mutating inputs in a function that looks pure.
- Forgetting `max` for the end, which shrinks `[1, 10]` when `[2, 3]` follows.
- Sorting by end instead of start, which breaks the "only the last one can overlap" argument.

### Practice
- Practice kit: open `python-practice/exercises/p23_patterns_arrays.py`, implement each function, then run `uv run --with pytest pytest tests/test_p23_patterns_arrays.py` from the `python-practice` folder.
- In the REPL, write `first_unique(s)` that returns the index of the first non-repeating character (or -1) with one Counter pass and one scan; try "leetcode" (0), "loveleetcode" (2) and "aabb" (-1).
- Write `max_vowels(s, k)`, the most vowels in any window of length k, using the add-one-remove-one update, then time it against `sum(...)` over a fresh slice per step on a 100,000-character string with `timeit`.
- Write `search_rotated(a, x)` for a rotated sorted list such as `[4, 5, 6, 7, 0, 1, 2]` by deciding at each step which half is sorted, and check it against `a.index(x)` on random inputs.

## Coding Patterns: Stacks, Queues, Trees, Graphs & Heaps [Core]

> This section covers the second half of most coding rounds: stacks, queues, heaps, binary trees, graphs and memoized dynamic programming, written with Python's standard library (list, collections.deque, heapq, functools.lru_cache, graphlib). The same structures run real AI backend code: a stack to validate or repair nested JSON from a model, a deque as a BFS frontier or an in-process job buffer, heapq to keep the top-k chunks by score in a retriever, topological sort to order the steps of an ingestion pipeline or agent workflow DAG, and memoized recursion for edit distance in fuzzy matching. Interviewers watch for two Python-specific signals: whether you pick the right container (deque, not `list.pop(0)`), and whether you know when recursion will hit the recursion limit.

### Why it exists
Many problems are really about order: last in first out (undo, matching brackets), first in first out (BFS, job queues), smallest first (scheduling, top-k), or "after everything it depends on" (build steps, course plans). Each order has a structure that hands you the next item in O(1) or O(log n) instead of rescanning a list. Python does not give you Stack or PriorityQueue classes to use in a coding round (`queue.Queue` and `queue.PriorityQueue` exist, but they are locking wrappers meant for threads); you use a list, a `deque` and the `heapq` functions, and you build trees and graphs from a small class and dicts. The trade-off: CPython has no tail-call optimization and a default recursion limit of 1000 frames, so a recursive solution that passes small tests can crash on real input.

### In plain words
A stack is a pile of plates: you always take the top one. A queue is the line at a counter: first come, first served. A heap is a hospital triage desk: the most urgent patient goes next, whenever they arrived. A tree is a family tree and a graph is a road map; BFS explores the map ring by ring like ripples from a stone, while DFS follows one road to its end before backing up. Memoization is writing each answer on a sticky note so you never solve the same small problem twice.

### Walkthrough: Stacks, queues, monotonic stacks and heaps
1. **A list is your stack**: `append` and `pop` at the end are O(1), `stack[-1]` peeks and `if not stack` tests for empty. Popping or peeking an empty list raises `IndexError`, so check first. This is the same as `push` and `pop` on a JS array.

   ```python
   stack = []
   stack.append("a")
   stack.append("b")
   print(stack[-1])      # b (peek)
   print(stack.pop())    # b
   print(not stack)      # False: "a" is still there
   ```

2. **collections.deque is your queue**: `append` and `popleft` are O(1) at both ends. `list.pop(0)` is O(n) because every remaining item shifts left. `deque(maxlen=n)` keeps only the last n items, handy for a "last 5 messages" buffer.

   ```python
   from collections import deque
   q = deque([1, 2])
   q.append(3)                      # enqueue on the right
   print(q.popleft())               # 1, O(1)
   recent = deque(maxlen=3)
   for msg in ["m1", "m2", "m3", "m4"]:
       recent.append(msg)           # the oldest item falls off the left
   print(list(recent))              # ['m2', 'm3', 'm4']
   ```

3. **Monotonic stack**: for "next greater" or "next smaller" questions, keep a stack of indices whose values are decreasing from bottom to top. When a bigger value arrives, pop and resolve every smaller waiting index. Each index is pushed once and popped at most once, so the nested loops are O(n) in total.

   ```python
   def next_greater(nums: list[int]) -> list[int]:
       out = [-1] * len(nums)
       stack: list[int] = []                # indices, values decreasing upward
       for i, x in enumerate(nums):
           while stack and nums[stack[-1]] < x:
               out[stack.pop()] = x         # x is the next greater value for that index
           stack.append(i)
       return out

   print(next_greater([2, 1, 3, 2, 4]))     # [3, 3, 4, 4, -1]
   ```

4. **heapq is a min-heap on a plain list**: there is no heap class, just functions. `heapify` is O(n) in place, `heappush` and `heappop` are O(log n), and `h[0]` is always the smallest item. The list is a valid heap, not a sorted list. JavaScript has no built-in heap at all.

   ```python
   import heapq
   h = [9, 4, 7, 1, 8, 2]
   heapq.heapify(h)                 # in place, O(n)
   heapq.heappush(h, 3)
   print(h[0])                      # 1, the minimum
   print(heapq.heappop(h), heapq.heappop(h))   # 1 2
   print(h)                         # [3, 4, 7, 9, 8]: a heap, NOT sorted
   ```

5. **Max-heap by negating, tuples for priority**: in 3.12 heapq only has min-heap functions (3.14 adds `heappush_max` and friends), so push `-x` and negate again on the way out. For priorities push tuples: they compare item by item, and a counter as the second item breaks ties so Python never compares the payloads, which would raise `TypeError: '<' not supported between instances of 'dict' and 'dict'`.

   ```python
   import heapq
   import itertools
   max_heap = [-x for x in [5, 1, 8]]
   heapq.heapify(max_heap)
   print(-heapq.heappop(max_heap))           # 8

   tasks, order = [], itertools.count()
   heapq.heappush(tasks, (2, next(order), {"job": "email"}))
   heapq.heappush(tasks, (1, next(order), {"job": "charge"}))
   heapq.heappush(tasks, (1, next(order), {"job": "refund"}))
   print(heapq.heappop(tasks)[2])            # {'job': 'charge'}: priority 1, pushed first
   ```

### Walkthrough: Binary trees, traversals and the recursion limit
1. **A small TreeNode class**: `@dataclass` writes `__init__`, `__repr__` and `__eq__` for you. Quote the annotation `"TreeNode | None"` because the class does not exist yet while its body runs; unquoted, it raises `NameError` in 3.12. `None` plays the role of JS `null`.

   ```python
   from dataclasses import dataclass

   @dataclass
   class TreeNode:
       val: int
       left: "TreeNode | None" = None
       right: "TreeNode | None" = None

   #       1
   #      / \
   #     2   3
   #    /
   #   4
   root = TreeNode(1, TreeNode(2, TreeNode(4)), TreeNode(3))
   ```

2. **Recursive DFS**: the base case is `if node is None` (compare with `is`, not `==`). Pre-order, in-order and post-order differ only in where you record the value. Never write `def inorder(node, out=[])`: a default list is created once, when the function is defined, and every later call shares it.

   ```python
   def inorder(node: TreeNode | None, out: list[int]) -> list[int]:
       if node is None:
           return out
       inorder(node.left, out)
       out.append(node.val)         # move this line up for pre-order, down for post-order
       inorder(node.right, out)
       return out

   def max_depth(node: TreeNode | None) -> int:
       return 0 if node is None else 1 + max(max_depth(node.left), max_depth(node.right))

   print(inorder(root, []), max_depth(root))   # [4, 2, 1, 3] 3
   ```

3. **Iterative traversal with an explicit stack**: the same in-order walk without recursion: go left as far as possible pushing nodes, pop one, record it, then turn right. The stack lives on the heap, so depth is limited only by memory.

   ```python
   def inorder_iter(root: TreeNode | None) -> list[int]:
       out: list[int] = []
       stack: list[TreeNode] = []
       node = root
       while stack or node:
           while node:                  # go as far left as possible
               stack.append(node)
               node = node.left
           node = stack.pop()
           out.append(node.val)
           node = node.right
       return out

   print(inorder_iter(root))            # [4, 2, 1, 3]
   ```

4. **Level by level with deque**: BFS processes the tree one level per round. `range(len(q))` reads the length once, at the start of the round, so children added during the round wait for the next one.

   ```python
   from collections import deque

   def level_sums(root: TreeNode | None) -> list[int]:
       if root is None:
           return []
       sums, q = [], deque([root])
       while q:
           total = 0
           for _ in range(len(q)):          # exactly this level's nodes
               node = q.popleft()
               total += node.val
               q.extend(child for child in (node.left, node.right) if child)
           sums.append(total)
       return sums

   print(level_sums(root))                  # [1, 5, 4]
   ```

5. **The recursion limit**: CPython stops at about 1000 frames by default (`sys.getrecursionlimit()`) and has no tail-call optimization. A tree shaped like a linked list, which is exactly what inserting sorted keys into a plain BST produces, crashes every recursive helper above. Recursion is fine when depth grows like log n (balanced trees); when depth can grow with n, use an explicit stack or BFS. `sys.setrecursionlimit` is a band-aid that depends on the C stack and the Python version.

   ```python
   import sys
   print(sys.getrecursionlimit())          # 1000
   chain = None
   for v in range(5000):                   # each node hangs off the left of the next
       chain = TreeNode(v, chain)
   try:
       max_depth(chain)
   except RecursionError as e:
       print("RecursionError:", e)         # maximum recursion depth exceeded
   ```

### Walkthrough: Graphs, topological sort and memoized DP
1. **Adjacency list as a dict of lists**: `defaultdict(list)` builds it from an edge list without key checks; for an undirected graph add both directions. Any hashable value can be a node: ints, strings or `(row, col)` tuples.

   ```python
   from collections import defaultdict
   edges = [("api", "db"), ("api", "cache"), ("worker", "db")]
   graph: defaultdict[str, list[str]] = defaultdict(list)
   for a, b in edges:
       graph[a].append(b)
       graph[b].append(a)           # undirected: both ways
   print(graph["db"])               # ['api', 'worker']
   ```

2. **BFS with a deque and a visited record**: mark a node as visited when you enqueue it, not when you dequeue it, or the same node enters the queue many times. In an unweighted graph BFS finds the shortest path, and a distance dict doubles as the visited set. `graph.get(node, [])` avoids inserting keys into the defaultdict.

   ```python
   from collections import deque

   def shortest_hops(graph: dict[str, list[str]], start: str, goal: str) -> int:
       dist = {start: 0}                # also the visited set
       q = deque([start])
       while q:
           node = q.popleft()
           if node == goal:
               return dist[node]
           for nxt in graph.get(node, []):
               if nxt not in dist:      # mark on enqueue
                   dist[nxt] = dist[node] + 1
                   q.append(nxt)
       return -1

   print(shortest_hops(graph, "cache", "worker"))   # 3: cache, api, db, worker
   ```

3. **DFS with an explicit stack, and grids as graphs**: swap `popleft()` for `pop()` on a list and the same loop is a depth-first search with no recursion limit. On a grid every cell is a node, neighbours come from a tuple of direction offsets, and Python's chained comparison `0 <= r < rows` does the bounds check. In JavaScript `0 <= r < rows` compiles but compares a boolean with a number, a silent bug.

   ```python
   DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

   def area_from(grid: list[list[int]], sr: int, sc: int) -> int:
       rows, cols = len(grid), len(grid[0])
       seen, stack = {(sr, sc)}, [(sr, sc)]
       while stack:
           r, c = stack.pop()
           for dr, dc in DIRS:
               nr, nc = r + dr, c + dc
               if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in seen:
                   seen.add((nr, nc))
                   stack.append((nr, nc))
       return len(seen)

   print(area_from([[1, 1, 0], [0, 1, 0], [1, 0, 1]], 0, 0))   # 3
   ```

4. **Topological sort**: Kahn's algorithm counts incoming edges, starts from the nodes with none, and each processed node lowers its neighbours' counts; if fewer than all nodes come out, there is a cycle (written by hand in the course schedule exercise below). In production Python, `graphlib.TopologicalSorter` (3.9+) does it: it takes `{node: predecessors}` and raises `graphlib.CycleError` with the cycle in `e.args[1]`.

   ```python
   from graphlib import CycleError, TopologicalSorter
   steps = {"embed": {"chunk"}, "chunk": {"fetch"}, "index": {"embed"}}
   print(list(TopologicalSorter(steps).static_order()))
   # ['fetch', 'chunk', 'embed', 'index']
   try:
       list(TopologicalSorter({"a": {"b"}, "b": {"a"}}).static_order())
   except CycleError as e:
       print("cycle:", e.args[1])       # cycle: ['a', 'b', 'a']
   ```

5. **Memoized recursion with functools.cache and lru_cache**: decorate a pure recursive function and every repeated call becomes a dict lookup, turning exponential recursion into O(number of distinct arguments). `@cache` (3.9+) is `@lru_cache(maxsize=None)`. Arguments must be hashable (an int or a tuple, not a list), and defining the cached helper inside the solver gives each call a fresh cache.

   ```python
   from functools import cache

   def climb_stairs(n: int) -> int:
       @cache
       def ways(i: int) -> int:         # ways to reach step i with 1- or 2-steps
           if i <= 1:
               return 1
           return ways(i - 1) + ways(i - 2)
       return ways(n)

   print(climb_stairs(5), climb_stairs(40))   # 8 165580141
   ```

6. **When memoization meets the recursion limit**: `climb_stairs(5000)` recurses 5000 deep and raises `RecursionError`, cache or not. The fix is bottom-up: iterate from the small cases to the big one with the same recurrence, often keeping only the last few values. On CPython 3.12, raising the limit does not rescue an lru_cache-wrapped function either: in testing it still failed at a few thousand levels, because each level also passes through C code.

   ```python
   def climb_stairs_iter(n: int) -> int:
       a, b = 1, 1                      # ways(i - 1), ways(i)
       for _ in range(n - 1):
           a, b = b, a + b
       return b

   print(climb_stairs_iter(5), len(str(climb_stairs_iter(5000))))   # 8 1045
   ```

### Concepts you must understand
- A list is the stack (`append` and `pop` at the end) and `collections.deque` is the queue (`append` and `popleft`); `list.pop(0)` and `list.insert(0, x)` are O(n).
- A monotonic stack keeps indices in increasing or decreasing value order and answers every "next greater or smaller" question in O(n), because each index is pushed and popped at most once.
- The heapq functions treat a plain list as a min-heap: `h[0]` is the smallest, push and pop are O(log n), `heapify` is O(n), and the list is not sorted.
- For a max-heap negate the numbers; for priorities push `(priority, counter, item)` tuples so ties never compare the payloads.
- Recursive tree code is fine when depth is about log n; CPython's default limit of 1000 frames and the lack of tail-call optimization make deep recursion raise RecursionError, so use an explicit stack or BFS when depth can grow with the input.
- BFS uses a deque and finds shortest paths in unweighted graphs; DFS uses a list as a stack (or recursion); both need a visited set, filled when a node is added, not when it is processed.
- Graphs are a dict of lists (`defaultdict(list)`), grid cells are `(row, col)` tuples in the visited set, and `0 <= r < rows` is a valid bounds check; negative indexes silently wrap to the other end of a Python list, so never skip it.
- Kahn's topological sort repeatedly takes nodes with no remaining prerequisites and detects a cycle when fewer than all nodes come out; `graphlib.TopologicalSorter` is the standard-library version for real pipelines.
- `functools.cache` and `lru_cache` memoize pure functions with hashable arguments; nest the cached helper inside the solver so the cache does not leak between calls, and switch to a bottom-up table when depth can exceed the recursion limit.
- Never use a mutable default argument such as `def f(out=[])` in a recursive helper: the list is created once and shared by every call.

| JavaScript | Python | Note |
| --- | --- | --- |
| `arr.push(x)`, `arr.pop()` | `stack.append(x)`, `stack.pop()` | Same O(1) stack at the end |
| `arr.shift()` | `q.popleft()` on a `deque` | `list.pop(0)` is O(n); deque is O(1) at both ends |
| `arr.at(-1)` | `stack[-1]` | Raises IndexError on an empty list, check `if stack` |
| a heap library or hand-written heap | `heapq.heappush(h, x)`, `heapq.heappop(h)` | Min-heap functions over a plain list |
| a max-heap comparator | push `-x`, negate on pop | heapq is min-only in 3.12 |
| `class TreeNode { constructor(...) }` | `@dataclass class TreeNode` | dataclass writes `__init__`, `__repr__` and `__eq__` |
| `null` | `None` | Test with `is None` |
| `new Map()` of arrays | `defaultdict(list)` | Adjacency list without key checks |
| `new Set()` of `"r,c"` strings | `set()` of `(r, c)` tuples | Tuples hash by value |
| `0 <= r && r < rows` | `0 <= r < rows` | In JS the chained form compares a boolean with a number |
| a manual Map as a cache | `@functools.cache` or `@lru_cache` | Arguments must be hashable |
| `RangeError: Maximum call stack size exceeded` | `RecursionError` at about 1000 frames | Python's default limit is much lower |

### Q. Write a function that checks whether a string of brackets is balanced. It must return False for "([)]" and for a lone ")".
**Short answer (45 seconds):** I push every opener onto a list used as a stack. On a closer, the stack must be non-empty and its top must be the matching opener, which I look up in a dict from closer to opener. At the end the stack must be empty. That is O(n) time and O(n) space.

**Deeper explanation:**

```python
def is_valid_parentheses(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}      # closer -> opener
    stack: list[str] = []
    for ch in s:
        if ch in pairs:                         # a closer
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:                                   # an opener
            stack.append(ch)
    return not stack                            # leftovers like "((" fail

print(is_valid_parentheses("{[]}"), is_valid_parentheses("([)]"), is_valid_parentheses(")"))
# True False False
```

The pattern is a stack for nesting: the bracket opened most recently must close first, which is exactly last in, first out. For "([)]" the stack holds `(` and `[` when `)` arrives; the top is `[`, so it fails. For ")" the stack is empty, and `not stack` short-circuits before `pop()`, which would otherwise raise `IndexError: pop from empty list`. For the empty string the loop never runs and `not []` is True, so it is balanced. `return not stack` uses container truthiness: an empty list is falsy, the same idea as checking `length === 0` in JS.

The same stack shows up in production: a streaming LLM response cut off mid-JSON can be repaired by walking it, tracking open brackets and string state, and appending the closers left on the stack in reverse order.

Complexity: O(n) time, O(n) space in the worst case (all openers).

**Follow-ups they will ask:**
- The string also contains letters?: skip characters that are neither openers nor closers, for example `elif ch in "([{": stack.append(ch)`.
- Only one bracket type?: a counter instead of a stack, failing if it ever goes negative, O(1) space.
- Longest valid parentheses substring?: a stack of indices seeded with -1; after each pop the current length is `i - stack[-1]`.

**Mistakes to avoid:**
- Calling `stack.pop()` or `stack[-1]` without checking emptiness first, which raises IndexError on ")".
- Returning True at the end without checking that the stack is empty.
- Counting each bracket type separately, which wrongly accepts "([)]".

### Q. For each day, return how many days until a warmer temperature. The nested-loop version times out on 100,000 days. Rewrite it with a monotonic stack.
**Short answer (45 seconds):** The slow version scans forward from every day, which is O(n^2) on a long falling run. Instead I keep a stack of indices still waiting for a warmer day; their temperatures are non-increasing from bottom to top. Each new day pops every colder waiting day and fills in its answer, so each index is pushed and popped once: O(n).

**Deeper explanation:** The version that times out:

```python
def daily_slow(temps: list[int]) -> list[int]:
    out = [0] * len(temps)
    for i in range(len(temps)):
        for j in range(i + 1, len(temps)):    # rescans the future for every day
            if temps[j] > temps[i]:
                out[i] = j - i
                break
    return out
```

The rewrite:

```python
def daily_temperatures(temps: list[int]) -> list[int]:
    answer = [0] * len(temps)
    stack: list[int] = []                # indices still waiting for a warmer day
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j            # day i is the first warmer day after j
        stack.append(i)
    return answer

print(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]))   # [1, 1, 4, 2, 1, 1, 0, 0]
```

Trace: 71 and 69 wait above 75 on the stack. 72 pops 69 (1 day) and 71 (2 days) but stops at 75, which is warmer. 76 pops 72 and then 75 (4 days). Days left on the stack keep their initial 0.

Edge cases: `[]` returns `[]`, `[50]` returns `[0]`, and equal days such as `[70, 70]` stay on the stack because the comparison is strictly `<`.

Complexity: O(n) time even though there is a `while` inside the `for`: the total number of pops across the whole run is at most n. Space is O(n) for the stack in a falling sequence.

**Follow-ups they will ask:**
- Circular array (the next warmer day can wrap around)?: loop `i` over `range(2 * n)`, use `i % n`, and only push during the first pass.
- Largest rectangle in a histogram?: an increasing stack of indices; on each pop, width runs from the new top to the current index.
- Stock span (consecutive previous days priced at or below today)?: pop while the top is at or below today's price; the span is the distance to the new top.

**Mistakes to avoid:**
- Pushing temperatures instead of indices and losing the distance.
- Using `<=`, which treats an equal day as warmer.
- Calling it O(n^2) because of the nested loops instead of counting pushes and pops.

### Q. Return the kth largest element of an unsorted list. Your first answer sorts it; the interviewer asks for something better when k is small and n is in the millions.
**Short answer (45 seconds):** I keep a min-heap of size k with heapq. I push until it holds k items, then replace the root whenever a bigger value arrives, so the heap always holds the k largest values seen so far and its root is the kth largest. That is O(n log k) time and O(k) space, and it works on a stream. Quickselect gives average O(n) if they want more.

**Deeper explanation:**

```python
import heapq

def kth_largest(nums: list[int], k: int) -> int:
    if not 1 <= k <= len(nums):
        raise ValueError(f"k must be between 1 and {len(nums)}, got {k}")
    heap: list[int] = []                   # the k largest values so far
    for x in nums:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:                  # beats the smallest of the top k
            heapq.heapreplace(heap, x)     # pop root and push x in one O(log k) step
    return heap[0]

print(kth_largest([3, 2, 1, 5, 6, 4], 2), kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4))   # 5 4
```

The pattern is a bounded heap. It is a min-heap, not a max-heap, because the item we evict is always the smallest of our candidates, and the root `heap[0]` is the smallest of the k largest, which is the answer. Duplicates count separately, as the second example shows. Validating k up front gives a clear ValueError instead of an IndexError on `heap[0]` for an empty list.

One-liners: `heapq.nlargest(k, nums)[-1]` has the same complexity; `sorted(nums)[-k]` is O(n log n) and perfectly fine for small inputs, and saying so is a senior signal. Quickselect partitions around a random pivot and recurses into one side: average O(n), worst case O(n^2), and it reorders or copies the data.

Complexity: O(n log k) time, O(k) space.

**Follow-ups they will ask:**
- Kth largest in a stream with `add()` calls?: a class that keeps the size-k heap as state; each add is O(log k).
- k closest points to the origin?: `heapq.nsmallest(k, points, key=lambda p: p[0] ** 2 + p[1] ** 2)`, no square root needed.
- Merge k sorted lists?: a heap of `(value, list_index, position)` tuples, or `heapq.merge(*lists)`.

**Mistakes to avoid:**
- Calling `heap.push(x)`: heapq is a set of functions over a plain list, not a class with methods.
- Returning `heap[-1]`, which is not the largest item; only `heap[0]` has a guaranteed position.
- Pushing negated values for a max-heap and forgetting to negate the result back.

### Q. Return the values of a binary tree level by level, left to right. Define the TreeNode class yourself.
**Short answer (45 seconds):** It is BFS with `collections.deque`. I process the queue in rounds: read `len(queue)` at the start of a round, pop exactly that many nodes into one level list, and enqueue their children for the next round. O(n) time and O(w) space, where w is the widest level.

**Deeper explanation:**

```python
from collections import deque
from dataclasses import dataclass

@dataclass
class TreeNode:
    val: int
    left: "TreeNode | None" = None
    right: "TreeNode | None" = None

def level_order(root: TreeNode | None) -> list[list[int]]:
    if root is None:
        return []
    levels: list[list[int]] = []
    queue = deque([root])
    while queue:
        level = []
        for _ in range(len(queue)):        # exactly the nodes of this level
            node = queue.popleft()
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        levels.append(level)
    return levels

root = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
print(level_order(root))                   # [[3], [9, 20], [15, 7]]
```

`range(len(queue))` is evaluated once, so the children appended during a round are left for the next round; that is what separates the levels. A deque makes each `popleft` O(1); `list.pop(0)` would make a wide tree O(n^2). The dataclass also generates `__eq__`, so `TreeNode(1) == TreeNode(1)` is True (compared by value), unlike two JS objects. The class annotations are quoted because `TreeNode` is not defined yet while its own body runs.

Edge cases: `None` returns `[]`, a single node returns `[[val]]`, and duplicate values are fine because nothing is keyed by value.

Complexity: O(n) time; O(w) space for the queue, which is up to about n/2 for a complete tree.

**Follow-ups they will ask:**
- Zigzag order?: the same loop, appending `level[::-1]` on every other round.
- Right side view?: take `level[-1]` from each round.
- Can you do it with DFS?: pass the depth down and append to `levels[depth]`; fine for balanced trees, but a skewed tree of a few thousand nodes hits RecursionError.

**Mistakes to avoid:**
- Using a list with `pop(0)` as the queue.
- Using a `while` that re-reads the queue length inside the round, which mixes levels together.
- Writing `left: TreeNode | None = None` unquoted in the class body, which raises `NameError: name 'TreeNode' is not defined`.

### Q. Count the islands in a grid of 1s and 0s. Your recursive DFS passes the small tests but crashes with RecursionError on a 300 by 300 all-land grid. Fix it.
**Short answer (45 seconds):** On one big island the recursive flood fill goes up to 90,000 frames deep, far past CPython's 1000-frame default. I keep the algorithm, connected components on a grid, but flood each island with a deque-based BFS and a visited set, so the frontier lives on the heap. O(rows * cols) time and space.

**Deeper explanation:** The crashing helper:

```python
def fill(r: int, c: int) -> None:      # recursion depth can reach rows * cols
    if 0 <= r < rows and 0 <= c < cols and grid[r][c] == 1 and (r, c) not in seen:
        seen.add((r, c))
        for dr, dc in DIRS:
            fill(r + dr, c + dc)
```

The fix:

```python
from collections import deque

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

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
            islands += 1                   # a new island: flood all of it
            seen.add((r, c))
            queue = deque([(r, c)])
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in DIRS:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return islands
```

Raising `sys.setrecursionlimit` only hides the problem: the stack still grows with the island. Swapping `popleft()` for `pop()` gives an iterative DFS with the same result. Marking cells when they are enqueued means each cell enters the queue once. Sinking cells with `grid[r][c] = 0` saves the set but mutates the caller's grid, so ask first.

Edge cases: `[]` and `[[]]` return 0 thanks to the guard before `grid[0]`, and `[[1]]` returns 1.

Complexity: O(rows * cols) time and space.

**Follow-ups they will ask:**
- Largest island area?: count the cells each BFS visits and keep the maximum.
- Land is added one cell at a time and you must report the count after each?: union-find with path compression, nearly O(1) per addition.
- Diagonals connect too?: add the four diagonal offsets to `DIRS`.

**Mistakes to avoid:**
- Marking visited when popping instead of when pushing, so cells are enqueued several times.
- Skipping the bounds check: `grid[-1]` is the last row in Python, so a negative index silently wraps instead of raising.

### Q. You get num_courses and prerequisite pairs (course, prereq). Return an order that takes every course, or None if it is impossible, and explain how your code detects the cycle.
**Short answer (45 seconds):** It is a topological sort (Kahn's algorithm): an adjacency list from each prerequisite to the courses it unlocks, an indegree count per course, and a deque seeded with the courses that have no prerequisites. Taking a course decrements its dependents and enqueues any that reach zero. If the order ends up shorter than num_courses, the missing courses sit on a cycle. O(V + E).

**Deeper explanation:**

```python
from collections import deque

def course_order(num_courses: int, prerequisites: list[tuple[int, int]]) -> list[int] | None:
    graph: list[list[int]] = [[] for _ in range(num_courses)]   # prereq -> courses it unlocks
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
    return order if len(order) == num_courses else None

print(course_order(4, [(1, 0), (2, 0), (3, 1), (3, 2)]), course_order(2, [(1, 0), (0, 1)]))
# [0, 1, 2, 3] None
```

Indegree is the number of unfinished prerequisites, and a course becomes available exactly when it reaches zero. In a cycle (0 needs 1 and 1 needs 0) neither ever reaches zero, so neither is enqueued and the length check catches it. A self-loop `(0, 0)` gives course 0 an indegree that never drops. Duplicate pairs add 2 and later subtract 2, so they stay consistent.

Nodes are 0 to n - 1, so a list of lists is enough; with string names use `defaultdict(list)`. In production code (ingestion steps, agent workflow nodes) use `graphlib.TopologicalSorter`, which raises `CycleError` naming the cycle.

Edge cases: 0 courses returns `[]`, one course with no pairs returns `[0]`.

Complexity: O(V + E) time and space.

**Follow-ups they will ask:**
- Do it with DFS?: three states (unvisited, in progress, done); reaching an in-progress node is a back edge, which is a cycle; append each node when it finishes and reverse at the end.
- Which courses can be taken in the same semester?: process the queue in rounds, like BFS levels; each round is one semester.
- Only return whether it is possible?: the same code returning `len(order) == num_courses`.

**Mistakes to avoid:**
- Building edges from course to prereq, which returns the order reversed.
- Detecting cycles in DFS with one visited set, which flags a harmless diamond (two paths to one node) as a cycle.
- `[[]] * n`, which gives every course the same list of dependents.

### Q. Write coin change, the fewest coins that make up an amount or -1, with lru_cache memoization. Then tell the interviewer what breaks when the amount is 100,000.
**Short answer (45 seconds):** `fewest(r)` is 1 plus the minimum of `fewest(r - coin)` over the coins that fit, with `fewest(0) = 0`. `@lru_cache` solves each remainder once: O(amount * coins). Greedy fails: for [1, 3, 4] and 6 it picks 4 + 1 + 1, not 3 + 3. At 100,000 the recursion raises RecursionError, so I switch to a bottom-up table.

**Deeper explanation:**

```python
from functools import lru_cache

def coin_change(coins: list[int], amount: int) -> int:
    values = tuple(set(coins))                  # duplicate coins add nothing

    @lru_cache(maxsize=None)                    # fresh cache for every call
    def fewest(remaining: int) -> float:
        if remaining == 0:
            return 0
        best = float("inf")
        for c in values:
            if c <= remaining:
                best = min(best, fewest(remaining - c) + 1)
        return best

    result = fewest(amount)
    return -1 if result == float("inf") else int(result)

print(coin_change([1, 2, 5], 11), coin_change([1, 3, 4], 6), coin_change([2], 3))   # 3 2 -1
```

This is top-down dynamic programming: optimal substructure (the best for 11 is built from the best for 10, 9 or 6) and overlapping subproblems (remainders repeat). Without the cache it is exponential. The cached helper takes only an int, which is hashable; caching a function that takes the coins list raises `TypeError: unhashable type: 'list'`.

Depth is amount divided by the smallest coin, so 100,000 with a 1-coin raises RecursionError, and on CPython 3.12 even a raised limit fails for lru_cache functions at a few thousand levels. The bottom-up table has no depth:

```python
def coin_change_table(coins: list[int], amount: int) -> int:
    inf = float("inf")
    dp = [0] + [inf] * amount                   # dp[a] = fewest coins for a
    for a in range(1, amount + 1):
        dp[a] = min((dp[a - c] + 1 for c in coins if c <= a), default=inf)
    return -1 if dp[amount] == inf else int(dp[amount])
```

Edge cases: amount 0 gives 0; no coins gives -1 for any positive amount. Both versions are O(amount * len(coins)) time and O(amount) space.

**Follow-ups they will ask:**
- Climbing stairs, 1 or 2 steps at a time?: the same shape, `ways(i) = ways(i - 1) + ways(i - 2)`, memoized or with two rolling variables for O(1) space.
- Count the ways instead of the fewest coins?: put coins in the outer loop so each combination is counted once: `dp[a] += dp[a - c]`.

**Mistakes to avoid:**
- A module-level `@lru_cache` helper that closes over the coins: the cache keeps answers from the previous call's coins.
- Returning `inf` or a float instead of the integer -1.

### Practice
- Practice kit: open `python-practice/exercises/p24_patterns_structures.py`, implement each function, then run `uv run --with pytest pytest tests/test_p24_patterns_structures.py` from the `python-practice` folder.
- In the REPL, write a `MinStack` class whose `push`, `pop`, `top` and `get_min` are all O(1) by storing `(value, min_so_far)` tuples on one list.
- Write `merge_k_sorted(lists)` with `heapq` and `(value, list_index, position)` tuples, then check it against `list(heapq.merge(*lists))`.
- Build the 5,000-node chain from the walkthrough, watch `max_depth` raise RecursionError, then rewrite it with an explicit stack of `(node, depth)` pairs.
