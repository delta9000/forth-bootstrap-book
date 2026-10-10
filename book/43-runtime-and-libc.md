# Chapter 43 — Runtime, libc, streams, and formatting

A C runtime joins process entry, memory ownership, and output into a callable library. Process entry initializes library state, and normal termination flushes pending streams. The artifact here is a set of Forth-built runtime objects, with the C library contracts that let an ordinary program allocate, copy, and print.

## From process entry to a C call

The shape is `_start` → initialize → `main` → `exit`, with library operations reaching Linux through `__seed_syscall6`. The C library is surveyed, not quoted in full. These excerpts are source readings; the checkpoint exercises only the allocation, memory, and string subset. Its source-range inventory TODO remains open: the bundle assigns no C line spans, so the excerpts below illustrate shared contracts without claiming those files as tangle inputs.

The runtime file stores instruction templates and names in the Forth dictionary. Calling a builder packages a template as an object; merely loading the file writes no target object.

The header separates the raw kernel result from the public C error convention (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:1`):

```forth file=cc/122-cc-sysv-runtime.fth
\ 122-cc-sysv-runtime.fth -- raw Linux syscall bridge for a source-built runtime.
\ Load after 010, 020, 030, and 081. Loading this file emits no target code.
\ cc-sysrt-object creates one ET_REL object; cc-obj-write saves it.
\
\ C signature: long __seed_syscall6(long number, long a1, long a2, long a3,
\                                long a4, long a5, long a6);
\ Return the raw kernel result. Values -4095..-1 are errors; no errno is set.
\ The caller, not this leaf, converts that result to its public libc contract.

```

## The raw syscall and errno boundary

The small adapters use a common shape: a `-name` word holds the exported spelling, a `-code` word holds instruction bytes, and an `-object` word packages them. Their results differ:

| Input | Result and exported name |
|---|---|
| Syscall number and arguments | Raw kernel result through `__seed_syscall6` |
| No arguments | Address of shared error storage through `__errno_location` |
| Calling C frame | Saved parent frame through `__seed_parent_frame` |
| Kernel signal frame | Resume interrupted context through `__seed_sigreturn` |

The raw bridge performs only the register shuffle. It copies each source before overwriting that register and obtains the final syscall argument from the C stack.

`cc-sysrt-name` and `cc-sysrt-code` give the bridge its symbol and leaf body (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:10`):

```forth file=cc/122-cc-sysv-runtime.fth
create cc-sysrt-name  s, __seed_syscall6
create cc-sysrt-code
[lit] 72 c, [lit] 137 c, [lit] 248 c,  \ mov rax,rdi       syscall number
[lit] 72 c, [lit] 137 c, [lit] 247 c,  \ mov rdi,rsi       argument 1
[lit] 72 c, [lit] 137 c, [lit] 214 c,  \ mov rsi,rdx       argument 2
[lit] 72 c, [lit] 137 c, [lit] 202 c,  \ mov rdx,rcx       argument 3
[lit] 77 c, [lit] 137 c, [lit] 194 c,  \ mov r10,r8        argument 4
[lit] 77 c, [lit] 137 c, [lit] 200 c,  \ mov r8,r9         argument 5
[lit] 76 c, [lit] 139 c, [lit] 76 c, [lit] 36 c, [lit] 8 c,
                                      \ mov r9,[rsp+8]    argument 6
[lit] 15 c, [lit] 5 c,                \ syscall           clobbers rcx,r11
[lit] 195 c,                          \ ret               result in rax

```

`cc-sysrt-object` emits the bridge without introducing any library state (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:23`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-object
  cc-obj-init
  cc-obj-text cc-obj-use
  cc-sysrt-code [lit] 26 cc-obj-bytes
  cc-sysrt-name [lit] 15 [lit] 1 [lit] 2 [lit] 0
  cc-obj-text [lit] 0 [lit] 26 cc-obj-symbol drop ;

```

An error remains a negative kernel result; this leaf never changes errno. A public wrapper chooses its failure return and stores the positive error number. Keeping storage in a separate object lets a raw caller use the bridge without importing an errno provider.

`cc-sysrt-errno-name` names the accessor, while `cc-sysrt-errno-storage` names its private storage symbol (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:30`):

```forth file=cc/122-cc-sysv-runtime.fth
\ A separate object owns errno for this explicitly single-threaded runtime.
\ Keep it separate so the raw bridge has no libc state or provider collision.
create cc-sysrt-errno-name  s, __errno_location
create cc-sysrt-errno-storage  s, __seed_errno
create cc-sysrt-errno-code
[lit] 72 c, [lit] 141 c, [lit] 5 c,   \ lea rax,[rip+errno]
[lit] 0 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
[lit] 195 c,                         \ ret

```

`cc-sysrt-errno-object` gives `cc-sysrt-errno-code` a relocated address of zero-initialized storage (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:39`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-errno-object
  cc-obj-init
  cc-obj-bss cc-obj-use [lit] 4 cc-obj-align [lit] 4 cc-obj-reserve drop
  cc-sysrt-errno-storage [lit] 12 cc-obj-local cc-obj-object cc-obj-default
  cc-obj-bss [lit] 0 [lit] 4 cc-obj-symbol >r
  cc-obj-text cc-obj-use cc-sysrt-errno-code [lit] 8 cc-obj-bytes
  cc-obj-text [lit] 3 cc-obj-pc32 r> [lit] 0 [lit] 4 - cc-obj-reloc
  cc-sysrt-errno-name [lit] 16 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 8 cc-obj-symbol drop ;

```

The C `errno` macro dereferences this accessor's result. The storage is shared by this single-threaded runtime; it is not thread-local. `forth-bootstrap/chain/runtime/gcc-seed/ERRNO.md` records the error-number and message contract.

## Entering main

`cc-sysrt-main-name` names the minimal entry's unresolved C callee; `cc-sysrt-start-name` names the exported entry. `cc-sysrt-start-code` captures the incoming arguments before aligning the call stack (Chapter 41).

The minimal entry passes `argc` and `argv` to `main`, then sends its result directly to Linux exit (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:49`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Process entry: preserve argc and argv before aligning the outgoing call.
\ Relocate the call to C main, then pass its return value to Linux exit.
create cc-sysrt-main-name  s, main
create cc-sysrt-start-name  s, _start
create cc-sysrt-start-code
[lit] 72 c, [lit] 139 c, [lit] 60 c, [lit] 36 c, \ mov rdi,[rsp]
[lit] 72 c, [lit] 141 c, [lit] 116 c, [lit] 36 c, [lit] 8 c,
                                                 \ lea rsi,[rsp+8]
[lit] 72 c, [lit] 131 c, [lit] 228 c, [lit] 240 c, \ and rsp,-16
[lit] 49 c, [lit] 192 c,                         \ xor eax,eax
[lit] 232 c, [lit] 0 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ call main (RELA at16)
[lit] 72 c, [lit] 137 c, [lit] 199 c,             \ mov rdi,rax
[lit] 184 c, [lit] 60 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ mov eax,60
[lit] 15 c, [lit] 5 c,                           \ syscall
[lit] 15 c, [lit] 11 c,                          \ ud2 if exit returned

```

`cc-sysrt-start-object` attaches the unresolved `main` reference to that call and exports `_start` (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:67`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-start-object
  cc-obj-init
  cc-sysrt-main-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol >r
  cc-obj-text cc-obj-use cc-sysrt-start-code [lit] 32 cc-obj-bytes
  cc-obj-text [lit] 16 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
  cc-sysrt-start-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 32 cc-obj-symbol drop ;

```

## Frameless adapters

The frame adapter reads the parent pointer without adding a frame of its own (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:76`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Private Forth-C frame contract, not a portable host backtrace interface.
\ The calling C function keeps RBP fixed; [RBP] is its parent's saved frame.
\ This leaf adds no frame and preserves every callee-saved register.
create cc-sysrt-frame-name s, __seed_parent_frame
create cc-sysrt-frame-code
[lit] 72 c, [lit] 139 c, [lit] 69 c, [lit] 0 c, \ mov rax,[rbp+0]
[lit] 195 c,                                    \ ret
: cc-sysrt-frame-object
  cc-obj-init
  cc-obj-text cc-obj-use cc-sysrt-frame-code [lit] 5 cc-obj-bytes
  cc-sysrt-frame-name [lit] 19 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 5 cc-obj-symbol drop ;

```

`cc-sysrt-frame-name`, `cc-sysrt-frame-code`, and `cc-sysrt-frame-object` implement a private fixed-RBP contract. A caller compiled with frame-pointer omission cannot use it as a portable backtrace function.

The signal-return adapter must leave the kernel-owned frame at the current stack pointer (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:89`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Linux AMD64 signal-handler return. The kernel owns the signal frame;
\ do not add a C/Forth frame or change RSP before rt_sigreturn.
create cc-sysrt-sigreturn-name s, __seed_sigreturn
create cc-sysrt-sigreturn-code
[lit] 184 c, [lit] 15 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ mov eax,15
[lit] 15 c, [lit] 5 c,                           \ syscall rt_sigreturn
[lit] 15 c, [lit] 11 c,                          \ ud2 if syscall returned
: cc-sysrt-sigreturn-object
  cc-obj-init
  cc-obj-text cc-obj-use cc-sysrt-sigreturn-code [lit] 9 cc-obj-bytes
  cc-sysrt-sigreturn-name [lit] 16 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 9 cc-obj-symbol drop ;

```

`cc-sysrt-sigreturn-name`, `cc-sysrt-sigreturn-code`, and `cc-sysrt-sigreturn-object` export that frameless restorer. A normal C prologue would move the stack away from the signal frame. The final trap handles an unexpected return from the syscall.

## Initialization and termination

The minimal entry suits a program with no initialization or cleanup. Buffered output changes the contract: returning from `main` must reach the library's `exit`, not terminate at the syscall boundary.

`cc-sysrt-init-name` names `__seed_init_runtime`. The runtime-aware entry saves the arguments across that call, restores them for `main`, and derives `envp` from the argument vector's terminating null pointer.

`cc-sysrt-runtime-start-code` routes normal termination through the C function named by `cc-sysrt-exit-name` (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:103`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Runtime-aware process entry. Keep argc/argv across initialization, pass
\ envp=argv+argc+1 as main's third argument (SysV), and keep the minimal
\ raw _start builder independent of the C runtime.
create cc-sysrt-init-name s, __seed_init_runtime
create cc-sysrt-runtime-start-code
[lit] 72 c, [lit] 139 c, [lit] 60 c, [lit] 36 c, \ mov rdi,[rsp]
[lit] 72 c, [lit] 141 c, [lit] 116 c, [lit] 36 c, [lit] 8 c,
                                                 \ lea rsi,[rsp+8]
[lit] 72 c, [lit] 131 c, [lit] 228 c, [lit] 240 c, \ and rsp,-16
[lit] 87 c, [lit] 86 c,                          \ push rdi; push rsi
[lit] 232 c, [lit] 0 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ call initializer (RELA16)
[lit] 94 c, [lit] 95 c,                          \ pop rsi; pop rdi
[lit] 72 c, [lit] 141 c, [lit] 84 c, [lit] 254 c, [lit] 8 c,
                                                 \ lea rdx,[rsi+rdi*8+8]
[lit] 49 c, [lit] 192 c,                         \ xor eax,eax
[lit] 232 c, [lit] 0 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ call main (RELA30)
[lit] 72 c, [lit] 137 c, [lit] 199 c,             \ mov rdi,rax
[lit] 232 c, [lit] 0 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ call exit (RELA38)
[lit] 15 c, [lit] 11 c,                          \ ud2 if exit returned
create cc-sysrt-exit-name s, exit
```

`cc-sysrt-runtime-start-object` supplies a separate relocation for each external call, using the object machinery (Chapter 40) (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:126`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-runtime-start-object
  cc-obj-init
  cc-obj-text cc-obj-use cc-sysrt-runtime-start-code [lit] 44 cc-obj-bytes
  cc-sysrt-init-name [lit] 19 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol >r
  cc-obj-text [lit] 16 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
  cc-sysrt-main-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol >r
  cc-obj-text [lit] 30 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
  cc-sysrt-exit-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol >r
  cc-obj-text [lit] 38 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
  cc-sysrt-start-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 44 cc-obj-symbol drop ;

```

Initialization publishes the same environment vector that the entry passes to `main` (`forth-bootstrap/chain/runtime/gcc-seed/startup.c:19`):

```c
/* Only the runtime entry passes a complete kernel argv/environment vector. */
extern char **environ;
void __seed_init_runtime(int count, char **arguments)
{
    __seed_init_program_name(count, arguments);
    environ = count >= 0 && arguments != NULL ? arguments + count + 1 : NULL;
}
```

The initializer also derives `__progname` from the basename of `argv[0]`, without allocating. `forth-bootstrap/chain/runtime/gcc-seed/STARTUP.md` describes this entry contract; the Forth template above is authoritative for its current body.

Normal exit removes each registered handler before calling it, then invokes the stream flush hook (`forth-bootstrap/chain/runtime/gcc-seed/process.c:52`):

```c
void exit(int status)
{
    struct seed_exit_handler *handler;
    /* Each record is removed before it runs, so a handler that calls exit
       continues with the remaining ones instead of repeating itself. A
       handler registered while exiting runs next. */
    while (seed_exit_count > 0) {
        handler = &seed_exit_handlers[--seed_exit_count];
        if (handler->kind) handler->with_status(status, handler->argument);
        else handler->plain();
    }
    if (__seed_exit_flush) __seed_exit_flush();
    _Exit(status);
}
```

Removing a handler first prevents it from repeating if it calls `exit` itself. `_Exit` bypasses handlers and flushing. `forth-bootstrap/chain/runtime/gcc-seed/PROCESS-POSIX.md` distinguishes these termination paths.

## Saving a continuation

A nonlocal continuation restores a live caller rather than returning through intervening functions. The buffer belongs to this runtime; it cannot be exchanged with a host libc's `jmp_buf`. `forth-bootstrap/chain/runtime/gcc-seed/NONLOCAL.md` gives the permitted C expression contexts and lifetime rules.

`cc-sysrt-setjmp-name` names the save operation; `cc-sysrt-setjmp-code` records preserved registers, the post-return stack pointer, and the return address (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:141`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Ordinary C90 nonlocal return. Layout: RBX,RBP,R12,R13,R14,R15,RSP,RIP.
\ The saved RSP is the caller's value after this leaf would return.
\ No signal mask, floating-point environment, or shadow stack is saved.
create cc-sysrt-setjmp-name s, setjmp
create cc-sysrt-setjmp-code
[lit] 72 c, [lit] 137 c, [lit] 31 c,             \ mov [rdi],rbx
[lit] 72 c, [lit] 137 c, [lit] 111 c, [lit] 8 c, \ mov [rdi+8],rbp
[lit] 76 c, [lit] 137 c, [lit] 103 c, [lit] 16 c, \ mov [rdi+16],r12
[lit] 76 c, [lit] 137 c, [lit] 111 c, [lit] 24 c, \ mov [rdi+24],r13
[lit] 76 c, [lit] 137 c, [lit] 119 c, [lit] 32 c, \ mov [rdi+32],r14
[lit] 76 c, [lit] 137 c, [lit] 127 c, [lit] 40 c, \ mov [rdi+40],r15
[lit] 72 c, [lit] 141 c, [lit] 68 c, [lit] 36 c, [lit] 8 c,
                                                \ lea rax,[rsp+8]
[lit] 72 c, [lit] 137 c, [lit] 71 c, [lit] 48 c, \ mov [rdi+48],rax
[lit] 72 c, [lit] 139 c, [lit] 4 c, [lit] 36 c,  \ mov rax,[rsp]
[lit] 72 c, [lit] 137 c, [lit] 71 c, [lit] 56 c, \ mov [rdi+56],rax
[lit] 49 c, [lit] 192 c,                         \ xor eax,eax
[lit] 195 c,                                    \ ret
```

`cc-sysrt-setjmp-object` exports the nonlocal continuation leaf independently of the restore operation (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:159`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-setjmp-object
  cc-obj-init
  cc-obj-text cc-obj-use cc-sysrt-setjmp-code [lit] 43 cc-obj-bytes
  cc-sysrt-setjmp-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 43 cc-obj-symbol drop ;

```

The initial return is zero. Restoring must instead return a nonzero C `int`, including when the caller requests zero. The restore code reads ESI before extending the value, so unspecified upper register bits cannot change it.

`cc-sysrt-longjmp-name` and `cc-sysrt-longjmp-code` normalize the result before restoring the stack and jumping to the saved address (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:165`):

```forth file=cc/122-cc-sysv-runtime.fth
\ Only ESI is the C int argument. Do not depend on its undefined upper bits.
\ Sign-extension is harmless for host int callers and matches Forth C values.
create cc-sysrt-longjmp-name s, longjmp
create cc-sysrt-longjmp-code
[lit] 137 c, [lit] 240 c,                         \ mov eax,esi
[lit] 133 c, [lit] 192 c,                         \ test eax,eax
[lit] 117 c, [lit] 5 c,                           \ jnz normalized
[lit] 184 c, [lit] 1 c, [lit] 0 c, [lit] 0 c, [lit] 0 c,
                                                 \ mov eax,1
[lit] 72 c, [lit] 152 c,                          \ cdqe
[lit] 72 c, [lit] 139 c, [lit] 31 c,              \ mov rbx,[rdi]
[lit] 72 c, [lit] 139 c, [lit] 111 c, [lit] 8 c,  \ mov rbp,[rdi+8]
[lit] 76 c, [lit] 139 c, [lit] 103 c, [lit] 16 c, \ mov r12,[rdi+16]
[lit] 76 c, [lit] 139 c, [lit] 111 c, [lit] 24 c, \ mov r13,[rdi+24]
[lit] 76 c, [lit] 139 c, [lit] 119 c, [lit] 32 c, \ mov r14,[rdi+32]
[lit] 76 c, [lit] 139 c, [lit] 127 c, [lit] 40 c, \ mov r15,[rdi+40]
[lit] 72 c, [lit] 139 c, [lit] 103 c, [lit] 48 c, \ mov rsp,[rdi+48]
[lit] 255 c, [lit] 103 c, [lit] 56 c,            \ jmp [rdi+56]
```

`cc-sysrt-longjmp-object` publishes the restore leaf under its C name (`forth-bootstrap/cc/122-cc-sysv-runtime.fth:183`):

```forth file=cc/122-cc-sysv-runtime.fth
: cc-sysrt-longjmp-object
  cc-obj-init
  cc-obj-text cc-obj-use cc-sysrt-longjmp-code [lit] 43 cc-obj-bytes
  cc-sysrt-longjmp-name [lit] 7 cc-obj-global cc-obj-func cc-obj-default
  cc-obj-text [lit] 0 [lit] 43 cc-obj-symbol drop ;
```

The function that called `setjmp` must still be active. A changed non-volatile automatic local in that function has an indeterminate value after `longjmp`; this mechanism does not restore ordinary local storage. It also saves no signal mask or floating-point environment. The Flex consumer belongs to Chapter 51; its runtime dependency is documented in `forth-bootstrap/chain/runtime/gcc-seed/NONLOCAL.md:3`.

## Allocation owns both payload and metadata

Small allocations share slabs and return freed slots to size-class lists. Large allocations own separate anonymous mappings. Slabs remain mapped until process termination, trading reclamation for reuse. These choices, including `malloc(0)` and errno preservation by `free`, are specified in `forth-bootstrap/chain/runtime/gcc-seed/README.md`.

The header distinguishes storage extent from the amount of payload the caller requested (`forth-bootstrap/chain/runtime/gcc-seed/alloc.c:8`):

```c
/* mmap gives page alignment; this LP64 header leaves 16-byte alignment. */
struct seed_allocation {
    size_t extent;
    size_t requested;
};
```

`free` uses the extent to choose a free list or unmap the large allocation. `realloc` uses the requested size to avoid copying beyond the old payload. Before adding the header, `malloc` rejects requests beyond its pointer-difference bound.

A failed mapping becomes a null pointer plus errno; a successful mapping becomes a payload pointer beyond the header (`forth-bootstrap/chain/runtime/gcc-seed/alloc.c:79`):

```c
    extent = payload + sizeof(struct seed_allocation);
    /* mmap(NULL, extent, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS,
       -1, 0). The kernel rounds the length to whole pages. */
    result = __seed_syscall6(9, 0, (long)extent, 3, 34, -1, 0);
    if (result < 0 && result >= -4095) {
        errno = (int)-result;
        return NULL;
    }
    header = (struct seed_allocation *)result;
    header->extent = extent;
    header->requested = size;
    return (void *)(header + 1);
}
```

## Failure preserves ownership

`calloc` checks multiplication before performing it, then clears only the requested payload (`forth-bootstrap/chain/runtime/gcc-seed/alloc.c:110`):

```c
void *calloc(size_t count, size_t size)
{
    size_t total;
    void *pointer;
    if (count != 0 && size > (size_t)-1 / count) {
        errno = ENOMEM;
        return NULL;
    }
    total = count * size;
    pointer = malloc(total);
    if (pointer != NULL)
        memset(pointer, 0, total);
    return pointer;
}
```

Growing an allocation must preserve the old object if replacement fails. The success path copies before freeing; reversing that order would lose the caller's data.

The tail of `realloc` keeps a shrinking object in place and commits a growing replacement only after allocation succeeds (`forth-bootstrap/chain/runtime/gcc-seed/alloc.c:136`):

```c
    header = (struct seed_allocation *)pointer - 1;
    old_size = header->requested;
    if (size <= old_size) {
        header->requested = size;
        return pointer;
    }
    replacement = malloc(size);
    if (replacement == NULL)
        return NULL;
    memcpy(replacement, pointer, old_size);
    free(pointer);
    return replacement;
}
```

## Bytes and strings

The memory functions use byte loops with explicit bounds. `memcpy` requires non-overlap; `memmove` selects its direction using the target's integer ordering of addresses. Comparisons use unsigned bytes, so high-bit bytes retain their ordering despite signed plain `char`.

The overlap-safe copy walks backward when a forward store could overwrite a later source byte (`forth-bootstrap/chain/runtime/gcc-seed/memory.c:14`):

```c
void *memmove(void *destination, const void *source, size_t count)
{
    unsigned char *out = destination;
    const unsigned char *in = source;
    size_t i;
    /* Integer address ordering is an explicit Linux AMD64 assumption. */
    if ((unsigned long)out <= (unsigned long)in) {
        for (i = 0; i < count; i = i + 1)
            out[i] = in[i];
    } else {
        i = count;
        while (i != 0) {
            i = i - 1;
            out[i] = in[i];
        }
    }
    return destination;
}
```

String functions add a terminator contract to the byte contract. Counted copying is not automatically termination: `strncpy` pads a short source, but need not append a null when the count is exhausted. `strdup` composes the ordinary allocation and copy operations.

Duplication allocates space for the terminator and propagates allocation failure (`forth-bootstrap/chain/runtime/gcc-seed/string.c:125`):

```c
char *strdup(const char *string)
{
    size_t length = strlen(string);
    char *copy = malloc(length + 1);
    if (copy != NULL)
        memcpy(copy, string, length + 1);
    return copy;
}
```

## Streams own state and pending bytes

`FILE` is a complete type in the current header, but its members remain private to this library. A descriptor alone cannot represent buffered bytes, ownership, error state, and end-of-file state.

Separate read and write cursors record which bytes belong to the stream rather than to the kernel offset (`forth-bootstrap/chain/runtime/gcc-seed/include/stdio.h:15`):

```c
struct __seed_FILE {
    unsigned char *__rpos;
    unsigned char *__rend;
    unsigned char *__wpos;
    unsigned char *__wend;
    unsigned char *__wbase;
    unsigned char *__buf;
    size_t __size;
    int __fd;
    int __flags;
    int __mode;
    int __error;
    int __eof;
    struct __seed_FILE *__next;
    unsigned char __small[16];
};
typedef struct __seed_FILE FILE;
```

The current implementation supports full, line, and no buffering. Standard error starts unbuffered; other streams choose their default at first I/O by testing whether the descriptor is a terminal. Buffer allocation failure falls back to unbuffered operation. `forth-bootstrap/chain/runtime/gcc-seed/STDIO-BUFFERING.md` explains the policy; its older remark that exit handlers are absent is superseded by `process.c` above.

## File lifetime and transfer counts

Opening a file must release the allocated stream object when the kernel rejects the path (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:332`):

```c
FILE *fopen(const char *path, const char *mode)
{
    int flags;
    int access;
    long descriptor;
    FILE *stream;
    if (!seed_open_mode(mode, &flags, &access)) return NULL;
    stream = malloc(sizeof(FILE));
    if (stream == NULL) return NULL;
    descriptor = seed_call(2, (long)path, flags, 0666);
    if (descriptor < 0) {
        errno = (int)-descriptor;
        free(stream);
        return NULL;
    }
    seed_stream_init(stream, (int)descriptor, access);
    seed_list_add(stream);
    return stream;
}
```

Read and write errors set a sticky stream error indicator. End-of-file has its own indicator; `clearerr` clears both. Interrupted reads and writes retry, while positive short transfers advance the buffer position before trying the remainder.

The direct write loop preserves partial progress and treats a zero-progress write as an error (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:143`):

```c
static size_t seed_write_out(FILE *stream, const unsigned char *data, size_t length)
{
    size_t done = 0;
    size_t part;
    long result;
    while (done < length) {
        part = length - done;
        if (part > 2147479552UL) part = 2147479552UL;
        result = __seed_syscall6(1, stream->__fd, (long)(data + done), (long)part, 0, 0, 0);
        if (result == -EINTR) continue;
        if (result <= 0) {
            errno = result < 0 ? (int)-result : EIO;
            stream->__error = 1;
            break;
        }
        done += (size_t)result;
    }
    return done;
}
```

`fread` and `fwrite` report complete objects, even if part of another object was transferred. They reject an overflowing size-times-count before I/O. Buffered acceptance is distinct from delivery: `fflush`, `fclose`, and normal exit must write pending output.

Closing releases ownership even when the close syscall reports an error, and never retries that syscall (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:449`):

```c
    owned = stream->__flags & SEED_OWNED;
    /* Linux releases the descriptor even when close reports EINTR. Retrying
       could close an unrelated descriptor that reused the same number. */
    result = __seed_syscall6(3, stream->__fd, 0, 0, 0, 0, 0);
    seed_release_buffer(stream);
    stream->__fd = -1;
    stream->__flags = 0;
    if (owned) {
        seed_list_remove(stream);
        free(stream);
    }
    if (failed) { errno = saved; return EOF; }
    if (result < 0) { errno = (int)-result; return EOF; }
    return 0;
}
```

A retry could close an unrelated descriptor that reused the released number. Position reporting also accounts for ownership: `ftell` adds pending output and subtracts unread input from the kernel offset, while append output must first be written to learn its position. Pushback belongs to that unread input. These details let file consumers reason about the stream position without knowing its buffer layout.

## Formatting counts what would fit

A formatter needs both a destination and a logical output count. The count answers how much space a caller needed even when its bounded buffer was too small. The same formatting engine can target a stream or memory.

The output record separates capacity, count, and failure state (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:746`):

```c
struct seed_print {
    FILE *stream;
    char *buffer;
    size_t capacity;
    int count;
    int failed;
};
```

Every emitted span checks count overflow and copies only the portion that fits before the reserved terminator (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:761`):

```c
static int seed_print_bytes(struct seed_print *output, const char *text, size_t size)
{
    size_t room;
    size_t copy;
    if (size > (size_t)(INT_MAX - output->count))
        return seed_print_error(output, SEED_EOVERFLOW);
    if (output->stream != NULL) {
        if (seed_put(output->stream, (const unsigned char *)text, size) != size) {
            output->failed = 1;
            return 0;
        }
    } else if (output->capacity > 0 && (size_t)output->count < output->capacity - 1) {
        room = output->capacity - 1 - (size_t)output->count;
        copy = size < room ? size : room;
        memcpy(output->buffer + output->count, text, copy);
    }
    output->count = output->count + (int)size;
    return 1;
}
```

Truncation does not stop the count. `%n` observes that logical count too; padding uses the same rule without iterating over bytes that cannot fit. Stream output instead reports failure when the stream cannot accept a whole span.

`vsnprintf` terminates within the supplied capacity after the shared formatter finishes (`forth-bootstrap/chain/runtime/gcc-seed/stdio.c:1115`):

```c
int vsnprintf(char *buffer, size_t size, const char *format, va_list arguments)
{
    struct seed_print output;
    size_t end;
    int result;
    output.stream = NULL;
    output.buffer = buffer;
    output.capacity = size;
    output.count = 0;
    output.failed = 0;
    result = seed_format(&output, format, arguments);
    if (size > 0) {
        end = (size_t)output.count;
        if (end >= size) end = size - 1;
        buffer[end] = 0;
    }
    return result;
}
```

A zero-capacity call can measure the required length without writing a terminator. Integer, pointer, character, and string conversions share this destination contract. Width and precision bound padding and string access; unsupported conversions fail rather than consume an argument under a guessed type.

Chapter 46 teaches the argument cursor used by this formatter. Floating representations and extended values belong to Chapters 47 and 49; the current library also formats them, as described in `forth-bootstrap/chain/runtime/gcc-seed/PRINTF-FLOAT.md`. Those additions do not change the capacity-versus-count rule.

## Where the library is built

Part 4 builds the tools that consume this runtime. The Forth bootstrap driver compiles the runtime C units, emits the runtime adapters, makes an archive, and links `seed-cc` and `seed-ar` (`forth-bootstrap/cc/driver/seed-cc-start.fth:335`). Chapter 50 owns that construction.

The C driver's runtime builder compiles the C sources and separately invokes these Forth object builders (`forth-bootstrap/cc/driver/seed-cc.c:791`). Its normal link order is the runtime-aware entry, the program objects, then the runtime archive (`forth-bootstrap/cc/driver/seed-cc.c:1252`). This makes the entry and the library's initialization and termination functions parts of the same contract.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. This is a restricted version of the runtime unit recipe in `forth-bootstrap/cc/driver/seed-cc-boot/runtime-unit.fth:5`: it keeps the workspace setup and include path but loads only compiler layers taught so far. It builds the canonical memory, string, and allocation sources, emits the raw entry and error boundary, and links them directly with the demo.

The full formatting checkpoint is deferred. The current `stdio.c` uses the argument machinery of Chapter 46 and floating types covered in Chapters 47 and 49. Even the runtime-aware entry's `startup.c` failed this restricted build with `cc: line 103: error 240`; the raw entry needs no such initializer. This checkpoint therefore verifies heap-backed string output through the raw bridge, not `printf`, buffering, or normal library exit. Chapter 50 builds the complete runtime through the driver.

All generated files live in a `mktemp -d` directory. The demo checks initial errno and process arguments, allocates `sizeof` the string literal (33 bytes, including its terminator), copies the string, writes its measured length, and frees it. No host C compiler or linker supplies an object.

<!-- tryit: expect "runtime: heap and strings ready" -->
```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
runtime=chain/runtime/gcc-seed
includes=$runtime/include
cat > "$work/demo.c" <<'C' || exit "$?"
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <seed-syscall.h>
int main(int argc, char **argv) {
    char *text;
    long length;
    long written;
    if (argc < 1 || argv[0] == NULL || errno != 0) return 1;
    text = malloc(sizeof "runtime: heap and strings ready\n");
    if (text == NULL) return 2;
    strcpy(text, "runtime: heap and strings ready\n");
    length = strlen(text);
    written = __seed_syscall6(1, 1, (long)text, length, 0, 0, 0);
    free(text);
    return written == length ? 0 : 3;
}
C
for unit in memory string alloc demo; do
  source="$runtime/$unit.c"
  if [ "$unit" = demo ]; then source="$work/demo.c"; fi
  {
    cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
        cc/121-cc-sysv.fth cc/123-cc-object-program.fth || exit "$?"
    printf 'create output-path s, %s/%s.o [lit] 0 c,\n' "$work" "$unit"
    printf 'create include-path s, %s/include [lit] 0 c,\n' "$runtime"
    printf 'include-path [lit] %s cc-prep-add-include\n' "${#includes}"
    cat <<'FORTH' || exit "$?"
cc-sysv-object-enable
[lit] 22020096 cc-arena-map
cc-io-direct-workspace cc-prep-direct-workspace
cc-om-direct-workspace cc-label-direct-workspace
cc-obj-direct-workspace cc-gfixup-direct-workspace
: object-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-sysv-object-program output-path cc-obj-write bye ;
object-main
FORTH
    cat "$source" || exit "$?"
  } | ./seed-forth || exit "$?"
done
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/081-cc-object.fth cc/122-cc-sysv-runtime.fth || exit "$?"
  for pair in syscall:cc-sysrt-object errno:cc-sysrt-errno-object \
              start:cc-sysrt-start-object; do
    name=${pair%%:*}
    builder=${pair#*:}
    printf 'create p-%s s, %s/%s.o [lit] 0 c,\n' "$name" "$work" "$name"
    printf '%s p-%s cc-obj-write\n' "$builder" "$name"
  done
  printf '%s\n' bye
} | ./seed-forth || exit "$?"
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/140-cc-link.fth || exit "$?"
  printf '%s\n' 'lnk-init'
  for unit in start demo syscall errno memory string alloc; do
    printf 'create p-%s s, %s/%s.o [lit] 0 c, p-%s lnk-add-object\n' \
        "$unit" "$work" "$unit" "$unit"
  done
  printf 'create output-path s, %s/demo [lit] 0 c,\n' "$work"
  printf '%s\n' 'create entry-name s, _start' \
    'entry-name [lit] 6 lnk-entry output-path lnk-link lnk-release bye'
} | ./seed-forth || exit "$?"
"$work/demo" || exit "$?"
)
```

Observed output:

```text
runtime: heap and strings ready
```

The executable returned success. No GCC is involved: `gcc-seed` is only the runtime directory's name.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-43-realloc-and-ownership).

**Trace — easy.** Follow a failed growing `realloc` from the replacement allocation back to its caller. Which pointer still owns the old bytes, and which statement would become unsafe if moved before the failure check?
