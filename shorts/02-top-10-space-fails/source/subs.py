import json, re
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
END = 57.6
order = ['hook', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1']
starts = [0.0] + [S[k]['s'] for k in order[1:]] + [END]
def W(sid, word): return next(w['s'] for w in S[sid]['words'] if w['w'].strip('.,?:!').lower().startswith(word.lower()))
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,MontBlack,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,9,4,5,40,40,0,1
Style: Rank,MontBlack,210,&H0000D4FF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,13,6,5,0,0,0,1
Style: Sub,MontXB,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,2,0,1,6,3,5,0,0,0,1
Style: Title,MontBlack,108,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,11,5,5,0,0,0,1
Style: Call,MontBlack,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,9,4,5,0,0,0,1
Style: Bub,MontXB,44,&H00FFFFFF,&H00FFFFFF,&H00202020,&H00202020,0,0,0,0,100,100,0,0,3,18,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
def E(t0, t1, style, text, layer=0): ev.append(f"Dialogue: {layer},{ts(t0)},{ts(t1)},{style},,0,0,0,,{text}")
YEL = r'\c&H00D4FF&'; WHT = r'\c&HFFFFFF&'; RED = r'\c&H3C5AFF&'; CYA = r'\c&HFFE38F&'

# ---- captions (word-by-word) ----
DISPLAY = {'hundred thousand dollar': '$100,000', 'hundred and twenty five million dollar': '$125 MILLION', 'forty': '40', 'sixteen.': '16.', 'ten,': '10,', 'Ten': '10'}
EMPH = {'fails.', 'loud.', 'sandwich', 'congress', '$100,000', 'moon.', 'miles', '40', 'yards.', 'zero.', 'feet.', 'meters.', 'goodbye,', '$125 million', 'exploded.', 'flopnik.', 'again.', 'dirt.', 'turd', 'confessed.', 'twinkletoes,', 'falling', 'one.', 'one?'}
for sid in order:
    ws = S[sid]['words']
    toks = []; i = 0
    while i < len(ws):
        merged = False
        for k, v in DISPLAY.items():
            n = len(k.split())
            if ' '.join(w['w'] for w in ws[i:i + n]) == k:
                toks.append({'w': v, 's': ws[i]['s'], 'e': ws[i + n - 1]['e']}); i += n; merged = True; break
        if not merged: toks.append(dict(ws[i])); i += 1
    chunks = []; cur = []
    for j, tk in enumerate(toks):
        cur.append(tk); txt = ' '.join(x['w'] for x in cur)
        nxt = toks[j + 1] if j + 1 < len(toks) else None
        if not nxt or re.search(r'[.,?:!]$', tk['w']) or len(cur) >= 3 or len(txt) + len(nxt['w']) > 15:
            chunks.append(cur); cur = []
    seg_end = starts[order.index(sid) + 1]
    for ci, ch in enumerate(chunks):
        c_end = chunks[ci + 1][0]['s'] if ci + 1 < len(chunks) else min(seg_end, ch[-1]['e'] + 0.5)
        for wi, w in enumerate(ch):
            t0 = w['s']; t1 = ch[wi + 1]['s'] if wi + 1 < len(ch) else c_end
            parts = []
            for k, x in enumerate(ch):
                up = x['w'].upper(); em = x['w'].lower() in EMPH
                if k == wi: parts.append(r'{' + YEL + r'\fscx100\fscy100\t(0,70,\fscx114\fscy114)\t(70,170,\fscx104\fscy104)}' + up + r'{\fscx100\fscy100' + WHT + '}')
                elif k < wi and em: parts.append('{' + YEL + '}' + up + '{' + WHT + '}')
                else: parts.append(up)
            pop = r'\fad(0,0)' + (r'\t(0,90,\fscx100\fscy100)' if wi == 0 else '')
            start_scale = r'\fscx88\fscy88' if wi == 0 else ''
            E(t0, t1, 'Cap', r'{\pos(540,1440)' + start_scale + pop + '}' + ' '.join(parts))

# ---- rank badges + titles ----
info = {'10': ('GEMINI 3 · 1965', 'THE SMUGGLED SANDWICH'), '9': ('ISS SPACEWALK · 2008', 'BYE BYE, TOOL BAG'), '8': ('APOLLO 14 · 1971', 'MOON GOLF'),
        '7': ('APOLLO 16 · 1972', 'CHARLIE DUKE VS. GRAVITY'), '6': ('MARS CLIMATE ORBITER · 1999', 'FEET VS. METERS'), '5': ('VANGUARD TV-3 · 1957', '"FLOPNIK"'),
        '4': ('VANGUARD TV-3BU · 1958', 'ATTEMPT #2'), '3': ('APOLLO 17 · 1972', 'GENE CERNAN, LAST MAN ON THE MOON'), '2': ('APOLLO 10 · 1969', 'WHO DID IT?'), '1': ('APOLLO 17 · 1972', '"TWINKLETOES"')}
for i, sid in enumerate(order):
    t0, t1 = starts[i], starts[i + 1]
    if sid == 'hook':
        E(0, t1, 'Title', r'{\pos(540,215)\fscx70\fscy70\t(0,120,\fscx100\fscy100)}10 REAL')
        E(0, t1, 'Title', r'{\pos(540,330)\fscx70\fscy70\t(0,120,\fscx100\fscy100)' + YEL + '}SPACE FAILS')
        continue
    E(t0, t1, 'Rank', r'{\pos(540,215)\fscx150\fscy150\t(0,140,\fscx96\fscy96)\t(140,220,\fscx100\fscy100)}#' + sid)
    E(t0 + 0.08, t1, 'Sub', r'{\pos(540,345)\fad(120,0)}' + info[sid][0])
    E(t0 + 0.08, t1, 'Sub', r'{\pos(540,1290)\fad(120,0)\fs40\c&HE0E0E0&}' + info[sid][1], 1) if False else None

# ---- callouts on the footage ----
def call(t0, t1, text, y=1150, color=WHT, size=70, layer=2):
    E(t0, t1, 'Call', r'{\pos(540,%d)\fs%d' % (y, size) + color + r'\fscx60\fscy60\t(0,110,\fscx106\fscy106)\t(110,180,\fscx100\fscy100)}' + text, layer)
call(W('8', 'forty'), starts[order.index('8') + 1], 'ACTUAL DISTANCE: ~40 YARDS', 1150, YEL, 56)
call(W('6', 'feet'), W('6', 'goodbye'), 'FEET', 640, RED, 120)
call(W('6', 'meters'), W('6', 'goodbye'), 'METERS', 840, CYA, 120)
call(W('6', 'goodbye'), starts[order.index('6') + 1], '-$125,000,000', 740, RED, 110)
call(W('5', 'flopnik'), starts[order.index('5') + 1], '"FLOPNIK"', 740, YEL, 130)
call(W('9', 'orbited'), starts[order.index('9') + 1], 'IT ORBITED FOR ~8 MONTHS', 1150, WHT, 50)
call(W('4', 'again') + 0.35, starts[order.index('4') + 1], 'BOOM. (AGAIN)', 1150, YEL, 60)
call(W('7', 'gravity'), W('7', 'astronaut'), 'GRAVITY: 1', 1150, WHT, 64)
call(W('7', 'astronaut'), starts[order.index('7') + 1], 'ASTRONAUT: 0', 1150, YEL, 64)
# apollo 10 transcript bubbles
b0 = W('2', 'nobody')
E(b0 - 0.1, starts[order.index('2') + 1], 'Bub', r'{\pos(540,560)\fad(100,0)}' + 'YOUNG: "I didn' + "'" + 't do it. It ain' + "'" + 't one of mine."', 3)
E(b0 + 0.45, starts[order.index('2') + 1], 'Bub', r'{\pos(540,680)\fad(100,0)}' + 'CERNAN: "I don' + "'" + 't think it' + "'" + 's one of mine."', 3)
E(W('2', 'give') - 0.05, b0 - 0.1, 'Bub', r'{\pos(540,560)\fad(100,0)}STAFFORD (CDR), MAY 1969', 3)
# #1 radio label + end card
call(W('1', 'hey') - 0.15, S['1']['e'] + 0.2, 'MISSION CONTROL, ON THE RADIO:', 1150, CYA, 46)
E(S['1']['e'] + 0.25, END, 'Title', r'{\pos(540,1440)\fs86\fscx60\fscy60\t(0,140,\fscx100\fscy100)}WHICH WAS WORST?', 4)
E(S['1']['e'] + 0.25, END, 'Sub', r'{\pos(540,1540)\fad(150,0)\fs52}COMMENT YOUR PICK', 4)
open('build/subs.ass', 'w').write(hdr + '\n'.join(ev) + '\n')
print(len(ev), 'events')
