import json, subprocess, numpy as np, soundfile as sf
from numpy.fft import rfft, irfft
SR = 48000; END = 176.0; N = int(SR * END)
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
music = np.zeros((N, 2))
# section moods: (start, end, chord midi list, intensity)
Dm = [38, 50, 57, 62, 65]; Bb = [34, 46, 53, 58, 62]; Gm = [31, 43, 50, 55, 58]; A7 = [33, 45, 52, 57, 61]; F = [29, 41, 48, 53, 57]; C = [36, 48, 55, 60, 64]
sections = [(0, ST['teams'], [Dm], 0.9), (ST['teams'], ST['incident'], [Dm, Bb, Gm, A7], 0.45), (ST['incident'], ST['strike'], [Dm, A7], 0.6),
            (ST['strike'], ST['earth'], [Dm, Bb, Gm, A7], 1.0), (ST['earth'], ST['india'], [Gm, A7], 0.7), (ST['india'], ST['counter'], [Dm, Bb, Gm, A7], 1.0),
            (ST['counter'], ST['stalemate'], [Dm, F, Gm, A7], 1.0), (ST['stalemate'], ST['storm'], [Dm, Gm], 0.6), (ST['storm'], ST['talks'], [A7], 0.35),
            (ST['talks'], ST['treaty'], [F, C], 0.45), (ST['treaty'], END, [F, C, Dm, Bb], 0.55)]
beat = 60 / 96
for (a, b, chords, inten) in sections:
    t = a; k = 0
    while t < b - 0.05:
        ch = chords[k % len(chords)]; d = min(beat * 8, b - t)
        for j, m in enumerate(ch):
            add(music, t, pad(hz(m), d + 0.8, (0.05 if j else 0.10) * (0.5 + 0.5 * inten), 900 + 1400 * inten, 0.4, 0.8), 1.0, pan=[0, -0.5, 0.4, -0.2, 0.5][j])
        t += d; k += 1
    if inten >= 0.6:
        tb = a; i = 0
        while tb < b - 0.05:
            add(music, tb, drum(), 0.32 * inten, pan=0)
            if i % 4 == 2: add(music, tb, snare(), 0.10 * inten, pan=0.2)
            if i % 8 == 7: add(music, tb + beat / 2, drum(0.8, 120, 60), 0.2 * inten)
            tb += beat; i += 1
# hook hit
add(music, 0.0, drum(2.0, 70, 30), 0.6)
# ---- SFX ----
sfx = np.zeros((N, 2))
news_times = []
import re
html = open('moonwar.html').read()
# headline times are computed in the page; approximate here from the same word anchors
def fnd(sid, w, n=0):
    try: return W(sid, w, n)
    except Exception: return None
for sid, w in [('teams', 'artemis'), ('pact', 'against'), ('ice', 'water'), ('incident', 'day'), ('incident', 'nobody'), ('strike', 'pact'), ('strike', 'seize'), ('physics', 'sound'), ('digin', 'fortresses'),
               ('earth', 'satellites'), ('earth', 'markets'), ('earth', 'warships'), ('india', 'pact'), ('india', 'joins'), ('crisium', 'surprise'), ('crisium', 'australia'), ('crisium2', 'lasts'), ('crisium2', 'oxygen'),
               ('massdriver', 'mass'), ('massdriver', 'satellite'), ('raid', 'commandos'), ('raid', 'apart'), ('counter', 'counterattacks'), ('counter', 'retake'), ('iran', 'iran'), ('iran', 'dry'), ('stalemate', 'freezes'),
               ('lastpush', 'collapses'), ('totals', 'casualties'), ('storm', 'solar'), ('storm', 'phones'), ('talks', 'rio'), ('treaty', 'treaty'), ('treaty', 'banned'), ('end', 'ended')]:
    tt = fnd(sid, w)
    if tt is not None: add(sfx, tt, blip(), 0.10)
add(sfx, 0.4, blip(), 0.1)
# artillery thuds during battles
battles = [(W('strike', 'seize') - 0.5, ST['digin']), (ST['digin'], ST['earth'] - 1), (W('india', 'artillery') - 0.2, W('india', 'joins') + 0.6), (W('crisium', 'race') + 1, ST['massdriver']),
           (W('raid', 'blow') - 0.2, W('raid', 'apart') + 1.2), (W('counter', 'push') + 1, ST['iran']), (ST['stalemate'], ST['lastpush']), (W('lastpush', 'throws'), W('lastpush', 'collapses') + 0.4), (0.0, ST['teams'] - 0.3)]
for (a, b) in battles:
    t = a + 0.2
    while t < b:
        add(sfx, t, boom(1.0, 70 + rng.random() * 30, 32), 0.18 + rng.random() * 0.12, pan=rng.uniform(-0.6, 0.6)); t += 0.35 + rng.random() * 0.6
# camera whooshes on section changes
for sid in order[1:]:
    add(sfx, ST[sid] - 0.4, whoosh(0.8, 300, 2500, 0.6), 0.12)
add(sfx, ST['earth'] - 0.1, static(2.5), 0.10)
add(sfx, W('storm', 'floods') - 0.3, geiger(8.5, 30), 0.22)
add(sfx, W('raid', 'apart'), boom(3.0, 55, 22), 0.6)
add(sfx, W('crisium2', 'oxygen'), boom(1.5, 60, 30), 0.3)
add(sfx, W('india', 'joins'), boom(1.8, 50, 25), 0.4)
add(sfx, W('treaty', 'treaty'), ding(1046.5, 1.6), 0.18); add(sfx, W('treaty', 'treaty') + 0.12, ding(1318.5, 1.6), 0.14); add(sfx, W('treaty', 'treaty') + 0.24, ding(1568, 1.8), 0.12)
add(sfx, ST['cta'], ding(1318.5, 0.9), 0.15); add(sfx, S['cta']['e'] + 0.1, ding(1760, 0.9), 0.15)
# "No smoke, no sound": the world goes silent for a beat
q0, q1 = W('physics', 'no') - 0.05, W('physics', 'shell') - 0.1
gate = np.ones(N); i0, i1 = int(q0 * SR), int(q1 * SR); r = int(0.06 * SR)
gate[i0:i1] = 0.0; gate[i0 - r:i0] = np.linspace(1, 0, r); gate[i1:i1 + r] = np.linspace(0, 1, r)
music *= gate[:, None]; sfx *= gate[:, None]
# cut-ins: more intense battle audio
for (a, b) in [(W('incident', 'american') - 0.2, ST['strike']), (ST['physics'], ST['digin']), (W('crisium2', 'battle'), ST['massdriver'])]:
    t = a + 0.5
    while t < b:
        if not (q0 <= t <= q1): add(sfx, t, boom(1.2, 80, 34), 0.3)
        t += 0.8
vo, vsr = sf.read('vo.wav')
idx = (np.arange(N) * vsr / SR).astype(int); vo48 = np.where(idx < len(vo), vo[np.minimum(idx, len(vo) - 1)], 0)
ve = np.convolve(np.abs(vo48), np.ones(4800) / 4800, 'same'); ve /= ve.max() + 1e-9
duck = np.convolve(1 - 0.55 * np.clip(ve * 6, 0, 1), np.ones(2400) / 2400, 'same'); music *= duck[:, None]; sfx *= (0.6 + 0.4 * duck)[:, None]
fe = np.ones(N); fe[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR))
for bb in (music, sfx): bb *= fe[:, None]
music /= np.abs(music).max() + 1e-9; sfx /= np.abs(sfx).max() + 1e-9
sf.write('build/music.wav', music * 0.9, SR); sf.write('build/sfx.wav', sfx * 0.9, SR); print('ok')
