"""Add the review-comment button (tools/preview-comment.js) to every page of one PR preview.

    python3 tools/preview_comments.py site/pr-preview/pr-<n> <n> <owner/repo>

The deploy workflow runs this from main after building each pull request, so the live site never gets the button
and a pull request cannot change it. The script itself is copied once to site/pr-preview/comment.js.
"""
import html
import pathlib
import sys


def main():
    root, pr, repo = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    tag = (f'<script src="/pr-preview/comment.js" data-pr="{html.escape(pr)}" '
           f'data-repo="{html.escape(repo)}" defer></script>\n')
    for page in root.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        cut = text.rfind("</body>")
        page.write_text(text[:cut] + tag + text[cut:] if cut >= 0 else text + tag, encoding="utf-8")


if __name__ == "__main__":
    main()
