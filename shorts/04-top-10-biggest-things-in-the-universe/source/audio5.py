import json, subprocess, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft
SR = 48000; END = 52.0; N = int(SR * END)
rng = np.random.default_rng(5)
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
order = [x['id'] for x in VO['segs']]
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


hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def pad(f, dur, amp=0.1, bright=1800, a=0.6, r=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * dt * k * tt + k) / k for k in range(1, 9) for dt in (0.996, 1.004))
    return lowpass(s, bright) * env(n, a, r) * amp
def pluck(f, dur=0.6, bright=3000):
    n = int(dur * SR); tt = np.arange(n) / SR
    return lowpass(sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 7)), bright) * np.exp(-tt * 6) * env(n, 0.002, 0.05)
def kick():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    return np.tanh(np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 6) * 1.6)
music = np.zeros((N, 2))
# chord per item, rising: Dm Bb F C ... each segment, getting brighter and fuller
prog = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64], [50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [48, 55, 60, 64], [45, 52, 57, 61], [50, 57, 62, 66], [50, 57, 62, 69], [50, 57, 62, 69]]
starts_all = starts + [END]
for i, sid in enumerate(order):
    t0, t1 = starts_all[i], starts_all[i + 1]; lvl = 0.5 + 0.5 * i / (len(order) - 1)
    for j, m in enumerate(prog[i]):
        add(music, t0 - 0.05, pad(hz(m), t1 - t0 + 0.9, 0.05 * lvl, 1200 + 1800 * lvl, 0.3, 0.8), 1.0, pan=[-0.5, 0.3, -0.2, 0.5][j])
    add(music, t0 - 0.05, pad(hz(prog[i][0] - 12), t1 - t0 + 0.9, 0.10 * lvl, 500, 0.2, 0.8))
    # arpeggio pulse
    step = 60 / 112 / 2; t = t0; k = 0
    while t < t1 - 0.05:
        add(music, t, pluck(hz(prog[i][k % 4] + 12), 0.5, 2500 + 2000 * lvl), 0.06 * (0.6 + 0.6 * lvl), pan=0.3 if k % 2 else -0.3); t += step; k += 1
    if i >= 2:
        tb = t0
        while tb < t1 - 0.05:
            add(music, tb, kick(), 0.25 * lvl); tb += 60 / 112 * 2
# final swell + quiet outro
add(music, starts[order.index('1')] - 0.05, pad(hz(38), END - starts[order.index('1')], 0.2, 400, 0.05, 1.5))
sfx = np.zeros((N, 2))
for i, sid in enumerate(order[1:-1], start=1):
    t0 = starts[i]; f0 = 3000 / (1 + i * 0.25)
    add(sfx, t0 - 0.35, whoosh(1.1 + 0.05 * i, f0 * 0.2, f0, 0.35), 0.35 + 0.02 * i)
    add(sfx, t0 + 0.05, boom(1.0 + 0.1 * i, 70 - i * 2, 32), 0.12 + 0.02 * i)
add(sfx, starts[order.index('1')], boom(3.0, 55, 22), 0.75)
add(sfx, 0.0, whoosh(1.4, 4000, 300, 0.15), 0.35)
add(sfx, S['outro']['s'], ding(1318.5, 0.9), 0.15); add(sfx, S['outro']['e'] + 0.1, ding(1760, 0.9), 0.15)
vo, vsr = sf.read('vo.wav')
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve /= ve.max() + 1e-9
duck = np.convolve(1 - 0.55 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same'); music *= duck[:, None]
fe = np.ones(N); fe[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
for b in (music, sfx): b *= fe[:, None]
music /= np.abs(music).max() + 1e-9; sfx /= np.abs(sfx).max() + 1e-9
sf.write('build/music.wav', music * 0.9, SR); sf.write('build/sfx.wav', sfx * 0.9, SR); print('ok')
