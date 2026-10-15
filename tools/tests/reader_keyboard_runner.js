/* Event-routing contract tests, not a browser or a native-scrolling emulator.
 * With `book`, execute the rendered mdBook focus helper and chapter-navigation
 * IIFE verbatim, before reader.js, matching the published script load order.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const request = JSON.parse(fs.readFileSync(0, "utf8"));
const reader = fs.readFileSync(request.script, "utf8");
let chapterNavigation = "";
if (request.book) {
    const book = fs.readFileSync(request.book, "utf8");
    const extract = (start, end) => {
        const first = book.indexOf(start);
        const last = book.indexOf(end, first);
        assert(first >= 0 && last > first, "mdBook keyboard contract changed");
        return book.slice(first, last);
    };
    chapterNavigation = extract("function mdbook_something_else_has_focus(e)",
        "(function codeSnippets()") + extract("(function chapterNavigation()",
        "(function clipboard()");
}

function fixture(withReader = true, rtl = false) {
    class Element {
        constructor(nodeName, parentElement = null, classes = []) {
            this.nodeName = this.tagName = nodeName.toUpperCase();
            this.parentElement = parentElement;
            this.listeners = [];
            this.classList = {contains: name => classes.includes(name)};
            this.scrollLeft = 0;
            this.scrollWidth = 602;
            this.clientWidth = 479;
        }
        addEventListener(type, callback, options = false) {
            if (type === "keydown") this.listeners.push({callback,
                capture: options === true || !!options.capture});
        }
        closest(selector) {
            assert.equal(selector, "pre > code, .mechanism-graphic-viewport");
            for (let node = this; node; node = node.parentElement) {
                if (node.nodeName === "CODE" && node.parentElement?.nodeName === "PRE") return node;
                if (node.classList.contains("mechanism-graphic-viewport")) return node;
            }
            return null;
        }
        querySelectorAll() { return []; }
    }
    const document = new Element("#document");
    const body = new Element("body", document);
    const main = new Element("main", body);
    const pre = new Element("pre", main);
    const code = new Element("code", pre, ["language-forth"]);
    const span = new Element("span", code, ["forth-builtin"]);
    const figure = new Element("figure", main);
    const viewport = new Element("div", figure, ["mechanism-graphic-viewport"]);
    const figureLink = new Element("a", viewport);
    const image = new Element("img", figureLink);
    const fullsizeLink = new Element("a", figure);
    const inline = new Element("code", main);
    const button = new Element("button", pre, ["clip-button"]);
    const input = new Element("input", main);
    const textarea = new Element("textarea", main);
    const select = new Element("select", main);
    const editable = new Element("span", code);
    editable.isContentEditable = true;
    const window = {location: {href: "current.html", hash: ""}, addEventListener() {}};
    document.querySelector = selector => ({main, html: {dir: rtl ? "rtl" : "ltr"},
        ".nav-chapters.next": {href: "next.html"},
        ".nav-chapters.previous": {href: "previous.html"}}[selector] || null);
    document.getElementById = () => null;
    const context = vm.createContext({document, window, location: window.location});
    if (chapterNavigation) vm.runInContext(chapterNavigation, context);
    let delivered = 0;
    document.addEventListener("keydown", () => { delivered++; });
    if (withReader) vm.runInContext(reader, context);
    function dispatch(target, key, options = {}) {
        window.location.href = "current.html";
        delivered = 0;
        document.activeElement = target;
        const path = [];
        for (let node = target; node; node = node.parentElement) path.push(node);
        const event = {key, target, altKey: false, ctrlKey: false, metaKey: false,
            shiftKey: false, defaultPrevented: false, cancelBubble: false, ...options,
            composedPath: () => path,
            preventDefault() { this.defaultPrevented = true; },
            stopPropagation() { this.cancelBubble = true; }};
        // Dispatch capture and bubble phases; registration order applies only
        // within one node/phase. No browser default action is simulated here.
        for (const capture of [true, false]) {
            for (const node of capture ? [...path].reverse() : path) {
                for (const listener of node.listeners) {
                    if (listener.capture === capture) listener.callback(event);
                }
                if (event.cancelBubble) break;
            }
            if (event.cancelBubble) break;
        }
        return {delivered, prevented: event.defaultPrevented,
            href: window.location.href, focus: document.activeElement};
    }
    return {Element, document, window, main, pre, code, span, inline, button, input,
        textarea, select, editable, body, viewport, figureLink, image, fullsizeLink, dispatch};
}

let cases = 0;
const check = (f, target, key, options, protectedCode, navigates = false) => {
    const result = f.dispatch(target, key, options);
    assert.equal(result.delivered, protectedCode ? 0 : 1, `${key}: document routing`);
    assert.equal(result.prevented, !!options.defaultPrevented || (!!chapterNavigation && navigates),
        `${key}: native default action`);
    assert.equal(result.href === "current.html", !(chapterNavigation && navigates), `${key}: navigation`);
    assert.equal(result.focus, target, `${key}: focus is not trapped or moved`);
    cases++;
    return result;
};

if (chapterNavigation) {
    const baseline = fixture(false);
    for (const key of ["ArrowLeft", "ArrowRight"]) {
        // Reproduce the real conflict before adding reader.js. preventDefault
        // alone would not fix it: mdBook does not check defaultPrevented.
        check(baseline, baseline.code, key, {}, false, true);
        check(baseline, baseline.viewport, key, {}, false, true);
        check(baseline, baseline.figureLink, key, {}, false, true);
        check(baseline, baseline.code, key, {defaultPrevented: true}, false, true);
    }
}
for (const rtl of [false, true]) {
    const f = fixture(true, rtl);
    for (const language of ["forth", "c", "sh", "text", ""]) {
        const code = new f.Element("code", f.pre, language ? [`language-${language}`] : []);
        for (const [width, offset] of [[602, 0], [602, 60], [602, 123], [479, 0]]) {
            code.scrollWidth = width;
            code.scrollLeft = offset;
            for (const key of ["ArrowLeft", "ArrowRight"]) check(f, code, key, {}, true);
        }
    }
    for (const target of [f.span, f.editable, f.viewport, f.figureLink, f.image]) {
        for (const key of ["ArrowLeft", "ArrowRight"]) check(f, target, key, {}, true);
    }
    // Figure panning remains native, even at boundaries or after resize.
    for (const width of [760, 479]) {
        f.viewport.scrollWidth = width;
        for (const offset of [0, 100, width - f.viewport.clientWidth]) {
            f.viewport.scrollLeft = offset;
            for (const key of ["ArrowLeft", "ArrowRight"]) {
                check(f, f.viewport, key, {}, true);
                check(f, f.figureLink, key, {repeat: true}, true);
                for (const modifier of ["altKey", "ctrlKey", "metaKey", "shiftKey"]) {
                    check(f, f.viewport, key, {[modifier]: true}, false);
                }
            }
        }
    }
    for (const key of ["Tab", "ArrowUp", "ArrowDown", "Home", "End", "Escape"]) {
        check(f, f.viewport, key, {}, false);
    }
    // A selected listing still retains the browser's native default action.
    f.window.getSelection = () => ({isCollapsed: false, anchorNode: f.span});
    check(f, f.code, "ArrowRight", {}, true);
    f.window.getSelection = () => ({isCollapsed: true, anchorNode: null});
    // Repeated keys and canceled events retain their native default state.
    for (const key of ["ArrowLeft", "ArrowRight"]) {
        check(f, f.code, key, {repeat: true}, true);
        check(f, f.code, key, {defaultPrevented: true}, true);
        for (const modifier of ["altKey", "ctrlKey", "metaKey", "shiftKey"]) {
            check(f, f.code, key, {[modifier]: true}, false);
        }
    }
    for (const key of ["Tab", "ArrowUp", "ArrowDown", "Home", "End", "Escape", "c"]) {
        check(f, f.code, key, {}, false);
    }
    check(f, f.code, "Tab", {shiftKey: true}, false);
    for (const target of [f.body, f.main, f.pre, f.inline, f.button, f.fullsizeLink]) {
        for (const key of ["ArrowLeft", "ArrowRight"]) {
            const result = check(f, target, key, {}, false, true);
            if (chapterNavigation) assert.equal(result.href,
                (key === "ArrowRight") !== rtl ? "next.html" : "previous.html");
        }
    }
    for (const target of [f.input, f.textarea, f.select]) {
        for (const key of ["ArrowLeft", "ArrowRight"]) check(f, target, key, {}, false);
    }
    // Delegation also covers listings revealed in details or added after setup.
    const details = new f.Element("details", f.main);
    const revealed = new f.Element("code", new f.Element("pre", details));
    details.open = true;
    check(f, revealed, "ArrowRight", {}, true);
    revealed.scrollWidth = revealed.clientWidth; // Retains focus after resize.
    check(f, revealed, "ArrowLeft", {}, true);
}
process.stdout.write(JSON.stringify({cases, actualMdBook: !!chapterNavigation}));
