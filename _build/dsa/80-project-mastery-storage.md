---
key: projectmasterystorage
name: Capstone versioned key-value store
stage: mastery
summary: Compose a write-ahead log, sorted snapshots and recovery with a simple compaction protocol.
why: Durable storage requires correctness across restarts as well as efficient in-memory lookup.
outcomes:
- Define and test recovery across explicit crash points.
- Quantify write amplification and replay work.
cues:
- Recent writes must survive a process restart.
- The log grows until old state is compacted.
traps:
- Truncating the log before the replacement snapshot is durable.
- Treating a partial final log record as a committed write.
---

=== build | Capstone: recoverable key-value notebook | 10-12 h
goal: Implement a small single-process key-value store with replay and safe snapshot replacement.
link: LevelDB sorted tables | https://github.com/google/leveldb/blob/main/doc/impl.md#sorted-tables | About 5 min: Compare this simplified snapshot with sorted tables.
link: LevelDB compactions | https://github.com/google/leveldb/blob/main/doc/impl.md#compactions | About 5 min: Study why persistent structures need compaction.

## The brief
Build a local notebook that survives process restarts. This is an instructional single-writer store, not LevelDB: there are no concurrent readers, transactions, distributed guarantees or claims of production-grade crash safety on every filesystem.

## Spec
Support UTF-8 string keys and values, `put`, `get` and `delete`; absent `get` returns a distinct missing result. Maintain an in-memory map and append newline-delimited JSON records to a write-ahead log. When creating the log, fsync its parent directory before acknowledging writes. A successful write means the complete record has been flushed and fsynced before updating memory and acknowledging. Encode embedded newlines via JSON. A delete of an absent key is an acknowledged no-op record.

On startup load a sorted-key JSON snapshot if present, then replay complete newline-terminated log records in order. Split records as bytes before UTF-8 decoding so a partial multibyte character in a truncated final record is also ignored; remove the tail before any subsequent append. A malformed complete record is an error. For compaction, write a new snapshot file in the same directory, flush and fsync it, atomically replace the old snapshot, fsync the directory where supported, then truncate and fsync the log. Replay is idempotent because put and delete are absolute operations; thus replaying the old log after snapshot replacement is safe. Report filesystem and directory-fsync assumptions and restrict guarantees to the tested platform.

## Milestones
1. **1-2 h:** Define record and snapshot formats, errors and a map-based reference.
2. **1-2 h:** Implement append, fsync, replay and partial-tail handling.
3. **1-2 h:** Implement sorted snapshot replacement and log truncation in the stated order.
4. **1-2 h:** Inject failures before and after each compaction step and restart.
5. **1-2 h:** Differential-test seeded operations, including deletes and encoded strings.
6. **1-2 h:** Benchmark log growth and recovery, then explain durability limits.

## Done when
- Put `a=1`, put `a=2`, delete `a`, put `b` with an embedded newline, restart: `a` is missing and `b` is intact.
- A truncated final log line is ignored, but a malformed newline-terminated line fails visibly. After a recovered truncated tail, truncate it before appending any new records so future writes do not join the partial line.
- At least 100 seeded sequences of 200 operations, with restarts and compactions, agree with an in-memory oracle. Inject failures after snapshot fsync, replacement, directory sync and log truncation; recovery retains every acknowledged operation under the stated filesystem assumptions.
- Benchmark 1,000, 10,000 and 50,000 fixed-seed writes with periodic overwrites, recording log bytes, snapshot bytes, compaction time and restart replay time before and after compaction. Report five-run medians and fsync policy.
- Explain `O(1)` expected in-memory lookup, replay proportional to log records, snapshot sorting `O(k log k)` for `k` live keys and write amplification from rewriting live state. Describe limitations of process-kill tests versus real power loss.

## Stretch goals
- Add checksums and fail closed on corrupted complete records.
- Implement multiple immutable sorted segments and a tombstone-aware merge; state the new recovery protocol before coding.

## Hints
- [Sorted tables](https://github.com/google/leveldb/blob/main/doc/impl.md#sorted-tables) provide production context, not a specification for this JSON snapshot.
- Read [compactions](https://github.com/google/leveldb/blob/main/doc/impl.md#compactions) and trace exactly which durable copy exists at every failure point.
