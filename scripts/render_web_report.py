#!/usr/bin/env python3
"""Render a Cricket Markdown report as a standalone, mobile-friendly HTML page."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
URL_RE = re.compile(r"(?<![\"=>])(https?://[^\s<]+)")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def inline_markup(value: str) -> str:
    """Escape report text while retaining the report's direct listing links."""
    parts: list[str] = []
    position = 0
    for match in LINK_RE.finditer(value.strip()):
        parts.append(linkify_plain_text(value[position : match.start()]))
        label, url = match.groups()
        parts.append('<a href="%s" target="_blank" rel="noreferrer">%s</a>' % (html.escape(url, quote=True), html.escape(label)))
        position = match.end()
    parts.append(linkify_plain_text(value[position:]))
    return "".join(parts)


def linkify_plain_text(value: str) -> str:
    escaped = html.escape(value)
    escaped = URL_RE.sub(r'<a href="\1" target="_blank" rel="noreferrer">\1</a>', escaped)
    return INLINE_CODE_RE.sub(r"<code>\1</code>", escaped)


def is_table_divider(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def table_row(line: str, tag: str) -> str:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return "<tr>%s</tr>" % "".join("<%s>%s</%s>" % (tag, inline_markup(cell), tag) for cell in cells)


def render_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            close_list()
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and is_table_divider(lines[index + 1]):
            close_list()
            output.append('<div class="table-wrap"><table>')
            output.append("<thead>%s</thead>" % table_row(line, "th"))
            output.append("<tbody>")
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                output.append(table_row(lines[index], "td"))
                index += 1
            output.append("</tbody></table></div>")
            continue

        if stripped.startswith("### "):
            close_list()
            output.append("<h3>%s</h3>" % inline_markup(stripped[4:]))
        elif stripped.startswith("## "):
            close_list()
            output.append("<h2>%s</h2>" % inline_markup(stripped[3:]))
        elif stripped.startswith("# "):
            close_list()
            output.append("<h1>%s</h1>" % inline_markup(stripped[2:]))
        elif stripped.startswith("- "):
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append("<li>%s</li>" % inline_markup(stripped[2:]))
        else:
            close_list()
            output.append("<p>%s</p>" % inline_markup(stripped).replace("  ", "<br>"))
        index += 1

    close_list()
    return "\n".join(output)


def document(title: str, body: str) -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Cricket's daily used Subaru Crosstrek search report.">
  <title>%s | Cricket</title>
  <style>
    :root { color-scheme: light; --ink: #172028; --muted: #5e6b75; --line: #d8e0e3; --paper: #ffffff; --page: #f3f6f5; --green: #156046; --green-pale: #e4f1ea; --blue: #075985; }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--page); color: var(--ink); font: 16px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header { background: #123b31; color: white; border-bottom: 4px solid #75b798; }
    .masthead, main { width: min(1120px, calc(100%% - 32px)); margin: 0 auto; }
    .masthead { padding: 22px 0 20px; display: flex; align-items: baseline; gap: 16px; }
    .brand { font-size: 1.35rem; font-weight: 750; letter-spacing: .02em; }
    .tagline { color: #cbe5d6; font-size: .95rem; }
    main { margin-top: 28px; margin-bottom: 48px; background: var(--paper); padding: clamp(20px, 4vw, 44px); border: 1px solid var(--line); box-shadow: 0 8px 24px rgba(23, 32, 40, .06); }
    h1, h2, h3 { line-height: 1.2; }
    h1 { margin: 0 0 24px; font-size: clamp(1.7rem, 4vw, 2.45rem); }
    h2 { margin: 40px 0 14px; padding-top: 12px; border-top: 1px solid var(--line); font-size: 1.45rem; }
    h3 { margin: 32px 0 12px; font-size: 1.15rem; color: var(--green); }
    p { margin: 10px 0; }
    h2 + p { font-size: 1.05rem; }
    ul { margin: 10px 0 18px; padding-left: 1.3rem; }
    li { margin: 6px 0; }
    a { color: var(--blue); text-underline-offset: 2px; }
    a:hover { color: #0c4a6e; }
    code { padding: 2px 5px; background: #eef3f5; border-radius: 3px; }
    .table-wrap { overflow-x: auto; margin: 14px 0 22px; border: 1px solid var(--line); border-radius: 6px; }
    table { width: 100%%; border-collapse: collapse; min-width: 880px; font-size: .9rem; }
    th, td { padding: 9px 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
    th { background: #edf5f0; color: #183a2d; font-weight: 700; white-space: nowrap; }
    tbody tr:nth-child(even) { background: #fafcfc; }
    tbody tr:last-child td { border-bottom: 0; }
    @page { size: letter; margin: .45in; }
    @media print {
      body { background: white; font-size: 9pt; }
      header { background: white; color: var(--ink); border-bottom: 2px solid #75b798; }
      .masthead, main { width: 100%%; margin: 0; }
      .masthead { padding: 0 0 10px; }
      .tagline { color: var(--muted); }
      main { border: 0; box-shadow: none; padding: 14px 0 0; }
      h1 { font-size: 20pt; margin-bottom: 14px; }
      h2 { margin-top: 24px; font-size: 14pt; break-after: avoid; }
      h3 { margin-top: 20px; font-size: 11pt; break-after: avoid; }
      .table-wrap { overflow: visible; margin: 8px 0 14px; }
      table { min-width: 0; font-size: 6.8pt; }
      th, td { padding: 4px; }
      tr, img { break-inside: avoid; }
      a { color: var(--ink); text-decoration: none; }
    }
    @media (max-width: 640px) { .masthead, main { width: min(100%% - 22px, 1120px); } .masthead { display: block; padding: 16px 0; } .tagline { margin-top: 3px; } main { margin-top: 12px; padding: 20px 14px; } h2 { margin-top: 30px; } }
  </style>
</head>
<body>
  <header><div class="masthead"><div class="brand">Cricket</div><div class="tagline">Daily used Subaru Crosstrek search</div></div></header>
  <main>%s</main>
</body>
</html>
""" % (html.escape(title), body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Markdown report to publish")
    parser.add_argument("--output", type=Path, default=Path("docs/index.html"), help="HTML output path")
    args = parser.parse_args()

    report_text = args.report.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document(args.report.stem, render_markdown(report_text)), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
