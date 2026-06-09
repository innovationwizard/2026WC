#!/usr/bin/env python3
"""
Convert THE_JOURNEY.md → web/static/the-journey.html (HTML fragment) for the unlisted
/la-caceria page. Minimal markdown (headers, hr, blockquote, table, lists, bold/em/code).
Build-time only — no runtime dependency, no pip install.

Run:  .venv/bin/python web/scripts/build_journey.py
"""
import os, re, html

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'THE_JOURNEY.md')
OUT = os.path.join(ROOT, 'web', 'static', 'the-journey.html')


def inline(s):
    s = html.escape(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'<em>\1</em>', s)
    s = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', s)
    return s


def convert(md):
    lines = md.split('\n')
    out, para, i, n = [], [], 0, len(lines)

    def flush():
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para.clear()

    while i < n:
        line = lines[i].rstrip()
        if not line.strip():
            flush(); i += 1; continue
        if re.match(r'^---+$', line.strip()):
            flush(); out.append('<hr>'); i += 1; continue
        h = re.match(r'^(#{1,3})\s+(.*)$', line)
        if h:
            flush(); lvl = len(h.group(1)); out.append(f'<h{lvl}>{inline(h.group(2))}</h{lvl}>'); i += 1; continue
        if line.lstrip().startswith('>'):
            flush(); buf = []
            while i < n and lines[i].lstrip().startswith('>'):
                buf.append(re.sub(r'^\s*>\s?', '', lines[i])); i += 1
            out.append('<blockquote>' + inline(' '.join(b.strip() for b in buf)) + '</blockquote>'); continue
        if line.lstrip().startswith('|'):
            flush(); rows = []
            while i < n and lines[i].lstrip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            cells = [[c.strip() for c in r.strip('|').split('|')] for r in rows]
            cells = [c for c in cells if not all(re.match(r'^:?-+:?$', x.strip() or '-') for x in c)]
            if cells:
                t = '<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells[0]) + '</tr></thead><tbody>'
                for r in cells[1:]:
                    t += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                out.append(t + '</tbody></table>')
            continue
        if re.match(r'^\s*[-*]\s+', line):
            flush(); items = []
            while i < n and re.match(r'^\s*[-*]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*]\s+', '', lines[i].strip())); i += 1
            out.append('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>'); continue
        para.append(line.strip()); i += 1
    flush()
    return '\n'.join(out)


def main():
    with open(SRC, encoding='utf-8') as f:
        md = f.read()
    frag = convert(md)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(frag)
    print(f"wrote {OUT} ({len(frag)} chars)")


if __name__ == '__main__':
    main()
