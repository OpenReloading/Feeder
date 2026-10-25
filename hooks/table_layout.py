"""Phone layout for tables and inline code, applied to each page's HTML at build time.

Inline code gets a <wbr> after each dot between names (`case_plate.pocket_clearance`), so it wraps there and not mid-word.
A table with a long cell gets `data-stack` and a `data-label` (its column header) on every cell: guide/stylesheets/extra.css
shows it as one block per row on a phone.
"""

import re

STACK_FROM = 60  # characters in the longest cell

CODE = re.compile(r"(?<!<pre>)<code>([^<]*)</code>")
DOT = re.compile(r"(?<=[A-Za-z_])\.(?=[A-Za-z_])")
TABLE = re.compile(r"<table>(.*?)</table>", re.S)
HEAD = re.compile(r"<th[^>]*>(.*?)</th>", re.S)
CELL = re.compile(r"<td([^>]*)>(.*?)</td>", re.S)
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
TAG = re.compile(r"<[^>]+>")


def text(fragment: str) -> str:
    return TAG.sub("", fragment).strip()


def stack(table: re.Match) -> str:
    body = table.group(1)
    head, _, rows = body.partition("</thead>")
    labels = [text(h).replace('"', "&quot;") for h in HEAD.findall(head)]
    if not labels or max((len(text(c)) for _, c in CELL.findall(rows)), default=0) < STACK_FROM:
        return table.group(0)

    def row(match: re.Match) -> str:
        n = iter(labels)
        return "<tr>" + CELL.sub(lambda c: f'<td{c.group(1)} data-label="{next(n, "")}">{c.group(2)}</td>', match.group(1)) + "</tr>"

    return f"<table data-stack>{head}</thead>{ROW.sub(row, rows)}</table>"


def on_page_content(html, **_):
    html = CODE.sub(lambda m: "<code>" + DOT.sub(".<wbr>", m.group(1)) + "</code>", html)
    return TABLE.sub(stack, html)
