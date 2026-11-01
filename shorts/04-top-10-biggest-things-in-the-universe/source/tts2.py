import sys, json, numpy as np, soundfile as sf, re
from kokoro_onnx import Kokoro
model, voices, voice, speed, out = sys.argv[1:6]
k = Kokoro(model, voices); sr = 24000
lines = json.load(open('script.json'))
def trim(a, th=0.008):
    e = np.convolve(np.abs(a), np.ones(240)/240, 'same'); idx = np.where(e > th)[0]
    return a[max(0, idx[0]-120):idx[-1]+240]
audio = [np.zeros(int(0.08*sr), np.float32)]; t = 0.08; segs = []
for L in lines:
    # synthesize per sentence-ish piece to get word timing anchors
    pieces = [p for p in re.split(r'(?<=[.?!])\s+', L['say']) if p]
    seg = {'id': L['id'], 's': t, 'words': []}
    for pi, p in enumerate(pieces):
        a, _ = k.create(p, voice=voice, speed=float(speed), lang='en-us'); a = trim(a)
        d = len(a)/sr
        ws = p.split(); wts = [len(re.sub(r'[^A-Za-z0-9]', '', w)) + 2 + (3 if re.search(r'[,.]{1}$|\.\.\.$', w) else 0) for w in ws]
        c = 0; tot = sum(wts)
        for w, wt in zip(ws, wts):
            dd = d*wt/tot; seg['words'].append({'w': w, 's': round(t+c, 3), 'e': round(t+c+dd, 3)}); c += dd
        audio.append(a); t += d
        if pi < len(pieces)-1:
            g = 0.12; audio.append(np.zeros(int(g*sr), np.float32)); t += g
    seg['e'] = t
    audio.append(np.zeros(int(L['gap']*sr), np.float32)); t += L['gap']
    segs.append(seg); print(L['id'], round(seg['s'], 2), round(seg['e'], 2))
full = np.concatenate(audio); sf.write(out+'.wav', full, sr)
json.dump({'dur': len(full)/sr, 'segs': segs}, open(out+'.json', 'w'), indent=0); print('TOTAL', len(full)/sr)
