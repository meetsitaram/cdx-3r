"""Build the README motion animation from out/motion/m_NNN.png (rendered by motion.frames) + labels.json.
Writes docs/images/cdx3r-motion.gif (and .mp4 if ffmpeg is on PATH). Run: python cad/fusion/render/mkmotion.py
"""
import glob
import json
import os
import shutil
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'out', 'motion')
DOCS = os.path.join(HERE, '..', '..', '..', 'docs', 'images')
W = 640
STEP = 2                       # every other rendered frame keeps the GIF small

fs = sorted(glob.glob(os.path.join(SRC, 'm_*.png')))[::STEP]
labels = json.load(open(os.path.join(SRC, 'labels.json')))[::STEP]
ims = [Image.open(f).convert('RGB') for f in fs]
box = None
for im in ims[::4]:
    b = ImageChops.difference(im, Image.new('RGB', im.size, 'white')).convert('L').point(lambda v: 255 if v > 10 else 0).getbbox()
    box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
pad = 20
box = (max(0, box[0] - pad), max(0, box[1] - pad), min(ims[0].width, box[2] + pad), min(ims[0].height, box[3] + pad))
try:
    FONT = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 26)
except OSError:
    FONT = ImageFont.load_default()
frames, dur = [], []
for i, im in enumerate(ims):
    im = im.crop(box)
    s = W / im.width
    im = im.resize((W, int(im.height * s)), Image.LANCZOS)
    c = Image.new('RGB', (W, im.height + 48), 'white')
    c.paste(im, (0, 48))
    d = ImageDraw.Draw(c)
    d.rectangle([0, 0, W, 44], fill=(32, 41, 51))
    d.text((16, 22), labels[i] if i < len(labels) else '', font=FONT, fill='white', anchor='lm')
    frames.append(c)
    hold = i + 1 < len(labels) and labels[i + 1] != labels[i]
    dur.append(800 if hold else 120)
os.makedirs(DOCS, exist_ok=True)
gif = os.path.join(DOCS, 'cdx3r-motion.gif')
pal = [f.quantize(colors=96, method=Image.MEDIANCUT, dither=Image.NONE) for f in frames]
pal[0].save(gif, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
print('gif', len(frames), frames[0].size, '%.1f MB' % (os.path.getsize(gif) / 1e6))
ff = shutil.which('ffmpeg')
if ff:
    tmp = os.path.join(SRC, 'mp4')
    os.makedirs(tmp, exist_ok=True)
    n = 0
    for f, ms in zip(frames, dur):                     # expand holds into repeated frames at 25 fps
        for _ in range(max(1, round(ms / 40))):
            f.save(os.path.join(tmp, 'f_%04d.png' % n)); n += 1
    mp4 = os.path.join(DOCS, 'cdx3r-motion.mp4')
    subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', '25', '-i', os.path.join(tmp, 'f_%04d.png'),
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-crf', '23', mp4],
                   check=True)
    shutil.rmtree(tmp)
    print('mp4', '%.1f MB' % (os.path.getsize(mp4) / 1e6))
else:
    print('no ffmpeg: mp4 not updated')

# README stills (motion.stills): trim the white margin, 1400 px wide max
for name in ('exo-on-body-back', 'exo-on-body-front', 'shoulder-close', 'elbow-close'):
    p = os.path.join(SRC, name + '.png')
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert('RGB')
    b = ImageChops.difference(im, Image.new('RGB', im.size, 'white')).convert('L').point(lambda v: 255 if v > 10 else 0).getbbox()
    im = im.crop((max(0, b[0] - 30), max(0, b[1] - 30), min(im.width, b[2] + 30), min(im.height, b[3] + 30)))
    if im.width > 1400:
        im = im.resize((1400, int(im.height * 1400 / im.width)), Image.LANCZOS)
    im.save(os.path.join(DOCS, name + '.png'), optimize=True)
    print('still', name, im.size)
