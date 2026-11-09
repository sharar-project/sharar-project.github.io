// Review comments on PR previews. The deploy workflow adds this script to every page under pr-preview/pr-<n>/
// (tools/preview_comments.py), never to the live site. Select text, click "Comment": GitHub opens a new issue in
// this repository with the passage quoted, a link back to it and the PR number, ready for the comment.
(() => {
  const me = document.currentScript;
  const PR = me.dataset.pr, REPO = me.dataset.repo;
  if (!PR || !REPO) return;
  const GH = `https://github.com/${REPO}`;
  const LABEL = "review";

  const css = document.createElement("style");
  css.textContent = `
.pc-bar { position: fixed; left: 50%; bottom: 16px; transform: translateX(-50%); z-index: 2147483000;
  display: flex; gap: 14px; align-items: center; max-width: calc(100vw - 32px); box-sizing: border-box;
  padding: 8px 14px; border-radius: 999px; background: #1d1d1f; color: #f5f5f7;
  font: 500 13px/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; box-shadow: 0 4px 16px rgba(0,0,0,.25); }
.pc-bar a { color: #f5f5f7; }
.pc-bar .pc-x { background: none; border: 0; color: inherit; font: inherit; cursor: pointer; padding: 0 2px; opacity: .7; }
.pc-btn { position: absolute; z-index: 2147483001; padding: 6px 12px; border: 0; border-radius: 999px; cursor: pointer;
  background: #a31f34; color: #fff; font: 600 13px/1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  box-shadow: 0 2px 10px rgba(0,0,0,.25); }
.pc-btn[hidden], .pc-bar[hidden] { display: none; }`;
  document.head.appendChild(css);

  const issues = `${GH}/issues?q=${encodeURIComponent(`is:issue is:open label:${LABEL} in:title "PR #${PR}"`)}`;
  const bar = document.createElement("div");
  bar.className = "pc-bar";
  bar.innerHTML = `<span>Preview of <a href="${GH}/pull/${PR}" target="_blank" rel="noopener">PR #${PR}</a>. ` +
    `Select text to comment.</span><a href="${issues}" target="_blank" rel="noopener">Open comments</a>` +
    `<button class="pc-x" type="button" aria-label="Hide">✕</button>`;
  bar.querySelector(".pc-x").onclick = () => { bar.hidden = true; };

  const btn = document.createElement("button");
  btn.className = "pc-btn";
  btn.type = "button";
  btn.textContent = "Comment";
  btn.hidden = true;
  document.body.append(bar, btn);

  let picked = null;   // { text, link, where } for the current selection

  const clean = s => s.replace(/\s+/g, " ").trim();

  // The nearest element at or before the selection that has an id: an <h3>, a <section>, or the page itself.
  function anchorOf(node) {
    let el = node.nodeType === 1 ? node : node.parentElement;
    const heads = document.querySelectorAll("section[id], h2[id], h3[id]");   // in document order
    let best = null;
    for (const h of heads) {
      if (h === el || h.contains(el) || (h.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING)) best = h;
    }
    if (!best) return { id: "", title: "" };
    const head = best.tagName === "SECTION" ? best.querySelector("h2, h3") : best;
    return { id: best.id, title: head ? clean(head.textContent) : "" };
  }

  // MathJax renders formulas as SVG, which has no text. Map each rendered formula back to its LaTeX.
  function texOf() {
    const map = new Map(), doc = window.MathJax?.startup?.document;
    if (doc?.getMathItemsWithin) {
      for (const it of doc.getMathItemsWithin(document.body)) {
        map.set(it.typesetRoot, it.display ? `$$${it.math.trim()}$$` : `$${it.math.trim()}$`);
      }
    }
    return map;
  }

  // The selected text, with each formula as LaTeX. Returns the text pieces between formulas too: a text fragment
  // can only match text, so the link is built from the first and last of them.
  const MATH = "\u0000";
  function selected(range) {
    const tex = texOf();
    let root = range.commonAncestorContainer;
    if (root.nodeType !== 1) root = root.parentNode;
    const inMath = root.closest("mjx-container");
    if (inMath) return { text: tex.get(inMath) || "", parts: [] };
    let out = "";
    const walk = n => {
      for (const c of n.childNodes) {
        if (!range.intersectsNode(c)) continue;
        if (c.nodeType === 3) {
          const a = c === range.startContainer ? range.startOffset : 0;
          const b = c === range.endContainer ? range.endOffset : c.length;
          out += c.textContent.slice(a, b);
        } else if (c.nodeType === 1) {
          if (c.tagName === "MJX-CONTAINER") out += MATH + (tex.get(c) || "") + MATH;
          else if (!/^(SCRIPT|STYLE|SVG|CANVAS)$/i.test(c.tagName)) {
            if (/^(P|LI|H\d|DIV|TD|TH|FIGCAPTION|DT|DD|BLOCKQUOTE|BR)$/.test(c.tagName)) out += " ";
            walk(c);
          }
        }
      }
    };
    walk(root);
    const parts = out.split(MATH).filter((_, i) => i % 2 === 0).map(clean);
    return { text: clean(out.split(MATH).join("")), parts };
  }

  // A link that scrolls to the passage and highlights it (a text fragment), falling back to its section.
  function linkTo(parts, id) {
    const base = `${location.origin}${location.pathname}#${id}`;
    const first = parts[0] || "", last = parts[parts.length - 1] || "";
    if (!first || !last) return base;
    const enc = s => encodeURIComponent(s).replace(/-/g, "%2D");
    const words = first.split(" ");
    if (parts.length === 1 && words.length <= 10) return `${base}:~:text=${enc(first)}`;
    const end = last.split(" ");
    return `${base}:~:text=${enc(words.slice(0, 5).join(" "))},${enc(end.slice(-5).join(" "))}`;
  }

  function onSelect() {
    const sel = getSelection();
    if (!sel || !sel.rangeCount || sel.isCollapsed ||bar.contains(sel.anchorNode) || btn.contains(sel.anchorNode)) { btn.hidden = true; picked = null; return; }
    const range = sel.getRangeAt(0);
    const { text, parts } = selected(range);
    if (!text) { btn.hidden = true; picked = null; return; }
    const rects = range.getClientRects();
    const r = rects.length ? rects[rects.length - 1] : range.getBoundingClientRect();
    const where = anchorOf(range.startContainer);
    picked = { text, link: linkTo(parts, where.id), where: where.title };
    btn.hidden = false;
    const x = Math.min(Math.max(8, r.right + scrollX - btn.offsetWidth), scrollX + document.documentElement.clientWidth - btn.offsetWidth - 8);
    btn.style.left = `${x}px`;
    btn.style.top = `${r.bottom + scrollY + 8}px`;
  }

  let t;
  document.addEventListener("selectionchange", () => { clearTimeout(t); t = setTimeout(onSelect, 150); });
  btn.addEventListener("mousedown", e => e.preventDefault());   // keep the selection while clicking

  btn.addEventListener("click", () => {
    if (!picked) return;
    const page = clean(document.title);
    const quote = picked.text.length > 1500 ? picked.text.slice(0, 1500) + " …" : picked.text;
    const short = picked.text.length > 50 ? picked.text.slice(0, 50).trim() + "…" : picked.text;
    const body = [
      quote.split("\n").map(l => `> ${l}`).join("\n"),
      "",
      `**Where:** [${picked.where || page}](${picked.link})`,
      `**Preview of:** #${PR}`,
      "",
      "<!-- Write your comment below. -->",
      "",
    ].join("\n");
    const q = new URLSearchParams({ title: `[PR #${PR}] "${short}"`, body, labels: LABEL });
    window.open(`${GH}/issues/new?${q}`, "_blank", "noopener");
    btn.hidden = true;
  });
})();
