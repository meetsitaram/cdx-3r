import sys
from PIL import Image
name = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
ims = [Image.open('asm/%s_%03d.png' % (name, f)).convert('RGB') for f in frames]
cols = 3; sc = 0.55
w, h = int(ims[0].width * sc), int(ims[0].height * sc)
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (w * cols, h * rows), 'white')
for i, im in enumerate(ims):
    S.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
S.save(out)
