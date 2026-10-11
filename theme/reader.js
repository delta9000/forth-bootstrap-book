/* Progressive enhancements only: the manuscript works without JavaScript. */
(() => {
    "use strict";

    // mdBook 0.5.4 omits the ID prefix in the search field's description.
    // Repair only that known reference; leave newer templates untouched.
    const searchbar = document.getElementById("mdbook-searchbar");
    const searchResultsHeader = document.getElementById("mdbook-searchresults-header");
    if (searchbar && searchResultsHeader &&
        searchbar.getAttribute("aria-describedby") === "searchresults-header") {
        searchbar.setAttribute("aria-describedby", searchResultsHeader.id);
    }

    const main = document.querySelector("main");
    if (!main) return;

    // A word-index or search link may land inside an optional implementation.
    const revealFragment = () => {
        let id;
        try { id = decodeURIComponent(location.hash.slice(1)); }
        catch { return; }
        if (!id) return;
        const target = document.getElementById(id);
        if (!target || !main.contains(target)) return;
        let opened = false;
        for (let parent = target.parentElement; parent; parent = parent.parentElement) {
            if (parent.tagName === "DETAILS" && !parent.open) {
                parent.open = true;
                opened = true;
            }
        }
        if (opened) target.scrollIntoView();
    };
    window.addEventListener("hashchange", revealFragment);
    revealFragment();

    // Print the complete manuscript, then restore the reader's disclosure state.
    const openedForPrint = new Set();
    window.addEventListener("beforeprint", () => {
        main.querySelectorAll("details:not([open])").forEach(details => {
            if (details.closest(".book-tools")) return;
            openedForPrint.add(details);
            details.open = true;
        });
    });
    window.addEventListener("afterprint", () => {
        openedForPrint.forEach(details => { details.open = false; });
        openedForPrint.clear();
    });

    // A caption identifies canonical source without entering copied code text.
    main.querySelectorAll("pre > code").forEach(code => {
        const source = Array.from(code.classList).find(name => name.startsWith("file="));
        const chunk = Array.from(code.classList).find(name => name.startsWith("chunk="));
        if (!source && !chunk) return;
        const caption = document.createElement("div");
        caption.className = "book-listing-label";
        caption.textContent = source ? `Source · ${source.slice(5)}` : `Source chunk · ${chunk.slice(6)}`;
        code.parentElement.before(caption);
    });

    // The concatenated print edition needs no per-chapter navigation.
    const titles = main.querySelectorAll(":scope > h1");
    if (titles.length !== 1) return;
    const heading = titles[0];
    const titleLink = heading.querySelector("a.header");
    const match = heading.textContent.match(/^Chapter (\d+)\s*[—–-]\s*(.+)$/);
    const parts = ["Front matter", "Part I · The seed", "Part II · The Forth library",
        "Part III · The C compiler", "Part IV · The bootstrap"];
    if (match && Number(match[1]) <= 56) {
        const chapter = Number(match[1]);
        const part = chapter < 4 ? 0 : chapter < 14 ? 1 : chapter < 27 ? 2 : chapter < 50 ? 3 : 4;
        const kicker = document.createElement("p");
        kicker.className = "book-kicker";
        kicker.textContent = `${parts[part]} / Chapter ${chapter}`;
        heading.before(kicker);
        if (titleLink) titleLink.textContent = match[2];
    }

    const sections = Array.from(main.querySelectorAll("h2[id]"));
    if (sections.length < 2) return;
    const nav = document.createElement("nav");
    nav.className = "book-tools";
    nav.setAttribute("aria-label", "Chapter navigation");
    const addLink = (label, target) => {
        const link = document.createElement("a");
        link.textContent = label;
        link.href = target;
        nav.append(link);
    };
    const checkpoint = sections.find(section => /^Try it\b/i.test(section.textContent.trim()));
    const exercises = sections.find(section => /^Exercises?$/i.test(section.textContent.trim()));
    if (checkpoint) addLink("Try it ↓", `#${checkpoint.id}`);
    if (exercises) addLink("Exercises ↓", `#${exercises.id}`);
    addLink("Lab guide", "labs.html");
    addLink("Glossary", "62-glossary.html");
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = `In this chapter · ${sections.length} sections`;
    details.append(summary);
    const list = document.createElement("ol");
    sections.forEach(section => {
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = `#${section.id}`;
        link.textContent = section.textContent.trim();
        item.append(link);
        list.append(item);
    });
    details.append(list);
    nav.append(details);
    sections[0].before(nav);
})();
