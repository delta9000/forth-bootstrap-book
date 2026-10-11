/* The book's seed-Forth dialect, not an ANSI Forth grammar.
 * Source contract: seed/000-seed.hex0 read_word/parse_decimal_code and
 * forth/010-lib.fth at the source pin recorded by this book.
 * No source execution, HTML interpolation, network, or external dependency.
 */
(() => {
    "use strict";
    const SPACE = /[ \t\r\n]/;
    const CONTROL = new Set(["if,", "else,", "then,", "begin,", "while,",
        "repeat,", "until,", "again,", "exit,", "branch", "0branch"]);
    const DEFINERS = new Set(["constant", "create", "variable", "defer", "code:"]);
    const META = new Set([":", ";", "[lit]", "[char]", "immediate", "is", "'"]);
    const CORE = new Set(["dup", "drop", "swap", ">r", "r>", "r@", "@", "!",
        "c@", "c!", "+", "nand", "0=", "/", "*", "key", "emit", "syscall6",
        "bye", "here", ",", "lit", "find", "execute", "state", "latest", "over", "-",
        "1+", "1-", "and", "or", "=", "<>", "0<", "<", ">", "<=", ">=",
        "nip", "rot", "2dup", "2drop", "+!", "-!", "c,", ",4", ",8", "allot",
        "char", "s,", "kw,", "token", "bytes,"]);
    const READERS = new Map([["char", ["string", 1]], ["s,", ["string", 1]],
        ["kw,", ["string", 1]], ["token", ["string", 1]], ["'", ["reference", 1]],
        ["is", ["reference", 1]], ["cc-binop,", ["reference", 2]]]);

    // The seed consumes a complete whitespace-delimited word before deciding
    // whether it is a comment marker. A backslash embedded in a word is inert.
    function lex(source) {
        const tokens = [];
        let i = 0;
        while (i < source.length) {
            const start = i;
            let kind = "";
            if (source[i] === "\0") {
                // Binary input is outside the book's text grammar. Preserve
                // the rest without trying to emulate the seed's NUL behavior.
                tokens.push({kind: "", text: source.slice(i)});
                break;
            }
            if (SPACE.test(source[i])) {
                while (i < source.length && SPACE.test(source[i])) i++;
            } else {
                while (i < source.length && !SPACE.test(source[i]) && source[i] !== "\0") i++;
                const word = source.slice(start, i);
                kind = "word";
                if (word === "\\") {
                    // Include the already-read delimiter in the search: a
                    // marker immediately followed by LF ends on that line.
                    const end = source.indexOf("\n", i);
                    i = end < 0 ? source.length : end;
                    kind = "comment";
                } else if (word === "(") {
                    const end = source.indexOf(")", i);
                    i = end < 0 ? source.length : end + 1;
                    kind = "comment";
                }
            }
            tokens.push({kind, text: source.slice(start, i)});
        }
        return tokens;
    }

    // A fence can be a body excerpt. An unquoted ; before any : tells us its
    // opening : is outside the excerpt. This is lexical context, not execution
    // of STATE writes or arbitrary user-defined immediate/defining words.
    function startsInDefinition(tokens) {
        let remaining = 0;
        for (const token of tokens) {
            if (token.kind !== "word") continue;
            if (remaining) { remaining--; continue; }
            if (READERS.has(token.text)) {
                remaining = READERS.get(token.text)[1];
            } else if (DEFINERS.has(token.text) || ["[char]", "[lit]"].includes(token.text)) {
                remaining = 1;
            } else if (token.text === ":") {
                return false;
            } else if (token.text === ";") {
                return true;
            }
        }
        return false;
    }

    function tokenize(source) {
        const tokens = lex(source);
        let inDefinition = startsInDefinition(tokens);
        let operand = "";
        let remaining = 0;
        for (const token of tokens) {
            if (token.kind !== "word") continue;
            const word = token.text;
            token.kind = "";
            if (remaining) {
                // Numbers are data only after [lit]. 1+, 2^63, 0branch, and
                // even a bare all-digit dictionary name must remain words.
                token.kind = operand === "number" ? (/^[0-9]+$/.test(word) ? "number" : "") : operand;
                remaining--;
                continue;
            }
            if (CONTROL.has(word)) token.kind = "control";
            else if (META.has(word) || DEFINERS.has(word)) token.kind = "meta";
            else if (CORE.has(word)) token.kind = "builtin";
            if (word === ":" && !inDefinition) {
                operand = "definition";
                remaining = 1;
                inDefinition = true;
            } else if (word === ";") {
                inDefinition = false;
            } else if (word === "[lit]") {
                operand = "number";
                remaining = 1;
            } else if (word === "[char]") {
                operand = "string";
                remaining = 1;
            } else if (!inDefinition) {
                if (DEFINERS.has(word)) {
                    operand = "definition";
                    remaining = 1;
                } else if (READERS.has(word)) {
                    [operand, remaining] = READERS.get(word);
                }
            }
        }
        return tokens;
    }

    function highlight(code) {
        const source = code.textContent;
        const fragment = code.ownerDocument.createDocumentFragment();
        for (const token of tokenize(source)) {
            if (token.kind) {
                const span = code.ownerDocument.createElement("span");
                span.className = `forth-${token.kind}`;
                span.textContent = token.text;
                fragment.appendChild(span);
            } else {
                fragment.appendChild(code.ownerDocument.createTextNode(token.text));
            }
        }
        // Repeated calls rebuild from text, never from existing highlight HTML.
        code.replaceChildren(fragment);
        code.classList.add("hljs", "forth-highlighted");
    }

    // mdBook's additional-js files run after book.js. Only tagged Forth fences
    // are touched; C, shell, inline code, and the bundled highlighter stay intact.
    function highlightAll(root) {
        const codes = root.querySelectorAll("pre > code.language-forth");
        codes.forEach(highlight);
        // Keep alignment on narrow screens, with keyboard access only for
        // listings that actually overflow. Print uses soft wrapping instead.
        const updateCode = code => {
            if (code.scrollWidth > code.clientWidth) {
                code.setAttribute("tabindex", "0");
                code.setAttribute("role", "region");
                code.setAttribute("aria-label", "Forth listing, scroll horizontally");
            } else {
                code.removeAttribute("tabindex");
                code.removeAttribute("role");
                code.removeAttribute("aria-label");
            }
        };
        const updateScroll = () => codes.forEach(updateCode);
        updateScroll();
        if (typeof window !== "undefined") {
            window.addEventListener("resize", updateScroll);
            // Closed details have no layout box. Observe the code's own size
            // so revealing it or resizing the sidebar updates keyboard access.
            if (window.ResizeObserver) {
                const observer = new window.ResizeObserver(entries => {
                    entries.forEach(entry => updateCode(entry.target));
                });
                codes.forEach(code => observer.observe(code));
            }
        }
        if (root.fonts) root.fonts.ready.then(updateScroll);
    }
    if (typeof module === "object" && module.exports) {
        module.exports = {tokenize, highlight, highlightAll};
    }
    if (typeof document !== "undefined") highlightAll(document);
})();
