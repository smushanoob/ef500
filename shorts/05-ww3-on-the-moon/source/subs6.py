import json, re
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
END = 176.0
order = [x['id'] for x in VO['segs']]
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
Style: Cap,MontBlack,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,9,4,5,40,40,0,1
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
DISPLAY = {'twenty forty nine.': '2049.', 'Fourteen': '14', 'nineteen.': '19.', 'twenty four.': '24.', 'thirty one.': '31.', 'thirty five.': '35.', 'forty.': '40.', 'sixty two.': '62.', 'seventy.': '70.', 'twenty thousand': '20,000', 'four thousand': '4,000', 'Forty': '40', 'six': '6', 'nine': '9', 'three': '3', 'hundred thousand dollar': '$100,000', 'hundred and twenty five million dollar': '$125 MILLION', 'forty': '40', 'sixteen.': '16.', 'ten,': '10,', 'Ten': '10'}
EMPH = {'war', 'ice.', 'coalition:', 'pact:', 'neutral.', 'water', 'air,', 'fuel,', 'power.', 'shackleton', 'strikes', 'first.', 'seize', 'six', 'farther', 'fortresses.', 'satellites', 'crash.', 'pacific.', 'india', 'joins', 'surprise.', 'oxygen', 'ammo.', 'mass', 'driver:', 'target.', 'commandos', 'apart.', 'counterattacks.', 'retake', 'dry.', 'freezes', 'win.', 'collapses', '20,000', '4,000', 'ice.', 'radiation.', 'phones', 'rio.', 'treaty', 'tranquility.', 'everyone.', 'banned', 'forever.', 'water.', 'comments.', 'side', 'fails.', 'loud.', 'sandwich', 'congress', '$100,000', 'moon.', 'miles', '40', 'yards.', 'zero.', 'feet.', 'meters.', 'goodbye,', '$125 million', 'exploded.', 'flopnik.', 'again.', 'dirt.', 'turd', 'confessed.', 'twinkletoes,', 'falling', 'one.', 'one?'}
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
            E(t0, t1, 'Cap', r'{\pos(540,1405)' + start_scale + pop + '}' + ' '.join(parts))


open('build/subs.ass', 'w').write(hdr + '\n'.join(ev) + '\n')
print(len(ev), 'events')
