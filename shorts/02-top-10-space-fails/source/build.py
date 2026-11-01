import json, subprocess, os, re
from PIL import Image

os.makedirs('build', exist_ok=True)
VO = json.load(open('vo.json'))
S = {s['id']: s for s in VO['segs']}
END = 57.6
FW, FH = 1080, 810  # footage box
def W(sid, word):  # time of a word within a segment
    return next(w['s'] for w in S[sid]['words'] if w['w'].strip('.,?:!').lower().startswith(word.lower()))

# ---------------- edit decision list ----------------
# (type, source, src_start, duration, extra)
def seg_bounds(i, ids):
    return S[ids[i]]['s'] if i else 0.0
order = ['hook', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']
starts = [0.0] + [S[k]['s'] for k in order[1:]] + [END]
dur = {k: starts[i + 1] - starts[i] for i, k in enumerate(order)}

A17 = 'clips/alsj_a17v.1445023.mpg'
edl = []
def clip(src, ss, d, **kw): edl.append(dict(kind='clip', src=src, ss=ss, d=d, **kw))
def img(src, d, crop, z0=1.0, z1=1.12, pan=(0, 0)): edl.append(dict(kind='img', src=src, d=d, crop=crop, z0=z0, z1=z1, pan=pan))

h = dur['hook']; clip('clips/vanguard_tv3_newsreel_1957-12-09.mp4', 50.6, h / 3, audio=False)
clip('clips/alsj_a16v.1212952.mov', 24.2, h / 3); clip(A17, 64.6, h - 2 * (h / 3))
img('img/g3_crew.jpg', dur['10'], (0.1, 0.44, 0.94, 0.94), 1.0, 1.14)
d = dur['9'] / 3
img('img/toolbag1.jpg', d, (0.05, 0.0, 0.95, 0.92), 1.05, 1.15); img('img/toolbag2.jpg', d, (0.05, 0.0, 0.95, 0.92), 1.05, 1.18); img('img/toolbag3.jpg', dur['9'] - 2 * d, (0.1, 0.0, 1.0, 0.92), 1.05, 1.2)
clip('clips/alsj_a14v.1350811.rm', 54.0, dur['8'])
clip('clips/alsj_a16v.1212952.mov', 25.0 - (W('7', 'astronaut') - S['7']['s']), dur['7'])
img('img/mco_KSC-98pc1352.jpg', dur['6'], (0.1, 0.05, 0.9, 0.95), 1.0, 1.15)
clip('clips/vanguard_tv3_newsreel_1957-12-09.mp4', 51.0 - (W('5', 'exploded') - S['5']['s']), dur['5'], audio=False)
clip('clips/vanguard_tv3bu_newsreel_1958-02-06.mp4', 26.0, 1.55, audio=False)
clip('clips/vanguard_tv3bu_newsreel_1958-02-06.mp4', 53.0, dur['4'] - 1.55, audio=False, zoom=1.8)
clip('clips/alsj_a17v.1653558.mpg', 53.5 - (W('3', 'dirt') - S['3']['s']), dur['3'])
d1 = W('2', 'give') - S['2']['s']; d2 = W('2', 'nobody') - W('2', 'give')
img('img/a10_crew.jpg', d1, (0.0, 0.05, 1.0, 0.55), 1.0, 1.1); img('img/a10_cabin.jpg', d2, (0.0, 0.0, 1.0, 0.88), 1.0, 1.12); img('img/a10_stafford.jpg', dur['2'] - d1 - d2, (0.0, 0.0, 1.0, 0.82), 1.05, 1.15)
t_tw = W('1', 'twinkletoes'); a = 50.54 - S['1']['s']
sB = 65.3 - (t_tw - 50.54)
clip(A17, 20.0, a); clip(A17, sB, 54.0 - 50.54); clip(A17, sB + (54.0 - 50.54), END - 54.0)
# fix last clip duration to land on END exactly
tot = sum(e['d'] for e in edl); edl[-1]['d'] += END - tot

# ---------------- render pieces ----------------
FPS = 30
pieces = []; t = 0.0; frame_t = 0
for i, e in enumerate(edl):
    nfr = round((t + e['d']) * FPS) - round(t * FPS)
    out = f'build/p{i:02d}.mp4'
    if e['kind'] == 'clip':
        z = e.get('zoom', 1.0)
        vf = (f"setpts=PTS-STARTPTS,fps={FPS},scale={FW}:{FH}:flags=lanczos,setsar=1," if z == 1 else
              f"setpts=PTS-STARTPTS,fps={FPS},crop=iw/{z}:ih/{z},scale={FW}:{FH}:flags=lanczos,setsar=1,")
        vf += "unsharp=5:5:0.5,eq=contrast=1.06:saturation=1.12"
        cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', f"{e['ss']:.3f}", '-i', e['src'], '-frames:v', str(nfr), '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', out]
    else:
        im = Image.open(e['src']).convert('RGB'); w0, h0 = im.size
        x0, y0, x1, y1 = e['crop']; box = [x0 * w0, y0 * h0, x1 * w0, y1 * h0]
        bw, bh = box[2] - box[0], box[3] - box[1]
        if bw / bh > 4 / 3: nb = bh * 4 / 3; box[0] += (bw - nb) / 2; box[2] = box[0] + nb
        else: nb = bw * 3 / 4; box[1] += (bh - nb) / 2; box[3] = box[1] + nb
        im.crop([int(v) for v in box]).resize((2160, 1620), Image.LANCZOS).save(f'build/i{i:02d}.jpg', quality=94)
        z0, z1 = e['z0'], e['z1']
        vf = (f"zoompan=z='{z0}+({z1}-{z0})*on/{max(1, nfr - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nfr}:s={FW}x{FH}:fps={FPS},"
              f"eq=contrast=1.04:saturation=1.08")
        cmd = ['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', f'build/i{i:02d}.jpg', '-frames:v', str(nfr), '-vf', vf, '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', out]
    subprocess.run(cmd, check=True)
    e['t0'] = t; e['nfr'] = nfr
    pieces.append(out); t += e['d']
open('build/concat.txt', 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in pieces))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', 'build/concat.txt', '-c', 'copy', 'build/fg.mp4'], check=True)
json.dump(edl, open('build/edl.json', 'w'), indent=1)
print('pieces', len(pieces), 'total', t)
