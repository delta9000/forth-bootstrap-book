/* A deliberately small DOM contract harness, not a browser/layout test. */
"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const request = JSON.parse(fs.readFileSync(0, "utf8"));
const api = require(request.script);
const escapeHTML = text => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
class Node {
    constructor(name, document, text = "") {
        this.nodeName = name.toUpperCase();
        this.nodeType = name === "#text" ? 3 : 1;
        this.ownerDocument = document;
        this.children = [];
        this.attrs = {};
        this._text = text;
        this.className = "";
        this.scrollWidth = 10;
        this.clientWidth = 10;
        this.classList = {
            add: (...names) => { this.className = [...new Set([...this.className.split(/\s+/).filter(Boolean), ...names])].join(" "); },
            contains: name => this.className.split(/\s+/).includes(name),
            remove: name => { this.className = this.className.split(/\s+/).filter(n => n !== name).join(" "); }
        };
    }
    get textContent() { return this._text + this.children.map(n => n.textContent).join(""); }
    set textContent(text) { this.children = []; this._text = text; this._html = undefined; }
    get nodeValue() { return this._text; }
    get firstChild() { return this.children[0] || null; }
    get nextSibling() { return null; } // hljs sees only initial text, never nested source markup.
    appendChild(node) {
        if (node.nodeName === "#FRAGMENT") this.children.push(...node.children);
        else this.children.push(node);
        return node;
    }
    replaceChildren(...nodes) { this.children = []; this._text = ""; this._html = undefined; nodes.forEach(n => this.appendChild(n)); }
    setAttribute(name, value) { this.attrs[name] = value; }
    removeAttribute(name) { delete this.attrs[name]; }
    get innerHTML() {
        return this._html ?? escapeHTML(this._text) + this.children.map(n => n.nodeType === 3 ? escapeHTML(n.textContent) : `<span class="${n.className}">${n.innerHTML}</span>`).join("");
    }
    set innerHTML(html) {
        if (!this.allowHighlighterHTML) throw Error("Forth must not write innerHTML");
        this._html = html;
    }
}
const elements = [];
const document = {
    createElement: name => new Node(name, document),
    createTextNode: text => new Node("#text", document, text),
    createDocumentFragment: () => new Node("#fragment", document),
    querySelectorAll: selector => {
        if (selector === "code") return elements;
        if (selector !== "pre > code.language-forth") throw Error("Unexpected selector: " + selector);
        return elements.filter(n => n.parentElement.nodeName === "PRE" && n.classList.contains("language-forth"));
    }
};
for (const input of request.blocks || []) {
    const code = document.createElement("code");
    code.className = input.classes || "language-forth";
    code.textContent = input.text;
    code.parentNode = code.parentElement = document.createElement(input.pre === false ? "p" : "pre");
    code.allowHighlighterHTML = !code.classList.contains("language-forth");
    code.scrollWidth = input.overflow ? 100 : 10;
    elements.push(code);
}
let bundledVersion;
if (request.bundled) {
    // Execute the pinned renderer's real syntax-highlighting section, including
    // its tabReplace setting, rather than a substitute hljs call sequence.
    const bundled = {console: {warn() {}, log() {}}, document};
    vm.runInNewContext(fs.readFileSync(request.bundled, "utf8"), bundled);
    bundledVersion = bundled.hljs.versionString;
    const core = fs.readFileSync(request.book, "utf8");
    const start = core.indexOf("// Syntax highlighting Configuration");
    const end = core.indexOf("Array.from(document.querySelectorAll('code.hljs'))", start);
    if (start < 0 || end < start) throw Error("mdBook highlighting contract changed");
    vm.runInNewContext(core.slice(start, end), {...bundled, window: {}});
}
const before = elements.map(n => ({html: n.innerHTML, classes: n.className, text: n.textContent}));
const listeners = {};
const resizeObservers = [];
vm.runInNewContext(fs.readFileSync(request.script, "utf8"), {
    document, window: {
        addEventListener: (name, callback) => { listeners[name] = callback; },
        ResizeObserver: class {
            constructor(callback) { this.callback = callback; this.nodes = []; resizeObservers.push(this); }
            observe(node) { this.nodes.push(node); }
        }
    }
});
const first = elements.map(n => n.innerHTML);
api.highlightAll(document);
const after = elements.map((n, i) => ({
    text: n.textContent, html: n.innerHTML, classes: n.className, attrs: n.attrs,
    unchanged: before[i].html === n.innerHTML && before[i].classes === n.className,
    idempotent: first[i] === n.innerHTML,
    spans: n.children.filter(x => x.nodeName === "SPAN").map(x => ({kind: x.className, text: x.textContent}))
}));
if (request.reveal) {
    elements.forEach(n => { n.scrollWidth = 100; n.clientWidth = 10; });
    resizeObservers.forEach(observer => observer.callback(observer.nodes.map(target => ({target}))));
}
if (request.resize && listeners.resize) {
    elements.forEach(n => { n.scrollWidth = 10; n.clientWidth = 10; });
    listeners.resize();
}
if (request.summary) {
    process.stdout.write(JSON.stringify({bundledVersion, blocks: after.map((n, i) => ({
        textPreserved: n.text === before[i].text, unchanged: n.unchanged,
        idempotent: n.idempotent, spans: n.spans.length
    }))}));
} else process.stdout.write(JSON.stringify({
    tokens: (request.sources || []).map(source => api.tokenize(source)),
    blocks: after, bundledVersion,
    resizedAttrs: elements.map(n => n.attrs)
}));
