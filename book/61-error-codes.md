# Appendix G — Compiler error codes

A compiler diagnostic identifies a failed check by number and by the reader's position in the input. Use the catalogue to find the raising word, its source location, and the chapter that explains that layer. The same number can belong to different checks, so keep the loaded layer and any diagnostic prefix beside it.

## How the codes are organised

The core compiler groups codes by source layer; later layers reuse numbers and add checks. The catalogue follows source files rather than treating a numeric range as a unique namespace. An absent number has no entry because these sources do not assign it a failure.

`cc-die` supplies the common diagnostic (Chapter 27). `cc-check-cap` and `cc-read-all` pass their caller's code to it. Preprocessor sinks and object bounds also carry a code to a shared check. The tables distinguish the word containing the numbered site from the helper that ultimately raises it.

| Numbered site uses | Failure route | Diagnostic form |
|---|---|---|
| `cc-die`, `cc-check-cap`, `cc-read-all` | Common compiler reporter | `cc: line N: error CODE` |
| `cc-workspace-map`, `cc-obj-bound` | Caller-selected code through `cc-die` | Same compiler form |
| Preprocessor sink code | `cc-prep-emit-byte` through `cc-check-cap` | Same compiler form |
| `cc-va-die` | `varargs: `, then `cc-die` | Prefix plus compiler form |
| `cc-bf-die` | `bitfield: `, then `cc-die` | Prefix plus compiler form |
| `cc-ag-die`, `cc-ld-die` | `aggregate-abi: ` or `long-double: `, then `cc-die` | Prefix plus compiler form |
| `cc-f64-fail` | Literal reason, then `die` | `cc-f64-literal: REASON`; no compiler line |
| Assembler helpers | `die` or `asm-tok-err` | Bare status, or offending token on stderr |

The common reporter writes to stderr and exits with the supplied code (`forth-bootstrap/cc/020-cc-arena.fth:405`). The assembler and literal converter have separate reporting paths. Linker and archive errors share the common reporter, but its reader position is not an ELF byte offset.

For compiler input, the reported position is `cc-src-line` in the preprocessed text. The source reader increments it at newlines (`forth-bootstrap/cc/030-cc-io.fth:108`); preprocessing counts emitted newlines, then rewinds that reader (`forth-bootstrap/cc/040-cc-prep.fth:61,2339`). Includes change the flattened position. It need not equal a line in the original file. Logical file/line tracking is separate; the implicit-function diagnostic can print that location before the flattened line (`forth-bootstrap/cc/121-cc-sysv.fth:937`).

## Codes in detail

Each row gives the numbered call sites and the containing words. Read the meaning with the selected target: a default hook can reject a form that a later loaded hook implements. Files with no numbered failure site, including the core lexer, ELF-header emitter, main entry and target predefines, have no table.

### 020-cc-arena.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 10 | `forth-bootstrap/cc/020-cc-arena.fth:437,456` | `cc-arena-map`, `cc-alloc` → `cc-die`, `cc-check-cap` | Arena exhausted or arena mapping failed. | [Chapter 27](27-arena-and-io-buffers.md) |

### 030-cc-io.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 20 | `forth-bootstrap/cc/030-cc-io.fth:88` | `cc-load-stdin` → `cc-read-all` | Input buffer full or I/O workspace mapping failed. | [Chapter 27](27-arena-and-io-buffers.md) |
| 21 | `forth-bootstrap/cc/030-cc-io.fth:132` | `cc-emit-byte` → `cc-check-cap` | Output buffer full. | [Chapter 27](27-arena-and-io-buffers.md) |
| 22 | `forth-bootstrap/cc/030-cc-io.fth:192` | `cc-write-output` → `cc-die` | Output path could not be opened. | [Chapter 27](27-arena-and-io-buffers.md) |

### 040-cc-prep.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 30 | `forth-bootstrap/cc/040-cc-prep.fth:906,1825,1830,1835,1882` | `cc-prep-load-file`, `cc-prep-include-literal`, `cc-prep-handle-include` → `cc-die` | Include file missing or include operand malformed. | [Chapter 28](28-the-preprocessor.md) |
| 31 | `forth-bootstrap/cc/040-cc-prep.fth:894` | `cc-prep-load-file` → `cc-check-cap` | Include nesting limit exceeded. | [Chapter 28](28-the-preprocessor.md) |
| 32 | `forth-bootstrap/cc/040-cc-prep.fth:912,916` | `cc-prep-load-file` → `cc-read-all` | Include storage full or mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| 33 | `forth-bootstrap/cc/040-cc-prep.fth:717,812,822` | `cc-prep-append`, `cc-prep-copy-path`, `cc-prep-add-include` → `cc-check-cap` | Path buffer or include-directory table full. | [Chapter 28](28-the-preprocessor.md) |
| 34 | `forth-bootstrap/cc/040-cc-prep.fth:294` | `cc-macro-record` → `cc-check-cap` | Macro table full or workspace mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| 38 | `forth-bootstrap/cc/040-cc-prep.fth:1704` | `cc-pp-cond-push` → `cc-check-cap` | Conditional nesting limit exceeded. | [Chapter 28](28-the-preprocessor.md) |
| 39 | `forth-bootstrap/cc/040-cc-prep.fth:2336` | `cc-preprocess` → `cc-die` | Conditional group left open at end of input. | [Chapter 28](28-the-preprocessor.md) |
| 40 | `forth-bootstrap/cc/040-cc-prep.fth:2238` | `cc-prep-handle-directive` → `cc-die` | Active `#error` directive. | [Chapter 28](28-the-preprocessor.md) |
| 41 | `forth-bootstrap/cc/040-cc-prep.fth:1719` | `cc-pp-need-group` → `cc-die` | Conditional directive has no open group. | [Chapter 28](28-the-preprocessor.md) |
| 42 | `forth-bootstrap/cc/040-cc-prep.fth:620` | `cc-pp-need-name` → `cc-die` | Required preprocessing identifier missing. | [Chapter 28](28-the-preprocessor.md) |
| 43 | `forth-bootstrap/cc/040-cc-prep.fth:153,173` | `cc-pp-flags-init`, `cc-pp-scratch-alloc` → `cc-die`, `cc-check-cap` | Scratch/shadow storage exhausted, incompatible capacity, or mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| 44 | `forth-bootstrap/cc/040-cc-prep.fth:1017` | `cc-pp-collect-args` → `cc-die` | Macro call reaches end of region before closing. | [Chapter 28](28-the-preprocessor.md) |
| 45 | `forth-bootstrap/cc/040-cc-prep.fth:1373` | `cc-pp-expand-call-body` → `cc-die` | Macro call has excess arguments. | [Chapter 28](28-the-preprocessor.md) |
| 46 | `forth-bootstrap/cc/040-cc-prep.fth:1002` | `cc-pp-ca-record` → `cc-check-cap` | Macro argument table full. | [Chapter 28](28-the-preprocessor.md) |
| 47 | `forth-bootstrap/cc/040-cc-prep.fth:165,627,2067,2070,2078,2090,2161` | `cc-pp-paste-bytes`, `cc-pp-need-rparen`, `cc-pp-read-direct-params`, `cc-pp-copy-hash`, `cc-prep-handle-define` → `cc-die` | Invalid macro parameters, stringizing/pasting operand, or missing `)`. | [Chapter 28](28-the-preprocessor.md) |
| 48 | `forth-bootstrap/cc/040-cc-prep.fth:2012,2068` | `cc-pp-read-params`, `cc-pp-read-direct-params` → `cc-check-cap` | Macro parameter table full. | [Chapter 28](28-the-preprocessor.md) |
| 49 | `forth-bootstrap/cc/040-cc-prep.fth:484,557,1585,1617,1905,1909,1912,1924,1927,1930,1948,1951,1954,1959,1960,1977,2214,2219` | `cc-pp-block-comment`, `cc-pp-line-splice-boundary`, `cc-pp-scan-char`, `cc-prep-directive-blanks`, `cc-pp-line-decimal`, `cc-pp-line-escape`, `cc-pp-line-filename`, `cc-prep-handle-line`, `cc-prep-handle-directive` → `cc-die`, `cc-check-cap` | Invalid line-control/directive syntax, comment, escape, or splice boundary. | [Chapter 28](28-the-preprocessor.md) |

### 060-cc-types.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 50 | `forth-bootstrap/cc/060-cc-types.fth:313` | `cc-sd-field-rec` → `cc-check-cap` | Record member table full. | [Chapter 30](30-types-and-symbols.md) |
| 213 | `forth-bootstrap/cc/060-cc-types.fth:336` | `cc-sf-set-array-inner-default` → `cc-die` | Nested array member unsupported by the default field hook. | [Chapter 30](30-types-and-symbols.md) |
| 240 | `forth-bootstrap/cc/060-cc-types.fth:169` | `cc-integer-literal-check` → `cc-die` | Malformed integer literal suffix. | [Chapter 45](45-typed-constants.md) |

### 070-cc-sym.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 60 | `forth-bootstrap/cc/070-cc-sym.fth:102` | `cc-sym-add` → `cc-check-cap` | Symbol table full. | [Chapter 30](30-types-and-symbols.md) |
| 61 | `forth-bootstrap/cc/070-cc-sym.fth:190` | `cc-scope-push` → `cc-check-cap` | Scope stack full. | [Chapter 30](30-types-and-symbols.md) |
| 62 | `forth-bootstrap/cc/070-cc-sym.fth:199` | `cc-scope-pop` → `cc-die` | Scope stack underflow. | [Chapter 30](30-types-and-symbols.md) |

### 081-cc-object.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 244 | `forth-bootstrap/cc/081-cc-object.fth:160,163,164,166,194,213` | `cc-obj-check-section`, `cc-obj-check-align`, `cc-obj-require-init`, `cc-obj-byte`, `cc-obj-patch` → `cc-die` | Invalid object section, alignment, initialization state, or patch range. | [Chapter 40](40-objects-and-relocations.md) |
| 246 | `forth-bootstrap/cc/081-cc-object.fth:239,251,256,272,276,280,395` | `cc-obj-check-definition`, `cc-obj-check-id`, `cc-obj-define`, `cc-obj-symbol`, `cc-obj-check-symbols` → `cc-die` | Invalid object symbol metadata. | [Chapter 40](40-objects-and-relocations.md) |
| 247 | `forth-bootstrap/cc/081-cc-object.fth:308,313` | `cc-obj-reloc-width`, `cc-obj-reloc` → `cc-die` | Invalid object relocation type, symbol, or range. | [Chapter 40](40-objects-and-relocations.md) |
| 248 | `forth-bootstrap/cc/081-cc-object.fth:456,458,461,465,487,493` | `cc-obj-check-output`, `cc-obj-make-temp-path`, `cc-obj-abandon-output`, `cc-obj-write` → `cc-die` | Object output path/publication or file I/O failure. | [Chapter 40](40-objects-and-relocations.md) |

### 090-cc-emit.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 80 | `forth-bootstrap/cc/090-cc-emit.fth:1186` | `cc-globals-alloc` → `cc-check-cap` | Global initialized-data area full. | [Chapter 32](32-codegen-part-2.md) |
| 81 | `forth-bootstrap/cc/090-cc-emit.fth:1215` | `cc-gfixup-add` → `cc-check-cap` | Global fixup table full or mapping failed. | [Chapter 32](32-codegen-part-2.md) |
| 82 | `forth-bootstrap/cc/090-cc-emit.fth:1194` | `cc-bss-alloc` → `cc-check-cap` | Global BSS area full. | [Chapter 32](32-codegen-part-2.md) |

### 100-cc-expr.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 90 | `forth-bootstrap/cc/100-cc-expr.fth:345` | `cc-find-field` → `cc-die` | Record member name not found. | [Chapter 34](34-expressions-part-2.md) |
| 91 | `forth-bootstrap/cc/100-cc-expr.fth:384` | `cc-parse-array-index` → `cc-die` | Named array base is neither local nor global. | [Chapter 34](34-expressions-part-2.md) |
| 92 | `forth-bootstrap/cc/100-cc-expr.fth:434` | `cc-parse-array-index` → `cc-die` | Named subscript lacks `]`. | [Chapter 34](34-expressions-part-2.md) |
| 93 | `forth-bootstrap/cc/100-cc-expr.fth:892` | `cc-parse-ident` → `cc-die` | Identifier not found. | [Chapter 34](34-expressions-part-2.md) |
| 94 | `forth-bootstrap/cc/100-cc-expr.fth:909` | `cc-parse-ident` → `cc-die` | Named call target is not callable. | [Chapter 34](34-expressions-part-2.md) |
| 95 | `forth-bootstrap/cc/100-cc-expr.fth:935` | `cc-parse-ident` → `cc-die` | Identifier cannot be used as a value. | [Chapter 34](34-expressions-part-2.md) |
| 96 | `forth-bootstrap/cc/100-cc-expr.fth:944` | `cc-parse-paren` → `cc-die` | Parenthesized expression lacks `)`. | [Chapter 34](34-expressions-part-2.md) |
| 97 | `forth-bootstrap/cc/100-cc-expr.fth:975` | `cc-parse-operand` → `cc-die` | Token cannot start an operand. | [Chapter 34](34-expressions-part-2.md) |
| 98 | `forth-bootstrap/cc/100-cc-expr.fth:1050` | `cc-parse-postfix-inc-dec` → `cc-die` | Postfix update requires an lvalue. | [Chapter 34](34-expressions-part-2.md) |
| 99 | `forth-bootstrap/cc/100-cc-expr.fth:1095,1118` | `cc-parse-postfix-index` → `cc-die` | Postfix subscript lacks `]`. | [Chapter 34](34-expressions-part-2.md) |
| 100 | `forth-bootstrap/cc/100-cc-expr.fth:1136` | `cc-parse-postfix-field` → `cc-die` | Member access lacks a record descriptor. | [Chapter 34](34-expressions-part-2.md) |
| 101 | `forth-bootstrap/cc/100-cc-expr.fth:1148` | `cc-parse-postfix-field` → `cc-die` | Member access lacks a field identifier. | [Chapter 34](34-expressions-part-2.md) |
| 102 | `forth-bootstrap/cc/100-cc-expr.fth:1320` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` lacks `(`. | [Chapter 34](34-expressions-part-2.md) |
| 103 | `forth-bootstrap/cc/100-cc-expr.fth:1328` | `cc-parse-sizeof` → `cc-die` | Core `sizeof(struct ...)` lacks a tag identifier. | [Chapter 34](34-expressions-part-2.md) |
| 104 | `forth-bootstrap/cc/100-cc-expr.fth:1332` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` tag not found. | [Chapter 34](34-expressions-part-2.md) |
| 105 | `forth-bootstrap/cc/100-cc-expr.fth:1335` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` name is not a record tag. | [Chapter 34](34-expressions-part-2.md) |
| 106 | `forth-bootstrap/cc/100-cc-expr.fth:1349` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` keyword unsupported. | [Chapter 34](34-expressions-part-2.md) |
| 107 | `forth-bootstrap/cc/100-cc-expr.fth:1359` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` identifier not found. | [Chapter 34](34-expressions-part-2.md) |
| 108 | `forth-bootstrap/cc/100-cc-expr.fth:1388` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` identifier is neither typedef nor local. | [Chapter 34](34-expressions-part-2.md) |
| 109 | `forth-bootstrap/cc/100-cc-expr.fth:1392` | `cc-parse-sizeof` → `cc-die` | Core `sizeof` operand token invalid. | [Chapter 34](34-expressions-part-2.md) |
| 110 | `forth-bootstrap/cc/100-cc-expr.fth:1294,1297,1397` | `cc-native-sizeof`, `cc-parse-sizeof` → `cc-die` | `sizeof` lacks a closing bracket or parenthesis. | [Chapter 34](34-expressions-part-2.md) |
| 113 | `forth-bootstrap/cc/100-cc-expr.fth:1012,1448` | `cc-native-inc-dec`, `cc-parse-prefix-inc-dec` → `cc-die` | Prefix update requires an lvalue. | [Chapter 34](34-expressions-part-2.md) |
| 114 | `forth-bootstrap/cc/100-cc-expr.fth:1501` | `cc-parse-unary` → `cc-die` | Core address operand is not an identifier. | [Chapter 34](34-expressions-part-2.md) |
| 115 | `forth-bootstrap/cc/100-cc-expr.fth:1506` | `cc-parse-unary` → `cc-die` | Core address identifier not found. | [Chapter 34](34-expressions-part-2.md) |
| 116 | `forth-bootstrap/cc/100-cc-expr.fth:1477,1485,1510` | `cc-parse-unary` → `cc-die` | Address operand is not an addressable object in this target. | [Chapter 34](34-expressions-part-2.md) |
| 117 | `forth-bootstrap/cc/100-cc-expr.fth:2163` | `cc-parse-ternary` → `cc-die` | Conditional expression lacks `:`. | [Chapter 34](34-expressions-part-2.md) |
| 118 | `forth-bootstrap/cc/100-cc-expr.fth:2236` | `cc-apply-compound-op` → `cc-die` | Compound operator dispatcher received an unknown operator. | [Chapter 34](34-expressions-part-2.md) |
| 120 | `forth-bootstrap/cc/100-cc-expr.fth:2257,2265,2286,2411` | `cc-parse-native-assign`, `cc-parse-assign` → `cc-die` | Invalid assignment destination or aggregate compound assignment. | [Chapter 34](34-expressions-part-2.md) |
| 121 | `forth-bootstrap/cc/100-cc-expr.fth:533,619` | `cc-native-parse-args`, `cc-parse-call` → `cc-die` | Call argument list lacks `)`. | [Chapter 37](37-functions-and-scope.md) |
| 122 | `forth-bootstrap/cc/100-cc-expr.fth:627` | `cc-parse-call` → `cc-die` | Core call exceeds its register argument limit. | [Chapter 37](37-functions-and-scope.md) |
| 123 | `forth-bootstrap/cc/100-cc-expr.fth:667` | `cc-parse-call` → `cc-die` | Core call target kind invalid. | [Chapter 37](37-functions-and-scope.md) |
| 124 | `forth-bootstrap/cc/100-cc-expr.fth:1595` | `cc-divisor` → `cc-die` | Constant division or remainder by zero. | [Chapter 33](33-expressions-part-1.md) |
| 125 | `forth-bootstrap/cc/100-cc-expr.fth:2530` | `cc-cx-operand` → `cc-die` | Core constant name is not an enumerator. | [Chapter 33](33-expressions-part-1.md) |
| 126 | `forth-bootstrap/cc/100-cc-expr.fth:2539` | `cc-cx-operand` → `cc-die` | Core constant operand token invalid. | [Chapter 33](33-expressions-part-1.md) |
| 127 | `forth-bootstrap/cc/100-cc-expr.fth:2536` | `cc-cx-operand` → `cc-die` | Core constant expression lacks `)`. | [Chapter 33](33-expressions-part-1.md) |
| 128 | `forth-bootstrap/cc/100-cc-expr.fth:2615` | `cc-parse-const-default` → `cc-die` | Core constant conditional lacks `:`. | [Chapter 33](33-expressions-part-1.md) |
| 129 | `forth-bootstrap/cc/100-cc-expr.fth:2646` | `cc-pp-eval-text` → `cc-die` | Preprocessing constant expression has trailing tokens. | [Chapter 33](33-expressions-part-1.md) |
| 212 | `forth-bootstrap/cc/100-cc-expr.fth:528` | `cc-native-parse-args` → `cc-die` | Record value crosses the private call ABI. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 219 | `forth-bootstrap/cc/100-cc-expr.fth:54` | `cc-check-static-init` → `cc-die` | Static initializer requires a nonconstant operation or aggregate copy. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 240 | `forth-bootstrap/cc/100-cc-expr.fth:2503` | `cc-const-unsupported` → `cc-die` | Unsupported constant expression form. | [Chapter 45](45-typed-constants.md) |

### 110-cc-decl.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 140 | `forth-bootstrap/cc/110-cc-decl.fth:67` | `cc-expect-kw-id` → `cc-die` | Expected a keyword token. | [Chapter 35](35-declarations-types-globals.md) |
| 141 | `forth-bootstrap/cc/110-cc-decl.fth:70` | `cc-expect-kw-id` → `cc-die` | Expected a different keyword. | [Chapter 35](35-declarations-types-globals.md) |
| 142 | `forth-bootstrap/cc/110-cc-decl.fth:78` | `cc-expect-punct-c` → `cc-die` | Expected a punctuation token. | [Chapter 35](35-declarations-types-globals.md) |
| 143 | `forth-bootstrap/cc/110-cc-decl.fth:81` | `cc-expect-punct-c` → `cc-die` | Expected a different punctuation character. | [Chapter 35](35-declarations-types-globals.md) |
| 144 | `forth-bootstrap/cc/110-cc-decl.fth:88` | `cc-expect-ident` → `cc-die` | Expected an identifier. | [Chapter 35](35-declarations-types-globals.md) |
| 145 | `forth-bootstrap/cc/110-cc-decl.fth:238` | `cc-lookup-struct-tag` → `cc-die` | Strict record lookup lacks a tag identifier. | [Chapter 35](35-declarations-types-globals.md) |
| 146 | `forth-bootstrap/cc/110-cc-decl.fth:243` | `cc-lookup-struct-tag` → `cc-die` | Strict record lookup cannot find tag. | [Chapter 35](35-declarations-types-globals.md) |
| 147 | `forth-bootstrap/cc/110-cc-decl.fth:247` | `cc-lookup-struct-tag` → `cc-die` | Strict record lookup found a non-tag name. | [Chapter 35](35-declarations-types-globals.md) |
| 148 | `forth-bootstrap/cc/110-cc-decl.fth:258` | `cc-lookup-struct-tag-soft` → `cc-die` | Soft record lookup lacks a tag identifier. | [Chapter 35](35-declarations-types-globals.md) |
| 149 | `forth-bootstrap/cc/110-cc-decl.fth:275` | `cc-parse-struct-def` → `cc-die` | Record definition lacks a tag identifier. | [Chapter 35](35-declarations-types-globals.md) |
| 150 | `forth-bootstrap/cc/110-cc-decl.fth:325` | `cc-parse-struct-def` → `cc-die` | Core record field keyword unsupported. | [Chapter 35](35-declarations-types-globals.md) |
| 151 | `forth-bootstrap/cc/110-cc-decl.fth:331` | `cc-parse-struct-def` → `cc-die` | Core record field type token invalid. | [Chapter 35](35-declarations-types-globals.md) |
| 152 | `forth-bootstrap/cc/110-cc-decl.fth:343` | `cc-parse-struct-def` → `cc-die` | Record field name missing. | [Chapter 35](35-declarations-types-globals.md) |
| 153 | `forth-bootstrap/cc/110-cc-decl.fth:420` | `cc-parse-fnptr-decl` → `cc-die` | Function-pointer declarator name missing. | [Chapter 35](35-declarations-types-globals.md) |
| 154 | `forth-bootstrap/cc/110-cc-decl.fth:444` | `cc-parse-fnptr-decl` → `cc-die` | Function-pointer declaration lacks `=` or `;`. | [Chapter 35](35-declarations-types-globals.md) |
| 156 | `forth-bootstrap/cc/110-cc-decl.fth:471` | `cc-parse-local-declarator` → `cc-die` | Core local array bound is not positive. | [Chapter 35](35-declarations-types-globals.md) |
| 157 | `forth-bootstrap/cc/110-cc-decl.fth:473` | `cc-parse-local-declarator` → `cc-die` | Core local array declaration lacks `]`. | [Chapter 35](35-declarations-types-globals.md) |
| 159 | `forth-bootstrap/cc/110-cc-decl.fth:528` | `cc-parse-decl-with-base` → `cc-die` | Local declarator lacks `,` or `;`. | [Chapter 35](35-declarations-types-globals.md) |
| 160 | `forth-bootstrap/cc/110-cc-decl.fth:700` | `cc-parse-struct-local-decl` → `cc-die` | Core record local name missing. | [Chapter 35](35-declarations-types-globals.md) |
| 161 | `forth-bootstrap/cc/110-cc-decl.fth:735` | `cc-parse-struct-local-decl` → `cc-die` | Core record-pointer local lacks `=` or `;`. | [Chapter 35](35-declarations-types-globals.md) |
| 162 | `forth-bootstrap/cc/110-cc-decl.fth:45` | `cc-fn-add-slots` → `cc-check-cap` | Function frame slot limit exceeded. | [Chapter 35](35-declarations-types-globals.md) |
| 184 | `forth-bootstrap/cc/110-cc-decl.fth:394` | `cc-skip-fnptr-params` → `cc-die` | Parameter list unterminated or lacks `)`. | [Chapter 35](35-declarations-types-globals.md) |
| 214 | `forth-bootstrap/cc/110-cc-decl.fth:396` | `cc-skip-fnptr-params` → `cc-die` | Floating type unavailable in the selected target. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 238 | `forth-bootstrap/cc/110-cc-decl.fth:648` | `cc-try-cast` → `cc-die` | Invalid object/array/function shape, member/subscript base, or qualifier loss. | [Chapter 39](39-lp64-storage-and-initializers.md) |

### 112-cc-stmt.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 170 | `forth-bootstrap/cc/112-cc-stmt.fth:466,870,874` | `cc-switch-case`, `cc-parse-stmt` → `cc-die` | Case lacks `:` or case/default appears outside a switch. | [Chapter 36](36-statements-if-while-for-return.md) |
| 171 | `forth-bootstrap/cc/112-cc-stmt.fth:698` | `cc-label-create` → `cc-check-cap` | Label table full or mapping failed. | [Chapter 36](36-statements-if-while-for-return.md) |
| 172 | `forth-bootstrap/cc/112-cc-stmt.fth:728` | `cc-define-label` → `cc-die` | Label defined twice. | [Chapter 36](36-statements-if-while-for-return.md) |
| 173 | `forth-bootstrap/cc/112-cc-stmt.fth:773` | `cc-parse-goto-stmt` → `cc-die` | Goto destination is not an identifier. | [Chapter 36](36-statements-if-while-for-return.md) |
| 174 | `forth-bootstrap/cc/112-cc-stmt.fth:760` | `cc-native-finish-gotos` → `cc-die` | Function ends with an undefined goto label. | [Chapter 36](36-statements-if-while-for-return.md) |

### 114-cc-func.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 180 | `forth-bootstrap/cc/114-cc-func.fth:78` | `cc-parse-param-list-loop` → `cc-die` | Parameter type name not found. | [Chapter 37](37-functions-and-scope.md) |
| 181 | `forth-bootstrap/cc/114-cc-func.fth:81` | `cc-parse-param-list-loop` → `cc-die` | Parameter type name is not a typedef. | [Chapter 37](37-functions-and-scope.md) |
| 182 | `forth-bootstrap/cc/114-cc-func.fth:87` | `cc-parse-param-list-loop` → `cc-die` | Parameter type token invalid. | [Chapter 37](37-functions-and-scope.md) |
| 183 | `forth-bootstrap/cc/114-cc-func.fth:98` | `cc-parse-param-list-loop` → `cc-die` | Parameter name missing. | [Chapter 37](37-functions-and-scope.md) |
| 184 | `forth-bootstrap/cc/114-cc-func.fth:118` | `cc-parse-param-list-loop` → `cc-die` | Parameter list unterminated or lacks `)`. | [Chapter 37](37-functions-and-scope.md) |
| 185 | `forth-bootstrap/cc/114-cc-func.fth:188` | `cc-parse-fn-return-type` → `cc-die` | Record return type lacks a tag identifier. | [Chapter 37](37-functions-and-scope.md) |
| 186 | `forth-bootstrap/cc/114-cc-func.fth:195` | `cc-parse-fn-return-type` → `cc-die` | Return type token invalid. | [Chapter 37](37-functions-and-scope.md) |
| 187 | `forth-bootstrap/cc/114-cc-func.fth:225` | `cc-parse-function` → `cc-die` | Function name missing. | [Chapter 37](37-functions-and-scope.md) |

### 115-cc-native.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 58 | `forth-bootstrap/cc/115-cc-native.fth:479` | `cc-naggregate` → `cc-die` | Record member declaration lacks `;`. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 143 | `forth-bootstrap/cc/115-cc-native.fth:327,339,349` | `cc-ngroup-name`, `cc-ngrouped-declarator` → `cc-die` | Expected a different punctuation character. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 190 | `forth-bootstrap/cc/115-cc-native.fth:125` | `cc-nenum` → `cc-die` | Enumerator name missing. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 192 | `forth-bootstrap/cc/115-cc-native.fth:133` | `cc-nenum` → `cc-die` | Enumerator lacks `,` or `}`. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 194 | `forth-bootstrap/cc/115-cc-native.fth:219` | `cc-nbase-raw` → `cc-die` | Type name not found. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 195 | `forth-bootstrap/cc/115-cc-native.fth:220` | `cc-nbase-raw` → `cc-die` | Type name is not a typedef. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 203 | `forth-bootstrap/cc/115-cc-native.fth:319,322,336,629` | `cc-ngroup-name`, `cc-ngrouped-declarator`, `cc-native-declaration` → `cc-die` | Declarator name missing or invalid. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 205 | `forth-bootstrap/cc/115-cc-native.fth:644` | `cc-native-declaration` → `cc-die` | Declaration lacks final `;`. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 210 | `forth-bootstrap/cc/115-cc-native.fth:61` | `cc-nsize` → `cc-die` | Record size requested without a descriptor. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 214 | `forth-bootstrap/cc/115-cc-native.fth:235` | `cc-nbase-raw` → `cc-die` | Floating type unavailable in the selected target. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 238 | `forth-bootstrap/cc/115-cc-native.fth:297,307,318,329,341,348,354,359,365,449` | `cc-nfunction-suffix`, `cc-npointer-array-default`, `cc-ngroup-name`, `cc-ngrouped-declarator`, `cc-nmember-default` → `cc-die` | Invalid object/array/function shape, member/subscript base, or qualifier loss. | [Chapter 39](39-lp64-storage-and-initializers.md) |

### 116-cc-prog.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 190 | `forth-bootstrap/cc/116-cc-prog.fth:54` | `cc-parse-enum-def` → `cc-die` | Enumerator name missing. | [Chapter 37](37-functions-and-scope.md) |
| 192 | `forth-bootstrap/cc/116-cc-prog.fth:92` | `cc-parse-enum-def` → `cc-die` | Enumerator lacks `,` or `}`. | [Chapter 37](37-functions-and-scope.md) |
| 193 | `forth-bootstrap/cc/116-cc-prog.fth:127` | `cc-parse-typedef` → `cc-die` | Core typedef base keyword unsupported. | [Chapter 37](37-functions-and-scope.md) |
| 194 | `forth-bootstrap/cc/116-cc-prog.fth:133` | `cc-parse-typedef` → `cc-die` | Type name not found. | [Chapter 37](37-functions-and-scope.md) |
| 195 | `forth-bootstrap/cc/116-cc-prog.fth:136` | `cc-parse-typedef` → `cc-die` | Type name is not a typedef. | [Chapter 37](37-functions-and-scope.md) |
| 196 | `forth-bootstrap/cc/116-cc-prog.fth:140` | `cc-parse-typedef` → `cc-die` | Core typedef base token invalid. | [Chapter 37](37-functions-and-scope.md) |
| 197 | `forth-bootstrap/cc/116-cc-prog.fth:164` | `cc-parse-typedef` → `cc-die` | Function-pointer typedef name missing. | [Chapter 37](37-functions-and-scope.md) |
| 198 | `forth-bootstrap/cc/116-cc-prog.fth:188` | `cc-parse-typedef` → `cc-die` | Typedef name missing. | [Chapter 37](37-functions-and-scope.md) |
| 199 | `forth-bootstrap/cc/116-cc-prog.fth:308` | `cc-register-fn-proto` → `cc-die` | Prototype function name missing. | [Chapter 37](37-functions-and-scope.md) |
| 202 | `forth-bootstrap/cc/116-cc-prog.fth:464` | `cc-parse-global-decl` → `cc-die` | Top-level base type token invalid. | [Chapter 37](37-functions-and-scope.md) |
| 203 | `forth-bootstrap/cc/116-cc-prog.fth:401` | `cc-gdecl-declarator` → `cc-die` | Declarator name missing or invalid. | [Chapter 37](37-functions-and-scope.md) |
| 205 | `forth-bootstrap/cc/116-cc-prog.fth:474` | `cc-parse-global-decl` → `cc-die` | Top-level declarator lacks required separator. | [Chapter 37](37-functions-and-scope.md) |
| 206 | `forth-bootstrap/cc/116-cc-prog.fth:864` | `cc-check-fns-defined` → `cc-die` | Referenced function remains undefined. | [Chapter 37](37-functions-and-scope.md) |
| 207 | `forth-bootstrap/cc/116-cc-prog.fth:869` | `cc-check-fns-defined` → `cc-die` | Whole program has no `main`. | [Chapter 37](37-functions-and-scope.md) |

### 117-cc-native-program.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 184 | `forth-bootstrap/cc/117-cc-native-program.fth:27` | `cc-native-params` → `cc-die` | Parameter list unterminated or lacks `)`. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 211 | `forth-bootstrap/cc/117-cc-native-program.fth:46` | `cc-native-function` → `cc-die` | Function defined twice. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 212 | `forth-bootstrap/cc/117-cc-native-program.fth:20,33` | `cc-native-params`, `cc-native-function` → `cc-die` | Record value crosses the private call ABI. | [Chapter 39](39-lp64-storage-and-initializers.md) |

### 118-cc-native-init.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 219 | `forth-bootstrap/cc/118-cc-native-init.fth:155` | `cc-ni-scalar` → `cc-die` | Static initializer requires a nonconstant operation or aggregate copy. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 220 | `forth-bootstrap/cc/118-cc-native-init.fth:79,80,91,99` | `cc-ni-infer` → `cc-die` | Inferred array initializer invalid or empty. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 221 | `forth-bootstrap/cc/118-cc-native-init.fth:96,103,123` | `cc-ni-infer` → `cc-die` | Inferred initializer malformed or unterminated. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 222 | `forth-bootstrap/cc/118-cc-native-init.fth:109,114` | `cc-ni-infer` → `cc-die` | Inferred nested initializer lacks required braces. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 223 | `forth-bootstrap/cc/118-cc-native-init.fth:88,143,236` | `cc-ni-infer`, `cc-ni-string`, `cc-ni-char-array` → `cc-die` | Character-array initializer too large or malformed. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 224 | `forth-bootstrap/cc/118-cc-native-init.fth:162` | `cc-ni-scalar` → `cc-die` | Aggregate initializer type/descriptor mismatch. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 225 | `forth-bootstrap/cc/118-cc-native-init.fth:218,241,260` | `cc-ni-list`, `cc-ni-char-array`, `cc-ni-value` → `cc-die` | Required initializer brace missing. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 226 | `forth-bootstrap/cc/118-cc-native-init.fth:223` | `cc-ni-list` → `cc-die` | Initializer has excess elements or lacks closing brace. | [Chapter 39](39-lp64-storage-and-initializers.md) |
| 227 | `forth-bootstrap/cc/118-cc-native-init.fth:273` | `cc-ni-value` → `cc-die` | Braced scalar initializer lacks `}`. | [Chapter 39](39-lp64-storage-and-initializers.md) |

### 121-cc-sysv.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 60 | `forth-bootstrap/cc/121-cc-sysv.fth:914` | `cc-sysv-implicit-record` → `cc-check-cap` | Symbol table full. | [Chapter 41](41-system-v-calls.md) |
| 121 | `forth-bootstrap/cc/121-cc-sysv.fth:1021` | `cc-sysv-parse-args` → `cc-die` | Call argument list lacks `)`. | [Chapter 41](41-system-v-calls.md) |
| 184 | `forth-bootstrap/cc/121-cc-sysv.fth:586` | `cc-sysv-signature` → `cc-die` | Parameter list unterminated or lacks `)`. | [Chapter 41](41-system-v-calls.md) |
| 206 | `forth-bootstrap/cc/121-cc-sysv.fth:971` | `cc-sysv-check-implicit-defined` → `cc-die` | Referenced function remains undefined. | [Chapter 41](41-system-v-calls.md) |
| 211 | `forth-bootstrap/cc/121-cc-sysv.fth:1309` | `cc-sysv-function` → `cc-die` | Function defined twice. | [Chapter 41](41-system-v-calls.md) |
| 228 | `forth-bootstrap/cc/121-cc-sysv.fth:946` | `cc-sysv-implicit-die` → `cc-die` | Undeclared function rejected by the implicit-declaration error option. | [Chapter 41](41-system-v-calls.md) |
| 230 | `forth-bootstrap/cc/121-cc-sysv.fth:70,71,671,677,978,1147` | `cc-sysv-check-signature`, `cc-sysv-cast-types`, `cc-sysv-symbol-signature`, `cc-sysv-check-callable` → `cc-die` | Invalid function signature, callable operand, or cast shape. | [Chapter 41](41-system-v-calls.md) |
| 231 | `forth-bootstrap/cc/121-cc-sysv.fth:73,351,390,605,621` | `cc-sysv-check-scalar-default`, `cc-sysv-check-declarator`, `cc-sysv-fnptr`, `cc-sysv-type-name-raw` → `cc-die` | Pointer depth/type encoding exceeds its representation. | [Chapter 41](41-system-v-calls.md) |
| 232 | `forth-bootstrap/cc/121-cc-sysv.fth:77` | `cc-sysv-check-scalar-default` → `cc-die` | Unsupported scalar value type or conversion. | [Chapter 41](41-system-v-calls.md) |
| 233 | `forth-bootstrap/cc/121-cc-sysv.fth:333,411,414,417,427,445,455,464,469,471,519,549,554,560,570,574,1195,1197,1198,1205,1212,1252,1256` | `cc-sysv-function-typedef`, `cc-sysv-identifier-list`, `cc-sysv-storage-note`, `cc-sysv-declaration-specifiers`, `cc-sysv-parameter-specifiers`, `cc-sysv-spec-check`, `cc-sysv-signature`, `cc-sysv-old-parameters`, `cc-sysv-params`, `cc-sysv-block-function` → `cc-die` | Invalid declaration specifiers, storage class, or parameter form. | [Chapter 41](41-system-v-calls.md) |
| 234 | `forth-bootstrap/cc/121-cc-sysv.fth:415,577,1006` | `cc-sysv-identifier-list`, `cc-sysv-signature`, `cc-sysv-parse-args` → `cc-die` | Parameter/argument table full. | [Chapter 41](41-system-v-calls.md) |
| 235 | `forth-bootstrap/cc/121-cc-sysv.fth:1015,1024` | `cc-sysv-parse-args` → `cc-die` | Call argument count disagrees with signature. | [Chapter 41](41-system-v-calls.md) |
| 236 | `forth-bootstrap/cc/121-cc-sysv.fth:1224` | `cc-sysv-varargs-prepare-default` → `cc-die` | Variadic definition lacks the variadic implementation hook. | [Chapter 41](41-system-v-calls.md) |
| 237 | `forth-bootstrap/cc/121-cc-sysv.fth:724,757,769,775,785,791,796,799,806,811,818,831,835,959,960,966,1263,1290,1292` | `cc-sysv-compatible-types`, `cc-sysv-row-qualifier-check`, `cc-sysv-value-shape`, `cc-sysv-array-pair-check`, `cc-sysv-array-binop`, `cc-sysv-array-compound`, `cc-sysv-array-ternary`, `cc-sysv-check-implicit-signature`, `cc-sysv-implicit-declarator`, `cc-sysv-block-function`, `cc-sysv-function` → `cc-die` | Incompatible declaration, signature, operand, or qualifier set. | [Chapter 41](41-system-v-calls.md) |
| 238 | `forth-bootstrap/cc/121-cc-sysv.fth:86,117,118,120,142,143,151,152,182,184,202,205,225,235,240,242,245,295,330,337,350,353,356,392,608,611,617,759,1253,1277` | `cc-sysv-size-product`, `cc-sysv-array-node`, `cc-sysv-array-tail`, `cc-sysv-array-extra`, `cc-sysv-grouped-array`, `cc-sysv-inherit-array`, `cc-sysv-sizeof-type`, `cc-sysv-index-base`, `cc-sysv-member-base`, `cc-sysv-local-layout`, `cc-sysv-function-typedef`, `cc-sysv-check-declarator`, `cc-sysv-fnptr`, `cc-sysv-type-name-raw`, `cc-sysv-row-qualifier-check`, `cc-sysv-block-function`, `cc-sysv-function` → `cc-die` | Invalid object/array/function shape, member/subscript base, or qualifier loss. | [Chapter 41](41-system-v-calls.md) |
| 239 | `forth-bootstrap/cc/121-cc-sysv.fth:1036,1084,1332` | `cc-sysv-track-pop`, `cc-sysv-prepare-call`, `cc-sysv-function` → `cc-die` | Generated stack accounting invalid or unbalanced. | [Chapter 41](41-system-v-calls.md) |
| 245 | `forth-bootstrap/cc/121-cc-sysv.fth:85,87` | `cc-sysv-size-product` → `cc-die` | Object storage/count limit exceeded or mapping failed. | [Chapter 41](41-system-v-calls.md) |
| 249 | `forth-bootstrap/cc/121-cc-sysv.fth:270` | `cc-ld-die` → `cc-die` | Invalid extended-floating scalar use or conversion. | [Chapter 49](49-aggregate-abi.md) |

### 123-cc-object-program.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 219 | `forth-bootstrap/cc/123-cc-object-program.fth:234` | `cc-om-scalar-initializer` → `cc-die` | Static initializer requires a nonconstant operation or aggregate copy. | [Chapter 41](41-system-v-calls.md) |
| 223 | `forth-bootstrap/cc/123-cc-object-program.fth:255` | `cc-om-string-initializer` → `cc-die` | Character-array initializer too large or malformed. | [Chapter 41](41-system-v-calls.md) |
| 232 | `forth-bootstrap/cc/123-cc-object-program.fth:241` | `cc-om-scalar-initializer` → `cc-die` | Unsupported binary64 relocation initializer. | [Chapter 41](41-system-v-calls.md) |
| 237 | `forth-bootstrap/cc/123-cc-object-program.fth:104,158,169,171,172,174,176,191,217` | `cc-sysv-object-implicit`, `cc-sysv-object-function`, `cc-om-compatible-object`, `cc-om-install-object`, `cc-sysv-object-declaration` → `cc-die` | Incompatible declaration, signature, operand, or qualifier set. | [Chapter 41](41-system-v-calls.md) |
| 238 | `forth-bootstrap/cc/123-cc-object-program.fth:92,205,240,467` | `cc-om-from-symbol`, `cc-sysv-object-declaration`, `cc-om-scalar-initializer`, `cc-sysv-object-program` → `cc-die` | Invalid object identity, storage shape, relocation leaf, or pending initializer. | [Chapter 41](41-system-v-calls.md) |
| 245 | `forth-bootstrap/cc/123-cc-object-program.fth:30,31,65` | `cc-om-record`, `cc-om-new` → `cc-die`, `cc-check-cap` | Object storage/count limit exceeded or mapping failed. | [Chapter 41](41-system-v-calls.md) |

### 125-cc-consteval.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 240 | `forth-bootstrap/cc/125-cc-consteval.fth:17` | `cc-const-new` → `cc-check-cap` | Typed constant workspace full. | [Chapter 45](45-typed-constants.md) |
| 241 | `forth-bootstrap/cc/125-cc-consteval.fth:382` | `cc-const-shift` → `cc-die` | Constant shift count invalid. | [Chapter 45](45-typed-constants.md) |
| 242 | `forth-bootstrap/cc/125-cc-consteval.fth:106,278,341,348,355,364,373` | `cc-const-range`, `cc-const-unary`, `cc-const-check-result`, `cc-const-add`, `cc-const-subtract`, `cc-const-multiply`, `cc-const-divide` → `cc-die` | Signed constant arithmetic overflow or integer conversion out of range. | [Chapter 45](45-typed-constants.md) |

### 126-cc-varargs.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 246 | `forth-bootstrap/cc/126-cc-varargs.fth:39,40,41,44,45,46,47,48,54,58,60,61,84,85,88,89,90,92,93,95` | `cc-va-field`, `cc-va-descriptor`, `cc-va-expect`, `cc-va-operand`, `cc-va-last-named` → `cc-va-die` | Invalid variadic intrinsic, list layout, or last named parameter. | [Chapter 46](46-varargs.md) |
| 247 | `forth-bootstrap/cc/126-cc-varargs.fth:172,177,179,185` | `cc-va-check-result-type`, `cc-va-record-default`, `cc-va-arg` → `cc-va-die` | Requested variadic argument type unsupported. | [Chapter 46](46-varargs.md) |

### 127-cc-binary64.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 232 | `forth-bootstrap/cc/127-cc-binary64.fth:174,182,217,229,282,289` | `cc-fp-convert`, `cc-fp-common-type`, `cc-fp-comparison-flags`, `cc-fp-complement`, `cc-fp-integer-use` → `cc-die` | Invalid floating conversion, scalar operation, or mapped static use. | [Chapter 47](47-floats.md) |

### 128-cc-float-literal.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 124 | `forth-bootstrap/cc/128-cc-float-literal.fth:481` | `cc-f64-ratio` → `cc-die` | Constant floating division by zero. | [Chapter 47](47-floats.md) |
| 248 | `forth-bootstrap/cc/128-cc-float-literal.fth:29` | `cc-f64-fail` → `die` | Malformed/unsupported literal, conversion limit, overflow, or workspace exhaustion. | [Chapter 47](47-floats.md) |

### 129-cc-bitfield.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 227 | `forth-bootstrap/cc/129-cc-bitfield.fth:189` | `cc-bf-initializer` → `cc-die` | Braced scalar initializer lacks `}`. | [Chapter 48](48-bitfields.md) |
| 238 | `forth-bootstrap/cc/129-cc-bitfield.fth:91` | `cc-bf-member` → `cc-die` | Nested array member has no positive outer bound. | [Chapter 48](48-bitfields.md) |
| 245 | `forth-bootstrap/cc/129-cc-bitfield.fth:86` | `cc-bf-layout-check` → `cc-die` | Record object size limit exceeded. | [Chapter 48](48-bitfields.md) |
| 248 | `forth-bootstrap/cc/129-cc-bitfield.fth:9` | `cc-bf-die` → `cc-die` | Unsupported bitfield type, width, or named zero-width field. | [Chapter 48](48-bitfields.md) |

### 131-cc-aggregate-abi.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 121 | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:217` | `cc-ag-parse-arguments` → `cc-die` | Call argument list lacks `)`. | [Chapter 49](49-aggregate-abi.md) |
| 232 | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:8` | `cc-ag-die` → `cc-die` | Unsupported record ABI class, scalar use, or record type/size mismatch. | [Chapter 49](49-aggregate-abi.md) |
| 233 | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:331` | `cc-ag-parameters` → `cc-die` | Definition parameter name missing. | [Chapter 49](49-aggregate-abi.md) |
| 234 | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:185` | `cc-ag-parse-arguments` → `cc-die` | Parameter/argument table full. | [Chapter 49](49-aggregate-abi.md) |
| 235 | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:182,191,219` | `cc-ag-parse-arguments` → `cc-die` | Call argument count disagrees with signature. | [Chapter 49](49-aggregate-abi.md) |

### 140-cc-link.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 250 | `forth-bootstrap/cc/140-cc-link.fth:49,122` | `lnk-bad`, `lnk-read-object` → `cc-die` | Malformed or unsupported ELF/archive metadata. | [Chapter 42](42-linker-and-archives.md) |
| 251 | `forth-bootstrap/cc/140-cc-link.fth:45,51,62,143,245,297,356,365` | `lnk-note-input`, `lnk-cap`, `lnk-map`, `lnk-unmap`, `lnk-sections`, `lnk-register`, `lnk-add-object`, `lnk-add-buffer` → `cc-check-cap`, `cc-die` | Linker/archive capacity, mapping, or unmapping failure. | [Chapter 42](42-linker-and-archives.md) |
| 252 | `forth-bootstrap/cc/140-cc-link.fth:312` | `lnk-register` → `cc-die` | Duplicate strong symbol definition. | [Chapter 42](42-linker-and-archives.md) |
| 253 | `forth-bootstrap/cc/140-cc-link.fth:421,424,442,444,446,449` | `lnk-resolve`, `lnk-find-entry` → `cc-die` | Unresolved symbol or invalid/missing entry. | [Chapter 42](42-linker-and-archives.md) |
| 254 | `forth-bootstrap/cc/140-cc-link.fth:462` | `lnk-reloc-fail` → `cc-die` | Unsupported relocation or relocation result out of range. | [Chapter 42](42-linker-and-archives.md) |
| 255 | `forth-bootstrap/cc/140-cc-link.fth:95,98,101,104,111,119,561,567,573,591,595` | `lnk-fstat`, `lnk-read-file`, `lnk-check-output-alias`, `lnk-make-temp-path`, `lnk-abandon-output`, `lnk-write` → `cc-die` | Linker input/output I/O or publication failure. | [Chapter 42](42-linker-and-archives.md) |

### 141-archive.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 251 | `forth-bootstrap/cc/141-archive.fth:72,80,85,261,297,333` | `arc-basename`, `arc-add-index`, `arc-add-object`, `arc-ordinary`, `arc-check-name`, `arc-parse-index` → `cc-check-cap` | Archive name/member/index capacity exceeded. | [Chapter 42](42-linker-and-archives.md) |

## Codes passed through shared checks

These are numbered sites too. A sink row cites where its code is selected; the overflow test runs in `cc-prep-emit-byte`. Mapping failures use `cc-workspace-map`, and object API limits use `cc-obj-bound`.

| Code | Source site | Containing word → raising helper | Meaning | Layer chapter |
|---|---|---|---|---|
| `20` | `forth-bootstrap/cc/030-cc-io.fth:281` | cc-io-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 27](27-arena-and-io-buffers.md) |
| `32` | `forth-bootstrap/cc/040-cc-prep.fth:689` | cc-prep-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| `34` | `forth-bootstrap/cc/040-cc-prep.fth:686` | cc-prep-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| `43` | `forth-bootstrap/cc/040-cc-prep.fth:155` | cc-pp-flags-init → cc-workspace-map | Workspace request/mapping failed. | [Chapter 28](28-the-preprocessor.md) |
| `245` | `forth-bootstrap/cc/081-cc-object.fth:99` | cc-obj-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 40](40-objects-and-relocations.md) |
| `81` | `forth-bootstrap/cc/090-cc-emit.fth:1157` | cc-gfixup-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 32](32-codegen-part-2.md) |
| `171` | `forth-bootstrap/cc/112-cc-stmt.fth:673` | cc-label-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 36](36-statements-if-while-for-return.md) |
| `245` | `forth-bootstrap/cc/123-cc-object-program.fth:23` | cc-om-direct-workspace → cc-workspace-map | Workspace request/mapping failed. | [Chapter 41](41-system-v-calls.md) |
| `35` | `forth-bootstrap/cc/040-cc-prep.fth:250` | `cc-pp-to-pool` → `cc-prep-emit-byte` | Macro pool full. | [Chapter 28](28-the-preprocessor.md) |
| `36` | `forth-bootstrap/cc/040-cc-prep.fth:2320` | `cc-preprocess` → `cc-prep-emit-byte` | Preprocessed source full. | [Chapter 28](28-the-preprocessor.md) |
| `37` | `forth-bootstrap/cc/040-cc-prep.fth:179` | `cc-pp-temp-begin` → `cc-prep-emit-byte` | Temporary macro expansion full. | [Chapter 28](28-the-preprocessor.md) |
| `244` | `forth-bootstrap/cc/081-cc-object.fth:159,162,214,215` | `cc-obj-check-section`, `cc-obj-check-align`, `cc-obj-patch` → `cc-obj-bound` | Invalid object section, alignment, initialization state, or patch range. | [Chapter 40](40-objects-and-relocations.md) |
| `245` | `forth-bootstrap/cc/081-cc-object.fth:176,264,268,318` | `cc-obj-room`, `cc-obj-symbol`, `cc-obj-reloc` → `cc-obj-bound` | Object storage/count limit exceeded or mapping failed. | [Chapter 40](40-objects-and-relocations.md) |
| `246` | `forth-bootstrap/cc/081-cc-object.fth:156,237,241,243,250,265,266,267` | `cc-obj-sym`, `cc-obj-check-definition`, `cc-obj-check-id`, `cc-obj-symbol` → `cc-obj-bound` | Invalid object symbol metadata. | [Chapter 40](40-objects-and-relocations.md) |
| `247` | `forth-bootstrap/cc/081-cc-object.fth:315,317` | `cc-obj-reloc` → `cc-obj-bound` | Invalid object relocation type, symbol, or range. | [Chapter 40](40-objects-and-relocations.md) |

The archive reader also raises metadata errors through `lnk-need` and `lnk-bad`; archive byte limits use `lnk-cap`. Their codes are defined in the linker table, not in an archive-only namespace. Representative archive sites are listed below alongside scalar hooks whose numbered reporter lives in another file.

| Code | Calling site | Raising word | Meaning | Layer chapter |
|---|---|---|---|---|
| `250` | `forth-bootstrap/cc/141-archive.fth:363,367,368` | `lnk-need` → `lnk-bad` | Archive magic/header invalid. | [Chapter 42](42-linker-and-archives.md) |
| `251` | `forth-bootstrap/cc/141-archive.fth:160,162` | `lnk-cap` | Archive byte capacity exceeded. | [Chapter 42](42-linker-and-archives.md) |
| `249` | `forth-bootstrap/cc/131-cc-aggregate-abi.fth:408,474,535,543` | `cc-ld-die` | Invalid long-double scalar use, cast, or mapped static initializer. | [Chapter 49](49-aggregate-abi.md) |
| `249` | `forth-bootstrap/cc/132-cc-long-double.fth:51,79,109,121,135,178,202` | `cc-ld-die` | Incompatible conversion, integer-only operator, or mapped static use. | [Chapter 49](49-aggregate-abi.md) |

## The assembler's codes

The following table belongs to the separate M1/hex2 program (Chapter 26). Its overlapping codes do not denote System V or object-writer failures. Capacity and output-open failures exit without a compiler diagnostic. `asm-tok-err` writes the offending token to stderr; undefined references, field-fit failures and malformed hex tokens use it (`forth-bootstrap/forth/130-asm.fth:412`).

### 130-asm.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 230 | `forth-bootstrap/forth/130-asm.fth:145` | `asm-write-output` → `die` | Output path could not be opened. | [Chapter 26](26-m1-and-hex2.md) |
| 231 | `forth-bootstrap/forth/130-asm.fth:593` | `asm-process-token` → `asm-do-ref` | Absolute `&label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 232 | `forth-bootstrap/forth/130-asm.fth:535` | `asm-do-pct-ref` → `asm-tok-err` | Relative `%target>base` base undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 233 | `forth-bootstrap/forth/130-asm.fth:529` | `asm-do-pct-ref` → `asm-tok-err` | Relative `%target>base` target undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 234 | `forth-bootstrap/forth/130-asm.fth:541` | `asm-do-pct-ref` → `asm-do-ref` | Relative `%label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 235 | `forth-bootstrap/forth/130-asm.fth:588` | `asm-process-token` → `asm-do-ref` | Relative `!label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 236 | `forth-bootstrap/forth/130-asm.fth:589` | `asm-process-token` → `asm-do-ref` | Relative `@label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 237 | `forth-bootstrap/forth/130-asm.fth:590` | `asm-process-token` → `asm-do-ref` | Relative `~label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 238 | `forth-bootstrap/forth/130-asm.fth:592` | `asm-process-token` → `asm-do-ref` | Absolute `$label` undefined. | [Chapter 26](26-m1-and-hex2.md) |
| 239 | `forth-bootstrap/forth/130-asm.fth:95` | `asm-load-stdin` → `asm-check-cap` | Source buffer full. | [Chapter 26](26-m1-and-hex2.md) |
| 240 | `forth-bootstrap/forth/130-asm.fth:117` | `asm-exp-emit-byte` → `asm-check-cap` | Macro expansion buffer full. | [Chapter 26](26-m1-and-hex2.md) |
| 241 | `forth-bootstrap/forth/130-asm.fth:132` | `asm-emit-byte` → `asm-check-cap` | Output buffer full. | [Chapter 26](26-m1-and-hex2.md) |
| 242 | `forth-bootstrap/forth/130-asm.fth:181` | `asm-store-label` → `asm-check-cap` | Label table full. | [Chapter 26](26-m1-and-hex2.md) |
| 243 | `forth-bootstrap/forth/130-asm.fth:631` | `asm-def-store` → `asm-check-cap` | DEFINE table full. | [Chapter 26](26-m1-and-hex2.md) |
| 244 | `forth-bootstrap/forth/130-asm.fth:513` | `asm-do-ref` → `asm-fit` | Label value does not fit its reference field. | [Chapter 26](26-m1-and-hex2.md) |
| 245 | `forth-bootstrap/forth/130-asm.fth:504` | `asm-do-ref` → `asm-fit` | Numeric value does not fit its reference field. | [Chapter 26](26-m1-and-hex2.md) |
| 246 | `forth-bootstrap/forth/130-asm.fth:553` | `asm-check-hex` → `asm-tok-err` | Bare token contains non-hexadecimal characters. | [Chapter 26](26-m1-and-hex2.md) |
| 247 | `forth-bootstrap/forth/130-asm.fth:558` | `asm-check-hex` → `asm-tok-err` | Hexadecimal token has an odd digit count. | [Chapter 26](26-m1-and-hex2.md) |

## The build controller's codes

The `seed-cc-start.fth` table below describes the Forth build controller in [Chapter 50](50-seed-cc-fixed-point.md). Those bare `die` codes identify controller failures, not C parser checks. Its successful completion uses status `0` (`forth-bootstrap/cc/driver/seed-cc-start.fth:351`).

### seed-cc-start.fth

| Code | Numbered site | Containing word → raising helper | Meaning | Layer chapter |
|---:|---|---|---|---|
| 101 | `forth-bootstrap/cc/driver/seed-cc-start.fth:76` | `checked-close` → `die` | Close failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 102 | `forth-bootstrap/cc/driver/seed-cc-start.fth:253` | `write-all` → `die` | Write failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 103 | `forth-bootstrap/cc/driver/seed-cc-start.fth:254` | `write-all` → `die` | Write made no progress. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 104 | `forth-bootstrap/cc/driver/seed-cc-start.fth:261` | `append-file` → `die` | Source file open failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 105 | `forth-bootstrap/cc/driver/seed-cc-start.fth:264` | `append-file` → `die` | Source file read failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 106 | `forth-bootstrap/cc/driver/seed-cc-start.fth:269` | `new-input` → `die` | Generated seed-input file open failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 107 | `forth-bootstrap/cc/driver/seed-cc-start.fth:304` | `mkdir-ok` → `die` | Directory creation failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 109 | `forth-bootstrap/cc/driver/seed-cc-start.fth:282` | `run-seed` → `die` | Fork failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 110 | `forth-bootstrap/cc/driver/seed-cc-start.fth:285` | `run-seed` → `die` | Child seed-input open failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 111 | `forth-bootstrap/cc/driver/seed-cc-start.fth:286` | `run-seed` → `die` | Child stdin redirection failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 112 | `forth-bootstrap/cc/driver/seed-cc-start.fth:288` | `run-seed` → `die` | Seed exec returned instead of executing. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 113 | `forth-bootstrap/cc/driver/seed-cc-start.fth:291` | `run-seed` → `die` | Wait did not return the expected child. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 114 | `forth-bootstrap/cc/driver/seed-cc-start.fth:292` | `run-seed` → `die` | Seed child exited unsuccessfully. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 115 | `forth-bootstrap/cc/driver/seed-cc-start.fth:314` | `compile-unit` → `die` | Object rename failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 120 | `forth-bootstrap/cc/driver/seed-cc-start.fth:221` | `scan` → `die` | Directory open failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 121 | `forth-bootstrap/cc/driver/seed-cc-start.fth:224` | `scan` → `die` | Directory scan failed. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 122 | `forth-bootstrap/cc/driver/seed-cc-start.fth:217` | `table-add` → `die` | Source/layer name table full. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 123 | `forth-bootstrap/cc/driver/seed-cc-start.fth:215` | `copy-name` → `die` | Copied-name storage full. | [Chapter 50](50-seed-cc-fixed-point.md) |

## The seed's own code

The seed can fail before the compiler finishes loading. Status `2` from `fatal_token` accompanies the rejected token followed by `?`, on stdout (`forth-bootstrap/seed/000-seed.hex0:478`). The fatal inputs are a token beyond the name-length bound and a nondecimal operand after `[lit]`; their branches are at `forth-bootstrap/seed/000-seed.hex0:416,588`. An ordinary unknown word is reported and reading continues; see [Chapter 9](09-dictionary.md#report_token-and-fatal_token-failing-out-loud).

Status alone does not identify this failure when a driver is involved: the C drivers also use `2` for their own errors.

## The C drivers' statuses

The compiler driver uses OS-failure status `1` (`forth-bootstrap/cc/driver/seed-cc.c:1080`); the archive driver selects `2` (`forth-bootstrap/cc/driver/seed-ar.c:185`). Both use the shared OS reporter (`forth-bootstrap/cc/driver/seed-tool.h:372`).

The compiled drivers print a message through `st_fail` rather than the compiler's numbered-line format (`forth-bootstrap/cc/driver/seed-tool.h:262`).

| Status | Source site | Raising function | Meaning | Layer chapter |
|---:|---|---|---|---|
| 1 | `forth-bootstrap/cc/driver/seed-cc.c:165,455,493,498,502,602,849` | `st_fail`, `st_fail2` | Path/input/snapshot failure or unexpected Forth stdout. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 2 | `forth-bootstrap/cc/driver/seed-cc.c:65,223,233,238,260,266,276,962` | `usage_fail`, `st_fail`, `st_fail2` | Invalid options, arguments, or unavailable math inputs. | [Chapter 50](50-seed-cc-fixed-point.md) |
| 2 | `forth-bootstrap/cc/driver/seed-ar.c:25,185` | `value_fail`, `st_fail_os` | Invalid archive operation/input or OS failure. | [Chapter 50](50-seed-cc-fixed-point.md) |

`seed-ar` also preserves a positive Forth child status, with a fallback of `1` for unexpected output or an abnormal child result (`forth-bootstrap/cc/driver/seed-ar.c:346`).

`seed-cc` preserves a positive Forth child failure status; its fallback is `1` (`forth-bootstrap/cc/driver/seed-cc.c:600`). The shared child launcher exits with status `127` if redirection or exec fails (`forth-bootstrap/cc/driver/seed-tool.h:1038,1040`).

The driver-generated preprocessing-output writer can itself raise compiler code `22` on output failures (`forth-bootstrap/cc/driver/seed-cc.c:654,657,658`). These are outside the compiler-layer tables.

## Runtime trap status

The private runtime's unavailable `localtime`, `ldexp` and `longjmp` paths print `seed-forth bootstrap: unsupported NAME` and exit with status `125` when executed. This is distinct from a compiler rejection of a constant expression. The trap emitter is `cc-native-unavailable` (`forth-bootstrap/cc/119-cc-native-runtime.fth:72`).
Its emitted exit status and conditional registration are at `forth-bootstrap/cc/119-cc-native-runtime.fth:87,105`. [Chapter 39](39-lp64-storage-and-initializers.md) owns that runtime layer.

## Why a number and a line, not a message?

A per-site message needs per-site text. The common code leaves most checks as a small numbered call and keeps formatting in the reporter. The number identifies the check; the line identifies the input position. Some later layers add a prefix or reason when the shared form cannot distinguish their failures.

For a particular diagnostic, search the owning source file for its literal code and inspect the surrounding condition. A code passed to a shared helper may appear where a buffer or sink is configured rather than where it overflows. Keep both locations when investigating it.

## Try it

Run from the `forth-bootstrap` checkout root with the seed built in Part 1. The layer-list script puts the executing main last (`forth-bootstrap/cc/compiler-layers.sh:6`). This input triggers the preprocessor entry for active `#error`; the final test checks its status after printing the diagnostic.

```sh
(
{ cat forth/010-lib.fth $(cc/compiler-layers.sh); printf '%s\n' '#error appendix diagnostic probe'; } | ./seed-forth 2>&1
status=$?
printf 'compiler status: %s\n' "$status"
test "$status" -eq 40
)
```

Observed output:

```text
cc: line 1: error 40
compiler status: 40
```
