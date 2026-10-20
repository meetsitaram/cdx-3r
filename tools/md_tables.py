"""Markdown table lint: a table whose separator row (|---|---|) has a different column count from its header doesn't
render as a table on GitHub; it shows as a run of raw text (the PVC cut list, Oct 2026).

    python tools/md_tables.py [files...]     # check (default: every .md in the repo); exit 1 on a broken table
    python tools/md_tables.py --fix [files]  # rewrite each broken separator to match its header
"""
import glob
import re
import sys

SEP = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$')


def cols(line):
    return line.strip().strip('|').count('|') + 1


def check(path, fix=False):
    lines = open(path, encoding='utf-8').read().split('\n')
    bad = []
    for i in range(1, len(lines)):
        if SEP.match(lines[i]) and lines[i - 1].strip().startswith('|'):
            h, s = cols(lines[i - 1]), cols(lines[i])
            if h != s:
                bad.append((i + 1, h, s))
                if fix:
                    lines[i] = '|' + '---|' * h
            k = i + 1                                       # body rows: a short or long row breaks its line
            while k < len(lines) and lines[k].strip().startswith('|'):
                c = cols(lines[k].replace('\\|', ''))
                if c != h:
                    bad.append((k + 1, h, c))
                k += 1
    if fix and bad:
        open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    return bad


if __name__ == '__main__':
    args = sys.argv[1:]
    fix = '--fix' in args
    files = [a for a in args if a != '--fix'] or [f for f in glob.glob('**/*.md', recursive=True)]
    n = 0
    for f in files:
        for line, h, s in check(f, fix):
            n += 1
            print('%s:%d: table header has %d columns, this row %d%s' % (f, line, h, s, ' (fixed)' if fix else ''))
    sys.exit(1 if n and not fix else 0)
