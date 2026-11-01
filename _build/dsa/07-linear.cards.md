=== card | 206
time: 20 min

## The problem

Turn a finite singly linked chain around in place and return its new head. The existing node objects must be reused: a chain with values 3, 5, 8 becomes 8, 5, 3. An empty chain has no head to return.

## Constraints and what they imply

Each node has a value and one `next` reference; assume the input is acyclic. The algorithm must not rely on random access or make a second chain. A constant number of node references suffices, even for chains too long for Python recursion.

## Brute force

Collect all node references in an array, then connect them in reverse order and terminate the old head. This visits and rewires n nodes in O(n) time but needs O(n) additional references. Repeatedly searching for the current tail instead uses O(1) space but takes O(n²) time.

## The insight

At every iteration `prev` heads exactly the already reversed prefix and `curr` heads the untouched suffix. Save `curr.next` before redirecting it: otherwise that suffix would no longer be reachable. Attaching the current node to `prev` increases the reversed prefix by one without losing any node.

## Optimal solution, traced

```steps
prev = None, curr = 3 -> 5 -> 8
    save 5, then point 3 to None
---
prev = 3, curr = 5 -> 8
    save 8 and point 5 to 3
---
prev = 5 -> 3, curr = 8
    reverse the last arrow; return {{8 -> 5 -> 3}}
```

The two parts start disjoint and cover the input. Each step transfers exactly one node and preserves this invariant. When the suffix is empty, the prefix contains all nodes in the desired order, so its head is the answer.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head):
    prev, curr = None, head
    while curr is not None:
        following = curr.next
        curr.next = prev
        prev, curr = curr, following
    return prev
```

## Complexity

Each node is processed once: O(n) time and O(1) auxiliary space. The input links are modified; values and node identities are preserved.

## Mistakes and edge cases

- Saving the successor after overwriting `next` loses the unprocessed suffix.
- Returning the old head returns the new tail instead.
- Empty and one-node lists require no special branch.

## Variations

- Reverse only a bounded segment by reconnecting its two boundary links.
- Reverse a doubly linked list by exchanging both directions at every node.

=== card | 21
time: 20 min

## The problem

Given two sorted singly linked chains, combine them into one sorted chain by relinking their existing nodes. For 1 → 4 and 2 → 3, return 1 → 2 → 3 → 4. Equal values are allowed and each node must appear exactly once.

## Constraints and what they imply

Inputs are finite, acyclic, nondecreasing, and disjoint; an input may be empty. Relinking avoids allocating one new node per result element. If the chains shared a node, naive rewiring could create a cycle, so disjointness is important.

## Brute force

Gather all node references in an array, sort by value, and reconnect consecutive references. This costs O((m+n) log(m+n)) time and O(m+n) auxiliary space. It ignores the useful ordering already present in each chain.

## The insight

The smallest remaining node must be one of the two heads. A sentinel before the result allows the same append operation even for the first node. Taking the left head on ties makes the merge stable with respect to the two input chains.

## Optimal solution, traced

```steps
Heads 1 and 2; result is empty
    attach 1, advance its chain to 4
---
Heads 4 and 2, then 4 and 3
    attach 2 and 3 in that order
---
The second chain is empty
    attach the entire remainder: {{1 -> 2 -> 3 -> 4}}
```

The output prefix is sorted and every appended node is no larger than either remaining head. Since each remainder is sorted, choosing the smaller head preserves that property. When a chain ends, the other remainder is already sorted and can be attached whole.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def merge_lists(a, b):
    dummy = tail = ListNode()
    while a is not None and b is not None:
        if a.val <= b.val:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a is not None else b
    return dummy.next
```

## Complexity

At most m+n nodes are examined, for O(m+n) time and O(1) auxiliary space including the sentinel. The input links change, but result nodes are the original nodes.

## Mistakes and edge cases

- Return `dummy.next`, not the artificial sentinel.
- Advance the selected source and the tail; forgetting either can lose nodes or loop.
- Either or both inputs may be empty; the final attachment handles them.

## Variations

- Merge descending chains by reversing the comparison.
- Merge several chains by maintaining a heap of their current heads.

=== card | 141
time: 20 min

## The problem

Decide whether repeated `next` references from a given head ever revisit a node. A chain may end at None or eventually enter a loop. Two different nodes with equal values are not a cycle.

## Constraints and what they imply

Each node has at most one successor, and node identity, not stored value, determines repetition. Use constant extra memory rather than storing every visited reference. The head may be None or a node pointing to itself.

## Brute force

Record each visited node identity in a set. Encountering a recorded node proves a loop; reaching None proves termination. This takes O(n) time and O(n) space for n distinct reachable nodes. It is straightforward but stores the entire path.

## The insight

Move one pointer by one edge and another by two. In an acyclic chain, the faster pointer eventually runs off the end. Once both pointers are inside a cycle, their positions modulo the cycle length differ by one additional step each iteration, so the difference eventually becomes zero.

## Optimal solution, traced

```steps
Chain A -> B -> C -> B, both pointers begin at A
    slow reaches B; fast reaches C
---
Move again: slow reaches C, fast follows C -> B -> C
    both references identify {{C}}
---
A meeting means the successor walk repeats
    return {{True}}
```

If a meeting occurs after movement, following the same deterministic successor relation returns to the same node, so a cycle exists. Conversely, after entering a cycle the relative position advances through all residues and must meet within one lap. Thus neither outcome is a false positive.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def has_cycle(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
```

## Complexity

With n distinct reachable nodes, the tail and at most one cycle lap take O(n) time. Only two references are stored, so auxiliary space is O(1); the chain is unchanged.

## Mistakes and edge cases

- Compare references with `is`, not node values.
- Test both `fast` and `fast.next` before advancing two steps.
- A self-loop meets after one step; an empty input immediately returns False.

## Variations

- After a meeting, find the cycle entry by restarting one pointer at the head.
- Measure the cycle length by walking once around from a meeting point.

=== card | 20
time: 20 min

## The problem

Determine whether a string containing only the three bracket pairs `()`, `[]`, and `{}` is properly nested and fully closed. For instance, `{[()]}` is valid but `([)]` is not. The empty string is valid.

## Constraints and what they imply

Every input character is one of the six brackets. A closing bracket must match the most recent opener that has not already been closed. Counts alone do not capture nesting order, so the relevant history must be retained.

## Brute force

Repeatedly remove any adjacent matching pair until no further removal is possible; accept exactly when the string is empty. This works because an innermost pair is adjacent after its contents disappear. Repeated scans and string rebuilding can take O(n²) time and O(n) space.

## The insight

A stack keeps unmatched openers in their order of appearance. The newest opener is the only one a closer may match. Remove it only when its type matches, and reject immediately if no matching opener exists.

## Optimal solution, traced

```steps
Read ( then [ in ([{}])
    stack contains ( and [
---
Read { then }
    push { and remove it again
---
Read ] then )
    stack becomes {{empty}}, so accept
```

After each valid prefix the stack is exactly its unmatched openers in opening order. The next closer must match its top, so rejection is necessary on mismatch. If the scan finishes with an empty stack every opener has a correct closer; otherwise at least one remains open.

## Code

```python
def valid_brackets(text):
    matching = {')': '(', ']': '[', '}': '{'}
    stack = []
    for char in text:
        if char in matching:
            if not stack or stack.pop() != matching[char]:
                return False
        else:
            stack.append(char)
    return not stack
```

## Complexity

Each character is pushed or examined once, giving O(n) time. A string of only openers uses O(n) stack space.

## Mistakes and edge cases

- A closer on an empty stack is invalid, not a reason to pop.
- Matching totals do not imply correct nesting.
- Leftover openers invalidate the result; empty input is accepted.

## Variations

- Ignore non-bracket characters before applying the same stack rule.
- Report the index of the first invalid closer rather than a Boolean.

=== card | 232
time: 20 min

## The problem

Implement a first-in, first-out queue using two last-in, first-out stacks. Support adding at the back, removing the front, inspecting the front, and checking emptiness. After adding 4 then 7, removing yields 4.

## Constraints and what they imply

Use stack-end operations only. Values may repeat and can be any Python objects. This implementation raises `IndexError` when removing or inspecting an empty queue, instead of inventing a sentinel value. A single operation may take linear time, but the average over a sequence should be constant.

## Brute force

For every removal, move all elements to a second stack, pop the oldest, then move the rest back. Each removal can cost O(n), for O(q²) total time across q operations and O(n) storage. Repeatedly reversing the same elements wastes work.

## The insight

Keep incoming values in one stack and ready-to-remove values in another. Transfer all incoming values only when the outgoing stack is empty. The transfer reverses arrival order, putting the oldest at the top. New arrivals remain behind all values already in the outgoing stack.

## Optimal solution, traced

```steps
Push 4 then 7
    incoming is [4, 7], outgoing is empty
---
Peek: transfer 7 then 4
    outgoing is [7, 4], top {{4}}
---
Push 9, then pop
    remove {{4}}; 7 still precedes 9
```

The queue order is outgoing from top to bottom followed by incoming from bottom to top. Pushing preserves this order. A transfer reverses incoming precisely when there are no older outgoing values, and popping the outgoing top removes exactly the oldest value.

## Code

```python
class TwoStackQueue:
    def __init__(self):
        self.incoming = []
        self.outgoing = []

    def push(self, value):
        self.incoming.append(value)

    def _refill(self):
        if not self.outgoing:
            while self.incoming:
                self.outgoing.append(self.incoming.pop())

    def pop(self):
        self._refill()
        return self.outgoing.pop()

    def peek(self):
        self._refill()
        return self.outgoing[-1]

    def empty(self):
        return not self.incoming and not self.outgoing
```

## Complexity

Each item enters incoming, moves to outgoing at most once, and leaves once. Thus a sequence of q operations costs O(q) amortized time, although an individual refill costs O(n). Space is O(n) for n queued items.

## Mistakes and edge cases

- Never transfer incoming onto a nonempty outgoing stack: newer values would jump ahead.
- Peek must refill just like pop but leave the front in place.
- Both stacks must be empty for the queue to be empty.

## Variations

- Build a stack from queues, accepting a costly push or pop.
- Use a deque when the exercise does not require stacks.

=== card | 19
time: 30 min

## The problem

Remove the node n positions from the end of a singly linked chain and return the resulting head. Positions are one-based: in 4 → 6 → 9 → 2, removing position 2 from the end removes 9. Relink the remaining existing nodes rather than constructing a replacement chain.

## Constraints and what they imply

The chain is finite, acyclic, and nonempty; `1 <= n <= length`. The head itself may need removal, so a pointer before the head simplifies the boundary case. A single forward traversal with constant auxiliary space is possible without knowing the length in advance.

## Brute force

First count the nodes, then walk again to the predecessor of the node at index `length - n` and unlink it. This takes O(L) time and O(1) space for length L, but makes two traversals and needs a separate head case unless it uses a sentinel. Alternatively, storing all node references gives random access but costs O(L) space.

## The insight

Put a dummy before the head and place `fast` n+1 edges ahead of `slow`, which starts at the dummy. Move both references together. When fast reaches None, slow is immediately before the target, including when that predecessor is the dummy. The fixed gap converts a distance from the end into a forward walk.

## Optimal solution, traced

```steps
Chain 4 -> 6 -> 9 -> 2, n = 2
    slow starts at dummy; move fast three edges to 9
---
Move both once, then again
    fast reaches None while slow reaches 6
---
Replace slow.next by slow.next.next
    result {{4 -> 6 -> 2}}
```

Initially the pointers have a gap of n+1 edges. Synchronous movement preserves the gap. At termination exactly n nodes follow slow, so its successor is the nth node from the end. Unlinking that successor preserves the order of every other node; `dummy.next` is the correct new head even when the target was first.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def remove_nth_from_end(head, n):
    dummy = ListNode(0, head)
    slow = fast = dummy
    for _ in range(n + 1):
        fast = fast.next
    while fast is not None:
        slow = slow.next
        fast = fast.next
    slow.next = slow.next.next
    return dummy.next
```

## Complexity

The fast pointer advances across the chain once, while slow advances at most L times. Total time is O(L), and the dummy and pointers use O(1) auxiliary space. The removed node is not copied, and the original chain is modified.

## Mistakes and edge cases

- The gap is n+1 when both pointers begin at the dummy; a gap of n puts slow on the target rather than its predecessor.
- Removing the only node or the original head must return the new `dummy.next`.
- The stated precondition excludes n=0 and n larger than the length; validate these separately if accepting untrusted input.

## Variations

- Return the removed node as well as the new head, detaching its next link if needed.
- Given a known length, make a preliminary count unnecessary and walk directly to the predecessor.

=== card | 142
time: 30 min

## The problem

Return the actual node at which a singly linked chain first enters a cycle, or None when the chain ends. For A → B → C → D → B, the answer is the node B, not an arbitrary meeting node. Values may repeat, so the answer is an object reference.

## Constraints and what they imply

Every reachable node has one successor or None. The input may be empty, acyclic, a self-loop, or a cycle beginning at the head. The links must remain unchanged, and the method uses O(1) auxiliary references rather than marking nodes or storing a visited set.

## Brute force

Walk from the head, keeping a set of previously visited node identities. The first repeated identity is the entry because a deterministic successor walk revisits nothing before entering its cycle. This takes O(n) time and O(n) space for n distinct reachable nodes. It is an excellent oracle but does not meet the constant-space goal.

## The insight

First find a meeting using speeds one and two. Let μ be the number of edges from the head to the entry, λ the cycle length, and t the number of slow steps at the meeting. The fast pointer has taken 2t steps, so t is a multiple of λ. Consequently the meeting point is t-μ edges around the cycle from the entry, and advancing μ more edges returns it to the entry. A pointer restarted at the head also reaches the entry after μ steps.

## Optimal solution, traced

```steps
A -> B -> C -> D -> B
    slow and fast start at A; cycle entry is B
---
After three moves both pointers meet at D
    restart one pointer at A, leave the other at D
---
Advance both once: A -> B and D -> B
    their first new meeting is {{B}}
```

The initial meeting exists for every cycle because the relative distance changes by one modulo λ. If the fast pointer reaches None there can be no cycle. During the second phase the restarted pointer cannot meet a cycle node before it has traversed its μ-edge tail. At exactly μ steps both pointers are at the entry by the modular argument, proving it is the first meeting.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def cycle_entry(head):
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            seeker = head
            while seeker is not slow:
                seeker = seeker.next
                slow = slow.next
            return seeker
    return None
```

## Complexity

Finding the meeting and then the entry requires O(n) time over the distinct reachable nodes. There are only a few references, so extra space is O(1). No node is changed.

## Mistakes and edge cases

- Comparing equal values instead of identical nodes can claim a false meeting.
- Do not return the phase-one meeting unless it happens to be the entry.
- Check the fast pointer's successor before taking two steps; a self-loop and a cycle at the head both work.

## Variations

- Determine only whether a cycle exists and stop at the first meeting.
- Once the entry is found, walk one lap to obtain the cycle length.

=== card | 394
time: 30 min

## The problem

Expand nested repetition expressions: a positive decimal count immediately followed by brackets repeats the bracket contents that many times. Literal letters are copied. For example `2[a3[b]]` expands to `abbbabbb`. Brackets delimit repetitions and are not included in the output.

## Constraints and what they imply

Assume a well-formed expression with positive counts, lowercase literal letters, balanced brackets, and no other characters; counts can have multiple digits. Nested groups can expand far beyond the encoded input, so any algorithm must at least write the output. The implementation is iterative, avoiding recursion depth limits.

## Brute force

Repeatedly locate an innermost bracketed group, find the digits before it, replace the whole group with the repeated interior, and rescan the resulting string. Although straightforward, repeated searching and copying can cost quadratic time or more in the size of intermediate strings. It also repeatedly examines literal characters already processed.

## The insight

Maintain a list of fragments for the current nesting level. On an opening bracket, save the outer fragments and repetition count, then start a fresh inner list. On a closing bracket, join the inner fragments and append its repeated text to the saved outer list. This stack represents precisely the nesting levels still open.

## Optimal solution, traced

```steps
Read 2[ then a then 3[
    saved contexts have counts 2 and 3; current text is empty
---
Read b] and expand the inner context
    outer fragments now represent abbb
---
Close the outer context
    repeat abbb twice to produce {{abbbabbb}}
```

Inductively, each fragment list is the fully decoded text read so far at its level. Opening a group postpones its contribution until the matching closer. At a closer, the inner list is complete, and repeating it exactly the requested number of times appends the correct contribution to its parent. At the end the only remaining list is the complete output.

## Code

```python
def decode_string(text):
    stack = []
    parts = []
    count = 0
    for char in text:
        if char.isdigit():
            count = count * 10 + int(char)
        elif char == '[':
            stack.append((parts, count))
            parts = []
            count = 0
        elif char == ']':
            outer, repeat = stack.pop()
            outer.append(''.join(parts) * repeat)
            parts = outer
        else:
            parts.append(char)
    return ''.join(parts)
```

## Complexity

Let N be encoded length and S the sum of lengths of all materialized group expansions, including nested intermediate results and the final output. Time is O(N+S), not necessarily O(N+output length): deeply nested count-one groups can repeatedly copy the same text. With positive counts, retained fragments represent disjoint portions of the final result; peak auxiliary space is O(N+L), where L is final output length, including transient copies.

## Mistakes and edge cases

- Accumulate every digit; treating `12` as two counts changes the result.
- Reset the count after opening a group, and restore the correct outer fragments after closing it.
- Adjacent groups and literal prefixes or suffixes are valid; malformed input is outside this contract.

## Variations

- Compute decoded length without materializing the string, using a stack of counts and lengths.
- Stream output with an explicit traversal when the expanded result is too large to retain.

=== card | 150
time: 30 min

## The problem

Evaluate an arithmetic expression supplied in postfix order: each operator follows its two operands. Tokens are signed decimal integers or one of `+`, `-`, `*`, `/`. For tokens `["7", "3", "-", "2", "*"]`, the result is 8.

## Constraints and what they imply

The token sequence is valid, ends with exactly one value, and never divides by zero. Division truncates toward zero, even for negative results. Python's `//` floors instead, and converting a huge integer quotient through a float can lose precision, so use integer arithmetic throughout.

## Brute force

Repeatedly find an operator immediately preceded by two numeric tokens, replace those three tokens with their evaluated result, and restart the scan. A valid postfix expression always has such a reducible operation until only one value remains. Repeated scanning and list splicing cost O(T²) time and O(T) space for T tokens, ignoring integer bit costs.

## The insight

Scan once while storing values of complete subexpressions. A number is already a complete subexpression. An operator consumes the two most recent subexpressions: pop the right operand first, then the left, and push their result. For division, floor the quotient of absolute values and apply the result's sign.

## Optimal solution, traced

```steps
Read 7 and 3
    stack is [7, 3]
---
Read -: pop right 3 then left 7
    push 4; read 2, giving [4, 2]
---
Read *: push 4 * 2
    final stack contains {{8}}
```

After each prefix the stack consists of complete subexpression values awaiting future operators, in their original order. Each operator replaces exactly its two operands with their value, maintaining the invariant. A valid full expression has one such value, which is the answer.

For example, the stack after processing two independent operands has their left-to-right values, even if either operand was itself produced by many earlier tokens. The stack does not need to retain the original expression text: its future behavior depends only on these computed values. That is why a local reduction is equivalent to evaluating the corresponding subtree.

## Code

```python
def evaluate_postfix(tokens):
    stack = []
    for token in tokens:
        if token not in {"+", "-", "*", "/"}:
            stack.append(int(token))
            continue
        right = stack.pop()
        left = stack.pop()
        if token == "+":
            value = left + right
        elif token == "-":
            value = left - right
        elif token == "*":
            value = left * right
        else:
            value = abs(left) // abs(right)
            if (left < 0) != (right < 0):
                value = -value
        stack.append(value)
    return stack[-1]
```

## Complexity

There are O(T) stack operations and O(T) space in the worst case, under the usual unit-cost arithmetic model. Python integers have arbitrary precision, so arithmetic on large intermediate values has additional bit-dependent time and storage costs.

## Mistakes and edge cases

- Subtraction and division depend on operand order: the first pop is the right operand.
- `-7 // 3` is -3 in Python, whereas truncation toward zero gives -2.
- A single numeric token is already the answer; division by zero and malformed token streams are excluded.

## Variations

- Build an expression tree by pushing nodes instead of computed values.
- Add exponentiation with an explicit rule for negative exponents and integer results.

=== card | 287
time: 30 min

## The problem

An array has n+1 entries, all integers from 1 through n. Exactly one distinct value appears more than once, possibly more than twice. Find that repeated value without modifying the array. For `[2, 1, 3, 2]`, return 2.

## Constraints and what they imply

Assume n is at least one, the value range and unique repeated value are guaranteed, and random array indexing is available. The desired extra space is O(1). Since the array has more entries than possible values, a repetition must exist; however, sorting it in place would violate the read-only requirement.

## Brute force

Compare every pair of entries and return the first equal value. Under the uniqueness promise this is the desired duplicate. It takes O(n²) time and O(1) space without mutating the array. A set makes the scan linear but requires O(n) space; sorting a copy also consumes linear extra space.

## The insight

Treat index i as a node whose successor is `nums[i]`. Following successors from index 0 must eventually repeat, because every successor is an index in 1..n. Index 0 is never a successor, so the walk has a nonempty tail before entering the cycle. The entry has two different incoming edges along this walk: one from the tail and one from the cycle. Their source indices contain the same value, which is the unique duplicate.

Find a meeting by moving one index once and another twice. Then restart one index at 0 and move both one step at a time; their first meeting is the cycle entry.

## Optimal solution, traced

```steps
Array [2, 1, 3, 2] gives edges 0 -> 2 -> 3 -> 2
    the path enters its loop at index 2
---
Slow and fast meet at index 3
    restart slow at 0; leave fast at 3
---
Advance each once: 0 -> 2 and 3 -> 2
    return the entry value {{2}}
```

Let μ be the tail length and λ the cycle length. At the first meeting after t slow steps, the two paths differ by t steps, a multiple of λ. The meeting point is therefore μ steps behind the entry modulo λ. Advancing both the restarted pointer and the meeting pointer by μ steps puts them at the entry; they cannot meet earlier because the restarted pointer remains outside the cycle. By the incoming-edge argument, that entry is the repeated value.

## Code

```python
def find_duplicate(nums):
    slow = fast = 0
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = 0
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow
```

## Complexity

The functional graph has n+1 indices. Each phase takes O(n) steps, so total time is O(n) and auxiliary space is O(1). No entry is written. The validity guarantees are essential for safe indexing and for interpreting the entry as the sole repeated value.

## Mistakes and edge cases

- Start from index 0; starting from an arbitrary value changes the tail argument and can produce the wrong entry.
- Return the entry index itself, not `nums[entry]`, which may be different.
- A duplicate can occur more than twice; n=1 produces `[1, 1]` and a self-loop at index 1.

## Variations

- Binary-search the value range using counts at or below each midpoint, giving O(n log n) time and O(1) space.
- If mutation is allowed, rearrange or mark entries to expose a repeated value, with a different input contract.

=== card | 224
time: 45 min

## The problem

Evaluate a valid integer expression containing decimal numbers, addition, subtraction, parentheses, unary plus and unary minus. Spaces may appear between tokens. For `8-(3-(2+1))`, the result is 8; for `-(4-7)+2`, it is 5. Do not use Python's expression evaluator.

## Constraints and what they imply

The expression is nonempty and syntactically valid. Numbers are nonnegative decimal literals; signs belong to operators rather than to the digits. Parentheses may nest, unary signs may repeat, and subtraction is left-associative. Whitespace separates tokens and does not split a number. Only addition and subtraction are present, so a running signed sum is sufficient at each nesting level.

Python integers are arbitrary precision. No artificial overflow or floating-point conversion is required. Very deep nesting is possible, so an explicit stack is safer than recursive descent if interpreter stack depth is limited.

## Brute force

Find an innermost parenthesized expression, evaluate it by scanning its signed terms, replace that whole region by its integer value, and repeat until no parentheses remain. Repeated searches and string replacements may copy the whole expression once per nesting level, giving O(N²) time in the worst case and O(N) space, excluding integer bit costs. Care is also needed to preserve unary signs when substituting a negative intermediate result.

## The insight

Maintain a sum for the current level and a sign to apply to the next operand. After a binary operator, set the sign for the next operand; while expecting an operand, multiply the sign by each unary minus, leaving it unchanged for unary plus. When an opening parenthesis appears, save the current sum and pending sign, then start a fresh inner sum. A closing parenthesis turns the inner sum into one operand of its saved outer level.

The `expect_operand` flag distinguishes a binary minus after a value from a unary minus before one. This matters for expressions such as `5--2`, where the two minus signs cancel. The saved sign applies to the whole group, not just its first number.

## Optimal solution, traced

```steps
Read -(4-7)+2: the leading minus sets sign to -1
    opening parenthesis saves outer sum 0 and sign -1
---
Inside the group, add 4 and subtract 7
    inner sum is -3; close and restore 0 + (-1)*(-3) = 3
---
Read +2
    final sum is {{5}}
```

For each active level, `total` equals the sum of all completed operands at that level, and `sign` is the accumulated sign for the next operand. Number tokens complete one operand, while opening a group saves the unfinished outer context. By induction on nesting depth, closing a group yields its correct value, which is incorporated using the saved sign. The top-level sum therefore equals the expression once every token is processed. Validity guarantees that each closer has a matching saved context and that the scan ends after an operand.

Repeated unary signs change only the pending sign; they do not finish an operand or alter the accumulated total. A closing parenthesis does finish an operand in the outer context, so a following minus is binary. These transitions make nested negative groups and adjacent operator signs behave consistently without inserting artificial zero literals into the expression.

## Code

```python
def calculate(text):
    total = 0
    sign = 1
    expect_operand = True
    stack = []
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
        elif char.isdigit():
            value = 0
            while i < len(text) and text[i].isdigit():
                value = value * 10 + int(text[i])
                i += 1
            total += sign * value
            sign = 1
            expect_operand = False
        elif char == '(':
            stack.append((total, sign))
            total, sign, expect_operand = 0, 1, True
            i += 1
        elif char == ')':
            outer, multiplier = stack.pop()
            total = outer + multiplier * total
            sign, expect_operand = 1, False
            i += 1
        else:
            factor = 1 if char == '+' else -1
            sign = sign * factor if expect_operand else factor
            expect_operand = True
            i += 1
    return total
```

## Complexity

Each character is consumed once, so there are O(N) parsing operations. The context stack uses O(D) entries for maximum nesting depth D, at most O(N). These are unit-cost arithmetic bounds; building and operating on arbitrary-size integers also has bit-dependent costs. The input text is unchanged.

## Mistakes and edge cases

- Applying a group's outer minus only to its first term gives the wrong answer for `-(4-7)`.
- Treating every minus as binary fails on a leading minus, repeated signs, or signs following an opening parenthesis.
- Do not use `eval`, floor division, or floating-point arithmetic; they are unnecessary here.
- Empty parentheses, missing operands, and invalid characters are outside the contract; validate them separately for untrusted input.

## Variations

- Add multiplication and division by tracking precedence or using a separate operator stack.
- Produce an abstract syntax tree instead of immediately evaluating each group.

=== card | 25
time: 45 min

## The problem

Reverse a finite singly linked chain in consecutive groups of k nodes. Keep the final group unchanged if it has fewer than k nodes. Return the new head and reuse the original nodes. For 1 → 2 → 3 → 4 → 5 with k=2, return 2 → 1 → 4 → 3 → 5.

## Constraints and what they imply

The input is acyclic, may be empty, and k is a positive integer. Values can repeat; correctness concerns node identity and link order, not just values. The nodes must be relinked in place with O(1) extra references. A dummy before the original head avoids a special case for the first reversed group.

The final short group must stay in its original order, so the algorithm must check that k nodes exist before changing any of their links. If k exceeds the entire chain length, return the original head unchanged.

## Brute force

Read all nodes into an array, reverse each complete slice of k references, and reconnect the array in order. This takes O(n) time and O(n) auxiliary space for n nodes. Reversing values rather than nodes might be shorter but changes the association of values to node identities and is not the requested operation.

Another constant-space approach can repeatedly locate each group's end from the start, then perform pointer rewiring. The key is to avoid scanning from the global head for every group, which could cost O(n²); advancing a boundary pointer after each completed group keeps the scans local.

## The insight

Maintain `group_prev`, the node immediately before the untouched suffix. Walk k links to find the last node of the next full group. If it does not exist, stop without modifying that suffix. Otherwise save `group_next`, the first node beyond the group, and reverse the group's arrows, initially pointing the old first node to `group_next`.

After reversal, connect `group_prev.next` to the old kth node. The old first node has become the group's tail, so it is the next `group_prev`. Both boundary links are thus correct before the next iteration starts.

## Optimal solution, traced

```steps
Dummy -> 1 -> 2 -> 3 -> 4 -> 5, k = 2
    locate 2 and save successor 3
---
Reverse 1 and 2, reconnect the dummy
    prefix is {{2 -> 1}}, group_prev is 1
---
Reverse 3 and 4, reconnect after 1
    prefix is {{2 -> 1 -> 4 -> 3}}
---
Only node 5 remains, fewer than k
    leave it unchanged and return {{2 -> 1 -> 4 -> 3 -> 5}}
```

At the start of each iteration, the prefix through `group_prev` is correctly transformed and the remaining suffix retains its original order. Checking the kth node proves the next k nodes exist. Reversing exactly those nodes with initial predecessor `group_next` produces the reverse order and connects its tail to the untouched remainder. Reconnecting the prefix establishes the invariant for the next group. If fewer than k nodes remain, the invariant and stop rule give the required final suffix.

Within a full group, `prev` heads the already reversed portion, ending at the saved successor, while `curr` begins the part not yet reversed. Saving `following` before changing a link keeps that unprocessed part reachable. Each iteration moves one node across the boundary; after k moves, the old kth node heads the whole reversed group and every original node remains present.

## Code

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_k_group(head, k):
    if k <= 0:
        raise ValueError("k must be positive")
    dummy = ListNode(0, head)
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next
            if kth is None:
                return dummy.next
        group_next = kth.next
        prev, curr = group_next, group_prev.next
        while curr is not group_next:
            following = curr.next
            curr.next = prev
            prev, curr = curr, following
        old_first = group_prev.next
        group_prev.next = kth
        group_prev = old_first
```

## Complexity

Finding each group end scans each full group once, and reversing scans those nodes once more. The final failed scan visits fewer than k nodes, so total time is O(n), including k larger than n. Only a fixed number of node references and one dummy are used, giving O(1) auxiliary space. Links in complete groups are changed in place.

## Mistakes and edge cases

- Do not start reversing until the kth node is confirmed; otherwise a short suffix is accidentally reversed.
- Save the successor beyond the group before modifying links, or the remainder can become unreachable.
- Advance `group_prev` to the old first node, now the tail, not to the new group head.
- k=1 preserves the chain; empty input and k greater than its length return the original head. Nonpositive k raises `ValueError`.

## Variations

- Reverse alternating full groups while leaving intervening groups untouched.
- Reverse the final short group too by changing the incomplete-group policy.
