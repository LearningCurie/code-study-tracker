---
key: projectfrontier
name: Build a tiny-sort experiment
stage: frontier
summary: Exhaustively test a fixed compare-swap network and compare its work with insertion sort.
why: Small sorting kernels show how rigorous validation and careful benchmarks qualify performance claims.
outcomes:
- Validate a sorting network over all small input permutations.
- Distinguish algorithmic operation counts from machine-specific timing.
cues:
- A fixed, tiny number of elements is sorted repeatedly.
- A reported improvement needs reproducible evidence.
traps:
- Passing distinct permutations but mishandling duplicate values.
- Claiming to reproduce a paper's low-level implementation from a high-level toy.
---

=== build | Four-value sorting kernel study | 6-8 h
goal: Compare a fixed sorting network with insertion sort on four-element inputs.
link: AlphaDev sort patch | https://www.nature.com/articles/s41586-023-06004-9#Sec16 | Read the production-patch discussion and scope its claims.
link: Rust sort implementation | https://doc.rust-lang.org/std/primitive.slice.html#method.sort_unstable | See how a library describes its current sort implementation.

## The brief
Write a small experiment exploring a frontier lesson's theme: specialised sorting for tiny inputs. Your compare-swap network is a conventional educational construction, not AlphaDev and not a reproduction of its assembly-level results.

## Spec
Implement two independent functions returning a sorted copy of exactly four integers: insertion sort and the network `(0,1), (2,3), (0,2), (1,3), (1,2)`, where each pair is compare-swapped. Reject other lengths. Instrument element comparisons consistently in each algorithm; a network always performs five, while insertion sort counts every actual comparison of input values. Keep instrumentation outside the timing comparison or use equivalently instrumented implementations and disclose which.

Test all 24 permutations of four distinct values and all 81 arrays over `{-1,0,1}` against the language's reference sort. Benchmark fixed-seed random, sorted, reverse and duplicate-heavy arrays. Report data generation separately, warm up, run five trials and show median time plus comparisons; do not claim a high-level timing proves instruction-level savings.

## Milestones
1. **1-2 h:** Implement insertion sort and reference checks for the fixed-size contract.
2. **1-2 h:** Implement and trace the five-comparator network.
3. **1-2 h:** Exhaustively test permutations, duplicates and input validation.
4. **1-2 h:** Benchmark input distributions and write a qualified interpretation.

## Done when
- Both functions sort all 24 permutations and all 81 duplicate-containing cases exactly like the reference and do not mutate inputs.
- The network makes exactly five element comparisons per input; insertion-sort comparison counts are checked by a hand trace for sorted and reverse input.
- Benchmark 100,000 arrays per distribution using the same arrays for both algorithms. Report five-run medians and comparison totals, runtime and machine; verify output outside timing.
- Explain why both are constant work for fixed length, why insertion sort's comparisons depend on order, and why interpreter and measurement overhead can hide or reverse small differences.
- The report explicitly distinguishes this experiment from the paper's implementation and makes no unmeasured speedup claim.

## Stretch goals
- Compare another valid four-input network and test it exhaustively.
- Run the benchmark in a compiled language and discuss whether the result changes.

## Hints
- The paper's [libc++ sort patch discussion](https://www.nature.com/articles/s41586-023-06004-9#Sec16) shows why the implementation level matters.
- Compare the wording in [Rust's sort documentation](https://doc.rust-lang.org/std/primitive.slice.html#method.sort_unstable) with the narrow scope of your own measurements.
