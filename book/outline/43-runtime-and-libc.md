# Runtime, libc, streams, and formatting

Part: 3

Scope: Teach process entry and the raw syscall boundary before the bounded C library. Connect allocation, memory, strings, streams, and formatting to the programs they support.

Sources taught: `cc/122-cc-sysv-runtime.fth` 1-187 (canonical, complete). The following C ranges are exact source excerpts, not tangle inputs. Paths are relative to `chain/runtime/gcc-seed/` at the pinned source revision:

| Source | Lines | Contract taught |
|---|---|---|
| `startup.c` | 19-25 | Publish the environment vector |
| `process.c` | 52-65 | Remove exit handlers before invoking them, then flush |
| `alloc.c` | 8-12, 79-91 | Allocation metadata and mapping result |
| `alloc.c` | 110-123, 136-148 | Checked zero allocation and failure-preserving resize |
| `memory.c` | 14-31 | Direction of an overlapping copy |
| `string.c` | 125-132 | Duplicate bytes including their terminator |
| `include/stdio.h` | 15-31 | Stream state and buffer ownership |
| `stdio.c` | 143-161, 332-350, 449-463 | Partial writes, open failure, and close ownership |
| `stdio.c` | 746-752, 761-779, 1115-1132 | Capacity, logical count, and termination |

Prerequisites: [42 — Linker and archives](42-linker-and-archives.md)

Checkpoint: Compile the canonical memory, string, and allocation units with the layers taught through Chapter 42. Emit the minimal entry, raw syscall bridge, and errno provider; link the objects with a demo that allocates, copies, writes, and frees a string. Compare the line `runtime: heap and strings ready` and require status zero. Full runtime startup, stdio, and formatting require later compiler layers and remain outside this checkpoint.

Reuses: [Runtime chapter](../43-runtime-and-libc.md) — Process entry, syscall wrappers, errno storage, allocation, memory, strings, streams, and bounded formatting.
