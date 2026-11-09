"""Edit a page's text in the browser, on the page as it looks on the site.

    python3 tools/edit.py                                   # the quantized-LLM repair post
    python3 tools/edit.py posts/sharar-paper.html           # any page in PAGES, by its path under src/

Then open http://localhost:8001. Click any paragraph, heading, list item, table cell or caption and type. Save (or
Cmd/Ctrl+S) writes the changes into the page's source under src/. Only the text you changed is rewritten; the rest of
the file stays byte for byte, and formulas stay LaTeX. Figures, code and the page's scripts are not editable here.

The server listens on 127.0.0.1 only. Other pages are served from site/, built once at start.
"""
import contextlib
import hashlib
import io
import http.server
import json
import sys
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

PORT = 8001
EDITABLE = {"p", "h1", "h2", "h3", "h4", "li", "td", "th", "figcaption", "dt", "dd", "blockquote"}
SKIP_INSIDE = {"script", "style", "svg", "template", "pre", "code", "button", "summary", "nav", "aside"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Blocks(HTMLParser):
    """Finds the innermost text elements of a page source, with the offsets of their start tag and inner HTML."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text, self.lines, self.open, self.skip, self.found = text, [0], [], [], []
        for i, ch in enumerate(text):
            if ch == "\n":
                self.lines.append(i + 1)
        self.feed(text)
        self.close()

    def pos(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        start = self.pos()
        end = start + len(self.get_starttag_text())
        if tag in SKIP_INSIDE:
            self.skip.append(tag)
        if tag in EDITABLE:
            for o in self.open:
                o["leaf"] = False  # only the innermost element is editable
            self.open.append({"tag": tag, "tag_end": end - 1, "inner": end, "leaf": not self.skip})

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if self.skip and tag == self.skip[-1]:
            self.skip.pop()
        if tag in EDITABLE:
            for i in range(len(self.open) - 1, -1, -1):
                if self.open[i]["tag"] == tag:
                    b = self.open.pop(i)
                    b["inner_end"] = self.pos()
                    inner = self.text[b["inner"]:b["inner_end"]]
                    if b["leaf"] and "{{" not in inner and "<!--" not in inner and inner.strip():
                        self.found.append(b)
                    break


def blocks(text):
    return sorted(Blocks(text).found, key=lambda b: b["inner"])


def annotate(text, found):
    """The source with data-edit="<n>" on each editable element's start tag."""
    out, last = [], 0
    for n, b in enumerate(found):
        out += [text[last:b["tag_end"]], f' data-edit="{n}"']
        last = b["tag_end"]
    return "".join(out + [text[last:]])


def merge(S, R, N):
    """Apply the browser's edit R -> N to the source S of the same element.

    R is the element as the browser serialized it when the page loaded, N as it is now. R differs from S only in
    spelling (entities, attribute order), so each changed span of R is mapped onto S and only that span is rewritten.
    """
    if R == N:
        return S
    rs = [None] * (len(R) + 1)
    for a, b, size in SequenceMatcher(None, R, S, autojunk=False).get_matching_blocks():
        for k in range(size):
            rs[a + k] = b + k
    if sum(x is not None for x in rs[:-1]) < 0.7 * len(R):
        raise ValueError("this element's source differs too much from how the browser shows it")

    def clean(i):  # a cut between R[i-1] and R[i] lands on one exact point of S
        return i == 0 or i == len(R) or (rs[i - 1] is not None and rs[i] is not None and rs[i] == rs[i - 1] + 1)

    def s_at(i):
        return 0 if i == 0 else len(S) if i == len(R) else rs[i]

    hunks = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, R, N, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        while not clean(i1):
            i1, j1 = i1 - 1, j1 - 1
        while not clean(i2):
            i2, j2 = i2 + 1, j2 + 1
        if hunks and i1 <= hunks[-1][1]:  # overlaps the previous change: one change
            p1, _, q1, _ = hunks.pop()
            i1, j1 = p1, q1
        hunks.append([i1, i2, j1, j2])
    for i1, i2, j1, j2 in reversed(hunks):
        new = N[j1:j2]
        old = S[s_at(i1):s_at(i2)]
        if "&nbsp;" not in old:
            new = new.replace("&nbsp;", " ")  # the browser types non-breaking spaces at the ends of words
        S = S[:s_at(i1)] + new + S[s_at(i2):]
    return S


CLIENT = r"""
<style>
[data-edit]{outline:1px dashed transparent;outline-offset:3px;border-radius:2px;transition:outline-color .15s}
[data-edit]:hover{outline-color:#c9c9cf}
[data-edit]:focus{outline:2px solid #a31f34;outline-offset:3px}
[data-edit].edited{background:#fff6d6;box-shadow:0 0 0 3px #fff6d6}
mjx-container[contenteditable=false]{cursor:default}
#edit-bar{position:fixed;right:16px;bottom:16px;z-index:9999;display:flex;gap:10px;align-items:center;
  font:500 13px/1 -apple-system,BlinkMacSystemFont,"Inter",sans-serif;background:#1d1d1f;color:#fff;
  padding:10px 10px 10px 14px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.25)}
#edit-bar button{font:inherit;border:0;border-radius:8px;padding:7px 12px;cursor:pointer;background:#3a3a3c;color:#fff}
#edit-bar button.primary{background:#a31f34}
#edit-bar button:disabled{opacity:.45;cursor:default}
</style>
<div id="edit-bar"><span id="edit-status">Edit mode: click any text</span>
<button id="edit-revert" disabled>Revert</button><button id="edit-save" class="primary" disabled>Save</button></div>
<script>
(() => {
  const VERSION = "__VERSION__";
  const els = [...document.querySelectorAll("[data-edit]")];
  const base = new Map(), dirty = new Set(), ownSpans = new WeakSet();
  const status = document.getElementById("edit-status");
  const save = document.getElementById("edit-save"), revert = document.getElementById("edit-revert");

  function texOf(el) {  // the element's inner HTML with every typeset formula put back as its LaTeX source
    const items = window.MathJax && MathJax.startup && MathJax.startup.document
      ? MathJax.startup.document.getMathItemsWithin(el) : [];
    const tex = new Map(items.map(m => [m.typesetRoot,
      (m.start.delim || (m.display ? "\\[" : "\\(")) + m.math + (m.end.delim || (m.display ? "\\]" : "\\)"))]));
    el.querySelectorAll("span[style]").forEach(s => { if (!ownSpans.has(s)) s.replaceWith(...s.childNodes); });
    const clone = el.cloneNode(true);
    const live = [...el.querySelectorAll("mjx-container")], copies = [...clone.querySelectorAll("mjx-container")];
    live.forEach((c, i) => copies[i].replaceWith(document.createTextNode(tex.get(c) ?? "")));
    clone.querySelectorAll("[contenteditable]").forEach(x => x.removeAttribute("contenteditable"));
    let html = clone.innerHTML;
    if (!base.has(el)) return html;
    return html.replace(/<br>$/, base.get(el).endsWith("<br>") ? "<br>" : "");
  }

  function update() {
    save.disabled = revert.disabled = !dirty.size;
    status.textContent = dirty.size ? `${dirty.size} unsaved change${dirty.size > 1 ? "s" : ""}` : "Edit mode: click any text";
  }

  function start() {
    els.forEach(el => {
      el.querySelectorAll("span[style]").forEach(s => ownSpans.add(s));
      el.querySelectorAll("mjx-container").forEach(m => m.setAttribute("contenteditable", "false"));
      base.set(el, texOf(el));
      el.contentEditable = "true";
      el.spellcheck = true;
      el.addEventListener("input", () => {
        texOf(el) === base.get(el) ? (dirty.delete(el), el.classList.remove("edited")) : (dirty.add(el), el.classList.add("edited"));
        update();
      });
      el.addEventListener("keydown", e => { if (e.key === "Enter") e.preventDefault(); });  // one element stays one element
      el.addEventListener("paste", e => {  // paste as plain text
        e.preventDefault();
        document.execCommand("insertText", false, (e.clipboardData.getData("text/plain") || "").replace(/\s*\n\s*/g, " "));
      });
      el.addEventListener("click", e => { if (e.target.closest("a")) e.preventDefault(); });
    });
    document.querySelectorAll("summary").forEach(s => s.addEventListener("click", e => {
      if (e.target.closest("[data-edit]")) e.preventDefault();
    }));
    update();
  }

  async function doSave() {
    if (!dirty.size) return;
    const edits = [...dirty].map(el => ({ id: +el.dataset.edit, before: base.get(el), after: texOf(el) }));
    status.textContent = "Saving…";
    const r = await fetch("/__save", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ version: VERSION, edits }) });
    const out = await r.json();
    if (!r.ok) { status.textContent = "Not saved"; alert(out.error); update(); return; }
    sessionStorage.setItem("edit-scroll", String(scrollY));
    location.reload();
  }

  save.onclick = doSave;
  revert.onclick = () => { if (confirm("Discard unsaved changes?")) location.reload(); };
  addEventListener("keydown", e => { if ((e.metaKey || e.ctrlKey) && e.key === "s") { e.preventDefault(); doSave(); } });
  addEventListener("beforeunload", e => { if (dirty.size && status.textContent !== "Saving…") e.preventDefault(); });
  const y = sessionStorage.getItem("edit-scroll");
  if (y) { sessionStorage.removeItem("edit-scroll"); requestAnimationFrame(() => scrollTo(0, +y)); }
  const ready = () => window.MathJax && MathJax.startup && MathJax.startup.promise;
  (function wait(n) { ready() ? MathJax.startup.promise.then(start) : n > 0 ? setTimeout(() => wait(n - 1), 100) : start(); })(100);
})();
</script>
"""


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "posts/repairing-quantized-llm.html"
    page = next((p for p in build.PAGES if p[0] == src), None)
    if not page:
        sys.exit(f"{src} is not in PAGES in tools/build.py; pages: " + ", ".join(p[0] for p in build.PAGES))
    path, url = build.SRC / src, "/" + page[1].removesuffix("index.html")
    quiet_build = lambda: contextlib.redirect_stdout(io.StringIO())
    with quiet_build():
        build.main()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(build.ROOT / "site"), **k)

        def log_message(self, *a):
            pass

        def send(self, code, body, kind="text/html; charset=utf-8"):
            data = body.encode()
            self.send_response(code)
            self.send_header("content-type", kind)
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", ""):
                self.send_response(302)
                self.send_header("location", url)
                self.end_headers()
            elif self.path.split("?")[0] in (url, url + "index.html"):
                text = path.read_text()
                version = hashlib.sha1(text.encode()).hexdigest()
                html = build.full_page(build.render(src, page[2], page[3], page[4], annotate(text, blocks(text))))
                html = html.replace("<!--FAVICON-->", build.FAVICON)
                self.send(200, html.replace("</body>", CLIENT.replace("__VERSION__", version) + "</body>", 1))
            else:
                super().do_GET()

        def do_POST(self):
            if self.path != "/__save" or self.headers.get("origin", f"http://localhost:{PORT}") not in (
                    f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
                return self.send(403, json.dumps({"error": "forbidden"}), "application/json")
            body = json.loads(self.rfile.read(int(self.headers["content-length"])))
            text = path.read_text()
            if hashlib.sha1(text.encode()).hexdigest() != body["version"]:
                return self.send(409, json.dumps({"error": f"{src} changed on disk since this page loaded. "
                                                  "Copy your edits, then reload."}), "application/json")
            found = blocks(text)
            try:
                for e in sorted(body["edits"], key=lambda e: -e["id"]):  # from the end, so offsets stay valid
                    b = found[e["id"]]
                    inner = merge(text[b["inner"]:b["inner_end"]], e["before"], e["after"])
                    text = text[:b["inner"]] + inner + text[b["inner_end"]:]
            except (ValueError, IndexError) as err:
                return self.send(400, json.dumps({"error": f"Not saved: {err}."}), "application/json")
            path.write_text(text)
            with quiet_build():
                build.main()  # keep site/ current for the other pages and for a plain preview
            print(f"saved {len(body['edits'])} change(s) to src/{src}", flush=True)
            self.send(200, json.dumps({"ok": True}), "application/json")

    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Editing src/{src}\nOpen http://localhost:{PORT}{url}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
