import json, subprocess, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft
SR = 48000; END = 57.6; N = int(SR * END)
rng = np.random.default_rng(5)
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
edl = json.load(open('build/edl.json'))
order = ['hook', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']
starts = [0.0] + [S[k]['s'] for k in order[1:]]
def W(sid, word): return next(w['s'] for w in S[sid]['words'] if w['w'].strip('.,?:!').lower().startswith(word.lower()))

def lowpass(x, fc):
    X = rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return irfft(X, len(x))
def bandpass(x, lo, hi):
    X = rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= (1 / (1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / (1 + (f / hi) ** 4)); return irfft(X, len(x))
def add(buf, t0, sig, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * 1.414
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), len(buf) - i)
    if n > 0: buf[i:i + n] += sig[:n] * gain
def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR)); e[:na] = np.linspace(0, 1, na)
    if nr < n: e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e
def whoosh(dur, f0, f1, peak=0.5):
    n = int(dur * SR); x = rng.standard_normal(n); out = np.zeros(n); blk = 2048; hop = 1024; win = np.hanning(blk)
    x = np.concatenate([x, np.zeros(blk)])
    for s in range(0, n, hop):
        u = s / n; fc = f0 * (f1 / f0) ** u; seg = x[s:s + blk] * win; X = rfft(seg); f = np.fft.rfftfreq(blk, 1 / SR)
        X *= np.exp(-0.5 * ((f - fc) / (fc * 0.7)) ** 2); y = irfft(X, blk) * win; m = min(blk, n - s); out[s:s + m] += y[:m]
    out /= np.abs(out).max() + 1e-9; u = np.linspace(0, 1, n)
    return out * np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.5)
def boom(dur=1.8, f0=70, f1=30):
    n = int(dur * SR); tt = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-tt * 5)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2) + lowpass(rng.standard_normal(n), 600) * np.exp(-tt * 6) * 0.8
    return np.tanh(s * 1.8)
def thud():
    n = int(0.35 * SR); tt = np.arange(n) / SR; f = 50 + 90 * np.exp(-tt * 30)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 12) * 2 + lowpass(rng.standard_normal(n), 400) * np.exp(-tt * 25))
def ding(f=1568, dur=0.8):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 6)) * np.exp(-tt * 5) * env(n, 0.002, 0.05)
def trombone():
    # wah wah wah waaah: Bb3 A3 Ab3 G3
    notes = [(233.08, 0.32), (220.0, 0.32), (207.65, 0.32), (196.0, 1.1)]; out = []
    for i, (f, d) in enumerate(notes):
        n = int(d * SR); tt = np.arange(n) / SR
        vib = 1 + (0.012 * np.sin(2 * np.pi * 5.5 * tt) * np.clip((tt - 0.25) * 3, 0, 1) if i == 3 else 0)
        ph = 2 * np.pi * np.cumsum(f * vib * (1 - 0.03 * (tt / d) if i == 3 else 1)) / SR
        s = sum(np.sin(k * ph) / k ** 0.8 for k in range(1, 12))
        wah = 0.5 + 0.5 * np.sin(np.pi * np.clip(tt / min(d, 0.3), 0, 1))
        s = lowpass(s, 900 + 1600 * wah.mean()) * env(n, 0.03, 0.08 if i < 3 else 0.4) * (0.6 + 0.4 * wah)
        out.append(s)
    x = np.concatenate(out); return x / np.abs(x).max()

# ---------- music: bouncy marimba + pluck bass + shaker, C major, 112 bpm ----------
music = np.zeros((N, 2)); bpm = 112; beat = 60 / bpm; step = beat / 2
def marimba(f, dur=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) + 0.25 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 30)) * env(n, 0.002, 0.05)
def pluck(f, dur=0.4):
    n = int(dur * SR); tt = np.arange(n) / SR
    return lowpass(sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 6)), 700) * np.exp(-tt * 7) * env(n, 0.003, 0.05)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
prog = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
pat = [0, 2, 1, 3, 2, 1, 3, 2]
t = 0.0; i = 0
while t < END:
    bar = int(t / (beat * 4)) % 4; ch = prog[bar]
    add(music, t, marimba(hz(ch[pat[i % 8]] + 12)), 0.22, pan=0.3 if i % 2 else -0.3)
    if i % 4 == 0: add(music, t, pluck(hz(ch[0] - 24)), 0.5)
    if i % 4 == 2: add(music, t, pluck(hz(ch[2] - 24)), 0.35)
    sh = bandpass(rng.standard_normal(int(0.05 * SR)), 5000, 12000) * np.exp(-np.arange(int(0.05 * SR)) / SR * 70)
    add(music, t, sh, 0.05 if i % 2 else 0.09, pan=0.15)
    if i % 4 == 0:
        n = int(0.3 * SR); tt = np.arange(n) / SR; k = np.tanh(np.sin(2 * np.pi * np.cumsum(50 + 80 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 10) * 1.5)
        add(music, t, k, 0.35)
    t += step; i += 1
# drop music out for comedic beats
gate = np.ones(N)
def mute(a, b, depth=1.0):
    ia, ib = int(a * SR), int(b * SR); r = int(0.04 * SR)
    g = np.ones(ib - ia) * (1 - depth); g[:r] = np.linspace(1, 1 - depth, r); g[-r:] = np.linspace(1 - depth, 1, r); gate[ia:ib] = np.minimum(gate[ia:ib], g)
mute(W('7', 'astronaut') - 0.05, starts[order.index('6')], 0.85)
mute(W('4', 'again') + 0.2, starts[order.index('3')], 1.0)
mute(W('2', 'give') - 0.05, W('2', 'nobody'), 0.8)
mute(W('1', 'hey') - 0.1, S['1']['e'] + 0.15, 0.7)
music *= gate[:, None]

# ---------- SFX ----------
sfx = np.zeros((N, 2))
add(sfx, 0.0, boom(1.6, 80, 30), 0.5)
for k in order[1:]:
    t0 = starts[order.index(k)]; add(sfx, t0 - 0.28, whoosh(0.5, 500, 4000, 0.6), 0.35); add(sfx, t0 + 0.02, ding(1318.5 if k != '1' else 1568, 0.6), 0.12)
add(sfx, W('5', 'exploded') - 0.05, boom(2.2, 70, 28), 0.85)
add(sfx, starts[order.index('4')] + 1.55, boom(1.8, 60, 30), 0.55)
add(sfx, W('4', 'again') + 0.3, trombone(), 0.42)
add(sfx, W('7', 'astronaut') - 0.4, thud(), 0.6)
add(sfx, W('3', 'dirt') - 0.15, thud(), 0.6)
add(sfx, W('1', 'twinkletoes') - 0.25, thud(), 0.55)
add(sfx, W('6', 'goodbye'), boom(1.2, 90, 40), 0.35)
for j in range(6):  # cash register-ish ticks on $100,000
    add(sfx, W('9', 'hundred') + j * 0.07, ding(2600 + j * 120, 0.15), 0.05)

# ---------- original clip audio (Apollo radio chatter, low) ----------
orig = np.zeros((N, 2))
for e in edl:
    if e['kind'] != 'clip' or e.get('audio', True) is False: continue
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f"{e['ss']:.3f}", '-t', f"{e['d']:.3f}", '-i', e['src'], '-vn', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    if len(a) == 0: continue
    a = bandpass(a, 250, 3800); a /= np.abs(a).max() + 1e-9
    n = len(a); fade = np.ones(n); r = min(n // 4, int(0.05 * SR)); fade[:r] = np.linspace(0, 1, r); fade[-r:] = np.linspace(1, 0, r)
    add(orig, e['t0'], a * fade, 0.18)

# ---------- voice ducking + mix ----------
vo, vsr = sf.read('vo.wav')
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve /= ve.max() + 1e-9
duck = np.convolve(1 - 0.6 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same')
music *= duck[:, None]; orig *= np.convolve(1 - 0.5 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same')[:, None]
fe = np.ones(N); fe[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR))
for b in (music, sfx, orig): b *= fe[:, None]
music /= np.abs(music).max() + 1e-9; sfx /= np.abs(sfx).max() + 1e-9
sf.write('build/music.wav', music * 0.9, SR); sf.write('build/sfx.wav', sfx * 0.9, SR); sf.write('build/orig.wav', orig, SR)
print('ok')
