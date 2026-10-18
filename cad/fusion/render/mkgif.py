import glob, os
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HERE, 'out'))
OUT = os.path.join(HERE, '..', '..', '..', 'docs', 'images', 'assembly')
os.makedirs(OUT, exist_ok=True)
CAP = {
 '2-frame': (10, [
  'Right half of the bottom node',
  'Left half of the bottom node',
  'Melt in 8 brass inserts',
  'Put the splice plate over the joint',
  'Screw it together (8 x M3 x 8)',
  'Backbones: left 412 mm, right 583 mm',
  'Slide on the middle node',
  'Slide on the top node',
  'Left beam (102 mm) and left diagonal (131 mm)',
  'Push on the left block (battery mount)',
  'Stick on the back pads (hook-and-loop)']),
 '3-tower': (10, [
  'Melt 4 inserts into the top node end',
  'Hold the tower above the frame',
  'Nuts first: 2 M6 nuts into their pockets (tape them)',
  'Slide the tower down over the pipe and node',
  'Screw the saddle on (4 x M3 x 8)',
  '2 pipe screws into the backbone']),
 '4-lift': (10, [
  'Upper lift link',
  'Press in its 2 bearings (608) each end',
  'Lower lift link',
  'Press in its bearings',
  'Drop both links into the tower fork',
  '2 bolts (M8 x 55) in from the front',
  'Lock nuts on the back',
  'Carriage',
  'Nuts first: S0 nut down the top hole, M6 nut behind the ear',
  'Lift the carriage onto the link ends',
  '2 bolts (M8 x 55) in from the back, down the tunnels',
  'Lock nuts on the front',
  'Squeeze the strut a little, drop its eyelets into the 2 fork slots, let go',
  'Thumb screw through each fork + eyelet, hand tight']),
 '4b-strut': (10, [
  'Squeeze the strut, drop each eyelet into its fork slot, let go',
  'Thumb screw through fork + eyelet into the hidden M6 nut, hand tight']),
 '5-scara': (10, [
  'Link 1 tray',
  'Press in 2 bearings (608)',
  'Melt in 4 inserts',
  'Pulleys + spacers onto the bearings',
  'Belt around both pulleys',
  'Lid (with its 2 bearings) on top',
  'Screw the lid down (4 x M3 x 12)',
  'Lift link 1 under the carriage',
  'Thin spacer between them',
  'S0 bolt (M8 x 55) up from below',
  'Link 2 tray',
  'Press in 2 bearings',
  'Melt in 4 inserts',
  'Pulleys + spacers onto the bearings',
  'Belt around both pulleys',
  'Lid (with its 2 bearings) underneath',
  'Screw the lid on (4 x M3 x 12)',
  'Lift link 2 under link 1',
  'Thin spacer between the links',
  'Thin spacer on top',
  'Elbow bolt (M8 x 100 cut to 75) down through both',
  'Spacer + lock nut underneath',
  'End plate',
  'Nut first: lock nut into the pocket on top',
  'Lift the end plate under link 2',
  'Thin spacer between them',
  'Thin spacer on top',
  'E bolt (M8 x 55) down into the nut']),
 '6-hinge': (10, [
  'Press 2 bearings (6806) into the housing',
  'Abduction sleeve through both bearings',
  'Yoke against the front bearing',
  'Long bolt (M8 x 100) in from the front',
  'Big washer (32 mm) on the back',
  'Lock nut on the back, tighten',
  'Press a bearing (6808) into each side of the yoke end',
  'Flexion sleeve through both bearings',
  'Arm link',
  'Nut first: lock nut into its hex pocket',
  'Arm link over the yoke end',
  'Bolt (M8 x 55) in and tighten']),
 '7-rest': (10, [
  'Bracket over the round boss on the tower',
  'Thumb screw through the slot (leave loose)',
  'Root arm onto the bracket',
  'Pin it (clevis pin)',
  'R-clip',
  'Blade 1',
  'Pin it',
  'R-clip',
  'Blade 2',
  'Pin it',
  'R-clip',
  'Blade 3',
  'Pin it',
  'R-clip',
  'Foam pads on with hook-and-loop',
  'Buckle onto the front tab']),
 '8-join': (16, ['Push the upper-arm pipes into the arm link']),
}
try:
    FONT = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 30)
    SMALL = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
except OSError:
    FONT = SMALL = ImageFont.load_default()

for name, (nfly, caps) in CAP.items():
    fs = sorted(glob.glob('asm/%s_*.png' % name))
    ims = [Image.open(f).convert('RGB') for f in fs]
    # crop to the action: every pixel that differs from the finished frame, plus the finished parts around it
    last = ims[-1]
    bbox = None
    for im in ims[:-1]:
        b = ImageChops.difference(im, last).convert('L').point(lambda v: 255 if v > 24 else 0).getbbox()
        if b:
            bbox = b if bbox is None else (min(bbox[0], b[0]), min(bbox[1], b[1]), max(bbox[2], b[2]), max(bbox[3], b[3]))
    W0, H0 = ims[0].size
    if bbox is None:
        bbox = (0, 0, W0, H0)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padx, pady = max(40, int(bw * 0.12)), max(40, int(bh * 0.12))
    bbox = [bbox[0] - padx, bbox[1] - pady, bbox[2] + padx, bbox[3] + pady]
    # at least 4:3, never taller than 1:1.2
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if bw < bh / 1.2:
        g = (bh / 1.2 - bw) / 2; bbox[0] -= g; bbox[2] += g
    elif bw > bh * 1.6:
        g = (bw / 1.6 - bh) / 2; bbox[1] -= g; bbox[3] += g
    bbox = (int(max(0, bbox[0])), int(max(0, bbox[1])), int(min(W0, bbox[2])), int(min(H0, bbox[3])))
    frames, dur = [], []
    ng = len(caps)
    for f, im in enumerate(ims):
        im = im.crop(bbox)
        s = 620 / max(im.size)
        im = im.resize((int(im.size[0] * s), int(im.size[1] * s)), Image.LANCZOS)
        cw = max(im.size[0], 620)
        canvas = Image.new('RGB', (cw, im.size[1] + 70), 'white')
        canvas.paste(im, ((cw - im.size[0]) // 2, 70))
        d = ImageDraw.Draw(canvas)
        gi = min(f // nfly, ng - 1)
        done = f >= ng * nfly
        label = 'Done!' if done and ng > 1 else caps[gi]
        num = '' if ng == 1 or done else '%d / %d   ' % (gi + 1, ng)
        d.rectangle([0, 0, cw, 58], fill=(32, 41, 51))
        x = 16
        if num:
            d.text((x, 14), num, font=SMALL, fill=(255, 204, 64)); x += d.textlength(num, font=SMALL)
        fnt = FONT
        while d.textlength(label, font=fnt) > cw - x - 16 and fnt.size > 22:
            fnt = ImageFont.truetype(fnt.path, fnt.size - 2)
        d.text((x, 29), label, font=fnt, fill='white', anchor='lm')
        frames.append(canvas)
        last_of_group = (f % nfly) == nfly - 1 and not done
        dur.append(1600 if last_of_group else (2500 if f == len(ims) - 1 else (60 if not done else 100)))
    pal = [fr.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE) for fr in frames]
    out = os.path.join(OUT, 'step%s.gif' % name)
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=dur, loop=0, optimize=True, disposal=1)
    print(name, len(frames), frames[0].size, '%.1f MB' % (os.path.getsize(out) / 1e6))
