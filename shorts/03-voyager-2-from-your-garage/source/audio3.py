import json, subprocess, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft
SR = 48000; END = 60.0; N = int(SR * END)
rng = np.random.default_rng(5)
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
edl = json.load(open('build/edl.json'))
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


# ---------- music: driving "how-to" groove that builds to launch, cosmic pads for flybys ----------
music = np.zeros((N, 2)); bpm = 120; beat = 60 / bpm; step = beat / 4
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def pluck(f, dur=0.25, bright=2500):
    n = int(dur * SR); tt = np.arange(n) / SR
    return lowpass(sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 8)), bright) * np.exp(-tt * 12) * env(n, 0.002, 0.03)
def pad(f, dur, amp=0.1, bright=1800):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * dt * k * tt) / k for k in range(1, 9) for dt in (0.997, 1.003))
    return lowpass(s, bright) * env(n, 0.8, 1.2) * amp
def kick():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    return np.tanh(np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 8) * 1.8)
def snare():
    n = int(0.25 * SR); tt = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 1200, 8000) * np.exp(-tt * 18) + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.5
prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
tL = S['launch']['s']; tJ = S['jup']['s']; tF = S['final']['s']
t = 0.0; i = 0
while t < tL:
    ch = prog[int(t / (beat * 4)) % 4]
    add(music, t, pluck(hz(ch[[0, 1, 2, 1][i % 4]] + 12)), 0.2, pan=0.3 if i % 2 else -0.3)
    if i % 8 == 0: add(music, t, pluck(hz(ch[0] - 12), 0.5, 600), 0.6)
    if i % 4 == 0 and t > S['s1']['s']: add(music, t, kick(), 0.45)
    if i % 8 == 4 and t > S['s3']['s']: add(music, t, snare(), 0.22)
    hat = bandpass(rng.standard_normal(int(0.04 * SR)), 7000, 15000) * np.exp(-np.arange(int(0.04 * SR)) / SR * 90)
    if i % 2 == 1: add(music, t, hat, 0.06)
    t += step; i += 1
# riser into launch
n = int(3.0 * SR); tt = np.arange(n) / SR
add(music, tL - 3.0, lowpass(rng.standard_normal(n), 3000) * (tt / 3.0) ** 3 * 0.5 + np.sin(2 * np.pi * np.cumsum(110 * 4 ** (tt / 3)) / SR) * (tt / 3) ** 2 * 0.25)
# launch: big drums + pad
t = tL; i = 0
while t < tJ:
    if i % 4 == 0: add(music, t, kick(), 0.8)
    if i % 8 == 4: add(music, t, snare(), 0.4)
    t += beat / 2; i += 1
add(music, tL, pad(hz(45), tJ - tL + 1, 0.12, 900)); add(music, tL, pad(hz(52), tJ - tL + 1, 0.08, 1400))
# flybys: cosmic pads per planet
for sid, root in [('jup', 50), ('sat', 53), ('ura', 55), ('nep', 57), ('end', 50)]:
    t0 = S[sid]['s']; t1 = S[order[order.index(sid) + 1]]['s'] if sid != 'end' else tF
    for m in (root, root + 7, root + 12, root + 16):
        add(music, t0 - 0.1, pad(hz(m), t1 - t0 + 1.0, 0.05, 2200), 1.0, pan=(m % 3 - 1) * 0.4)
    add(music, t0 - 0.05, pluck(hz(root + 24), 1.2, 4000), 0.25)
# final step: music out, then a cheeky outro sting
fade = np.ones(N); i0 = int((tF - 0.1) * SR); fade[i0:i0 + int(0.15 * SR)] = np.linspace(1, 0, int(0.15 * SR)); fade[i0 + int(0.15 * SR):] = 0
music *= fade[:, None]
for k, m in enumerate([72, 76, 79, 84]):
    add(music, W('final', 'balloon') + 0.45 + k * 0.11, pluck(hz(m), 0.6, 4000), 0.35)

# ---------- SFX ----------
sfx = np.zeros((N, 2))
add(sfx, 0.0, whoosh(0.7, 3000, 300, 0.2), 0.4)
for k in order[1:]:
    t0 = S[k]['s']; add(sfx, t0 - 0.3, whoosh(0.55, 500, 4500, 0.6), 0.3)
    if k.startswith('s') and k[1:].isdigit(): add(sfx, t0 + 0.02, ding(1318.5, 0.5), 0.1)
# launch rumble
n = int((tJ - tL + 0.5) * SR); tt = np.arange(n) / SR
rum = lowpass(rng.standard_normal(n), 180) * np.minimum(1, tt / 0.6) * np.exp(-np.maximum(0, tt - 4.0) * 1.2)
crack = bandpass(rng.standard_normal(n), 300, 3000) * (0.5 + 0.5 * (rng.random(n) > 0.995)) * np.minimum(1, tt / 0.8) * np.exp(-np.maximum(0, tt - 3.5) * 1.5) * 0.25
add(sfx, tL, rum / (np.abs(rum).max() + 1e-9) + crack, 0.9)
add(sfx, tL + 0.05, boom(2.5, 60, 25), 0.7)
add(sfx, W('launch', 'bye') - 0.2, whoosh(1.4, 1500, 200, 0.3), 0.4)
for sid in ('jup', 'sat', 'ura', 'nep'):
    add(sfx, S[sid]['s'] - 0.6, whoosh(1.2, 300, 2500, 0.55), 0.35)
add(sfx, W('jup', 'steal'), whoosh(0.8, 800, 3000, 0.4), 0.3)
add(sfx, W('s3', 'smaller'), ding(2093, 0.4), 0.1)
add(sfx, W('final', 'weather') - 0.1, ding(880, 0.6), 0.15)

# ---------- voice ducking + mix ----------
vo, vsr = sf.read('vo.wav')
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve /= ve.max() + 1e-9
duck = np.convolve(1 - 0.55 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same')
music *= duck[:, None]
fe = np.ones(N); fe[-int(0.4 * SR):] = np.linspace(1, 0, int(0.4 * SR))
for b in (music, sfx): b *= fe[:, None]
music /= np.abs(music).max() + 1e-9; sfx /= np.abs(sfx).max() + 1e-9
sf.write('build/music.wav', music * 0.9, SR); sf.write('build/sfx.wav', sfx * 0.9, SR)
print('ok')
