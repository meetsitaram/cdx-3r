"""Frames folder (f00.png.., captions.txt) -> a captioned GIF for docs/ASSEMBLY.md and a self-contained HTML page (the
user reviews on a phone: publish it as an Artifact).

    python mkpage.py <frames_dir> <gif_out> <html_out> "<title>" "<subtitle>"
"""
import base64
import io
import json
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont


def crop_box(ims, pad=24):
    box = None
    for im in ims:
        bg = Image.new('RGB', im.size, im.getpixel((0, 0)))
        b = ImageChops.difference(im, bg).getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    w, h = ims[0].size
    return (max(0, box[0] - pad), max(0, box[1] - pad), min(w, box[2] + pad), min(h, box[3] + pad))


def main(src, gif_out, html_out, title, sub):
    fs = sorted(f for f in os.listdir(src) if f.startswith('f') and f.endswith('.png'))
    caps = open(os.path.join(src, 'captions.txt'), encoding='utf-8').read().splitlines()
    ims = [Image.open(os.path.join(src, f)).convert('RGB') for f in fs]
    box = crop_box(ims)
    ims = [im.crop(box) for im in ims]
    try:
        font = ImageFont.truetype('segoeui.ttf', 22)
    except OSError:
        font = ImageFont.load_default()
    frames = []
    for im, cap in zip(ims, caps):
        fr = Image.new('RGB', (im.width, im.height + 46), 'white')
        fr.paste(im, (0, 46))
        ImageDraw.Draw(fr).text((14, 10), cap, fill=(30, 30, 30), font=font)
        frames.append(fr)
    pal = [fr.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE) for fr in frames]
    os.makedirs(os.path.dirname(gif_out), exist_ok=True)
    pal[0].save(gif_out, save_all=True, append_images=pal[1:], duration=900, loop=0, optimize=True, disposal=1)
    uris = []
    for im in ims:
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=85)
        uris.append('data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode())
    page = PAGE.replace('@TITLE@', title).replace('@SUB@', sub).replace('@N@', str(len(uris) - 1))
    page = page.replace('@F@', json.dumps(uris)).replace('@C@', json.dumps(caps[:len(uris)]))
    open(html_out, 'w', encoding='utf-8').write(page)
    return len(frames)


PAGE = '''<title>@TITLE@</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{--bg:#f3f1ee;--fg:#1f1d1a;--muted:#6b645b;--card:#ffffff;--line:#e0dad2;--accent:#c4661c;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#181715;--fg:#eeeae4;--muted:#a59e94;--card:#ffffff;--line:#3a3631;--accent:#e08a3c;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#181715;--fg:#eeeae4;--muted:#a59e94;--card:#ffffff;--line:#3a3631;--accent:#e08a3c;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:16px}
main{max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:12px}
h1{font-size:21px;margin:0;text-wrap:balance}
.sub{color:var(--muted);margin:0;font-size:13px;max-width:65ch}
.view{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.view img{display:block;width:100%;height:auto}
.cap{font-size:16px;font-weight:600;min-height:3em;margin:0}
.ctl{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
button{font:inherit;border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:8px;padding:8px 12px;min-width:44px;cursor:pointer}
button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
input[type=range]{flex:1;min-width:160px;accent-color:var(--accent)}
</style>
<main>
  <h1>@TITLE@</h1>
  <p class="sub">@SUB@</p>
  <div class="view"><img id="img" alt="Animation frame"></div>
  <p class="cap" id="cap"></p>
  <div class="ctl"><button id="play">Pause</button><input id="k" type="range" min="0" max="@N@" step="1" value="0" aria-label="Frame"></div>
</main>
<script>
const F=@F@, C=@C@; let k=0, on=true, t=null;
const img=document.getElementById('img'), cap=document.getElementById('cap'), sl=document.getElementById('k'), pb=document.getElementById('play');
function draw(){img.src=F[k];cap.textContent=C[k];sl.value=k;}
function tick(){k=(k+1)%F.length;draw();}
function setPlay(v){on=v;pb.textContent=v?'Pause':'Play';clearInterval(t);if(v)t=setInterval(tick,900);}
pb.onclick=()=>setPlay(!on); sl.oninput=()=>{setPlay(false);k=+sl.value;draw();};
draw(); setPlay(!matchMedia('(prefers-reduced-motion: reduce)').matches);
</script>
'''

if __name__ == '__main__':
    print(main(*sys.argv[1:6]))
