---
key: backtrack
name: Complete search and backtracking
stage: strategy
summary: Enumerate every candidate systematically with choose, explore, unchoose; prune what cannot succeed; and know from the constraints whether the search will finish.
why: Some problems have no shortcut: list every arrangement, place pieces under constraints, find the best subset of a handful of items. Backtracking is the disciplined way to try everything once and nothing twice, and it is the brute force you test every later dynamic programming and greedy solution against. The same machinery runs in real software: regular-expression engines, package resolvers and SAT solvers are backtracking searches, and their worst cases (catastrophic regex backtracking, a resolver that tries hundreds of versions) are exactly the exponential trees this module teaches you to count, prune and avoid.
outcomes:
- Draw the search tree for a problem and count its nodes to predict the running time before writing code
- Generate subsets, permutations and combinations from one choose, explore, unchoose template, without duplicates when the input has repeated values
- Build constructions (string partitions, combination sums, balanced brackets) piece by piece, keeping only prefixes that can still be completed
- Prune with feasibility, bound and symmetry rules, and measure the effect in nodes visited
- Solve constraint puzzles such as N-queens and Sudoku with O(1) conflict checks and most-constrained-first ordering
- Search grid paths with mark and restore, and explain why a global visited set gives wrong answers there
- Decide from n whether exhaustive search fits the time limit, and switch to meet in the middle or dynamic programming when it does not
cues:
- The output is every configuration: "return all", "list every", "generate each"
- n is tiny: about 10 for orderings, 20-25 for subsets, a fixed 9x9 board
- Choices interact through constraints (no two attack, each digit once per row, brackets balance) rather than a simple sum
- A path on a grid or graph may not reuse a cell, and you need all such paths or the best one
- Not if the question asks only for a count or an optimum and the rest of the problem depends on a small summary (an index, a remaining sum): that is dynamic programming
traps:
- Recording `res.append(path)` instead of a copy, so every stored answer ends up as the same final (usually empty) list
- Forgetting to undo a choice (pop, unmark, restore the cell), which silently corrupts sibling branches
- Skipping duplicates with `i > 0` instead of `i > start`, which drops valid answers such as [1, 2, 2]
- Pruning with a rule that is not safe, for example "the running sum already exceeds the target" when numbers can be negative
- Starting an exhaustive search without estimating it: 12! is 479 million leaves, far beyond Python's few million nodes per second
systems:
- Backtracking regular-expression engines (Python's `re`, PCRE, Perl): a Cloudflare WAF rule containing `.*(?:.*=.*)` backtracked so heavily on 2 July 2019 that CPUs serving HTTP traffic hit nearly 100% worldwide; RE2, Go's regexp and Rust's regex avoid backtracking to guarantee linear time
- pip's dependency resolver (since version 20.3) backtracks: it picks package versions, discovers a conflict, discards work and tries other versions, which is why some installs download many versions of one package
- SAT solvers are backtracking at heart: DPLL assigns a variable, propagates forced values and backtracks on a conflict; modern CDCL solvers add clause learning and non-chronological backjumping
- Constraint solvers such as Google OR-Tools CP-SAT and mixed-integer programming solvers explore search trees with propagation and bounds, the industrial form of pruning
further:
- Chapter · 40 min | Erickson, Algorithms, ch. 2 Backtracking (N Queens, Subset Sum, The General Pattern; PDF pages 1-10) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf
- Chapter · 30 min | Competitive Programmer's Handbook, ch. 5 Complete search (PDF pages 57-66) | https://cses.fi/book/book.pdf#page=57
- Article · 30 min | Peter Norvig: Solving every Sudoku puzzle (constraint propagation plus search) | https://norvig.com/sudoku.html
- Article · 25 min | Russ Cox: Regular expression matching can be simple and fast (why backtracking engines blow up) | https://swtch.com/~rsc/regexp/regexp1.html
bank: backtrack
---

=== primer | How do you turn "try every possibility" into a search tree you can count? | 15 min
goal: Model an exhaustive search as a tree of partial solutions, write it with one choose, explore, unchoose template, and count its nodes before running it
tag: backtrack-tree | The search tree and the backtracking template
link: Erickson, Algorithms, ch. 2 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf#page=9 | 10 min: section 2.4 'The General Pattern' (PDF pages 9-10): each call makes one decision, and the recursive call must be told everything that earlier decisions constrain
practice: 1863

> [!key]
> Exhaustive search is a walk over a **search tree**: the root is "nothing decided yet", each level makes one decision, each edge is one choice, and each leaf is a complete candidate. **Backtracking** walks that tree depth first while keeping one mutable partial solution: *choose* a value, *explore* everything below it, *unchoose* it, then try the next value. The cost is the number of nodes times the work per node, so you can count it before you write a line.

## Intuition

A bike lock has three dials, each showing 0 to 9. Trying every code is 1,000 attempts, and you would naturally do it in order: fix the first dial, run through the second, and for each of those run through the third. When the third dial has shown all ten digits, you roll it back and advance the second. That rolling back is backtracking.

Draw what you did and you get a tree: the root (no dial set) has 10 children, each of those has 10, each of those has 10 leaves. 1,000 leaves, 1,111 nodes.

Now add a rule: no two neighbouring dials may show the same digit. If the first two dials already read 4 4, there is no point trying any third digit: the whole subtree below "4 4" is dead. Skipping it is **pruning**, and it is the reason backtracking beats generating every candidate and filtering afterwards.

## How it works

### The tree

- A **node** is a partial solution: the decisions made so far (the `path`).
- **Level k** holds every node with k decisions made.
- The **children** of a node are the valid choices for the next decision.
- A **leaf** is a complete candidate: record it, test it or score it.

Binary strings of length 3 with no two adjacent 1s, drawn as a tree (x marks a rejected choice):

```text
                         ""
              /                     \
            "0"                     "1"
         /       \               /       \
     "00"         "01"        "10"       "11" x
    /    \       /    \      /    \
 "000"  "001" "010" "011"x "100" "101"
```

Five leaves survive: 000, 001, 010, 100, 101.

### The template

Write the recursive function against a contract, not a trace: *"given the decisions in `path`, visit every valid completion of it"*. Inside, you make one decision and trust the recursive call to finish the job (the Recursion Fairy from the recursion module).

```python
def no_adjacent_ones(n):
    """All binary strings of length n with no two adjacent 1s."""
    res, path = [], []

    def dfs():
        if len(path) == n:                  # complete candidate: a leaf
            res.append("".join(path))
            return
        for c in "01":                      # the choices at this level
            if c == "1" and path and path[-1] == "1":
                continue                    # invalid: prune this branch
            path.append(c)                  # choose
            dfs()                           # explore
            path.pop()                      # unchoose

    dfs()
    return res


print(no_adjacent_ones(3))   # ['000', '001', '010', '100', '101']
```

One list, `path`, is shared by every call. Each choice costs O(1) to make and O(1) to undo, which is why the mutable style is the standard. The alternative is to pass a fresh copy down (`dfs(path + [c])`): no undo bugs are possible, but every node pays O(n) for the copy.

### Generators and the library

If the caller may stop early (the first valid answer is enough), make `dfs` a generator that `yield`s leaves. If you need every leaf and there is no pruning at all, `itertools.product("01", repeat=n)` walks the same tree in C and is much faster than any Python recursion.

## Cost

Count the nodes, then multiply by the work done at each one.

- **b choices per level, depth d:** b^d leaves and (b^(d+1) - 1) / (b - 1) nodes in total, so the internal nodes add only a constant factor. For binary choices that is 2^(n+1) - 1 nodes: 15 for n = 3, 2,097,151 for n = 20.
- **Orderings of n items:** level k has n! / (n - k)! nodes and the total is about e times n!: 16 nodes for n = 3, 9,864,101 for n = 10 against 3,628,800 leaves.
- **Output:** copying a leaf of length n costs O(n), so listing all subsets costs O(n 2^n) and all permutations O(n · n!). When the output is that big, no algorithm can be faster.
- **Pruned trees:** the node count is the number of *valid prefixes*. For the no-adjacent-ones strings there are 1, 2, 3, 5, 8, ... valid prefixes of lengths 0, 1, 2, 3, 4 (Fibonacci numbers), so the tree grows like 1.618^n instead of 2^n.
- **Space:** O(depth) for `path` and the call stack, plus whatever you store.

A simple recursive call in CPython costs a few hundred nanoseconds; with real work per node expect between a few hundred thousand and a few million nodes per second. The last primer of this module turns that into limits on n.

## When to use it

- The answer is the whole list of configurations ("return all possible ...").
- You need *any* configuration satisfying constraints, and the inputs are small.
- You need a trustworthy brute force to stress-test a cleverer solution.

| Situation | Use |
|---|---|
| Every leaf wanted, no constraints between choices | `itertools.product`, `permutations`, `combinations` (C speed) |
| Constraints that kill prefixes early | Hand-written backtracking with pruning |
| Only a count or an optimum, and the future depends only on a small summary such as the index | Dynamic programming (next module) |
| A known polynomial algorithm exists (sorting, BFS, matching) | That algorithm, not search |

## Worked trace

`no_adjacent_ones(3)`, watching the shared `path` and the results:

```steps
**Choose** "0" three times: the path reaches length 3, a leaf, so record it
    path  {{0 0 0}}      res  000
---
**Unchoose** the last "0" and **choose** "1": "001" is valid, record it
    path  0 0 {{1}}      res  000 001
---
Unchoose twice to "0", choose "1" then "0": record "010"
    path  0 {{1 0}}      res  000 001 010
---
Unchoose "0" and try "1" after "01": **rejected** (two adjacent 1s), no call is made
    path  0 1 {{1}} x    res  000 001 010
---
Unchoose back to the root, choose "1", then "0", then "0": record "100"
    path  {{1 0 0}}      res  000 001 010 100
---
Unchoose the last "0" and choose "1": record "101"
    path  1 0 {{1}}      res  000 001 010 100 101
---
Back at "1", try "1": **rejected**; every loop has finished, so the search ends
    path  1 {{1}} x      res  000 001 010 100 101
```

## Template

```python
def backtrack_all(n, choices, ok):
    """Every length-n sequence over choices in which each new element passes ok(path, c)."""
    res, path = [], []

    def dfs():
        if len(path) == n:            # leaf: a complete candidate
            res.append(path[:])       # copy: path keeps changing after this
            return
        for c in choices:
            if not ok(path, c):
                continue              # prune: no completion of this prefix is valid
            path.append(c)            # choose
            dfs()                     # explore
            path.pop()                # unchoose

    dfs()
    return res
```

For example, `backtrack_all(3, "01", lambda p, c: not (c == "1" and p and p[-1] == "1"))` returns the same five strings as lists of characters.

## Pitfalls

- **Storing the live list.** `res.append(path)` stores a reference; after the search finishes `path` is empty, so every entry prints as `[]`. Store `path[:]`, `tuple(path)` or `"".join(path)`.
- **Undo in the wrong place.** The `pop()` must run after every `append()`, whatever the recursive call found. Putting it inside an `if` or after an early `return` leaves debris in `path` for the next sibling.
- **Filtering only at the leaves.** Checking validity only when the candidate is complete visits the whole 2^n tree; checking each prefix visits only valid prefixes.
- **Changing the collection you loop over.** Removing used items from `choices` while a `for` loop iterates over it skips elements; mark them used instead (next primers).

## Check yourself

Q: How many times is `dfs` called by `no_adjacent_ones(4)`, and how many strings does it return?
A: 19 calls and 8 strings. Calls happen once per valid prefix: 1 of length 0, 2 of length 1, 3 of length 2, 5 of length 3 and 8 of length 4, so 1 + 2 + 3 + 5 + 8 = 19, and the 8 prefixes of length 4 are the leaves that get recorded.

Q: You need all 4-letter strings over "ACGT" to feed a parser test. Hand-written backtracking or `itertools.product`?
A: `itertools.product("ACGT", repeat=4)`. There is no constraint to prune with, so every one of the 256 leaves is wanted; the library walks the same tree in C, lazily, with no recursion and no undo bugs.

Q: A colleague's version does `path.append(c); dfs(); ` and then `if len(res) < limit: path.pop()`. What goes wrong once the limit is reached?
A: After the limit, choices are appended and never popped, so `path` keeps growing: later nodes see a corrupted prefix, `len(path) == n` is skipped past, and the recursion can run off the intended depth. The undo must be unconditional; to stop early, return a flag (or raise) and still pop on the way out.

## Lab

- **1863 Sum of All Subset XOR Totals.** Draw the include/exclude tree for [1, 3] (four leaves), then write the backtracking that passes the running XOR down instead of storing subsets. Expected: [1, 3] gives 6, [5, 1, 6] gives 28 and [3, 4, 5, 6, 7, 8] gives 480; your function makes 2^(n+1) - 1 calls (15 for n = 3). Then check a curious fact on random inputs: the answer always equals (OR of all numbers) shifted left by n - 1.
- **Count before you run.** Add a call counter to `no_adjacent_ones` and predict the counts for n = 10 and n = 20 from the Fibonacci pattern before measuring. Expected: 375 calls and 144 strings for n = 10; 46,366 calls and 17,711 strings for n = 20.

> [!know]
> You now know how to see any exhaustive search as a tree, write it with choose, explore, unchoose, and count its nodes before running it.

=== primer | How do you generate every subset, and why are there exactly 2^n? | 14 min
goal: Generate all subsets three ways (start index, include or exclude, bitmask), explain the 2^n count, and pick the shape that suits the problem
tag: backtrack-subsets | Subsets: start index, include or exclude, bitmasks
link: USACO Guide: Complete Search with Recursion | https://usaco.guide/bronze/complete-rec#generating-subsets-recursively | 10 min: 'Generating Subsets Recursively' and 'Generating Subsets with Bitmasks', the same two shapes worked on the Apple Division problem
link: Python docs: itertools recipes | https://docs.python.org/3/library/itertools.html#itertools-recipes | 2 min: the powerset recipe (chain combinations of every size), the library way to list subsets when nothing needs pruning
practice: 78

> [!key]
> Each of the n elements is either in a subset or out of it: two independent choices, n times, so there are **2^n subsets**. You can walk them as an **include or exclude** tree (one level per element, subsets at the leaves), as a **start index** tree (every node is a subset and children only add later elements), or with **bitmasks** (count from 0 to 2^n - 1 and read bit i as "element i is in"). All three cost O(n 2^n) to list, which is also the size of the output.

## Intuition

A pizza place offers three toppings: olives, ham, peppers. For each topping you say yes or no, so there are 2 x 2 x 2 = 8 pizzas, from plain to everything. Write each pizza as three yes/no digits and you have the binary numbers 000 to 111: the number 101 means olives and peppers, no ham. That is the whole theory of subsets: n yes/no decisions, or equivalently the n-bit numbers.

## How it works

### Include or exclude: one level per element

Element i is decided at depth i. The left branch takes it, the right branch does not. Leaves are complete subsets; there are 2^n leaves and 2^(n+1) - 1 nodes.

```python
def subsets_in_out(nums):
    """Include or exclude: one binary decision per element; leaves are subsets."""
    res, path = [], []

    def dfs(i):
        if i == len(nums):
            res.append(path[:])
            return
        path.append(nums[i])                 # include nums[i]
        dfs(i + 1)
        path.pop()
        dfs(i + 1)                           # exclude nums[i]

    dfs(0)
    return res
```

This shape generalises when an element has more than two fates (give the item to Ann, to Bob or to nobody: three branches) and it is the shape you memoise in the next module, because the state is just `i` plus whatever summary you carry (a running sum, a running XOR).

### Start index: "which element comes next?"

Every node is itself a subset, so record at every node. A child may only add an element with a larger index than the last one used. That rule is why each subset appears exactly once: it can only be built in increasing index order, so [1, 2] is generated and [2, 1] never is.

```python
def subsets(nums):
    """Every subset of nums (distinct values), in 'start index' order."""
    res, path = [], []

    def dfs(start):
        res.append(path[:])                  # every node is a subset: record a copy
        for i in range(start, len(nums)):
            path.append(nums[i])             # choose nums[i] as the next element
            dfs(i + 1)                       # explore: only later elements may follow
            path.pop()                       # unchoose

    dfs(0)
    return res


print(subsets([1, 2, 3]))
# [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
```

This tree has exactly 2^n nodes (one per subset, no wasted internal nodes), and it is the shape that extends to combinations (stop at size k), combination sums and duplicate skipping in the next primers.

### Bitmasks: no recursion at all

```python
def subsets_bits(nums):
    """Bit i of mask says whether nums[i] is in the subset."""
    n = len(nums)
    return [[nums[i] for i in range(n) if mask >> i & 1] for mask in range(1 << n)]
```

In Python, `mask >> i & 1` parses as `(mask >> i) & 1` because shifts bind tighter than `&`. Bitmasks shine when the subset itself should be a number: a dictionary key, a DP state over subsets (advanced DP module), or a quick test such as `mask & (mask >> 1) == 0` for "no two adjacent elements chosen".

| Shape | Nodes visited | Output order for [1, 2, 3] | Best for |
|---|---|---|---|
| Include or exclude | 2^(n+1) - 1 | [1,2,3], [1,2], [1,3], [1], ... [] | Several fates per element; carrying a running value; converting to DP |
| Start index | 2^n | [], [1], [1,2], [1,2,3], [1,3], ... | Combinations, size limits, duplicate skipping, pruning by sum |
| Bitmask loop | 2^n iterations | [], [1], [2], [1,2], [3], ... | n up to about 20, subsets as integers, no recursion |

## Cost

- **Count:** each element doubles the number of subsets, so there are 2^n. Each subset takes O(n) to build, so listing is **O(n 2^n) time**. The output itself has n · 2^(n-1) elements in total (each element is in half the subsets), so no method can list them faster.
- **Space:** O(n) for the path and recursion, plus the output. The output is the problem at scale: storing all subsets of 20 elements creates 1,048,576 lists and took about 150 MB in CPython when measured. If you only need to test or score each subset, process it at the leaf instead of storing it.
- **Practical limit:** 2^20 is about a million, fine in Python in a second or two; 2^25 is 33 million, slow; 2^30 is a billion, out of reach. Beyond about 25 elements you need pruning, meet in the middle or DP (last primer of this module).

## When to use it

- "Return all subsets", "every possible group", "power set".
- Choosing any subset under a constraint when n is at most about 20: pick teammates, split items into two groups (each element: group A or group B is again a subset choice).
- As the **brute-force oracle** for subset-style DP: subset sum, 0/1 knapsack, partition. You will test next module's tables against exactly this enumeration.
- Not when n is 40 or more, or when only a count or a best value is needed and a small summary (index and remaining capacity) captures the future: that is dynamic programming.

## Worked trace

The start index version on [1, 2, 3]. Watch `path` grow and shrink, and notice that every node records a subset:

```steps
dfs(0): record the empty subset, then choose 1
    path []          res []
---
dfs(1) with path [1]: record it, choose 2
    path [{{1}}]        res [], [1]
---
dfs(2) with path [1, 2]: record it, choose 3
    path [1, {{2}}]     res [], [1], [1,2]
---
dfs(3) with path [1, 2, 3]: record it; no index is left, so return
    path [1, 2, {{3}}]  res [], [1], [1,2], [1,2,3]
---
**Unchoose** 3 and 2, then choose 3 straight after 1: record [1, 3]
    path [1, {{3}}]     res ..., [1,2,3], [1,3]
---
Unchoose back to the root; the loop moves on and chooses 2: record [2], then [2, 3]
    path [{{2}}, 3]     res ..., [1,3], [2], [2,3]
---
Finally choose 3 alone: record [3]. Eight subsets, eight calls, nothing generated twice
    path [{{3}}]        res ..., [2,3], [3]
```

## Template

```python
def subsets(nums):
    res, path = [], []

    def dfs(start):
        res.append(path[:])
        for i in range(start, len(nums)):
            path.append(nums[i])
            dfs(i + 1)
            path.pop()

    dfs(0)
    return res
```

To test any of the three versions, compare canonical forms: `sorted(sorted(s) for s in result)` against the same form built from `itertools.combinations(nums, r)` for every r.

## Pitfalls

- **Aliasing.** `res.append(path)` gives `[[], [], [], [], [], [], [], []]` for [1, 2, 3]: eight references to one list that ends empty.
- **`dfs(start + 1)` instead of `dfs(i + 1)`.** The child must continue after the element just chosen, not after the loop's starting point. With the wrong index, [1, 2, 3] produces 16 lists including [2, 2], [3, 2] and [3, 3, 3].
- **Duplicates in the input.** With [1, 2, 2] all three methods produce [1, 2] twice and [2] twice (8 subsets, only 6 distinct). The fix, sort and skip, is in the next primer.
- **Overflow in other languages.** In C++ or Java `1 << n` overflows a 32-bit int for n >= 31; write `1LL << n`. Python integers do not overflow.

## Check yourself

Q: What are the first and last subsets produced by `subsets_in_out([1, 2, 3])`, and why?
A: First [1, 2, 3], last []. The include branch is explored before the exclude branch at every level, so the leftmost leaf takes everything and the rightmost leaf takes nothing.

Q: Which mask makes `subsets_bits([4, 5, 6])` produce [4, 6], and in which position of the output list is it?
A: Mask 0b101 = 5 (bits 0 and 2 set), so it is at index 5 of the output: [], [4], [5], [4, 5], [6], [4, 6], ...

Q: Why can the start index tree never produce both [1, 2] and [2, 1]?
A: A child only chooses indices greater than the last one chosen, so every path lists its elements in increasing index order. Each set of indices has exactly one increasing ordering, hence exactly one node.

Q: You must split 18 weights into two groups with the smallest possible difference of sums. Which shape do you use and how many candidates do you check?
A: Each weight goes to group A or group B, which is a subset choice (the subset that goes to A), so 2^18 = 262,144 candidates. A bitmask loop or the include/exclude recursion carrying the running sum of group A both work; the recursion avoids rebuilding sums and can stop early on a difference of 0.

## Lab

- **78 Subsets.** Write the start index version from memory, then the bitmask version, and compare them in canonical form. Expected: [1, 2, 3] gives the 8 subsets [], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3] (any order is accepted); [0] gives [] and [0]; the time is O(n 2^n).
- **Agree with the library.** For random lists of distinct numbers with n from 0 to 10, assert that all three versions match the powerset recipe from the itertools docs in canonical form and that each returns exactly 2^n subsets. Expected: no assertion fails, and n = 10 gives 1,024 subsets.

> [!know]
> You now know how to list every subset with a start index, an include or exclude tree, or a bitmask, and why 2^n of them cost O(n 2^n).

=== primer | How do choose, explore, unchoose generate permutations and combinations without duplicates? | 15 min
goal: Generate permutations with a used array and k-combinations with a start index, and remove duplicate outputs caused by repeated input values by sorting and skipping equal siblings
tag: backtrack-perms | Permutations, combinations and duplicate skipping
link: USACO Guide: Complete Search with Recursion | https://usaco.guide/bronze/complete-rec#permutations | 10 min: 'Generating Permutations Recursively' and 'Lexicographical Order'; its problem, Creating Strings, is exactly the repeated-letters case
link: Python docs: itertools.permutations | https://docs.python.org/3/library/itertools.html#itertools.permutations | 3 min: the note that elements are unique by position, not value, so repeated values give repeated tuples
practice: 46, 90

> [!key]
> A **permutation** fills position after position with any element not used yet: keep a `used` array, mark before recursing, unmark after. A **combination** ignores order, so it only picks elements to the right of the last pick (a start index). When the input has **repeated values**, sort it and never try the same value twice at the same depth: for subsets and combinations skip `i > start and a[i] == a[i - 1]`; for permutations skip a copy whose equal left neighbour is still unused. Each distinct answer is then built exactly once.

## Intuition

Seat three guests on three chairs. Chair 1 can take any of the 3, chair 2 any of the 2 left, chair 3 the last one: 3 x 2 x 1 = 6 seatings. The "guests left" are exactly the unused elements, and putting a guest back in the queue when you try a different seating is the unchoose step.

Now pick a committee of 2 from 4 people. Order does not matter: Ann-and-Bob is Bob-and-Ann. If you always list members in alphabetical order (only pick people after the last one picked), each committee appears once: that is the start index.

Finally, two of the guests are identical twins. Swapping them gives the "same" seating, so 6 becomes 3. The cure is a rule that the twins always sit in a fixed order relative to each other.

## How it works

### Permutations: a used array

```python
def permutations(nums):
    """Every ordering of nums (distinct values)."""
    res, path, used = [], [], [False] * len(nums)

    def dfs():
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i, x in enumerate(nums):
            if used[i]:
                continue
            used[i] = True                   # choose x for the next position
            path.append(x)
            dfs()                            # explore
            path.pop()                       # unchoose
            used[i] = False

    dfs()
    return res
```

The output for [1, 2, 3] is in lexicographic order: [1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]. An in-place alternative swaps `nums[k]` with each later element, recurses on position k + 1 and swaps back; it needs no `used` array but does not produce lexicographic order.

### Combinations: a start index and a size

```python
def combinations(n, k):
    """Every k-subset of 1..n in increasing order."""
    res, path = [], []

    def dfs(start):
        if len(path) == k:
            res.append(path[:])
            return
        for x in range(start, n + 1):
            if k - len(path) > n - x + 1:    # not enough numbers left: prune
                break
            path.append(x)
            dfs(x + 1)
            path.pop()

    dfs(1)
    return res
```

The `break` is a first taste of pruning: if you still need 3 numbers but only 2 remain, no completion exists, and every later x has even fewer remaining.

### Duplicates: sort, then skip equal siblings

Equal values are interchangeable, so the fix is to decide that among equal values only one representative choice is ever explored at each position of the tree.

```python
def subsets_with_dup(nums):
    """Distinct subsets when nums may contain repeats."""
    nums = sorted(nums)
    res, path = [], []

    def dfs(start):
        res.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue                     # same value already tried at this depth
            path.append(nums[i])
            dfs(i + 1)
            path.pop()

    dfs(0)
    return res
```

Why `i > start` and not `i > 0`? The rule must stop a value being chosen twice **as the same next element** (siblings), not stop it being used twice **in one subset** (parent and child). For [1, 2, 2]: at depth 1 after [1], index 1 picks the first 2; then at depth 2 the second 2 is at `i == start`, so [1, 2, 2] is allowed. Back at depth 1, index 2 is a sibling of index 1 with the same value, so it is skipped. Result: [], [1], [1, 2], [1, 2, 2], [2], [2, 2], six distinct subsets instead of eight lists with repeats.

For permutations, there is no start index, so the rule is stated with `used`: **copies of a value must be used left to right**. Skip `nums[i]` if `nums[i] == nums[i - 1]` and `nums[i - 1]` is not yet used. Then the twins can only appear in one relative order, and [1, 1, 2] gives [1, 1, 2], [1, 2, 1], [2, 1, 1]. The variant `used[i - 1]` (right to left) is also correct, but it rejects duplicates later: on eight 1s it visits 2,781 nodes instead of 9.

## Cost

- **Permutations:** n! leaves, each copied in O(n), and about e · n! nodes in total, so **O(n · n!) time**, O(n) extra space. Measured in CPython: all 362,880 permutations of 9 elements by this recursion took about 2 s (986,410 nodes); `itertools.permutations(range(10))` produced 3,628,800 tuples in a couple of seconds. Ten elements is roughly the end of the road for Python recursion.
- **Combinations:** C(n, k) leaves, O(k) each. C(30, 5) = 142,506 is easy; C(40, 20) is 1.4 × 10^11 and is not.
- **Distinct permutations** of a multiset: n! divided by the factorial of each value's count, for example "aabbc" has 5! / (2! · 2!) = 30. The skip rule makes the work proportional to this smaller number. Generating all n! and calling `set()` afterwards does the full work: deduplicating the permutations of ten equal values builds 3.6 million tuples to keep one.

## When to use it

| You need | Tool |
|---|---|
| All orderings, no constraints, distinct values | `itertools.permutations` |
| All k-subsets, no constraints | `itertools.combinations` |
| Orderings or subsets with repeated values, without duplicates | Sort and skip (this primer) |
| Orderings with constraints that kill prefixes (no two equal neighbours, partial sums) | Hand-written backtracking with pruning |
| The best ordering when only "which items are used and the last one" matters | Bitmask DP, O(2^n · n^2) instead of n! (advanced DP module) |

The itertools functions do not prune and treat equal values at different positions as different, so they are right only for the unconstrained, distinct case.

## Worked trace

Permutations of [1, 2, 3], showing the shared `path` and `used` flags:

```steps
Choose 1, then 2, then 3: a full path, record [1, 2, 3]
    path [1, 2, 3]   used {{T T T}}   res [1,2,3]
---
**Unchoose** 3, then **unchoose** 2: path [1], only 1 is used
    path [1]         used T {{F F}}   res [1,2,3]
---
The loop at depth 1 moves on and chooses 3
    path [1, {{3}}]     used T F {{T}}   res [1,2,3]
---
At depth 2 the only unused element is 2: record [1, 3, 2]
    path [1, 3, {{2}}]  used T {{T}} T   res [1,2,3] [1,3,2]
---
Unchoose 2, unchoose 3, unchoose 1: back at the root, nothing used
    path []          used {{F F F}}   res [1,2,3] [1,3,2]
---
The root loop chooses 2, then the smallest unused, 1, then 3: record [2, 1, 3]
    path [{{2}}, 1, 3]  used T T T   res ... [2,1,3]
---
The same pattern finishes [2, 3, 1], [3, 1, 2], [3, 2, 1]: six leaves in all
    path []          used F F F   res 6 permutations
```

## Template

```python
def permutations_with_dup(nums):
    """Distinct orderings when nums may contain repeats."""
    nums = sorted(nums)
    res, path, used = [], [], [False] * len(nums)

    def dfs():
        if len(path) == len(nums):
            res.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                continue                     # equal copies must be used left to right
            used[i] = True
            path.append(nums[i])
            dfs()
            path.pop()
            used[i] = False

    dfs()
    return res
```

With distinct values the skip line never fires, so this one function covers both cases.

## Pitfalls

- **Forgetting to sort.** The skip rules compare neighbours; on unsorted input equal values are not adjacent and duplicates slip through.
- **`i > 0` where `i > start` is needed** (subsets, combinations): it forbids a value from being reused deeper in the same path and loses [1, 2, 2] and [2, 2].
- **Unmarking in the wrong order.** Reset `used[i]` after the recursive call returns, not before; and reset it on every path out of the loop body.
- **Using `x in path` to test "used".** It works for distinct values but is O(n) per check and wrong with duplicates; index-based `used` is O(1) and correct.

## Check yourself

Q: In the trace, right after [1, 3, 2] is recorded, what are `path` and `used` after the next two unchoose steps, and what is the next element chosen?
A: After unchoosing 2: path [1, 3], used [T, F, T]. After unchoosing 3: path [1], used [T, F, F]. The depth 1 loop has no elements left after index 2, so 1 is unchosen too, and the root loop chooses 2 next.

Q: How many lists does `subsets_with_dup([2, 1, 2, 2])` return, and how many would `subsets` (the version without the skip) return on the same input?
A: 8 distinct subsets ([], [1], [1, 2], [1, 2, 2], [1, 2, 2, 2], [2], [2, 2], [2, 2, 2]): the count of 1s is 0 or 1 and the count of 2s is 0 to 3, so 2 x 4 = 8. Without the skip you get all 2^4 = 16 lists with repeats.

Q: Prove that the left-to-right rule for permutations never loses a distinct permutation.
A: Take any distinct permutation and label the copies of each value in the order they appear in it: first copy, second copy, and so on. Assigning the sorted copies in that same order is a valid sequence of choices that never breaks the rule, because each copy is chosen only after the one to its left. So every distinct permutation has at least one path, and the rule allows only that labelling, so exactly one.

## Lab

- **46 Permutations.** Write the used-array version from memory. Expected: [1, 2, 3] gives 6 orderings, [0, 1] gives [0, 1] and [1, 0], [1] gives [[1]]; O(n · n!) time and O(n) extra space.
- **90 Subsets II.** Sort, then skip equal siblings with `i > start`. Expected: [1, 2, 2] gives [], [1], [1, 2], [1, 2, 2], [2], [2, 2]; [0] gives [] and [0]; [4, 4, 4, 1, 4] gives 10 subsets (0 or 1 copy of 1, times 0 to 4 copies of 4). Then deliberately change `i > start` to `i > 0` and watch [1, 2, 2] lose two answers.

> [!know]
> You now know how to generate permutations and combinations with choose, explore, unchoose, and how sorting plus skipping equal siblings removes duplicates without extra work.

=== primer | How do you build partitions and well-formed strings piece by piece? | 15 min
goal: Solve construction problems (cuts of a string, multisets that hit a target, balanced brackets) by choosing the next piece and keeping only prefixes that can still be completed
tag: backtrack-build | Constructions: partitions, combination sums, brackets
link: Erickson, Algorithms, ch. 2 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf#page=10 | 15 min: section 2.5 'Text Segmentation' (PDF pages 10-15): choose where the first word ends, recurse on the rest, and see why the same suffixes are solved again and again, the doorway to dynamic programming
practice: 22, 131, 39

> [!key]
> Many answers are sequences of **pieces**: the next cut of a string, the next coin of a sum, the next bracket. Keep as state the position reached and a few counters, let the choices be the pieces that may come next, and test each prefix with a rule that says "this can still be completed". If the rule is exact, every leaf is an answer and the search does no wasted work; if it is merely safe, it still removes whole subtrees.

## Intuition

You cut a ribbon of letters into segments, and every segment must read the same backwards. Where does the first cut go? Try each position whose first segment is a palindrome; whatever is left is the same problem on a shorter ribbon. That is the whole algorithm: one decision (where this piece ends), then delegate the rest.

Brackets work the same way with counters instead of positions. Writing a balanced string of three pairs, you may open a bracket while you have openers left, and close one only while some opener is unmatched. Respect those two rules at every step and you can never get stuck, so every string you finish is valid.

## How it works

### Partitions: choose where the next piece ends

```python
def partition_palindromes(s):
    """Every way to cut s into pieces that are all palindromes."""
    n = len(s)
    pal = [[False] * (n + 1) for _ in range(n + 1)]     # pal[i][j]: s[i:j] is a palindrome
    for i in range(n, -1, -1):
        for j in range(i, n + 1):
            pal[i][j] = j - i < 2 or (s[i] == s[j - 1] and pal[i + 1][j - 1])
    res, path = [], []

    def dfs(start):
        if start == n:
            res.append(path[:])
            return
        for end in range(start + 1, n + 1):             # choose where the next piece ends
            if pal[start][end]:
                path.append(s[start:end])
                dfs(end)
                path.pop()

    dfs(0)
    return res


print(partition_palindromes("aab"))   # [['a', 'a', 'b'], ['aa', 'b']]
```

The `pal` table is filled from short ranges to long ones so that `pal[i + 1][j - 1]` is ready when `pal[i][j]` needs it: a small dynamic programming table that turns each palindrome test into an O(1) lookup.

### Combination sums: reuse means "stay on this index"

```python
def combination_sum(candidates, target):
    """Multisets of candidates (each reusable) that sum to target; candidates distinct and positive."""
    cs = sorted(candidates)
    res, path = [], []

    def dfs(start, remaining):
        if remaining == 0:
            res.append(path[:])
            return
        for i in range(start, len(cs)):
            if cs[i] > remaining:
                break                                   # sorted: every later candidate is too big too
            path.append(cs[i])
            dfs(i, remaining - cs[i])                   # i, not i + 1: cs[i] may be used again
            path.pop()

    dfs(0, target)
    return res


print(combination_sum([2, 3, 5], 8))   # [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
```

Two details carry the whole problem. Recursing with `i` lets the same candidate repeat, while the start index still forbids going back to smaller candidates, so [2, 3, 3] appears once and [3, 2, 3] never. Sorting turns "too big" into a `break` rather than a `continue`, because once one candidate overshoots, every later one does.

### Brackets: counters are the state

```python
def generate_parentheses(n):
    """Every well-formed string of n pairs."""
    res, path = [], []

    def dfs(opened, closed):
        if len(path) == 2 * n:
            res.append("".join(path))
            return
        if opened < n:                                  # an opener is always completable
            path.append("("); dfs(opened + 1, closed); path.pop()
        if closed < opened:                             # a closer needs an unmatched opener
            path.append(")"); dfs(opened, closed + 1); path.pop()

    dfs(0, 0)
    return res
```

For n = 3 it returns `((()))`, `(()())`, `(())()`, `()(())`, `()()()`. The two rules are exact: any prefix with `closed <= opened <= n` can be finished (add the missing openers, then all the closers), and any prefix breaking them cannot. So the search never enters a dead branch.

## Cost

- **Palindrome partitions:** a string of length n has n - 1 gaps, each cut or not, so at most 2^(n-1) partitions; the worst case is a string of one repeated letter, where every one of them is valid. With O(n) to copy each answer, that is **O(n · 2^n)** time, plus O(n^2) time and space for the table.
- **Brackets:** the number of answers is the Catalan number C(n): 1, 2, 5, 14, 42, 132, 429, 1430 for n = 1 to 8, which grows like 4^n / (n^1.5 · 1.77). Because the rules are exact, every node lies on the way to some answer, so the total work is **O(n · C(n))**, against 2^(2n) strings if you generated everything and filtered: 256 strings to keep 14 when n = 4, and 65,536 to keep 1,430 when n = 8.
- **Combination sums:** depth at most target / (smallest candidate); the sorted `break` means every node that is entered has room left. The count is output-sensitive and has no neat closed form.

## When to use it

- "All ways to split, cut, segment or build" something under a validity rule.
- Problems where a prefix can be checked cheaply: palindromic pieces, dictionary words, balanced counts, partial sums within a bound.
- Not when the question is only **how many** ways or **whether** one exists and the rest of the problem depends only on where you are (the position, the remaining sum). Then the same suffix is solved again and again (Erickson's text segmentation shows it), and you should memoise: counting decodings of a digit string and "can this string be split into dictionary words" are dynamic programming in the next module. Listing every answer stays backtracking, since the output itself can be exponential.

## Worked trace

`partition_palindromes("aab")`, watching the pieces in `path`:

```steps
start 0: piece "a" (s[0:1]) is a palindrome: choose it
    a a b      path [{{a}}]
---
start 1: piece "a" (s[1:2]) is a palindrome: choose it
    a a b      path [a, {{a}}]
---
start 2: piece "b" is a palindrome; start 3 is the end: record
    a a b      path [a, a, {{b}}]      res [a,a,b]
---
Unchoose "b" and the second "a"; at start 1 try "ab": not a palindrome, skip
    a {{a b}}      path [a]            res [a,a,b]
---
Unchoose "a"; at start 0 try "aa": a palindrome, choose it
    {{a a}} b      path [{{aa}}]
---
start 2: choose "b", reach the end: record
    a a {{b}}      path [aa, {{b}}]       res [a,a,b] [aa,b]
---
Unchoose; at start 0 try "aab": not a palindrome. Done: two partitions
    {{a a b}}      path []             res [a,a,b] [aa,b]
```

## Template

```python
def all_splits(s, ok):
    """Every way to cut s into consecutive pieces p with ok(p) True."""
    res, path = [], []

    def dfs(start):
        if start == len(s):
            res.append(path[:])
            return
        for end in range(start + 1, len(s) + 1):
            piece = s[start:end]
            if ok(piece):                   # the prefix stays completable only through valid pieces
                path.append(piece)
                dfs(end)
                path.pop()

    dfs(0)
    return res
```

`all_splits("aab", lambda p: p == p[::-1])` gives the palindrome partitions; `all_splits(text, words.__contains__)` lists every segmentation into dictionary words.

## Pitfalls

- **`dfs(i + 1)` in combination sum.** It forbids reuse, so [2, 3, 6, 7] with target 7 returns only [[7]] and loses [2, 2, 3].
- **`continue` without sorting.** Without sorting, an overshooting candidate does not imply the next one overshoots; with sorting, use `break` to stop the loop.
- **Validity checked only at the end.** Generating all 2^(2n) bracket strings and filtering is correct but wastes almost all the work; check each prefix.
- **Slicing inside hot loops.** `s[start:end] == s[start:end][::-1]` costs O(length) per test; for long strings precompute the palindrome table as above.

## Check yourself

Q: Predict the output of `combination_sum([2, 3, 5], 8)` in order.
A: [[2, 2, 2, 2], [2, 3, 3], [3, 5]]. Sorted candidates and the start index list each multiset in non-decreasing order, and the depth-first order puts every answer starting with 2 before those starting with 3.

Q: Why does `generate_parentheses` never reach a dead end?
A: It only extends prefixes with closed <= opened <= n. Any such prefix can be completed by adding n - opened openers and then n - closed closers, so every branch it enters leads to at least one valid string, and every leaf it reaches has length 2n and is valid.

Q: How many palindrome partitions does "aaaa" have, and how many does "abcd" have?
A: "aaaa": 8, because every substring is a palindrome and each of the 3 gaps can be cut or not (2^3). "abcd": 1, only single letters are palindromes, so the only partition is a, b, c, d.

## Lab

- **22 Generate Parentheses.** Use the two counters. Expected: n = 3 gives the 5 strings above, n = 1 gives ["()"], and the counts for n = 1..8 are 1, 2, 5, 14, 42, 132, 429, 1430.
- **131 Palindrome Partitioning.** Precompute the table, then cut. Expected: "aab" gives [["a", "a", "b"], ["aa", "b"]], "a" gives [["a"]], and "aabb" gives 4 partitions.
- **39 Combination Sum.** Sort, recurse with `i`, `break` on overshoot. Expected: [2, 3, 6, 7] with target 7 gives [[2, 2, 3], [7]], [2, 3, 5] with target 8 gives 3 combinations, [2] with target 1 gives [].

> [!know]
> You now know how to construct answers piece by piece, with the position and a few counters as state, and how an exact "still completable" rule makes every branch productive.

=== primer | How does pruning make exponential search fast enough? | 15 min
goal: Cut search trees with feasibility, bound and symmetry rules and with a good choice order, check that each rule is safe, and measure its effect in nodes visited
tag: backtrack-prune | Pruning: feasibility, bounds, symmetry, ordering
link: Competitive Programmer's Handbook (free PDF) | https://cses.fi/book/book.pdf#page=61 | 10 min: section 5.4 'Pruning the search' (PDF pages 61-63): five successive observations take a 7x7 grid path count from 483 seconds and 76 billion calls to 0.6 seconds
link: Wikipedia: Branch and bound | https://en.wikipedia.org/wiki/Branch_and_bound#Generic_version | 8 min: 'Generic version': the incumbent, the bound function and the rule "discard a node whose bound cannot beat the incumbent"
practice: 698, 2305

> [!key]
> A pruning rule proves that **nothing below this node can be an answer**, or cannot beat the best answer found so far, and skips the whole subtree. Use three kinds: **feasibility** (the prefix already breaks a constraint that can only get worse), **bound** (an optimistic estimate of the best completion cannot beat the incumbent: branch and bound) and **symmetry** (the subtree mirrors one already explored). Then **order** the choices so good answers come early, because a better incumbent makes every bound bite harder. Pruning rarely changes the worst-case big-O, but on real instances it often removes almost the whole tree.

## Intuition

Packing a suitcase with a weight limit to carry the most value. If the bag is already over the limit, no amount of extra packing fixes it: stop (feasibility). If you have already found a packing worth 11 and the items still on the bed are worth 9 in total, then even taking all of them from an empty bag gives 9: this branch cannot win, stop (bound). If two items are identical, trying the first and then the second is the same as trying them the other way round: skip one (symmetry). And you will find good packings sooner if you consider the most valuable-per-kilo items first (ordering).

## How it works

### Feasibility: constraints that only get worse

A feasibility rule is safe when a violation can never be undone by later choices. With positive numbers, "the running sum exceeds the target" qualifies; with negative numbers it does not, because a later negative could bring the sum back. Before adding any prune, write down the monotonicity it relies on. Earlier primers already used feasibility: the bracket counters, the sorted `break` in combination sum, "not enough elements left" for combinations.

### Bounds: branch and bound

For an optimisation search, keep the best complete answer so far (the **incumbent**) and, at each node, compute an **optimistic bound**: a value at least as good as any completion of this prefix. If the bound cannot beat the incumbent, cut. The bound must never underestimate (for a maximisation), or you will cut the true optimum. For 0/1 knapsack, "current value plus the value of every remaining item" is a valid, simple bound:

```python
def best_value(items, cap):
    """0/1 knapsack by backtracking with feasibility and bound pruning.
    items: list of (weight, value); returns (best value, nodes visited)."""
    items = sorted(items, key=lambda wv: wv[1] / wv[0], reverse=True)   # promising first
    n = len(items)
    suffix = [0] * (n + 1)                     # suffix[i] = total value of items[i:]
    for i in range(n - 1, -1, -1):
        suffix[i] = suffix[i + 1] + items[i][1]
    best, nodes = 0, 0

    def dfs(i, room, value):
        nonlocal best, nodes
        nodes += 1
        best = max(best, value)
        if i == n or value + suffix[i] <= best:
            return                             # bound: even taking everything left cannot win
        w, v = items[i]
        if w <= room:                          # feasibility: only take what fits
            dfs(i + 1, room - w, value + v)
        dfs(i + 1, room, value)

    dfs(0, cap, 0)
    return best, nodes
```

Stronger bounds prune more but cost more to compute. The classic stronger bound for knapsack fills the remaining room greedily by value density and takes a fraction of the first item that does not fit; it is the same idea as the linear-programming relaxations that integer-programming solvers use as bounds.

### Symmetry: do not explore mirror images

If two subtrees are guaranteed to contain equivalent answers, explore one. You have already seen this: skipping equal values at the same depth (previous primers). Other forms: in N-queens the boards with the first queen in the right half mirror those with it in the left half, so search half and double the count (careful with the middle column when n is odd); in the handbook's grid-path search, every path that starts by going right mirrors one that starts by going down.

### Ordering: find a good incumbent early

Order affects nothing about correctness and everything about speed. Trying items by value density, highest first, finds a near-optimal packing in the first few leaves, and from then on the bound cuts almost everything. The same instance of 20 items took 5,516 nodes with density order, 20,378 in input order and 74,049 with the worst items first.

## Cost

Worst-case cost stays exponential: an adversarial instance can defeat any cheap prune. What changes is the typical node count, which you should **measure**. On random knapsack instances (weights and values 10 to 60, capacity half the total weight) in CPython:

| n | No pruning | Feasibility only | Feasibility + bound + density order |
|---|---|---|---|
| 20 | 2,097,151 nodes, 0.75 s | 1,224,944 nodes, 1.1 s | 5,516 nodes, 0.005 s |
| 25 | 67,108,863 nodes (about 25 s, not run) | 39,086,389 nodes, 28 s | 73,651 nodes, 0.07 s |

Two lessons hide in that table. Feasibility alone saved only 40% of the nodes and was *slower* per node at n = 20, because each node does more work; a prune must save more than it costs. The bound, helped by the ordering, removed over 99.7% of the tree. Dynamic programming solves the same problem in O(n · capacity), which wins when the capacity is small; branch and bound wins when weights are huge (no table fits) and the bound is tight.

## When to use it

- Always add the cheap, obviously safe prunes: they are free speed.
- Add bounds whenever the search is an optimisation ("minimum", "maximum", "fewest").
- Look for symmetry when the problem has interchangeable parts: equal values, mirror boards, identical containers.
- Do not trust a prune you cannot justify in one sentence ("this can only get worse because..."). Test the pruned search against the unpruned one on small inputs.

## Worked trace

Items A (weight 3, value 10), B (2, 4), C (2, 4), D (1, 1), capacity 4. Density order is A, B, C, D, so `suffix` is [19, 9, 5, 1, 0].

```steps
Root: best 0, bound 0 + 19 = 19 > 0. Take A (it fits)
    at A   room 4  value 0   bound {{19}}  best 0
---
After A: best 10, bound 10 + 9 = 19. B weighs 2 > room 1: **infeasible**, skip the take branch
    at B   room 1  value 10  bound 19  best {{10}}
---
Skip B. C also weighs 2 > room 1: skip its take branch too
    at C   room 1  value 10  bound 15  best 10
---
Skip C. D fits: take it. Bound 10 + 1 = 11 > 10, so continue
    at D   room 1  value 10  bound 11  best 10
---
Leaf after taking D: value 11 becomes the incumbent
    leaf   room 0  value {{11}}  best {{11}}
---
Leaf after skipping D: value 10, nothing new. Back up to the root
    leaf   room 1  value 10  best 11
---
Root, skip A: bound 0 + 9 = 9 <= 11, **cut**. The 14 nodes below it are never visited
    at B   room 4  value 0   bound {{9}}   best 11  CUT
```

Seven nodes instead of 31, and the answer, A plus D for 11, is proved optimal: B plus C would give only 8.

## Template

```python
def branch_and_bound(choices_of, bound, value, is_complete, root):
    """Maximise value over complete states; children from choices_of; bound must never underestimate."""
    best = None

    def dfs(state):
        nonlocal best
        if is_complete(state):
            if best is None or value(state) > best:
                best = value(state)
            return
        if best is not None and bound(state) <= best:
            return                                   # this subtree cannot beat the incumbent
        for child in choices_of(state):              # order: most promising first
            dfs(child)

    dfs(root)
    return best
```

In practice you write the specialised version, as in `best_value`, with mutable state and undo; this skeleton shows the shape: complete, bound, branch.

## Pitfalls

- **Unsafe bounds.** For maximisation the bound must be at least the best completion; a bound that sometimes underestimates cuts the optimum and returns a wrong answer that looks plausible.
- **Prunes that depend on monotonicity you do not have:** negative numbers, costs that can decrease, constraints that later choices can repair.
- **Forgetting `nonlocal best`** (or a one-element list) so the incumbent is updated in a local variable and never prunes anything.
- **Over-engineered bounds.** A bound that costs O(n) per node must cut much more than a factor n of nodes to pay off. Measure.

## Check yourself

Q: In the trace, why is "skip A" cut without visiting a single node below it?
A: Without A the best possible value is 0 plus all remaining values, 4 + 4 + 1 = 9, and the incumbent is already 11. Since 9 <= 11, no completion of that prefix can beat the incumbent.

Q: A colleague prunes combination sum with `if remaining < 0: return` on input that may contain negative numbers. Give a counterexample.
A: Candidates [5, -3], each usable once, target 2. Choosing 5 first gives remaining -3, which is pruned, yet 5 + (-3) = 2 is the answer. The prune assumes sums only grow, which negative numbers break.

Q: Why does the ordering change the node count but never the answer?
A: Ordering only changes which leaves are reached first. Every prune is still justified by a valid bound against the current incumbent, so the optimum is never cut; a good order just makes the incumbent good earlier, which makes more bounds succeed.

## Lab

- **698 Partition to K Equal Sum Subsets** (derive). First write the plain search: each number goes into one of k buckets, no bucket may exceed total / k. Count nodes, then add one prune at a time (sort descending, then look for symmetry between buckets) and count again. Expected: [4, 3, 2, 3, 5, 2, 1] with k = 4 gives True; [1, 2, 3, 4] with k = 3 gives False; [2, 2, 2, 2, 3, 4, 5] with k = 4 gives False.
- **2305 Fair Distribution of Cookies.** Minimise the largest child's total: an optimisation, so keep an incumbent and cut any branch where a child's total already reaches it. Expected: [8, 15, 10, 20, 8] with k = 2 gives 31; [6, 1, 3, 2, 2, 4, 1, 2] with k = 3 gives 7; [5, 5, 5, 5] with k = 2 gives 10. Record your node counts with and without each prune.

> [!know]
> You now know how to make exponential search practical with safe feasibility, bound and symmetry prunes and a good choice order, and how to measure that they pay off.

=== primer | How do you solve N-queens and Sudoku with O(1) conflict checks? | 16 min
goal: Model a puzzle as variables, domains and constraints, check conflicts in O(1) with sets, and branch on the most constrained variable first
tag: backtrack-csp | Constraint satisfaction: N-queens and Sudoku
link: Erickson, Algorithms, ch. 2 (free PDF) | https://jeffe.cs.illinois.edu/teaching/algorithms/book/02-backtracking.pdf#page=1 | 12 min: section 2.1 'N Queens' (PDF pages 1-4): the row-by-row recursion, its proof of correctness and the recursion tree for n = 4
link: Peter Norvig: Solving every Sudoku puzzle | https://norvig.com/sudoku.html | 20 min: read 'Constraint Propagation' and 'Search' (variable ordering by minimum remaining values), then skim 'Results'; one essay, no section anchors
practice: 51, 37

> [!key]
> A **constraint satisfaction problem** has variables, a domain of values for each, and constraints between them. Backtracking assigns one variable per level and undoes on return; the two things that make it fast are **O(1) conflict checks** (keep a set per constraint of the values already used: columns and both diagonals for queens; rows, columns and boxes for Sudoku) and **choosing the most constrained variable next** (fewest legal values), so dead ends show up near the root, where cutting them saves the most.

## Intuition

You are seating guests at a wedding with a list of "these two must not sit together". If you seat the easy guests first, you discover at the very end that the difficult uncle fits nowhere, and you have to undo almost everything. Seat the difficult uncle first, when he still has options, and conflicts surface immediately. That is the most-constrained-first rule, and it is why good Sudoku solvers look for the cell with the fewest candidates.

And you would never check "does this seat conflict?" by walking around the whole table: you keep a list of who is at each table. That is the set-per-constraint idea.

## How it works

### N-queens: one queen per row

Place n queens on an n x n board so no two share a row, column or diagonal. Since every row holds exactly one queen, make the **rows the variables** and the column the value: row r chooses a column c. Three sets record what is taken:

- `cols`: columns already used.
- `diag`: values of **r - c** already used. Moving down-right adds 1 to both r and c, so r - c is constant along a down-right diagonal.
- `anti`: values of **r + c** already used. Moving down-left adds 1 to r and subtracts 1 from c, so r + c is constant along an anti-diagonal.

```python
def solve_n_queens(n):
    """All boards with n non-attacking queens, one queen per row."""
    cols, diag, anti = set(), set(), set()     # r - c is constant on a diagonal, r + c on an anti-diagonal
    queen_col = [0] * n
    res = []

    def place(r):
        if r == n:
            res.append(["." * c + "Q" + "." * (n - c - 1) for c in queen_col])
            return
        for c in range(n):
            if c in cols or r - c in diag or r + c in anti:
                continue                       # attacked: O(1) check with three sets
            cols.add(c); diag.add(r - c); anti.add(r + c); queen_col[r] = c
            place(r + 1)
            cols.remove(c); diag.remove(r - c); anti.remove(r + c)

    place(0)
    return res
```

Rows never conflict by construction, so the representation itself removed one constraint. For extra speed the three sets become three integers used as bitmasks, but the logic is identical.

### Sudoku: 81 variables, 27 units

Each empty cell is a variable with domain 1 to 9; each row, column and 3 x 3 box is a unit whose digits must differ. Keep a set of used digits per row, column and box, so a cell's candidates are `digits - rows[r] - cols[c] - boxes[b]` with `b = r // 3 * 3 + c // 3`. Then always branch on the empty cell with the **fewest candidates**:

```python
def pick_cell(empty, rows, cols, boxes):
    """Most constrained first: the empty cell with the fewest legal digits, and those digits."""
    digits = set("123456789")
    best = None
    for r, c in empty:
        cand = digits - rows[r] - cols[c] - boxes[r // 3 * 3 + c // 3]
        if best is None or len(cand) < len(best[2]):
            best = (r, c, cand)
            if len(cand) <= 1:
                break                          # forced (or dead): cannot do better
    return best
```

A cell with zero candidates means the current partial grid is already doomed, and the search backs up immediately; a cell with one candidate is a forced move with no branching at all. Real solvers go further: after each assignment they **propagate** (remove the digit from every peer's candidates and fill any cell left with one option), as in Norvig's essay, or encode the puzzle as **exact cover** and use Knuth's Dancing Links.

## Cost

- **N-queens:** row-by-row placement with a column set allows at most n! leaves, and the diagonal sets cut far more. Measured in CPython: n = 8 visits 2,057 nodes for its 92 solutions (compare 8! = 40,320 permutations, 8^8 = 16.8 million one-per-row boards, and 4.4 billion ways to pick any 8 squares); n = 10 visits 35,539 nodes (724 solutions); n = 12 visits 856,189 nodes (14,200 solutions) in about 4 seconds. Each node does O(n) checks of O(1) each, so time is O(n) per node; space is O(n).
- **Sudoku:** the naive bound is 9^(empty cells), astronomically large, and the real cost depends almost entirely on ordering. On 20 test puzzles (10 easy, 10 hard), filling cells in reading order needed over a million nodes on 7 of the hard ones, while most-constrained-first solved all 20 with about 411,000 nodes in total and about 150 nodes on an easy puzzle (the lab reproduces this).

## When to use it

- Puzzles and configuration problems with hard "must differ" or "must not attack" rules and small, fixed sizes: N-queens, Sudoku, KenKen, graph colouring of small graphs, timetables with a handful of slots.
- Any search where some variables are far more constrained than others: ordering pays off most there.
- For large industrial instances (timetabling a university, configuring a product line, verifying a circuit) do not write your own: encode the problem for a **SAT or CP solver** (OR-Tools CP-SAT, MiniSat). They run the same backtracking with propagation, learned constraints and decades of engineering.
- Not when only a count is needed and a formula or DP exists, and not when constraints are soft costs (then it is optimisation: branch and bound, or local search).

## Worked trace

4-queens, one row at a time. Q is a queen, x marks a square attacked by queens already placed:

```steps
Row 0: column 0 is free, place a queen
    {{Q}} . . .
    . . . .
    . . . .
    . . . .
---
Row 1: columns 0 and 1 are attacked; place at column 2
    Q . . .
    x x {{Q}} .
    . . . .
    . . . .
---
Row 2: every column is attacked: **dead end**. Remove the row 1 queen, try column 3
    Q . . .
    x x . {{Q}}
    . . . .
    . . . .
---
Row 2: column 0 attacked, place at column 1
    Q . . .
    . . . Q
    x {{Q}} . .
    . . . .
---
Row 3: all four columns attacked: dead end. Rows 2 and 1 have no columns left either, so back up to row 0
    {{Q}} . . .
    . . . Q
    . Q . .
    x x x x
---
Row 0 moves to column 1; row 1 skips columns 0-2 and takes column 3
    . {{Q}} . .
    x x x {{Q}}
    . . . .
    . . . .
---
Row 2 takes column 0; row 3 skips columns 0 and 1 and takes column 2: a **solution**
    . Q . .
    . . . Q
    {{Q}} . . .
    x x {{Q}} .
```

Recorded as columns per row, the first solution is [1, 3, 0, 2]; the search then continues and finds its mirror image [2, 0, 3, 1].

## Template

```python
def count_n_queens(n):
    """Number of solutions, with the three constraint sets as bitmasks."""
    full = (1 << n) - 1

    def place(cols, diag, anti):
        if cols == full:
            return 1
        total = 0
        free = full & ~(cols | diag | anti)    # columns not attacked in this row
        while free:
            bit = free & -free                 # lowest free column
            free ^= bit
            total += place(cols | bit, (diag | bit) << 1 & full, (anti | bit) >> 1)
        return total

    return place(0, 0, 0)
```

Here `diag` and `anti` hold the squares attacked *in the current row*: shifting them by one per row moves each diagonal along. The logic is the set version's, with every set operation a single machine instruction.

## Pitfalls

- **Checking diagonals with `abs(r1 - r2) == abs(c1 - c2)` against every placed queen.** Correct, but O(n) per check; the sets make it O(1).
- **Undoing in the wrong order or forgetting one set.** Remove exactly what you added, after the recursive call; a forgotten `diag.remove` makes later boards look attacked and silently loses solutions.
- **Copying the board at every node.** Build the output strings only at the leaves (or store columns and render at the end).
- **Sudoku without restoring the cell.** If `search` fails, reset the cell to "." and put it back on the empty list before returning, or later branches see a phantom digit.
- **Odd n with the mirror trick.** Halving the first row and doubling counts the middle column twice; handle it separately.

## Check yourself

Q: Which squares of a 5 x 5 board does a queen at row 1, column 3 forbid in row 3?
A: Columns 1 and 3. Column 3 is the same column; column 1 is on the same anti-diagonal (r + c = 4, and 3 + 1 = 4); the same diagonal (r - c = -2) would need column 5, which is off a board whose columns are 0 to 4.

Q: Why does choosing the Sudoku cell with the fewest candidates reduce the tree so dramatically?
A: Branching on a cell with 2 candidates makes 2 subtrees instead of, say, 7, and a cell with 0 candidates proves the branch dead immediately. Constrained cells fail fast, so mistakes are discovered near the root, where one cut removes a huge subtree; with reading order, a wrong early guess may only be discovered dozens of levels deeper, after exploring everything in between.

Q: The bitmask template returns 92 for n = 8. How many solutions does `solve_n_queens(6)` find, and roughly how many nodes does it visit compared with the 720 orderings of 6 columns?
A: 4 solutions, found by visiting only 153 nodes, against 1,957 nodes and 720 leaves in the full permutation tree: the diagonal sets kill most partial boards after two or three rows (likewise n = 8 visits 2,057 nodes against 8! = 40,320 permutations).

## Lab

- **51 N-Queens.** Write the three-set version and render boards only at the leaves. Expected: n = 4 gives ['.Q..', '...Q', 'Q...', '..Q.'] and ['..Q.', 'Q...', '...Q', '.Q..'], n = 1 gives [['Q']], and the counts for n = 1 to 10 are 1, 0, 0, 2, 10, 4, 40, 92, 352, 724.
- **37 Sudoku Solver.** Sets for rows, columns and boxes, then the most-constrained cell. Expected: your solved grid passes a checker that every row, column and box holds 1 to 9 and every given digit is unchanged; with most-constrained-first, a typical puzzle needs only a few hundred nodes (the lab below measures it).

> [!know]
> You now know how to model a puzzle as variables, domains and constraints, check conflicts in O(1) with sets or bitmasks, and branch on the most constrained variable.

=== primer | Why must a grid word search undo its marks when flood fill never does? | 14 min
goal: Search paths on a grid with mark and restore, prune early, and explain why a per-path visited mark is correct here while a global visited set is wrong
tag: backtrack-grid | Grid paths with mark and restore
link: Competitive Programmer's Handbook (free PDF) | https://cses.fi/book/book.pdf#page=61 | 10 min: section 5.4 (PDF pages 61-63) counts the paths that visit every square of a 7x7 grid, marking and unmarking squares, and shows which observations prune it
practice: 79

> [!key]
> When a path may not reuse a cell, "visited" is a property of the **current path**, not of the whole search: mark a cell when the path enters it and **restore it when the path backs out**, so other paths may use it. Flood fill asks a different question (which cells are reachable at all), where a cell explored once never needs exploring again, so a global visited set is right and the cost is O(cells). Word search costs up to O(m · n · 4 · 3^(L-1)) for a word of length L, so prune hard: check the letters exist, fail fast on mismatches.

## Intuition

Trace a word with your finger on a letter grid, never lifting it and never touching a square twice. If the finger reaches a dead end, you lift it back a square and try a different neighbour; the square you backed out of is free again for the next attempt. Now imagine instead you stuck a pin in every square you ever touched and never removed it: after one failed attempt half the grid is pinned, and a perfectly good route through those squares becomes impossible. That is the global-visited bug.

Flood fill (painting a region) is different: if a square has been painted, painting it again tells you nothing new, whichever route reached it. Reachability does not depend on the path; "is this word spelled by a path" does.

## How it works

### Depth-first search with mark and restore

From every cell whose letter matches the first letter, try to extend the path one letter at a time to edge-adjacent cells. Mark the current cell so the path cannot step on it again, and restore it on the way back whether or not the search succeeded.

```python
from collections import Counter


def exist(board, word):
    """Is word spelled by a path of edge-adjacent cells, each cell used at most once?"""
    rows, cols = len(board), len(board[0])
    if Counter(word) - Counter(ch for row in board for ch in row):
        return False                        # some letter is missing from the board entirely

    def dfs(r, c, k):                       # can word[k:] start at (r, c)?
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[k]:
            return False
        if k == len(word) - 1:
            return True
        board[r][c] = "#"                   # mark: this path now uses the cell
        found = (dfs(r + 1, c, k + 1) or dfs(r - 1, c, k + 1) or
                 dfs(r, c + 1, k + 1) or dfs(r, c - 1, k + 1))
        board[r][c] = word[k]               # restore on the way back, found or not
        return found

    return any(dfs(r, c, 0) for r in range(rows) for c in range(cols))
```

Overwriting the cell with "#" doubles as the visited mark and the mismatch test (no word contains "#"), and costs no extra memory. A separate `visited` set that you add to and remove from works the same way.

### Why a global visited set breaks

On the board below, look for "ABBBB" starting at the A:

```text
B B B
B A C
```

The search tries "up" first: A, then the B above it, then the B to its right, which is a dead end, then the B to its left and the B below that, also a dead end. With a global set, those four B cells stay marked. When the search then tries "left" from the A, the B there is already marked, and the answer comes back False. The true path is A, left, up, right, right. With mark and restore every failed attempt unmarks its cells, the left branch runs normally and finds it.

### Pruning that pays

- **Letter counts:** if the word needs three Es and the board has two, answer False before any search (the `Counter` line).
- **Fail at the first mismatch:** `dfs` checks the letter before recursing, so a wrong neighbour costs one comparison.
- **Search from the rarer end:** if the last letter of the word is rarer on the board than the first, search for the reversed word; fewer starting cells means a smaller forest.
- **Many words at once:** put the words in a trie and walk the grid once, pruning when no word has the current prefix (the trie module's word search II).

## Cost

There are m · n starting cells. From the first letter there are up to 4 neighbours; after that at most 3, because the cell you came from is marked. A path of L letters therefore explores at most 4 · 3^(L-2) extensions per start, which is usually written **O(m · n · 4 · 3^(L-1))** as a safe upper bound, i.e. O(m · n · 3^L). Space is **O(L)** for the recursion stack; the marks live in the board itself. In practice the mismatch test kills most branches after one or two letters, so typical boards are far faster than the bound, but an adversarial board (all As, word "AAAA...AB") does approach it.

## When to use it

| Question | Technique |
|---|---|
| Is there a path spelling this word, cells not reused? | Backtracking with mark and restore |
| Most valuable path without revisiting cells (path with maximum gold) | Same, keeping a running total and a best |
| Count paths that visit every free cell exactly once | Same, plus pruning (the handbook's 7x7 example) |
| Which cells are reachable, region sizes, islands | Flood fill or BFS with a global visited set, O(cells) |
| Fewest steps from A to B | BFS (graphs module), never backtracking |
| Many words in one grid | Trie plus backtracking |

The cue that decides it: does the path's own history restrict where it may go next? If yes, the state is the path, and you need backtracking.

## Worked trace

Board rows "CAR" and "AOT", word "CART". The four neighbours are tried in the order down, up, right, left; "#" marks cells on the current path.

```steps
Start at (0,0): "C" matches word[0]; mark it
    {{#}} A R
    A O T          path C
---
Down to (1,0): "A" matches word[1]; mark it
    # A R
    {{#}} O T          path C A
---
From (1,0) we need "R": down and left are off the board, up is marked, right is "O". **Dead end**: restore (1,0) and return False
    # A R
    {{A}} O T          path C
---
Back at (0,0): up is off the board; right is (0,1) "A": matches word[1], mark it
    # {{#}} R
    A O T          path C A
---
From (0,1) we need "R": down is "O", up is off the board, right is (0,2) "R": mark it
    # # {{#}}
    A O T          path C A R
---
From (0,2) we need "T", the last letter: down is (1,2) "T". **Found**
    # # #
    A O {{T}}          path C A R T
---
Every call restores its cell on the way out: the board is unchanged when exist returns True
    {{C A R}}
    A O T          result True
```

The failed detour through (1,0) is exactly where a global visited set would have done damage on a less lucky board: the cell would stay pinned for every later attempt.

## Template

```python
def grid_paths(grid, start, is_goal, can_enter):
    """Count simple paths (no cell twice) from start to any goal cell."""
    rows, cols = len(grid), len(grid[0])
    on_path = set()

    def dfs(r, c):
        if is_goal(r, c):
            return 1
        on_path.add((r, c))                  # mark
        total = 0
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in on_path and can_enter(nr, nc):
                total += dfs(nr, nc)
        on_path.remove((r, c))               # restore
        return total

    return dfs(*start)
```

Change the accumulation (`total += ...`) to `max` with a running value for "best path" problems, or return True early for existence.

## Pitfalls

- **Returning before restoring.** `if dfs(...): return True` placed before `board[r][c] = word[k]` leaves "#" in the caller's board; harmless for one query, a bug if the board is reused or the function is called for several words.
- **A global visited set** (above). If a cell is legitimately reachable by different paths, its mark must belong to a path.
- **Marking after the bounds check fails** or checking bounds after indexing: test `0 <= r < rows` first, and remember Python's negative indexes do not raise, they wrap around to the other side of the grid.
- **Recursion depth.** L is the depth; Python's default limit of about 1,000 frames is fine for words, not for snake-like paths over a 100 x 100 grid, which need an explicit stack.

## Check yourself

Q: Using the trace's board and order (down, up, right, left), how many cells are marked at the moment "T" is found, and which cells are they?
A: Three: (0,0) "C", (0,1) "A" and (0,2) "R". The last letter is matched by the base case `k == len(word) - 1` before any mark, and (1,0) was restored when its branch failed.

Q: State the worst-case time of `exist` for a 3 x 4 board and a word of length 6, as an expression, and explain the 3.
A: At most 12 starting cells times 4 · 3^4 extensions, i.e. about 12 · 4 · 81 = 3,888 extension steps. The 3 is because after the first move one of the four neighbours is the cell the path came from, which is marked.

Q: Your friend replaces the restore line with nothing and adds a global `visited` set cleared once per starting cell. On which board and word does it fail?
A: The board B B B / B A C with the word "ABBBB": the first branch from A (up) marks four Bs and fails, so the left branch finds its first B already marked and the answer is False, although A, left, up, right, right spells the word.

## Lab

- **79 Word Search.** Write `exist` with the letter-count check and mark and restore, then test it on your own board C A T / O R E / D O G. Expected: "CAT", "COD", "CORE", "CAR", "TAC" and "DOGE" are True; "TERRA", "ART" and "ROT" are False; after every call the board is unchanged. Then run the B B B / B A C board with "ABBBB" through a global-visited version and watch it answer False.

> [!know]
> You now know how to search simple paths on a grid with mark and restore, why the visited mark belongs to the path, and how to bound and prune the 3^L blow-up.

=== primer | Will exhaustive search finish in time, and what do you do when it will not? | 16 min
goal: Estimate a search's node count from its shape or by random sampling, turn it into seconds for Python, and switch to pruning, meet in the middle or dynamic programming when it is too slow
tag: backtrack-cost | Estimating search cost, meet in the middle
link: Competitive Programmer's Handbook (free PDF) | https://cses.fi/book/book.pdf#page=64 | 5 min: section 5.5 'Meet in the middle' (PDF pages 64-65): split the list in two, list each half's subset sums, and combine them in O(2^(n/2)) time
link: Wikipedia: Subset sum problem | https://en.wikipedia.org/wiki/Subset_sum_problem#Horowitz_and_Sahni | 5 min: 'Horowitz and Sahni': the 1974 meet-in-the-middle algorithm and why it runs in about 2^(n/2) time
practice: 2305, 51

> [!key]
> Search time is **nodes x work per node**. Count the nodes from the tree's shape (2^n subsets, about e · n! for orderings, k^n for k-way assignments), or estimate them by **random probes** down the tree, then divide by Python's speed: roughly a million nodes per second when each node does real work. That makes n of about 20-22 the limit for subsets and 9-10 for orderings. When the estimate is too big, prune (earlier primer), **meet in the middle** (two half-size searches combined by sorting: 2^n becomes 2^(n/2)), or notice that the future depends only on a small summary and **memoise** it, which is dynamic programming.

## Intuition

Before driving somewhere you estimate: 300 km at 100 km/h is three hours, so no, you will not make the 2 p.m. meeting. Search deserves the same arithmetic. The distance is the number of nodes, which you can read off the tree's shape; the speed is how many nodes per second your language manages. Ten seconds of arithmetic before coding saves an hour of waiting for a program that would have run until next year.

## How it works

### Count the tree

| Shape | Leaves | n you can afford in Python (a few seconds) |
|---|---|---|
| Subsets (2 choices per element) | 2^n | about 20-22 |
| Assignments (k choices per element) | k^n | k = 3: about 13; k = 4: about 10 |
| Orderings (permutations) | n!, about e · n! nodes | about 9-10 |
| k-subsets | C(n, k) | whenever C(n, k) is at most a few million |
| Meet in the middle over subsets | 2 · 2^(n/2) plus a sort | about 40-44 |

C++ is typically 10 to 50 times faster per node, which moves each limit by a little: 2^25 instead of 2^21, 11! instead of 10!. Exponential trees laugh at constant factors; only a better algorithm moves the limit a lot.

### Measure the speed

Measured in CPython on one machine: a bare recursive call that does nothing ran at about 4.8 million calls per second; the permutation backtracking with a `used` array at about 0.5 million nodes per second; N-queens with three sets at about 0.2 million. Your machine will differ, so time 10^5 nodes of *your* search and extrapolate.

### Sample the tree: Knuth's estimator

When pruning makes the tree irregular, you cannot count it by formula. Donald Knuth's 1975 trick: walk one random path from the root to a leaf, and at each level multiply the number of children you saw. If the root had 8 children and the chosen child had 5, level 2 is estimated at 40 nodes, and so on. Summing these products estimates the tree size, and the average over many random walks is an unbiased estimate.

```python
import random


def estimate_nodes(children, root, probes=1000, rng=random.Random(42)):
    """Knuth's estimator: average over random root-to-leaf walks of 1 + d1 + d1*d2 + ..."""
    total = 0
    for _ in range(probes):
        node, weight, est = root, 1, 1
        while True:
            kids = children(node)
            if not kids:
                break
            weight *= len(kids)          # this level has about weight nodes
            est += weight
            node = rng.choice(kids)
        total += est
    return total / probes
```

On N-queens (`children` returns the safe placements in the next row), 2,000 probes estimated 2,028 nodes for n = 8 (exact: 2,057), 36,138 for n = 10 (exact: 35,539) and 838,571 for n = 12 (exact: 856,189), each in well under a second, while the exact n = 12 search took about 4 seconds.

### Meet in the middle

For subset problems, split the n elements into two halves of n/2. List all 2^(n/2) subset sums of each half; then every subset of the whole is one left subset plus one right subset. Sort the right sums once, and for each left sum binary-search the best partner. Two lists of a million instead of a trillion subsets: for n = 40 this ran in under 3 seconds in Python, where plain search would face 2^40, about 1.1 · 10^12 subsets.

### When the future depends on a small summary: memoise

Count the subsets of 20 numbers (each 1 to 9) that sum to 40. Include/exclude search makes 2,097,151 calls. But the answer below a node depends only on **(index, remaining sum)**, and there are at most 21 x 41 such pairs; caching by that pair needed 1,133 distinct states for the same answer, 19,056. Whenever the subtree under a node is determined by a small state rather than the whole path, search becomes dynamic programming, which is the next module.

## Cost

The estimators themselves are cheap: counting by formula is free, a probe costs O(depth · branching), and a thousand probes cost about as much as a thousand short paths. Meet in the middle costs O(2^(n/2)) to list each half (building the sums incrementally, each new element doubles the list), O(2^(n/2) · n) to sort, and O(2^(n/2) · n) for the binary searches, so **O(n · 2^(n/2)) time and O(2^(n/2)) memory**: memory, not time, is usually what stops it near n = 45 to 50.

## When to use it

- **Exhaustive search is the right answer** when the output must list every configuration, when the problem is NP-hard and the input is small (subset sum, scheduling small task sets, graph colouring, the travelling salesman for a dozen cities), or when you need an oracle to test a clever solution against.
- **It is the wrong answer** when the count says hours. Then: prune if a bound or constraint is available; meet in the middle if the problem splits into two independent halves whose results combine by sorting or hashing (sums, XORs); dynamic programming if the subtree depends on a small state.

### In real software

Backtracking's exponential worst case is a real-world hazard. Python's `re`, PCRE and Perl match regular expressions by backtracking; on 2 July 2019 a Cloudflare firewall rule containing `.*(?:.*=.*)` made the engine try so many ways of splitting the input that CPUs serving HTTP traffic went to nearly 100% across their network. Their write-up counts it: `.*.*=.*` takes 555 steps to match `x=` followed by 20 xs and 4,067 steps to fail on 20 xs alone, and they moved to engines with run-time guarantees (RE2 and Rust's regex, which, like Go's regexp, never backtrack). pip's resolver backtracks over package versions since version 20.3, which is why pip's documentation suggests adding version constraints to shrink the search space.

## Worked trace

Meet in the middle on [3, 34, 4, 12, 5, 2] with target 20: the largest subset sum not above 20.

```steps
Split into halves and list each half's 8 subset sums; sort the right half
    left  [3, 34, 4]   sums 0 3 34 37 4 7 38 41
    right [12, 5, 2]   sorted {{0 2 5 7 12 14 17 19}}
---
Left sum 0: the best partner is the largest right sum <= 20, which is 19: total 19
    left 0    need <= 20   right {{19}}   best 19
---
Left sum 3: need a partner <= 17; bisect finds 17: total {{20}}, the target itself
    left 3    need <= 17   right {{17}}   best 20
---
Left sum 34 is already above 20: skip it (as are 37, 38 and 41)
    left {{34}}   too big
---
Left sum 4: partner <= 16 is 14: total 18. Left sum 7: partner <= 13 is 12: total 19
    left 4, 7   right 14, 12   best 20
---
Answer 20 = 3 + 17, that is 3 + 12 + 5. 8 + 8 sums replaced 64 subsets
    best {{20}}
```

## Template

```python
from bisect import bisect_right


def all_sums(nums):
    """Sums of every subset of nums (2^len values)."""
    sums = [0]
    for x in nums:
        sums += [s + x for s in sums]
    return sums


def best_sum_at_most(nums, target):
    """Largest subset sum <= target, in O(2^(n/2) * n) time instead of O(2^n)."""
    half = len(nums) // 2
    left = all_sums(nums[:half])
    right = sorted(all_sums(nums[half:]))
    best = -1
    for s in left:
        if s <= target:
            k = bisect_right(right, target - s)    # right[k - 1] is the largest partner that fits
            best = max(best, s + right[k - 1])     # right[0] == 0, so k >= 1 here
    return best
```

For "how many subsets sum to exactly T", replace the sorted list with a `Counter` of right sums and add `count[T - s]` for each left sum.

## Pitfalls

- **Estimating leaves but forgetting the work per node.** Copying a path of length n at each leaf, or an O(n) validity check per node, multiplies the count by n.
- **Trusting a time limit written for C++.** A problem designed for 2^25 operations in C++ will usually not pass in plain Python; look for pruning or a better algorithm first.
- **Meet in the middle without the "independent halves" property.** It works when a full answer is exactly one left part combined with one right part by a simple rule (sum, XOR, concatenation); constraints that cross the split (adjacency, order) break it.
- **Memory.** 2^22 large Python integers in a list took about 170 MB when measured (each int is a separate object); tuples or lists per subset take far more. Store sums, not subsets, and consider `array('q')` or NumPy for the halves.

## Check yourself

Q: A search over orderings of 11 items does O(1) work per node at about 0.5 million nodes per second. Roughly how long will it run?
A: About e · 11! = 2.7 x 39.9 million, so about 108 million nodes, which at 0.5 million per second is about 220 seconds, close to 4 minutes. Too slow for an interactive tool: prune, or look for a state to memoise (bitmask DP).

Q: Why does Knuth's estimator multiply the numbers of children along a random path?
A: If you reach a node by choosing uniformly at each level, the probability of reaching it is 1 / (d1 · d2 · ... · dk). Weighting the count of each level by the inverse of that probability gives an unbiased estimate of the number of nodes at that level (Horvitz-Thompson), and summing levels estimates the whole tree.

Q: You must split 40 positive weights into two groups with sums as equal as possible. Plain search, meet in the middle or DP?
A: Meet in the middle when the weights are large (DP needs a table of size about the total sum, which may be billions): list the 2^20 sums of each half, sort one, and for each left sum binary-search the partner closest to half the total. If the weights are small integers (total up to about 10^6), a subset-sum DP over sums is simpler and exact. Plain 2^40 search is out.

## Lab

- **2305 Fair Distribution of Cookies.** Before coding, compute the tree size: each of up to 8 bags goes to one of up to 8 children, so 8^8 = 16.8 million leaves without pruning. Measure the nodes of your pruned version on the worst input you can construct. Expected: [8, 15, 10, 20, 8] with k = 2 gives 31 and [6, 1, 3, 2, 2, 4, 1, 2] with k = 3 gives 7; with an incumbent bound and symmetry pruning your node count should be a tiny fraction of k^n.
- **51 N-Queens, estimated.** Write `children` for partial boards (a tuple of columns), run `estimate_nodes` with 2,000 probes for n = 8, 10 and 12, then count the exact nodes of your solver. Expected: estimates within a few per cent of the exact counts 2,057, 35,539 and 856,189, and the estimator finishes long before the exact n = 12 search.

> [!know]
> You now know how to predict whether a search finishes by counting or sampling its tree, and what to reach for when it will not: pruning, meet in the middle or memoisation.

=== lab | Sudoku solver: from blind search to most-constrained-first | 50 min
goal: Build three Sudoku solvers, plain, with constraint sets, and most-constrained-first, and measure nodes and time on 20 puzzles to see what each idea buys
link: Peter Norvig: Solving every Sudoku puzzle | https://norvig.com/sudoku.html | 20 min: 'Constraint Propagation' and 'Search' for the minimum-remaining-values heuristic, and 'Results' for his timings to compare with yours

You will write the search three times, changing one idea at a time, and count the nodes (calls to `search`) each version needs. The numbers make the primer's claims concrete: O(1) checks make each node cheaper; choosing the most constrained cell makes the tree smaller, and that matters far more.

## Setup

- Python 3.10 or later (for `int.bit_count`), no packages needed.
- Download two puzzle files from Norvig's site into your working folder: `https://norvig.com/easy50.txt` (50 puzzles, 9 lines each, separated by `========`) and `https://norvig.com/top95.txt` (95 hard puzzles, one 81-character line each). You will use the first 10 of each.

## Steps

1. Save the loader, the plain solver and the harness as `sudoku_lab.py`:

```python
import time


class Budget(Exception):
    pass


def parse(line):
    """81 characters, digits and '.' or '0' for blanks -> 9x9 list of str."""
    line = line.strip().replace("0", ".")
    return [list(line[9 * r: 9 * r + 9]) for r in range(9)]


def load(path):
    """Norvig's files: top95.txt has one puzzle per line; easy50.txt has 9 lines per puzzle."""
    text = open(path).read()
    if "====" in text:
        chunks = [c for c in text.split("========") if c.strip()]
        return [parse("".join(c.split())) for c in chunks]
    return [parse(l) for l in text.splitlines() if l.strip()]


def solve_plain(board, limit=10**6):
    """Reading order, and a scan of row, column and box for every check."""
    nodes = 0

    def ok(r, c, d):
        br, bc = r // 3 * 3, c // 3 * 3
        for i in range(9):
            if board[r][i] == d or board[i][c] == d or board[br + i // 3][bc + i % 3] == d:
                return False
        return True

    def search(pos):
        nonlocal nodes
        nodes += 1
        if nodes > limit:
            raise Budget
        while pos < 81 and board[pos // 9][pos % 9] != ".":
            pos += 1
        if pos == 81:
            return True
        r, c = divmod(pos, 9)
        for d in "123456789":
            if ok(r, c, d):
                board[r][c] = d
                if search(pos + 1):
                    return True
                board[r][c] = "."
        return False

    return search(0), nodes


def valid_solution(board, orig):
    units = ([[(r, c) for c in range(9)] for r in range(9)] +
             [[(r, c) for r in range(9)] for c in range(9)] +
             [[(br + i, bc + j) for i in range(3) for j in range(3)] for br in (0, 3, 6) for bc in (0, 3, 6)])
    same = all(orig[r][c] in (".", board[r][c]) for r in range(9) for c in range(9))
    return same and all(sorted(board[r][c] for r, c in u) == list("123456789") for u in units)


def run(name, solver, puzzles, limit=10**6):
    total_nodes, total_time, gave_up = 0, 0.0, 0
    for p in puzzles:
        b = [row[:] for row in p]
        t = time.perf_counter()
        try:
            ok, nodes = solver(b, limit)
            assert ok and valid_solution(b, p)
        except Budget:
            nodes, gave_up = limit, gave_up + 1
        total_time += time.perf_counter() - t
        total_nodes += nodes
    print(f"{name:6} nodes {total_nodes:>10,}  time {total_time:6.1f} s  gave up on {gave_up}")


if __name__ == "__main__":
    puzzles = load("easy50.txt")[:10] + load("top95.txt")[:10]
    run("plain", solve_plain, puzzles)
```

2. Run it and write down the total nodes, the time and how many puzzles hit the budget of a million nodes.
3. Write `solve_sets(board, limit)`: the same reading order, but keep `rows`, `cols` and `boxes` as lists of nine sets, fill them from the givens, and replace `ok` with three membership tests; add to the sets when you place a digit and remove when you undo. Add it to the `run` calls. Before running, predict its node count.
4. Write `solve_mrv(board, limit)`: keep a list of empty cells; at each node compute every empty cell's candidates (`digits - rows[r] - cols[c] - boxes[b]`), branch on the cell with the fewest, stop scanning early when a cell has 0 or 1 candidates, and put the cell back on the list when you undo. Run all three.
5. Make MRV cheaper per node: replace the sets with 9-bit integers (`free = ~(rows[r] | cols[c] | boxes[b]) & 0x1FF`, count with `free.bit_count()`, take the lowest digit with `free & -free`). Run again.
6. Print the per-puzzle node counts for the hard puzzles under MRV and find the hardest one. Optional: add Norvig's propagation (when a cell has exactly one candidate, fill it immediately and repeat) and measure again.
7. Fill in a table: version, total nodes, time, puzzles over budget, microseconds per node.

## What you should see

Measured with exactly these 20 puzzles in CPython (your times will differ, node counts should be close):

- **plain:** about 8 million nodes in total (10 easy puzzles: about 250,000 between them; 7 of the 10 hard puzzles hit the budget), around 100 seconds, about 14 microseconds per node.
- **sets:** exactly the same node counts as plain, because the search order and the pruning are identical, but about 5 times faster per node (about 20 seconds in total). Cheaper nodes do not shrink the tree.
- **mrv with sets:** about 411,000 nodes for all 20 puzzles and none over budget; the easy puzzles need about 150 nodes each (almost every cell is forced), the hardest needs about 180,000. Time is around 30 seconds, because recomputing candidates for every empty cell makes each node about 70 microseconds: fewer, dearer nodes.
- **mrv with bitmasks:** a similar node count (ties are broken differently, so it was about 570,000 here) in about 6 seconds: the best of both.
- The lesson in one line: ordering changed the tree size by orders of magnitude; representation changed the cost per node by a constant factor. Fix the tree first.

## Check yourself

Q: Why do the plain and sets versions visit exactly the same number of nodes?
A: Both fill cells in reading order and try digits 1 to 9, rejecting exactly the same digits (a digit is rejected by the scan if and only if it is in one of the three sets). Same tree, same order, same pruning; only the cost of each check differs.

Q: MRV visited 20 times fewer nodes than plain but was slower than the sets version on some puzzles. How do you decide whether a heuristic pays?
A: Total time is nodes times cost per node. A heuristic pays only if the node reduction factor beats its per-node overhead factor; measure both, then cut the overhead (bitmasks, early exit when a forced cell is found, incremental candidate counts) so the smaller tree also becomes the faster run.

=== practice
- 1863 core
  cue: At most 12 numbers, and the answer adds up a value computed for every possible group of them.
  hint: Draw the groups as a tree in which each number is either taken or left. What do you need to carry down so that a leaf knows its group's value?
  insight: Recurse on (index, running XOR): dfs(i + 1, x ^ nums[i]) + dfs(i + 1, x), adding x at the leaves, so nothing is stored. Bonus: each bit set in any number is set in exactly half of the subset XORs, so the total equals (OR of all numbers) << (n - 1).
  cost: O(2^n) time and O(n) stack; O(n) with the OR identity
  pattern: backtrack-tree
- 78 core
  cue: Return every possible collection of the given distinct numbers, the empty one included.
  hint: Each number has two fates. Or: if every list is built in increasing index order, in how many ways can each list be built?
  insight: Record the current path at every node of a start-index recursion (for i from start: choose, recurse on i + 1, unchoose), or count masks 0 to 2^n - 1 and read bit i as "take element i". Either way each subset is produced exactly once.
  cost: O(n · 2^n) time, O(n) extra space besides the output
  pattern: backtrack-subsets
- 46 core
  cue: Every ordering of a list of distinct numbers must be listed.
  hint: Fill the positions one at a time. What must you remember about which numbers are still available, and how do you give one back?
  insight: Keep a used array; for each unused index mark it, append, recurse, pop and unmark; record a copy when the path has n elements. The tree has n! leaves and about e · n! nodes.
  cost: O(n · n!) time, O(n) extra space besides the output
  pattern: backtrack-perms
- 90 core
  cue: All distinct collections of the numbers, when the input may contain equal values.
  hint: A repeated answer appears when two equal values are tried as the same next element. What does sorting make adjacent?
  insight: Sort, then in the start-index loop skip i > start with nums[i] == nums[i - 1]: an equal value is never tried twice at one depth, but may still follow its twin deeper down. Writing i > 0 would wrongly forbid answers such as [2, 2].
  cost: O(n · 2^n) time, O(n) extra space besides the output
  pattern: backtrack-perms
- 39 core
  cue: List the multisets of candidates that hit a target exactly, where each candidate may be used any number of times.
  hint: How do you allow a candidate again without also producing the same multiset in a different order?
  insight: Sort; after choosing candidates[i] recurse from the same index i (reuse) but never from an earlier one (no reordering), and break out of the loop as soon as a candidate exceeds the remaining amount, since every later one does too.
  cost: Exponential in target / smallest candidate, output-sensitive; O(target / smallest) recursion depth
  pattern: backtrack-build
- 22 core
  cue: All strings of n pairs of brackets that are correctly nested.
  hint: Build the string left to right. When is adding an opener safe, and when is adding a closer safe?
  insight: Track opened and closed counts: add '(' while opened < n and ')' while closed < opened. Every such prefix can be completed, so every leaf of length 2n is valid and no work is wasted; the number of answers is the Catalan number.
  cost: O(n · Catalan(n)), roughly O(4^n / sqrt(n)) time; O(n) depth
  pattern: backtrack-build
- 131 core
  cue: Every way to cut a string so that each piece reads the same backwards.
  hint: Decide where the first piece ends; what is left is the same problem on a suffix. How do you avoid testing the same substring again and again?
  insight: From position start, try each end where s[start:end] is a palindrome, recurse from end, then pop. Precompute pal[i][j] from shorter ranges to longer ones (s[i] == s[j - 1] and pal[i + 1][j - 1]) so each test is O(1).
  cost: O(n · 2^n) time in the worst case (one repeated letter), O(n^2) for the table
  pattern: backtrack-build
- 79 core
  cue: Is a word spelled by a chain of neighbouring cells, where no cell may appear twice in the chain?
  hint: Try each starting cell and extend one letter at a time. Which cells are forbidden: those touched by any earlier attempt, or only those on the current chain?
  insight: DFS matching word[k] at (r, c); overwrite the cell with a marker while it is on the path and restore it on the way back, success or failure. Prune with a letter-count check and by failing at the first mismatch. A global visited set gives wrong answers.
  cost: O(m · n · 3^L) time, O(L) recursion depth
  pattern: backtrack-grid
- 698 derive
  cue: Decide whether at most 16 numbers can be split into k groups with exactly equal sums.
  hint: The target per group is fixed. Place the numbers one by one into groups that still have room. Which placements are pointless to try more than once?
  insight: Target = total / k (fail at once if it is not an integer or the largest number exceeds it). Sort descending so big numbers fail early, put number i into each bucket with room, and if placing it into an empty bucket fails, stop trying: every other empty bucket is equivalent. Bitmask DP over the set of used numbers also works.
  cost: Exponential worst case (k^n before pruning); O(n · 2^n) with bitmask DP
  pattern: backtrack-prune
- 51 core
  cue: Place n pieces on an n x n board so that no two share a row, column or diagonal, listing every arrangement.
  hint: One piece per row is forced. What single number identifies each diagonal, so that every conflict check is O(1)?
  insight: Recurse row by row, keeping sets of used columns, of r - c (constant along one diagonal direction) and of r + c (the other). Place, recurse, remove; build the board strings only at the leaves.
  cost: O(n!) time in the worst case, far less in practice; O(n) extra space besides the output
  pattern: backtrack-csp
- 2305 stretch
  cue: Hand out at most 8 bags to k children so that the largest child's total is as small as possible.
  hint: Try every assignment, but remember the best answer so far. When can a branch no longer beat it, and which children are interchangeable at a given moment?
  insight: Assign bags (largest first) to children in turn; cut a branch as soon as a child's total reaches the best maximum found so far, and at each level skip a child whose current total equals one already tried there (two empty children are interchangeable). A DP over subsets of bags also works.
  cost: O(k^n) worst case, a tiny fraction with pruning; O(n) depth
  pattern: backtrack-prune
- 37 stretch
  cue: Fill a 9 x 9 grid so that every row, column and 3 x 3 box holds each digit once; exactly one solution exists.
  hint: Make every conflict check O(1), then ask which empty cell is the best one to guess next.
  insight: Keep used-digit sets or 9-bit masks per row, column and box. At each step branch on the empty cell with the fewest candidates (0 means back up now, 1 is a forced move), place, recurse, undo. Filling forced cells immediately (propagation) shrinks the tree further.
  cost: Exponential in the worst case; typically hundreds to thousands of nodes on a fixed 9 x 9 board
  pattern: backtrack-csp
