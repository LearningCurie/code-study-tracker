---
key: linear
name: Linked lists, stacks and queues
stage: contain
summary: Pointer rewiring that never loses a node, the stack as a record of open contexts, and queues built from deques, ring buffers and two stacks, with the CPython internals behind each.
why: These are the simplest structures with an access rule (who can be reached, who leaves next), and most bugs with them are lost references or the wrong end. Problems use them to test whether you can rewire pointers safely and spot LIFO or FIFO order inside a story. Real software leans on them everywhere: CPython's stack-based bytecode and call stack, undo histories, job and network queues, the deque under every BFS, the doubly linked list inside LRU caches and the intrusive lists all over the Linux kernel. Knowing what each costs in Python (and why `list.pop(0)` is a trap) turns them from trivia into tools.
outcomes:
- Reverse, merge and splice singly linked lists in place, using a dummy head so the first node is never a special case
- Find the middle, the n-th node from the end, a cycle and its entry with fast and slow pointers, and prove why Floyd's entry step works
- Use a stack of open contexts for matching, nesting and expression evaluation, with truncating division and unary minus handled
- Choose between list, collections.deque, a ring buffer and a two-stack queue, and prove the two-stack queue is amortised O(1)
- Explain how CPython's deque, functools.lru_cache and pymalloc use linked structures, and what each saves
- Implement a deque three ways and stress-test them against collections.deque
cues:
- Node objects with next (and maybe prev) pointers are given, often with O(1) extra space required
- Matching or nesting: brackets, tags, paths with "..", encodings such as 3[ab] or nested parentheses
- Most recent first (undo, the last unmatched item) or first come, first served (tasks, buffers, BFS)
- You already hold a reference to an item and must delete or move it in O(1)
traps:
- Overwriting node.next before saving it, which cuts off the rest of the list
- Using list.pop(0) or list.insert(0, x) as a queue: each call shifts every element
- Popping an empty stack on a stray closer, or forgetting that leftover openers also mean failure
- Python's // floors (-7 // 2 is -4) while C, Java and most problem statements truncate towards zero
- Recursing along a long linked list: CPython raises RecursionError at about 1,000 frames
systems:
- CPython's collections.deque is a doubly linked list of 64-slot blocks, so appends and pops at either end never move another element
- functools.lru_cache maps keys to links in a circular doubly linked list with a root sentinel (the C version uses the same design), giving O(1) move-to-front and eviction
- The Linux kernel embeds circular doubly linked list links inside its structs (include/linux/list.h), and kfifo is a ring buffer whose size is a power of two
- CPython's interpreter is a stack machine: `a + b * c` compiles to postfix order (LOAD a, LOAD b, LOAD c, BINARY_OP *, BINARY_OP +)
further:
- Chapter · 25 min | Open Data Structures: 3.2 DLList, a doubly linked list with a dummy node | https://opendatastructures.org/ods-python/3_2_DLList_Doubly_Linked_Li.html
- Chapter · 20 min | Open Data Structures: 2.4 ArrayDeque, a deque in a circular array | https://opendatastructures.org/ods-python/2_4_ArrayDeque_Fast_Deque_O.html
- Docs · 15 min | Linux kernel: the doubly linked list implementation | https://docs.kernel.org/core-api/list.html#linux-implementation-of-doubly-linked-lists
- Article · 10 min | cp-algorithms: why Floyd's cycle finding works | https://cp-algorithms.com/others/tortoise_and_hare.html#why-does-it-work
bank: linked stack
---

=== recap | Linked lists: rewiring, reversal and dummy heads | 12 min
goal: Reverse, merge and splice singly linked lists in place without losing a node, using a dummy head so the first node is not a special case
tag: linear-rewire | Pointer rewiring with a dummy head
link: Open Data Structures: 3.1 SLList | https://opendatastructures.org/ods-python/3_1_SLList_Singly_Linked_Li.html | 10 min: the whole short section; push, pop and add at the tail of a singly linked list, each with its cost
practice: 206, 21, 25

> [!key]
> A linked list is a chain of separate node objects, each holding a value and a reference to the next. Every algorithm on it is **pointer rewiring**: save what you are about to overwrite, change one arrow, advance. A **dummy head** (a throwaway node placed before the first) turns the head into an ordinary node, so insert, delete and merge need no special case.

## Internals

- **Cost in CPython.** A node class with `__slots__ = ("val", "next")` takes 48 bytes per node (80 without slots), plus the value object. A Python list stores an 8-byte reference per item in one contiguous array. Linked lists lose on memory and on cache locality, because every `.next` jumps to wherever the allocator put that node. They win only when you already hold the node (or its predecessor): insert, delete and splice are then O(1) and nothing else moves. Reaching index i is O(i), so there is no binary search.
- **Reversal invariant.** At every step, `prev` heads the reversed part (the nodes already visited, backwards) and `curr` heads the untouched rest. The two chains are disjoint and together hold every node, so when `curr` is None, `prev` is the whole reversed list.
- **Merge invariant.** `dummy.next` to `tail` is the sorted merge of the nodes taken so far, and each of them is no larger than any node still waiting. Taking from `a` on ties keeps the merge stable.
- **Doubly linked and circular.** A `prev` pointer lets a node you hold unlink itself in O(1) without searching for its predecessor. Production code makes the list circular around one sentinel (`root.next` is the first node, `root.prev` the last), so there are no None checks at all: the Linux kernel's `list.h` and the `root` link of `functools.lru_cache` both work this way. O(1) unlink plus a dict from key to node is the LRU cache design you build in the design module.
- **Where singly linked lists still win.** Free lists, where only push and pop at one end matter: CPython's pymalloc pushes each freed block onto its pool's `freeblock` list and pops from it on the next allocation.

## Template

```python
class ListNode:
    __slots__ = ("val", "next")

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def from_list(values):
    """Build a list from a Python sequence; return the head (None if empty)."""
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def reverse(head):
    """Reverse in place and return the new head."""
    prev, curr = None, head
    while curr:
        nxt = curr.next        # 1. save the rest of the list
        curr.next = prev       # 2. turn this arrow around
        prev = curr            # 3. grow the reversed part
        curr = nxt             # 4. move into the rest
    return prev


def merge_two(a, b):
    """Merge two sorted lists by relinking their nodes (stable: ties take from a)."""
    dummy = tail = ListNode()
    while a and b:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a or b         # attach whatever is left
    return dummy.next
```

## Worked example

```steps
Start: `prev` is None and `curr` is the head; nothing is reversed yet
    None    [1] -> [2] -> [3] -> [4] -> None
    prev    curr
---
Save the rest first: `nxt = curr.next`, so node 2 stays reachable
    None    [1] -> [2] -> [3] -> [4] -> None
    prev    curr   nxt
---
Turn the arrow: `curr.next = prev`. Without `nxt`, nodes 2, 3 and 4 would now be lost
    None {{<-}} [1]    [2] -> [3] -> [4] -> None
    prev    curr   nxt
---
Advance: `prev = curr`, `curr = nxt`. The invariant holds again: prev heads the reversed part, curr the rest
    None <- {{[1]}}    {{[2]}} -> [3] -> [4] -> None
            prev   curr
---
Iteration 2 makes the same four moves: node 2 now points back at node 1
    None <- [1] {{<-}} [2]    [3] -> [4] -> None
                   prev   curr
---
Iteration 3: node 3 points back at node 2
    None <- [1] <- [2] {{<-}} [3]    [4] -> None
                          prev   curr
---
Iteration 4: `curr` becomes None and the loop stops; return `prev`, the new head 4 -> 3 -> 2 -> 1
    None <- [1] <- [2] <- [3] {{<-}} [4]
                                 prev
```

## Pitfalls

- Writing `curr.next = prev` before saving `curr.next`: the rest of the list is unreachable.
- Returning `head` after a reversal: the old head is now the tail.
- Rebuilding a list without ending it (`tail.next = None`, or attaching the remainder): you keep stale links or create a cycle.
- Tuple assignment assigns targets left to right. `curr.next, prev, curr = prev, curr, curr.next` is correct, but `prev, curr, curr.next = curr, curr.next, prev` writes to the *new* `curr`'s next and crashes at the end of the list.
- Recursive reversal uses one frame per node: fine for a few hundred nodes, RecursionError for a few thousand.
- Comparing nodes with `==` when you mean the same node: use `is`.

## Quick check

Q: Run two iterations of `reverse` on 1 -> 2 -> 3 -> 4 -> 5. What are `prev` and `curr`, and what does each chain look like?
A: `prev` is node 2 and `curr` is node 3. The reversed chain is 2 -> 1 -> None and the untouched chain is 3 -> 4 -> 5 -> None; together they still hold all five nodes.

Q: Why does `merge_two` need no special case for an empty input or for choosing the head of the result?
A: The dummy is the head of the result from the start, so the first real node is attached like any other. If one list is empty the loop never runs and `tail.next = a or b` attaches the other list whole.

> [!know]
> You now know how to rewire linked lists safely (save, flip, advance) and why a dummy or sentinel node removes edge cases.

=== recap | Fast and slow pointers: middle, cycle and cycle entry | 12 min
goal: Find the middle, the n-th node from the end, a cycle and its entry in O(1) extra space, and prove why Floyd's entry step works
tag: linear-fastslow | Fast and slow pointers (Floyd)
link: cp-algorithms: Floyd's cycle finding | https://cp-algorithms.com/others/tortoise_and_hare.html#why-does-it-work | 10 min: 'Why does it work?' (both steps), the same distance argument with a figure
practice: 141, 19, 142, 287

> [!key]
> Two pointers walking the same list at different speeds, or a fixed distance apart, answer position questions in one pass with O(1) memory. When fast (two steps) falls off the end, slow (one step) is at the middle. If there is a cycle, fast must catch slow inside it. Then **Floyd's second phase** finds where the cycle starts: restart one pointer at the head, step both by one, and they meet at the entry.

## Internals

Let **mu** be the number of steps from the head to the cycle entry and **lambda** the cycle length.

- **Why they meet.** Slow enters the cycle after mu steps; fast is already inside. From then on fast gains exactly one node per step, so the distance from fast forward to slow (between 0 and lambda - 1) shrinks by one each step and reaches zero before slow completes a lap. They meet within mu + lambda steps: O(n).
- **Why the entry step works.** At the meeting, slow has walked t steps and fast 2t, and they stand on the same cycle node, so the extra distance t is a whole number of laps: t = k × lambda. Slow's position inside the cycle, counted from the entry, is (t - mu) mod lambda. Walking mu more steps reaches (t - mu + mu) mod lambda = t mod lambda = 0: the entry. A pointer starting at the head also reaches the entry after exactly mu steps, so stepping both one at a time they arrive together. They cannot meet earlier, because before step mu the head pointer is still outside the cycle.
- **Cost.** O(n) time and O(1) space. A set of visited nodes is simpler and also O(n) time, but costs O(n) memory.
- **Gap pointers.** To delete the n-th node from the end in one pass, start both pointers at a dummy, move fast n + 1 steps, then move both until fast is None: slow is then just before the target, and the dummy covers deleting the head.
- **Beyond lists.** Floyd works on any function iterated over a finite set, x -> f(x), because the sequence must eventually repeat. Find the Duplicate Number reads i -> nums[i] as next pointers, and Pollard's rho factorisation detects its cycle the same way.

## Template

```python
def middle(head):
    """Second middle for even lengths; for the first, loop while fast.next and fast.next.next."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow


def cycle_entry(head):
    """Node where the cycle starts, or None if the list ends."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:                 # phase 1: they met inside the cycle
            p = head
            while p is not slow:         # phase 2: both walk mu steps to the entry
                p = p.next
                slow = slow.next
            return p
    return None


def remove_nth_from_end(head, n):
    """Keep a gap of n + 1 nodes so slow stops just before the node to delete."""
    dummy = ListNode(0, head)
    slow = fast = dummy
    for _ in range(n + 1):
        fast = fast.next
    while fast:
        slow, fast = slow.next, fast.next
    slow.next = slow.next.next
    return dummy.next
```

## Worked example

```steps
S (slow) and F (fast) start at the head. Node 6 links back to node 3, so mu = 3 and lambda = 4
    0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6
                   ^              |
                   +--------------+
    SF
---
t = 1: slow moves one node, fast two
    0 -> {{1}} -> {{2}} -> 3 -> 4 -> 5 -> 6
                   ^              |
                   +--------------+
         S    F
---
t = 2
    0 -> 1 -> {{2}} -> 3 -> {{4}} -> 5 -> 6
                   ^              |
                   +--------------+
              S         F
---
t = 3: slow enters the cycle after mu = 3 steps. Going round the loop, fast (node 6) is one step behind it
    0 -> 1 -> 2 -> {{3}} -> 4 -> 5 -> {{6}}
                   ^              |
                   +--------------+
                   S              F
---
t = 4: they meet at node 4. Slow walked 4, fast 8; the difference 4 is exactly one lap (lambda = 4)
    0 -> 1 -> 2 -> 3 -> {{4}} -> 5 -> 6
                   ^              |
                   +--------------+
                        SF
---
Phase 2: P restarts at the head, S stays at the meeting node; both now move one node per step
    {{0}} -> 1 -> 2 -> 3 -> {{4}} -> 5 -> 6
                   ^              |
                   +--------------+
    P                   S
---
k = 1
    0 -> {{1}} -> 2 -> 3 -> 4 -> {{5}} -> 6
                   ^              |
                   +--------------+
         P                   S
---
k = 2
    0 -> 1 -> {{2}} -> 3 -> 4 -> 5 -> {{6}}
                   ^              |
                   +--------------+
              P                   S
---
k = 3 = mu: both stand on node 3, the cycle entry, exactly as the proof predicts
    0 -> 1 -> 2 -> {{3}} -> 4 -> 5 -> 6
                   ^              |
                   +--------------+
                   PS
```

## Pitfalls

- The loop guard must be `while fast and fast.next`: dropping either half crashes on an empty list or on the last node.
- Even lengths: this `middle` returns the second middle (node 3 of 1, 2, 3, 4). Merge sort on a list cuts after the middle, so it needs the first middle: with the second, a two-node list splits into itself and an empty list and the recursion never ends.
- Comparing values (`slow.val == fast.val`) gives false meetings when values repeat; compare nodes with `is`.
- Phase 2 restarts from the real head (not a dummy) and moves both pointers one step at a time.
- In Find the Duplicate Number, start at index 0: it is never a value, so it lies on the tail outside the cycle.

## Quick check

Q: A list has 2 nodes before its cycle and a cycle of 5 nodes (nodes 0 to 6, node 6 links back to node 2). When do slow and fast first meet, and how many steps does phase 2 take?
A: They meet after t = 5 steps, at node 5: t must be a multiple of lambda = 5 and at least mu = 2, so 5 is the first chance. Phase 2 takes mu = 2 steps (P: 0, 1, 2; S: 5, 6, 2) and returns node 2.

> [!know]
> You now know how to find middles, gaps, cycles and cycle entries with two pointers, and why the entry step lands exactly on the entry.

=== recap | Stacks for matching and nesting | 10 min
goal: Use a stack of open contexts to match brackets, resolve paths and expand nested encodings in one pass
tag: linear-nesting | Stack of open contexts
link: Python tutorial: Using lists as stacks | https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-stacks | 3 min: the short section; append and pop at the end of a list are the fast stack operations
practice: 20, 394

> [!key]
> Nesting closes in the reverse order it opened, which is exactly last in, first out. Keep a **stack of open contexts**: push when something opens, and when something closes check that it matches the top and pop. The invariant: the stack holds every context that is open right now, innermost on top.

## Internals

- **The Python stack is a list.** `append` and `pop()` at the end are amortised O(1) (CPython over-allocates about 12.5%, so most appends write into spare capacity) and `stack[-1]` peeks. `insert(0, x)` and `pop(0)` shift every element. `collections.deque` works equally well; `queue.LifoQueue` adds locking for threads and is much slower. In C++ use `std::vector` or `std::stack`, in Java `ArrayDeque` rather than the legacy, synchronised `Stack`.
- **Why one stack is enough.** A closer may only close the innermost open context, which is the top. Everything deeper must stay open until the top is closed, so nothing below the top is ever needed early.
- **Saving context.** When entering a nested region changes your working state (the text decoded so far, a repeat count, a running sum), push the *outer* state and start fresh; on the closer, pop and combine. Recursion does the same with the call stack; the explicit stack cannot hit Python's limit of about 1,000 frames.
- **Same pattern elsewhere.** File paths (`..` pops a directory, `.` and empty parts are skipped), HTML and XML tag matching, undo (each edit pushes the information needed to reverse it), and iterative DFS.

## Template

```python
PAIRS = {")": "(", "]": "[", "}": "{"}


def is_balanced(s):
    stack = []                          # openers still waiting for their closer
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack.pop() != PAIRS[ch]:
                return False            # wrong closer, or nothing open
    return not stack                    # leftovers were never closed


def decode(s):
    """'3[a2[c]]' -> 'accaccacc'. On '[' save the outer context; on ']' restore it."""
    stack = []                          # (outer parts, repeat count) per open '['
    parts, num = [], 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch == "[":
            stack.append((parts, num))
            parts, num = [], 0
        elif ch == "]":
            outer, k = stack.pop()
            outer.append("".join(parts) * k)
            parts = outer
        else:
            parts.append(ch)
    return "".join(parts)


def simplify_path(path):
    stack = []
    for part in path.split("/"):
        if part == "..":
            if stack:
                stack.pop()
        elif part and part != ".":
            stack.append(part)
    return "/" + "/".join(stack)
```

## Worked example

```steps
`{` opens a context: push it
    input   { [ ( ) ( ) ] }
            ^
    stack   {{{}}
---
`[` opens: push
    input   { [ ( ) ( ) ] }
              ^
    stack   { {{[}}
---
`(` opens: push
    input   { [ ( ) ( ) ] }
                ^
    stack   { [ {{(}}
---
`)` closes: the top is `(`, a match, so pop
    input   { [ ( ) ( ) ] }
                  ^
    stack   { [
---
`(` opens again: push
    input   { [ ( ) ( ) ] }
                    ^
    stack   { [ {{(}}
---
`)` matches the top: pop
    input   { [ ( ) ( ) ] }
                      ^
    stack   { [
---
`]` matches the top `[`: pop
    input   { [ ( ) ( ) ] }
                        ^
    stack   {
---
`}` matches the top `{`: pop. The input is finished and the stack is empty, so the string is balanced
    input   { [ ( ) ( ) ] }
                          ^
    stack   (empty)
```

## Pitfalls

- A stray closer with nothing open (`")"`): check `not stack` before popping.
- Returning True at the end without checking that the stack is empty (`"(("`).
- Multi-digit counts: accumulate `num = num * 10 + digit` and reset after pushing.
- Building strings with `+=` inside nested repeats can turn quadratic; collect parts in lists and `join` once.

## Quick check

Q: Trace `is_balanced("([)]")`. At which character does it fail, and what is on the stack then?
A: At the third character, `)`. The stack is `( [` with `[` on top, which is not the partner of `)`, so it returns False. Counting each bracket type separately would wrongly accept this string; the stack catches the crossing.

Q: What does `decode("2[a3[b]]")` return, and what is on the stack just after the second `[`?
A: `"abbbabbb"`. After the second `[` the stack holds two saved contexts: `([], 2)` for the outer level and `(["a"], 3)` for the inner one, and the working parts are empty.

> [!know]
> You now know how to handle any nesting with a stack of open contexts, saving and restoring state at each level.

=== recap | Evaluating expressions with stacks | 12 min
goal: Evaluate postfix with one stack and infix with a sign or operator stack, handling precedence, parentheses, unary minus and truncating division
tag: linear-expr | Expression evaluation with stacks
link: Wikipedia: Shunting yard algorithm | https://en.wikipedia.org/wiki/Shunting_yard_algorithm#The_algorithm_in_detail | 10 min: 'The algorithm in detail', the precedence and associativity rules for the operator stack
practice: 150, 224

> [!key]
> **Postfix** (reverse Polish) puts each operator after its operands, so one stack evaluates it: push numbers, and on an operator pop the right operand, then the left, and push the result. **Infix** has to wait for precedence and parentheses: Dijkstra's shunting yard keeps an operator stack, and with only + and - a stack of saved (result, sign) pairs is enough.

## Internals

- **Postfix needs no rules.** The order of operations is the order of the tokens. CPython compiles your code to exactly this: `dis` shows `a + b * c` as LOAD a, LOAD b, LOAD c, BINARY_OP (*), BINARY_OP (+). The interpreter is a stack machine whose `BINARY_OP` pops two values and pushes one.
- **Shunting yard in one rule.** Before pushing an operator, pop and apply every operator on the stack that binds at least as tightly (strictly tighter for right-associative ones such as `**`), stopping at `(`; on `)`, pop until the matching `(`. Each token is pushed and popped at most once: O(n).
- **Plus, minus and parentheses** (Basic Calculator). Keep the running `result`, the `sign` of the next number and its digits `num`. On `(` push the outer `(result, sign)` and restart; on `)` finish the inner result, pop, and combine `outer + outer_sign * inner`. A unary minus needs no extra code: `-(` sets the sign before the push.
- **Times and divide without parentheses** (Basic Calculator II, in the bank). Keep a stack of signed terms: push `+n` or `-n`, and combine `*` and `/` with the top at once; the answer is the sum.
- **Division.** Problem statements, C and Java truncate towards zero; Python's `//` floors. `-7 // 2` is -4 but truncation gives -3. `int(a / b)` truncates too, through a float that is exact only up to 2^53.

## Template

```python
def div_trunc(a, b):
    """Integer division that truncates towards zero, like C and Java (Python's // floors)."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def eval_rpn(tokens):
    stack = []
    for tok in tokens:
        if tok in ("+", "-", "*", "/"):
            b = stack.pop()             # right operand is on top
            a = stack.pop()
            if tok == "+":
                stack.append(a + b)
            elif tok == "-":
                stack.append(a - b)
            elif tok == "*":
                stack.append(a * b)
            else:
                stack.append(div_trunc(a, b))
        else:
            stack.append(int(tok))      # handles "-3" as a number
    return stack[-1]


def calculate(s):
    """+, -, parentheses, unary minus and spaces."""
    result, sign, num = 0, 1, 0
    stack = []                          # (result so far, sign before '(') per open group
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch in "+-":
            result += sign * num
            num, sign = 0, (1 if ch == "+" else -1)
        elif ch == "(":
            stack.append((result, sign))
            result, sign = 0, 1
        elif ch == ")":
            result += sign * num
            num = 0
            outer, outer_sign = stack.pop()
            result = outer + outer_sign * result
    return result + sign * num
```

## Worked example

```steps
`calculate("8-(3-(2+4))")`. Read `8-`: result = 8, and the next number gets sign -1
    8-(3-(2+4))
     ^
    result 8   sign -1   num 0   stack []
---
`(`: save the outer state (8, -1) and start a fresh group
    8-(3-(2+4))
      ^
    result 0   sign +1   num 0   stack [{{(8, -1)}}]
---
`3-`: inside the group, result = 3 and the next sign is -1
    8-(3-(2+4))
        ^
    result 3   sign -1   num 0   stack [(8, -1)]
---
`(`: save (3, -1) and start the inner group
    8-(3-(2+4))
         ^
    result 0   sign +1   num 0   stack [(8, -1), {{(3, -1)}}]
---
`2+4`: result = 2 and num = 4 is still pending
    8-(3-(2+4))
            ^
    result 2   sign +1   num 4   stack [(8, -1), (3, -1)]
---
`)`: the inner group is 2 + 4 = 6; pop (3, -1) and combine: 3 - 6 = -3
    8-(3-(2+4))
             ^
    result {{-3}}   sign +1   num 0   stack [(8, -1)]
---
`)`: pop (8, -1) and combine: 8 - (-3) = 11. Input ends with nothing pending: the answer is 11
    8-(3-(2+4))
              ^
    result {{11}}   sign +1   num 0   stack []
```

## Pitfalls

- Popping operands in the wrong order: the top is the *right* operand of `a - b` and `a / b`.
- Treating `"-3"` as an operator in postfix input: test membership in the operator set, not the first character.
- Forgetting the last pending number: return `result + sign * num`.
- Calling `eval` on input: it runs arbitrary code, and its `/` returns floats.

## Quick check

Q: What does `eval_rpn(["2", "1", "+", "3", "*"])` return, and what is on the stack just before the `*`?
A: 9. After `2 1 +` the stack is `[3]`; pushing `3` makes it `[3, 3]`; `*` pops both and pushes 9.

> [!know]
> You now know how to evaluate postfix with one stack and infix with saved signs or an operator stack, without eval.

=== recap | Queues, deques and ring buffers | 12 min
goal: Choose between list, collections.deque and a ring buffer for FIFO work, and explain the internals that make each fast or slow
tag: linear-ring | Queues and ring buffers
link: Python docs: collections.deque | https://docs.python.org/3/library/collections.html#collections.deque | 5 min: the deque section up to 'deque Recipes': O(1) at both ends, maxlen, and indexing that is O(n) in the middle

> [!key]
> A queue adds at the back and removes at the front. A Python list does the back well and the front badly, because `pop(0)` shifts every element, so use `collections.deque`: O(1) at both ends. When the capacity is fixed, a **ring buffer** (an array, a head index and a size, wrapping with modulo) gives the same O(1) with no allocation at all.

## Internals

- **Why not a list.** `pop(0)` and `insert(0, x)` move every remaining reference. Draining 100,000 items from the front of a list took about 3.6 s on the machine used for this guide; `deque.popleft` took about 9 ms. A BFS written with `pop(0)` silently becomes quadratic.
- **collections.deque** is a doubly linked list of blocks, each holding 64 references (`BLOCKLEN 64` in CPython's `_collectionsmodule.c`). Appends and pops at either end write into the end block or link a fresh one, so no element ever moves, `realloc` is never called, and the link overhead is two pointers per 64 items instead of per item. The price: `d[i]` walks blocks from the nearer end, O(n) in the middle, so use a list for random access. `deque(maxlen=n)` discards from the opposite end when full, a ready-made "last n items" buffer.
- **Ring buffer invariant.** Item i of the queue lives at `(head + i) % capacity` for i from 0 to size - 1. Keep a `size` (or leave one slot unused), because with only head and tail indices `head == tail` means both empty and full. With a power-of-two capacity, `% cap` becomes the bit mask `& (cap - 1)`: the Linux kernel's `kfifo` sizes are powers of two for this reason. io_uring talks to the kernel through two ring buffers shared with user space (submission and completion queues), and network cards use descriptor rings in the same way.
- **Across threads and machines.** `queue.Queue` blocks on `get` and locks around every operation, for producer and consumer threads. Redis lists serve as job queues between processes: `LPUSH` to add, blocking `BRPOP` to take, and `BLMOVE` to move a job atomically into an "in progress" list so a crashed worker does not lose it.

## Template

```python
class RingBuffer:
    """Fixed-capacity FIFO queue in a circular array."""

    def __init__(self, capacity):
        self.buf = [None] * capacity
        self.head = 0                   # index of the oldest item
        self.size = 0

    def push(self, x):
        if self.size == len(self.buf):
            raise OverflowError("ring buffer is full")
        self.buf[(self.head + self.size) % len(self.buf)] = x
        self.size += 1

    def pop(self):
        if self.size == 0:
            raise IndexError("pop from an empty ring buffer")
        x, self.buf[self.head] = self.buf[self.head], None   # drop the reference
        self.head = (self.head + 1) % len(self.buf)
        self.size -= 1
        return x
```

## Worked example

```steps
Capacity 4. Push a, b, c: each goes to (head + size) % 4
    slot     0    1    2    3
    buf      a    b    c    .
    head 0, size 3, next write at 3
---
Pop twice: a, then b. Head moves forward; the slots are cleared so the objects can be freed
    slot     0    1    2    3
    buf      .    .    {{c}}    .
    head 2, size 1, next write at 3
---
Push d into slot 3
    slot     0    1    2    3
    buf      .    .    c    {{d}}
    head 2, size 2, next write at (2 + 2) % 4 = 0
---
Push e: the write index wraps round to slot 0
    slot     0    1    2    3
    buf      {{e}}    .    c    d
    head 2, size 3, next write at 1
---
Push f: size equals capacity, so the buffer is full; another push raises OverflowError
    slot     0    1    2    3
    buf      e    {{f}}    c    d
    head 2, size 4 (full)
---
Pop returns c, the oldest item, from slot 2; head wraps forward to 3. Queue order is d, e, f
    slot     0    1    2    3
    buf      e    f    .    d
    head {{3}}, size 3, next write at (3 + 3) % 4 = 2
```

## Pitfalls

- `list.pop(0)` in a BFS or a scheduler loop: O(n) per call.
- Not clearing a slot on pop keeps the object alive (a leak when items are large).
- `deque[i]` inside a loop is O(n) per access in the middle; deques are for the ends.
- In C and Java, `(head - 1) % cap` can be negative; Python's `%` never is for a positive capacity.

## Quick check

Q: Why does CPython's deque use 64-item blocks instead of one node per item or one big circular array?
A: One node per item would cost two pointers and one allocation per element. One big array would need occasional O(n) copies when it grows (fine amortised, but every element moves). Blocks of 64 keep the per-item overhead and the number of allocations small, never move existing elements, and keep neighbours together in memory for better cache behaviour.

> [!know]
> You now know how to pick a FIFO structure in Python and how deques and ring buffers achieve O(1) at the ends.

=== recap | A queue from two stacks, and why it is amortised O(1) | 10 min
goal: Build a FIFO queue from two LIFO stacks and prove that every operation costs O(1) amortised
tag: linear-twostack | Queue from two stacks
link: cp-algorithms: Minimum queue with two stacks | https://cp-algorithms.com/data_structures/stack_queue_modification.html#queue-modification-method-3 | 5 min: 'Queue modification (method 3)', the same transfer with a running minimum stored in each stack
practice: 232

> [!key]
> Push onto an **in** stack; pop from an **out** stack; only when *out* is empty, move everything across, which reverses it into FIFO order. One pop can cost O(n), but each element is moved at most once in its life, so any m operations cost O(m) in total: **amortised O(1)** per operation.

## Internals

- **Why the order is right.** *in* holds the newest items with the newest on top. Pouring it onto an empty *out* puts the oldest on top. Never pour while *out* still has items: they are older than everything in *in* and must leave first.
- **Aggregate argument.** Follow one element: it is pushed onto *in* (1 operation), moved during one transfer (a pop and a push, 2), and popped from *out* (1). That is at most 4 stack operations over its whole life, whatever the interleaving. m queue operations involve at most m elements, so the total work is at most about 4m.
- **Banker's argument.** Charge each push 3 units instead of 1 and leave 2 on the element. A transfer spends exactly the 2 units stored on each element it moves, so the bank never goes negative and every operation's charged cost is constant. (The potential function 2 × len(in) says the same thing.)
- **When amortised is not enough.** The bound is about totals: one unlucky pop still moves n elements. Hard latency targets (audio, trading, kernel paths) prefer a ring buffer or a deque with true O(1) operations. Functional languages use this front-and-back-list queue because it works with immutable lists.
- **Why it matters later.** Store `(x, max so far)` in each stack and the queue reports its maximum in O(1) amortised: one way to get every sliding-window maximum, next to the monotonic deque in the monotonic stacks module.

## Template

```python
class TwoStackQueue:
    def __init__(self):
        self.inbox, self.outbox = [], []

    def push(self, x):
        self.inbox.append(x)

    def _refill(self):
        if not self.outbox:             # only when empty: this keeps FIFO order
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self):
        self._refill()
        return self.outbox.pop()        # IndexError when the queue is empty

    def peek(self):
        self._refill()
        return self.outbox[-1]

    def __len__(self):
        return len(self.inbox) + len(self.outbox)
```

## Worked example

```steps
push 1, 2, 3: each is one append to in (top on the right)
    in   [1, 2, 3]
    out  []
    moves so far: 0
---
pop: out is empty, so pour in across: 3, then 2, then 1. The oldest, 1, is now on top of out and is returned
    in   []
    out  [3, 2]          returned {{1}}
    moves so far: {{3}}
---
push 4: goes to in; out still holds older items and is left alone
    in   [{{4}}]
    out  [3, 2]
    moves so far: 3
---
pop: out is not empty, so no transfer; return 2 in O(1)
    in   [4]
    out  [3]             returned {{2}}
    moves so far: 3
---
pop: return 3, still no transfer
    in   [4]
    out  []              returned {{3}}
    moves so far: 3
---
pop: out is empty again, so pour the single item across and return 4. Four items, four moves in total
    in   []
    out  []              returned {{4}}
    moves so far: {{4}}
```

## Pitfalls

- Pouring on every pop and pouring back on every push: each operation becomes O(n), O(n^2) overall.
- Pouring while *out* is not empty: newer items land on top of older ones and FIFO order breaks.
- `peek` must refill exactly like `pop`, and the size is `len(in) + len(out)`.

## Quick check

Q: Push 1 to 5, pop, push 6, pop, pop. How many element moves happen in total, and what do the stacks hold at the end?
A: 5 moves, all during the first pop, which returns 1. The next two pops return 2 and 3 straight from *out*. At the end *in* is `[6]` and *out* is `[5, 4]`, with 4 on top, the next item to leave.

> [!know]
> You now know how to build a queue from two stacks and prove its amortised O(1) cost by counting each element's moves.

=== lab | Deque three ways: list, linked list and ring buffer | 45 min
goal: Implement a deque with a list, a circular doubly linked list and a growable ring buffer, prove each correct against collections.deque, and measure why the built-in wins
link: Open Data Structures: 2.4 ArrayDeque | https://opendatastructures.org/ods-python/2_4_ArrayDeque_Fast_Deque_O.html | 10 min: the circular array deque with its resize rule, the design behind RingDeque below

You will build the same four-operation deque (`append`, `appendleft`, `pop`, `popleft`) on three different foundations, check all three against `collections.deque` with a random tester, and time them on a queue workload. If you built the `dsakit` stress runner in the correctness module, use it; the 30-line tester below does the same job.

## Steps

1. Save this as `deque3.py`. Read each class before running it and predict the cost of `appendleft` and `popleft` for each.

```python
import random
import time
from collections import deque


class ListDeque:
    """Python list underneath: the right end is cheap, the left end shifts every element."""

    def __init__(self):
        self.a = []

    def append(self, x):
        self.a.append(x)

    def appendleft(self, x):
        self.a.insert(0, x)              # O(n)

    def pop(self):
        if not self.a:
            raise IndexError("pop from an empty deque")
        return self.a.pop()

    def popleft(self):
        if not self.a:
            raise IndexError("pop from an empty deque")
        return self.a.pop(0)             # O(n)

    def __len__(self):
        return len(self.a)


class _Node:
    __slots__ = ("val", "prev", "next")

    def __init__(self, val=None):
        self.val = val
        self.prev = self.next = self


class LinkedDeque:
    """Circular doubly linked list with one sentinel: no None checks at either end."""

    def __init__(self):
        self.root = _Node()              # root.next is the front, root.prev the back
        self.n = 0

    def _insert_after(self, node, val):
        new = _Node(val)
        new.prev, new.next = node, node.next
        node.next.prev = new
        node.next = new
        self.n += 1

    def _unlink(self, node):
        if node is self.root:
            raise IndexError("pop from an empty deque")
        node.prev.next = node.next
        node.next.prev = node.prev
        self.n -= 1
        return node.val

    def append(self, x):
        self._insert_after(self.root.prev, x)

    def appendleft(self, x):
        self._insert_after(self.root, x)

    def pop(self):
        return self._unlink(self.root.prev)

    def popleft(self):
        return self._unlink(self.root.next)

    def __len__(self):
        return self.n


class RingDeque:
    """Circular array that doubles when full; item i lives at (head + i) % capacity."""

    def __init__(self, capacity=8):
        self.buf = [None] * capacity
        self.head = 0
        self.n = 0

    def _grow(self):
        old, cap = self.buf, len(self.buf)
        self.buf = [old[(self.head + i) % cap] for i in range(self.n)] + [None] * cap
        self.head = 0

    def append(self, x):
        if self.n == len(self.buf):
            self._grow()
        self.buf[(self.head + self.n) % len(self.buf)] = x
        self.n += 1

    def appendleft(self, x):
        if self.n == len(self.buf):
            self._grow()
        self.head = (self.head - 1) % len(self.buf)
        self.buf[self.head] = x
        self.n += 1

    def pop(self):
        if self.n == 0:
            raise IndexError("pop from an empty deque")
        i = (self.head + self.n - 1) % len(self.buf)
        x, self.buf[i] = self.buf[i], None
        self.n -= 1
        return x

    def popleft(self):
        if self.n == 0:
            raise IndexError("pop from an empty deque")
        x, self.buf[self.head] = self.buf[self.head], None
        self.head = (self.head + 1) % len(self.buf)
        self.n -= 1
        return x

    def __len__(self):
        return self.n


OPS = ("append", "appendleft", "pop", "popleft")


def stress(cls, trials=2000, steps=200, seed=0):
    rng = random.Random(seed)
    for t in range(trials):
        mine, ref, log = cls(), deque(), []
        for _ in range(rng.randint(0, steps)):
            op = rng.choice(OPS)
            log.append(op)
            if op.startswith("append"):
                x = rng.randint(0, 99)
                getattr(mine, op)(x)
                getattr(ref, op)(x)
            else:
                want = got = "IndexError"
                try:
                    want = getattr(ref, op)()
                except IndexError:
                    pass
                try:
                    got = getattr(mine, op)()
                except IndexError:
                    pass
                assert got == want, (cls.__name__, t, log)
            assert len(mine) == len(ref), (cls.__name__, t, log)
    print(f"{cls.__name__}: {trials} random runs agree with collections.deque")


def queue_workload(cls, n):
    """Fill with n items, then n rounds of append + popleft (a FIFO queue at steady size n)."""
    d = cls()
    for i in range(n):
        d.append(i)
    t0 = time.perf_counter()
    for i in range(n):
        d.append(i)
        d.popleft()
    return time.perf_counter() - t0


if __name__ == "__main__":
    for cls in (ListDeque, LinkedDeque, RingDeque):
        stress(cls)
    kinds = (ListDeque, LinkedDeque, RingDeque, deque)
    print(f"{'n':>8} " + " ".join(f"{c.__name__:>12}" for c in kinds))
    for n in (10_000, 20_000, 40_000, 80_000):
        row = [min(queue_workload(c, n) for _ in range(3)) for c in kinds]
        print(f"{n:>8} " + " ".join(f"{t * 1e3:>10.1f}ms" for t in row))
```

2. Run `python3 deque3.py`. All three stress tests must pass before you look at any timing.
3. Break `LinkedDeque._insert_after` on purpose: swap the last two lines so `node.next = new` runs before `node.next.prev = new`. Run the stress test, read the failing operation log it prints, and explain from a drawing which link is now wrong. Restore the order.
4. Break `RingDeque._grow` by copying `old` as it is (`self.buf = old + [None] * cap`) without unrolling from `head`. Find a failing case, then explain why it only fails after the head has wrapped.
5. Write down, before reading the timing table, how the time per operation should change when n doubles for each column. Then compare with the table and compute the ratios.
6. Optional: add `rotate(k)` to `RingDeque` and `LinkedDeque`, and a stress test against `deque.rotate`.

## What you should see

- The three stress tests pass with the correct code, and each planted bug fails within the first few random runs. The linked-list bug fails on a log as short as `append, pop`: the sentinel's back link is never updated, so `pop` finds the sentinel and reports an empty deque; the ring bug needs the head to move and the buffer to fill first, so its shortest failing log is about ten operations long.
- The list version's total time grows about four times per doubling of n once the list is large (from a few microseconds per operation at 10,000 items to about 50 at 80,000 on the machine used here), because every `pop(0)` shifts n references.
- The linked and ring versions stay roughly flat at 0.5 to 2 microseconds per operation, and `collections.deque` at about 0.1: roughly ten times faster again, because its loop runs in C over 64-item blocks instead of Python objects per item. Exact numbers vary by machine and run; the shapes do not.
- The planted `RingDeque` bug survives until an `appendleft` (or a `popleft`) has moved `head` away from 0 before a resize; while head is 0 the old array is already in order, so copying it unchanged happens to be right.

## Check yourself

Q: Your linked and ring deques have the same O(1) bounds. Which would you expect to use less memory per item, and why?
A: The ring deque: one 8-byte reference per slot (with at most half the slots empty just after a doubling), while each linked node is a separate object of about 56 bytes with `__slots__` (header plus three references) on top of its value. That memory gap is also part of why the linked version is no faster despite never copying.

=== practice
- 206 core
  cue: Every arrow in a singly linked chain must point the other way, without building a new list.
  hint: Walk once from the head. At each node, what must you remember before you change its next pointer?
  insight: Keep prev (head of the part already reversed) and curr (head of the rest). Save nxt = curr.next, point curr.next at prev, then advance prev = curr and curr = nxt. When curr is None, prev is the new head.
  cost: O(n) time, O(1) extra space
  pattern: linear-rewire
- 21 core
  cue: Two chains that are already in order must become one chain in order, reusing their nodes.
  hint: Deciding which node becomes the head of the result is a special case. How can you avoid making it?
  insight: Start from a dummy node with a tail pointer. Repeatedly attach the smaller of the two current heads and advance that list; when one runs out, attach the other whole. Return dummy.next.
  cost: O(m + n) time, O(1) extra space
  pattern: linear-rewire
- 141 core
  cue: Decide whether following next pointers ever ends, using constant memory.
  hint: Picture two runners on a track, one twice as fast as the other. What happens if the track loops?
  insight: Move slow one node and fast two nodes per step. If fast reaches None there is no cycle; if there is one, fast gains one node per step inside it and must land on slow within one lap. Compare nodes with `is`.
  cost: O(n) time, O(1) space
  pattern: linear-fastslow
- 20 core
  cue: Three kinds of brackets must close in the reverse of the order they opened.
  hint: When a closing bracket arrives, which opening bracket is the only one it may legally close?
  insight: Push every opener. On a closer the stack must be non-empty and its top must be the matching opener, which you pop. At the end the stack must be empty, otherwise something was never closed.
  cost: O(n) time, O(n) space
  pattern: linear-nesting
- 232 core
  cue: First-in, first-out behaviour built only from last-in, first-out containers.
  hint: Pouring one stack into another reverses its order. When is it safe to pour?
  insight: Push into an in stack; pop and peek from an out stack, refilling out from in only when out is empty. Each element is moved at most once, so every operation is O(1) amortised even though one refill can move n elements.
  cost: O(1) amortised per operation, O(n) space
  pattern: linear-twostack
- 19 core
  cue: Delete the node a given distance from the end of a list, in a single pass.
  hint: If one pointer starts n + 1 nodes ahead of another and both move together, where is the back pointer when the front one falls off the end?
  insight: From a dummy placed before the head, move fast n + 1 steps, then move fast and slow together until fast is None. Slow is now just before the target, so set slow.next = slow.next.next. The dummy makes deleting the head an ordinary case.
  cost: O(n) time, O(1) space
  pattern: linear-fastslow
- 142 derive
  cue: Return the node where a loop begins, not just whether one exists, with constant memory.
  hint: When fast and slow meet, compare how far each has walked. What does the difference tell you about laps of the cycle?
  insight: At the meeting slow has walked t steps and fast 2t, so t is a whole number of laps. Walking mu (the distance from the head to the entry) more steps from the meeting point therefore lands on the entry. Restart one pointer at the head and step both by one: they meet exactly at the entry.
  cost: O(n) time, O(1) space
  pattern: linear-fastslow
- 394 core
  cue: Counts followed by bracketed text that may itself contain counted brackets, such as 2[x3[y]].
  hint: When you meet an opening bracket, what must you remember about the text and the count outside it?
  insight: On "[" push (text built so far, repeat count) and start a fresh text; on "]" pop and set text = outer + inner * count. Accumulate multi-digit counts with num = num * 10 + d, and collect text in lists joined once.
  cost: O(length of the output) time and space
  pattern: linear-nesting
- 150 core
  cue: An arithmetic expression in which every operator comes after its two operands.
  hint: When an operator arrives, where are its operands, and which of the two is on top?
  insight: Push numbers; on an operator pop b (the right operand) and then a (the left) and push a op b. Division truncates towards zero, so use int(a / b) for small values or sign-aware integer division, never Python's //.
  cost: O(n) time, O(n) space
  pattern: linear-expr
- 224 derive
  cue: Plus, minus, nested parentheses and minus signs in front of whole groups, to be evaluated without eval.
  hint: A parenthesised group is just a sub-result. What do you need to remember about the outside when you step into one?
  insight: Keep result, the sign of the next number and the current digits. On "(" push (result, sign) and reset to 0 and +1; on ")" add the pending number, pop (outer, s) and set result = outer + s * result. A leading or unary minus only sets sign to -1.
  cost: O(n) time, O(n) space for the nesting depth
  pattern: linear-expr
- 287 stretch
  cue: n + 1 values in the range 1..n with one value repeated; the array must not change and extra space must be O(1).
  hint: Read nums[i] as "the node after i". Starting from index 0, what shape does following those links trace out?
  insight: Index 0 is never a value, so following i -> nums[i] from 0 walks a tail into a cycle. The cycle's entry is reached by two different indices, so it is the repeated value. Run both phases of Floyd's algorithm on indices.
  cost: O(n) time, O(1) space
  pattern: linear-fastslow
- 25 stretch
  cue: Reverse every consecutive block of k nodes, leaving a final short block as it is.
  hint: Before reversing a block, make sure it really has k nodes. Which links must you reconnect after reversing it?
  insight: Keep group_prev, the node before the block (a dummy at first). Find the k-th node; if it is missing, stop. Reverse the block so its first node points to the node after the block, then set group_prev.next to the old k-th node and move group_prev to the old first node, now the block's tail.
  cost: O(n) time, O(1) extra space
  pattern: linear-rewire
