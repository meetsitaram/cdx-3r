"""Assembly guide player: the step animations (docs/images/assembly/*.gif) as a page you can pause and step through.

GIFs can't be paused (on GitHub or in most viewers). This unpacks each GIF into frame sheets (JPEG atlases, <= 72 frames
each so phones decode them) and writes a page that plays them with play / pause / frame step / scrubber. Publish the
output folder as an Artifact (index.html + sheets/). Re-run after the GIFs are re-rendered.

    python tools/assembly_player.py <out_dir>
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIFS = os.path.join(ROOT, 'docs', 'images', 'assembly')
GUIDE = os.path.join(ROOT, 'docs', 'ASSEMBLY.md')
W = 400                      # frame width in the sheets (px)
COLS, PER_SHEET = 8, 72


def frames(path):
    im = Image.open(path)
    out = []
    try:
        while True:
            out.append((im.convert('RGB'), im.info.get('duration', 200)))
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return out


def titles():
    """GIF file -> the guide's step heading above it."""
    md = open(GUIDE, encoding='utf-8').read()
    out, head = {}, None
    for line in md.splitlines():
        if line.startswith('## '):
            head = line[3:].strip()
        m = re.search(r'images/assembly/([\w-]+\.gif)', line)
        if m and head:
            alt = re.search(r'!\[([^\]]*)\]', line)
            out[m.group(1)] = head if m.group(1) not in out else head
            out[m.group(1) + ':alt'] = alt.group(1) if alt else ''
    return out


def build(out_dir):
    os.makedirs(os.path.join(out_dir, 'sheets'), exist_ok=True)
    tt = titles()
    steps = []
    for f in sorted(os.listdir(GIFS)):
        if not f.endswith('.gif'):
            continue
        fr = frames(os.path.join(GIFS, f))
        w0, h0 = fr[0][0].size
        h = round(h0 * W / w0)
        sheets = []
        for k in range(0, len(fr), PER_SHEET):
            chunk = fr[k:k + PER_SHEET]
            rows = (len(chunk) + COLS - 1) // COLS
            sheet = Image.new('RGB', (COLS * W, rows * h), 'white')
            for i, (im, _) in enumerate(chunk):
                sheet.paste(im.resize((W, h), Image.LANCZOS), ((i % COLS) * W, (i // COLS) * h))
            name = 'sheets/%s_%d.jpg' % (f[:-4], k // PER_SHEET)
            sheet.save(os.path.join(out_dir, name), quality=78, optimize=True)
            sheets.append(dict(src=name, n=len(chunk)))
        title = tt.get(f, f[:-4])
        if any(x['title'] == title for x in steps):                  # a second animation in the same step
            title += ': ' + (tt.get(f + ':alt', '').split(':')[0] or 'close-up')
        steps.append(dict(id=f[:-4], title=title, alt=tt.get(f + ':alt', ''), w=W, h=h, cols=COLS,
                          per=PER_SHEET, sheets=sheets, dur=[d for _, d in fr]))
    page = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assembly_player.html'),
                encoding='utf-8').read().replace('__STEPS__', json.dumps(steps))
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(page)
    return steps


if __name__ == '__main__':
    st = build(sys.argv[1])
    print('%d steps, %d frames' % (len(st), sum(len(s['dur']) for s in st)))
