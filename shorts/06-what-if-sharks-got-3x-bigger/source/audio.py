import json, subprocess, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft
SR = 48000; END = 130.0; N = int(SR * END)
rng = np.random.default_rng(5)
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
order = [x['id'] for x in VO['segs']]
starts = [0.0] + [S[k]['s'] for k in order[1:]]
def W(sid, word, n=0): return [w['s'] for w in S[sid]['words'] if w['w'].strip('.,?:!').lower().startswith(word.lower())][n]
def W_old(sid, word): return next(w['s'] for w in S[sid]['words'] if w['w'].strip('.,?:!').lower().startswith(word.lower()))

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


ST = {sid: (S[sid]['s'] if i else 0.0) for i, sid in enumerate(order)}
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def pad(f, dur, amp=0.1, bright=1500, a=0.8, r=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * dt * k * tt + k) / k for k in range(1, 8) for dt in (0.995, 1.005))
    return lowpass(s, bright) * env(n, a, r) * amp
def drum(dur=1.2, f0=95, f1=42):
    n = int(dur * SR); tt = np.arange(n) / SR; f = f1 + (f0 - f1) * np.exp(-tt * 9)
    return np.tanh((np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 4.5) + lowpass(rng.standard_normal(n), 900) * np.exp(-tt * 18) * 0.5) * 1.7)
def snare():
    n = int(0.3 * SR); tt = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 900, 7000) * np.exp(-tt * 14) * 0.8 + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 20) * 0.4
def blip():
    n = int(0.22 * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1760 * tt) * (tt < 0.08) + np.sin(2 * np.pi * 1318.5 * tt) * (tt >= 0.09)) * np.exp(-tt * 9) * env(n, 0.003, 0.03)
def static(dur):
    n = int(dur * SR); return bandpass(rng.standard_normal(n), 1500, 6000) * (0.5 + 0.5 * (rng.random(n) > 0.6)) * env(n, 0.05, 0.2)
def geiger(dur, rate=18):
    n = int(dur * SR); out = np.zeros(n); k = int(rate * dur)
    for _ in range(k):
        i = int(rng.random() * (n - 400)); out[i:i + 300] += bandpass(rng.standard_normal(300), 2000, 9000) * np.exp(-np.arange(300) / 40)
    return out

def bubbles(dur, rate=6):
    n = int(dur * SR); out = np.zeros(n)
    for _ in range(int(rate * dur)):
        i = int(rng.random() * (n - 6000)); m = int(SR * (0.03 + rng.random() * 0.05)); tt = np.arange(m) / SR; f0 = 500 + rng.random() * 1400
        out[i:i + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + tt * 18)) / SR) * np.exp(-tt * 40) * (0.3 + rng.random() * 0.7)
    return out
def ambience(dur):
    n = int(dur * SR); x = lowpass(rng.standard_normal(n), 220); x /= np.abs(x).max() + 1e-9
    tt = np.arange(n) / SR; return x * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * tt))
def pulse(dur=0.9, f=41):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.tanh(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) * 2.2) * env(n, 0.01, 0.2)
def impact(dur=2.2):
    return boom(dur, 60, 26) * 0.9 + np.concatenate([whoosh(0.25, 3000, 400, 0.1), np.zeros(int(dur * SR) - int(0.25 * SR))]) * 0.3
def riser(dur):
    return whoosh(dur, 200, 4000, 0.92)

music = np.zeros((N, 2))
Cm = [36, 48, 55, 60, 63]; Ab = [32, 44, 51, 56, 60]; Fm = [29, 41, 48, 53, 56]; G = [31, 43, 50, 55, 59]; Eb = [27, 39, 46, 51, 55]; Bb = [34, 46, 53, 58, 62]
sections = [(0, ST['count'], [Cm], 1.0), (ST['count'], ST['size'], [Cm, Ab], 0.45), (ST['size'], ST['hunger'], [Cm, Ab, Fm, G], 0.75),
            (ST['hunger'], ST['food'], [Fm, G, Cm, Cm], 0.8), (ST['food'], ST['coast'], [Cm, Ab, Eb, G], 0.9), (ST['coast'], ST['bites'], [Fm, G], 1.0),
            (ST['bites'], ST['whatif'], [Ab, Eb], 0.4), (ST['whatif'], ST['crash'], [Cm, Ab, Fm, G], 1.0), (ST['crash'], ST['us'], [Fm, Cm], 0.55),
            (ST['us'], ST['cta'], [Ab, Bb], 0.35), (ST['cta'], END, [Cm, Ab], 0.5)]
beat = 60 / 84
for (a, b, chords, inten) in sections:
    t = a; k = 0
    while t < b - 0.05:
        ch = chords[k % len(chords)]; d = min(beat * 8, b - t)
        for j, m in enumerate(ch):
            add(music, t, pad(hz(m), d + 0.9, (0.05 if j else 0.11) * (0.5 + 0.5 * inten), 700 + 1200 * inten, 0.5, 0.9), 1.0, pan=[0, -0.5, 0.4, -0.2, 0.5][j])
        t += d; k += 1
    if inten >= 0.7:
        tb = a; i = 0
        while tb < b - 0.05:
            add(music, tb, pulse(0.9, hz(chords[(i // 8) % len(chords)][0] + 12) / 2), 0.35 * inten)
            if i % 2 == 1: add(music, tb, drum(0.6, 110, 55), 0.12 * inten)
            if i % 8 == 6: add(music, tb, snare(), 0.06 * inten, pan=0.2)
            tb += beat / (2 if inten >= 0.95 else 1); i += 1
add(music, 0, ambience(END), 0.25)
sfx = np.zeros((N, 2))
add(sfx, 0.0, impact(2.6), 0.75); add(sfx, W('hook', 'twice') - 0.05, impact(2.0), 0.55)
add(sfx, 0, bubbles(END, 3.5), 0.05)
for sid in order[1:]: add(sfx, ST[sid] - 0.45, whoosh(0.9, 250, 2600, 0.6), 0.13)
hits = [('count', 'hundred'), ('count', 'seven'), ('count', 'one'), ('count', 'three'), ('size', 'twenty'), ('size', 'school'), ('size', 'twenty', 1), ('whale', 'largest'), ('hunger', 'twelve'), ('hunger', 'twenty'),
        ('collapse', 'tuna'), ('collapse', 'seals'), ('food', 'south'), ('food', 'california'), ('food', 'australia'), ('cold', 'north', 1), ('cold', 'norway'), ('cold', 'alaska'), ('rivers', 'thousand'),
        ('bites', 'us'), ('bites', 'australia'), ('bites', 'bahamas'), ('whatif', 'six'), ('beaches', 'florida'), ('beaches', 'sydney'), ('beaches', 'surfers'), ('end', 'fewer'), ('us', 'hundred')]
for h in hits:
    t0 = W(*h) if len(h) == 2 else W(h[0], h[1], h[2]); add(sfx, t0 - 0.02, thud(), 0.22); add(sfx, t0, ding(1046.5 if h[0] in ('bites', 'count') else 784, 0.5), 0.05)
add(sfx, W('size', 'thirteen') - 0.1, riser(1.2), 0.2); add(sfx, W('size', 'thirteen') + 1.0, impact(2.2), 0.45)
add(sfx, W('hunger', 'can'), impact(2.0), 0.5); add(sfx, W('beaches', 'rammed') - 0.05, impact(2.4), 0.8); add(sfx, W('beaches', 'rammed'), bubbles(2.0, 60), 0.35)
add(sfx, W('crash', 'starve'), impact(2.4), 0.45); add(sfx, W('coast', 'right'), impact(1.8), 0.35)
add(sfx, ST['cta'], ding(1318.5, 0.9), 0.15); add(sfx, S['cta']['e'] + 0.1, ding(1760, 0.9), 0.15)
# beat of silence before "It's us."
q0, q1 = W('us', 'change') + 0.35, W('us', 'us') - 0.02
gate = np.ones(N); i0, i1 = int(q0 * SR), int(q1 * SR); r = int(0.05 * SR)
gate[i0:i1] = 0.0; gate[i0 - r:i0] = np.linspace(1, 0, r); gate[i1:i1 + r] = np.linspace(0, 1, r)
music *= gate[:, None]; sfx *= gate[:, None]; add(sfx, W('us', 'us'), impact(2.6), 0.6)
vo, vsr = sf.read('vo.wav')
if vo.ndim > 1: vo = vo.mean(1)
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve /= ve.max() + 1e-9
duck = np.convolve(1 - 0.55 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same'); music *= duck[:, None]; sfx *= (0.6 + 0.4 * duck)[:, None]
fe = np.ones(N); fe[-int(1.5 * SR):] = np.linspace(1, 0, int(1.5 * SR))
for bb in (music, sfx): bb *= fe[:, None]
music /= np.abs(music).max() + 1e-9; sfx /= np.abs(sfx).max() + 1e-9
sf.write('build/music.wav', music * 0.9, SR); sf.write('build/sfx.wav', sfx * 0.9, SR); print('ok')
