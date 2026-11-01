import json, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft

SR = 48000
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(11)
d = json.load(open('vo_heart.json'))
words = d['words']
def wAt(line, w): return next(x['s'] for x in words if x['line'] == line and x['w'] == w)
def lineStart(i): return next(x['s'] for x in words if x['line'] == i)
tS2, tS3, tS4, tS5, tS6, tS7, tS8, tS9 = [lineStart(i) for i in range(1, 9)]
tNum = wAt(0, '17,000'); tSpace = wAt(1, 'SPACE.'); tThousands = wAt(2, 'thousands')
tSideways = wAt(3, 'sideways'); tMissing = wAt(3, 'MISSING'); tOrbit = wAt(3, 'ORBIT.')
tCatch = wAt(5, 'catches'); tPasses = wAt(5, 'passes'); tWith = wAt(5, 'with'); tLasers = wAt(5, 'LASERS.')
tDown = wAt(6, 'Down'); tInto = wAt(6, 'into'); tBack = wAt(6, 'back'); tYou = wAt(6, 'YOU.')
tBlink = wAt(7, 'BLINK.'); tLook = wAt(8, 'LOOK')
BLINK0 = tBlink + 0.12; S9START = BLINK0 + 0.2
tWaves0 = tS5 + 0.45; tWaveHit = tCatch - 0.05

music = np.zeros((N, 2)); sfx = np.zeros((N, 2))
t_all = np.arange(N) / SR

def env_adsr(n, a, r, curve=2.0):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na) ** 0.7
    if nr < n: e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e

def lowpass(x, fc):
    X = rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / fc) ** 4); return irfft(X, len(x))
def bandpass(x, lo, hi):
    X = rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= (1 / (1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / (1 + (f / hi) ** 4)); return irfft(X, len(x))

def add(buf, t0, sig, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1) * 1.414
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), N - i)
    if n > 0: buf[i:i + n] += sig[:n] * gain

def tv_filter_noise(dur, f0, f1, q=0.5, shape=None):
    # time-varying band-passed noise via short overlapping blocks
    n = int(dur * SR); out = np.zeros(n); blk = 1024; hop = 512; win = np.hanning(blk)
    x = rng.standard_normal(n + blk)
    for s in range(0, n, hop):
        u = s / n; fc = f0 * (f1 / f0) ** (u if shape is None else shape(u))
        seg = x[s:s + blk] * win; X = rfft(seg); f = np.fft.rfftfreq(blk, 1 / SR)
        bw = fc * q; X *= np.exp(-0.5 * ((f - fc) / bw) ** 2); y = irfft(X, blk) * win
        e = min(blk, n - s); out[s:s + e] += y[:e]
    return out / (np.max(np.abs(out)) + 1e-9)

def whoosh(dur, f0=300, f1=3000, peak=0.6, q=0.8):
    x = tv_filter_noise(dur, f0, f1, q)
    u = np.linspace(0, 1, len(x)); e = np.where(u < peak, (u / peak) ** 2.2, ((1 - u) / (1 - peak)) ** 1.6)
    return x * e

def boom(dur=2.5, f0=55, f1=28, gain=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 4); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-tt * 1.6)
    click = lowpass(rng.standard_normal(n), 900) * np.exp(-tt * 30) * 0.5
    tail = lowpass(rng.standard_normal(n), 180) * np.exp(-tt * 2.2) * 0.35
    return np.tanh((s + click + tail) * 1.6) * gain

def ping(freq=1400, dur=0.9, decay=7):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * decay) + 0.35 * np.sin(2 * np.pi * freq * 2.01 * tt) * np.exp(-tt * decay * 1.8)
    return s * env_adsr(n, 0.003, 0.05)

def zap(dur=0.35, f0=2600, f1=180):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / dur); ph = 2 * np.pi * np.cumsum(f) / SR
    mod = np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR) * 2.5
    s = np.sin(ph + mod) * np.exp(-tt * 6) + 0.25 * bandpass(rng.standard_normal(n), 2000, 9000) * np.exp(-tt * 18)
    return s * env_adsr(n, 0.002, 0.06)

def riser(dur, f0=200, f1=2400):
    x = tv_filter_noise(dur, f0, f1, 0.35)
    n = len(x); tt = np.arange(n) / SR
    tone = np.sin(2 * np.pi * np.cumsum(220 * (4 ** (tt / dur))) / SR) * 0.25
    return (x * 0.8 + tone) * (np.linspace(0, 1, n) ** 2.5)

def shimmer(dur, base=1760):
    n = int(dur * SR); out = np.zeros(n)
    for k in range(40):
        t0 = rng.uniform(0, dur * 0.85); f = base * rng.choice([1, 1.25, 1.5, 2, 2.5, 3]) * rng.uniform(0.995, 1.005)
        p = ping(f, 0.6, 9) * rng.uniform(0.2, 0.6); i = int(t0 * SR); m = min(len(p), n - i); out[i:i + m] += p[:m]
    return out

def tick():
    n = int(0.03 * SR); tt = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 3000, 9000) * np.exp(-tt * 250) + np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 300) * 0.5

def reverb(x, secs=1.8, mix=0.25):
    n = int(secs * SR); tt = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-tt * 3.5)[:, None]; ir[:, 0] = lowpass(ir[:, 0], 6000); ir[:, 1] = lowpass(ir[:, 1], 6000)
    out = np.zeros_like(x)
    L = len(x) + n
    for c in range(2):
        X = rfft(x[:, c], L); I = rfft(ir[:, c], L); out[:, c] = irfft(X * I, L)[:len(x)]
    out /= np.max(np.abs(out)) + 1e-9; out *= np.max(np.abs(x))
    return x * (1 - mix) + out * mix

# ---------------- MUSIC ----------------
def saw(f, tt):
    s = np.zeros_like(tt)
    for k in range(1, 14): s += np.sin(2 * np.pi * f * k * tt) / k * (-1) ** (k + 1)
    return s
def note(f, dur, amp=1.0, a=0.4, r=1.0, bright=1800, det=0.006):
    n = int(dur * SR); tt = np.arange(n) / SR
    s = (saw(f * (1 - det), tt) + saw(f * (1 + det), tt) + 0.6 * np.sin(2 * np.pi * f * 0.5 * tt))
    return lowpass(s, bright) * env_adsr(n, a, r) * amp

hz = lambda m: 440 * 2 ** ((m - 69) / 12)
# D minor: Dm - Bb - F - C   (4s each)
chords = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]
music_end = BLINK0 + 0.02
t0 = 0.0; k = 0
while t0 < music_end:
    ch = chords[k % 4]; dur = 4.0
    for i, m in enumerate(ch):
        nn = note(hz(m), dur + 0.8, 0.07 if i else 0.09, a=0.25, r=0.9, bright=1400 + 900 * min(1, t0 / 20))
        add(music, t0, nn, 1.0, pan=[-0.4, 0.3, -0.2, 0.45][i])
    # bass
    bn = note(hz(ch[0] - 12), dur, 0.22, a=0.02, r=0.3, bright=400, det=0.002)
    add(music, t0, bn)
    t0 += dur; k += 1
# pulse arp 16ths from tS3
bpm = 120; step = 60 / bpm / 4
s = tS3 - 0.1; i = 0
while s < music_end - 0.05:
    ch = chords[int(s // 4) % 4]; m = ch[[0, 2, 1, 3, 2, 1, 3, 2][i % 8]] + 12
    nn = note(hz(m), step * 1.6, 0.05, a=0.003, r=0.12, bright=3200, det=0.003)
    g = 0.5 + 0.5 * min(1, (s - tS3) / 8)
    add(music, s, nn, g, pan=0.35 if i % 2 else -0.35); s += step; i += 1
# kick + hats from after SPACE
def kick():
    n = int(0.45 * SR); tt = np.arange(n) / SR; f = 45 + 110 * np.exp(-tt * 35)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7) * 1.8)
def hat():
    n = int(0.08 * SR); tt = np.arange(n) / SR
    return bandpass(rng.standard_normal(n), 6000, 15000) * np.exp(-tt * 60)
b = tSpace + 0.75
while b < music_end - 0.05:
    add(music, b, kick(), 0.55)
    add(music, b + 0.25, hat(), 0.12, pan=0.2)
    b += 0.5
# S9 ending pad: soft, airy
endpad = [62, 69, 74, 77, 81]
for i, m in enumerate(endpad):
    add(music, S9START + 0.3 + i * 0.05, note(hz(m), DUR - S9START, 0.045, a=1.6, r=1.5, bright=2600, det=0.004), 1.0, pan=(-1) ** i * 0.5)
add(music, tLook - 0.02, note(hz(38), DUR - tLook, 0.18, a=0.05, r=1.5, bright=300, det=0.001))

# music fades
fade = np.ones(N)
iB = int(BLINK0 * SR); fade[iB:int((BLINK0 + 0.05) * SR)] = np.linspace(1, 0, int(0.05 * SR))
fade[int((BLINK0 + 0.05) * SR):int((S9START + 0.3) * SR)] = 0
# end pad region is added after S9START+0.3, keep it (fade only applies to earlier content) -> apply only before S9
pre = music.copy(); pre[int((S9START + 0.3) * SR):] = 0
post = music - pre
music = pre * fade[:, None] + post
music = reverb(music, 2.2, 0.3)

# ---------------- SFX ----------------
add(sfx, 0.0, boom(2.2, 70, 30), 0.45)
add(sfx, 0.0, whoosh(1.0, 2500, 300, 0.1), 0.35)
add(sfx, tNum - 0.75, whoosh(1.4, 250, 4500, 0.42, 0.6), 0.5, pan=0.3)
add(sfx, tNum - 0.05, boom(1.6, 80, 35), 0.45)
add(sfx, tS2 - 0.15, whoosh(0.45, 3000, 600, 0.4), 0.3)
add(sfx, tS2, riser(tSpace - tS2, 150, 1800), 0.35)
add(sfx, tSpace - 0.02, boom(3.0, 60, 26), 0.75)
add(sfx, tSpace, shimmer(1.6, 1760), 0.12, pan=-0.2)
add(sfx, tS3 - 0.2, whoosh(0.9, 3500, 250, 0.25), 0.45)
add(sfx, tThousands - 0.1, shimmer(2.0, 2640), 0.10, pan=0.3)
add(sfx, tS4 - 0.1, whoosh(0.8, 400, 1800, 0.5), 0.3)
for (a, bb) in [(tSideways - 0.35, 0), (tSideways + 0.15, 0), (tMissing - 0.65, 0)]:
    add(sfx, a, zap(0.25, 900, 300), 0.18); add(sfx, a + 0.65, boom(0.6, 90, 50), 0.18)
add(sfx, tMissing - 0.1, riser(tOrbit - tMissing + 0.1, 300, 2600), 0.3)
add(sfx, tOrbit, ping(1318.5, 1.6, 2.5), 0.22); add(sfx, tOrbit, ping(1975.5, 1.6, 2.5), 0.15)
add(sfx, tS5 - 0.45, whoosh(1.1, 3800, 160, 0.55, 0.7), 0.7)
add(sfx, tS5 + 0.45, boom(1.0, 70, 40), 0.3)
w = tWaves0
while w < tWaveHit - 0.5:
    add(sfx, w, ping(1180, 0.9, 6), 0.16, pan=0.1); w += 0.32
add(sfx, tWaveHit, zap(0.4, 3000, 600), 0.3)
add(sfx, tS6 + 0.15, whoosh(1.0, 300, 1500, 0.5), 0.3)
add(sfx, tPasses - 0.1, zap(0.4, 3400, 900), 0.4, pan=-0.3)
add(sfx, tWith - 0.05, zap(0.45, 3800, 700), 0.45, pan=0.3)
add(sfx, tLasers, boom(1.2, 75, 38), 0.3)
add(sfx, tDown - 0.05, zap(0.5, 2200, 150), 0.38)
for j in range(14):
    add(sfx, tInto - 0.1 + j * 0.065 + rng.uniform(0, 0.03), ping(rng.choice([1760, 2093, 2349, 2637, 3136]), 0.18, 22), 0.09, pan=rng.uniform(-0.6, 0.6))
add(sfx, tBack - 0.3, whoosh(0.6, 500, 5000, 0.85), 0.4)
add(sfx, tYou - 0.02, ping(1567.98, 0.9, 5), 0.3); add(sfx, tYou + 0.11, ping(2093, 1.0, 4.5), 0.3)
tt0 = tS8
while tt0 < BLINK0 - 0.1:
    add(sfx, tt0, tick(), 0.25); tt0 += 0.09
add(sfx, BLINK0 + 0.02, boom(0.9, 60, 35), 0.35)
# night ambience: crickets + wind
n9 = N - int(S9START * SR); tt = np.arange(n9) / SR
wind = lowpass(rng.standard_normal(n9), 500) * 0.06 * np.minimum(1, tt / 0.8)
crk = np.zeros(n9)
for c in range(3):
    f = 4300 + c * 260; rate = 2.4 + c * 0.6; ph0 = rng.uniform(0, 1)
    gate = (np.sin(2 * np.pi * (tt * rate + ph0)) > 0.55).astype(float)
    trill = (np.sin(2 * np.pi * 60 * tt) > 0).astype(float)
    crk += np.sin(2 * np.pi * f * tt) * gate * trill * 0.012 * (0.6 + 0.4 * c)
amb = (wind + lowpass(crk, 7000)) * np.minimum(1, tt / 0.6)
add(sfx, S9START, amb, 1.0)
add(sfx, tLook - 0.02, ping(880, 2.2, 1.6), 0.18); add(sfx, tLook + 0.1, ping(1318.5, 2.2, 1.6), 0.14); add(sfx, tLook + 0.2, ping(1760, 2.2, 1.6), 0.1)
add(sfx, tLook - 0.4, whoosh(0.8, 300, 2400, 0.6), 0.2)
sfx = reverb(sfx, 1.2, 0.15)

# end fade
fe = np.ones(N); fe[int((DUR - 0.6) * SR):] = np.linspace(1, 0.0, N - int((DUR - 0.6) * SR))
music *= fe[:, None]; sfx *= fe[:, None]

# ducking under voice
vo, vsr = sf.read('vo_heart.wav')
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve = ve / (ve.max() + 1e-9)
duck = 1 - 0.55 * np.clip(ve * 6, 0, 1)
duck = np.convolve(duck, np.ones(2400) / 2400, 'same')
music *= duck[:, None]
music /= np.max(np.abs(music)) + 1e-9; sfx /= np.max(np.abs(sfx)) + 1e-9
sf.write('music.wav', music * 0.9, SR); sf.write('sfx.wav', sfx * 0.9, SR)
print('ok', tS9, BLINK0, S9START)
