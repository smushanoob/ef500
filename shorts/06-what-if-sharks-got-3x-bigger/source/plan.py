import json, subprocess, os, sys, glob
VO = json.load(open('vo.json')); S = {s['id']: s for s in VO['segs']}
order = [s['id'] for s in VO['segs']]
ST = {k: (S[k]['s'] if i else 0.0) for i, k in enumerate(order)}
def W(sid, w, n=0): return [x['s'] for x in S[sid]['words'] if x['w'].strip('.,?:!').lower().startswith(w.lower())][n]
FPS = 30
RAW = {os.path.splitext(os.path.basename(f))[0]: f for f in glob.glob('raw/*') + glob.glob('rawnoaa/*') if not f.endswith('.part')}
# labels shown on the "REAL FOOTAGE" chip
LAB = {'noaa_sixgill': 'BLUNTNOSE SIXGILL SHARK · NOAA', 'noaa_grouper': 'DEEP-SEA SHARKS FEEDING · NOAA', 'noaa_sandtiger': 'SMALLTOOTH SAND TIGER · NOAA', 'noaa_greenland': 'GREENLAND SHARK · NOAA', 'noaa_dogfish': 'DOGFISH SHARK · NOAA', 'gw_play': 'GREAT WHITE', 'gw_cage1': 'GREAT WHITE', 'gw_cage2': 'GREAT WHITE', 'tiger_bah': 'TIGER SHARK · BAHAMAS', 'tiger_fiji': 'TIGER SHARK · FIJI',
       'whale': 'WHALE SHARK', 'hammer': 'HAMMERHEAD HUNTING', 'aerial_bt': 'BLACKTIP REEF SHARK · AUSTRALIA', 'grey': 'GREY REEF SHARKS · BORNEO', 'bt_hawaii': 'BLACKTIP REEF SHARK · HAWAII',
       'thresher': 'THRESHER SHARK', 'ocsheriff': 'GREAT WHITES OFF ORANGE COUNTY, CA', 'diving': 'SHARK DIVE', 'bull': 'BULL SHARKS · MEXICO', 'gw_efield': 'GREAT WHITE · SOUTH AUSTRALIA'}
# (key, src start seconds, t0, t1, crop-x 0..1, zoom0, zoom1, dim)
PLAN = json.load(open('shotplan.json')) if os.path.exists('shotplan.json') else []
shots = []
for i, (key, ss, t0, t1, cx, z0, z1, dim) in enumerate(PLAN):
    t0 = eval(str(t0)); t1 = eval(str(t1)); n = int(round((t1 - t0) * FPS)) + 2
    sid = f'{i:02d}_{key}'; shots.append(dict(id=sid, key=key, t0=t0, t1=t1, n=n, z0=z0, z1=z1, dim=dim, credit=True, label=LAB.get(key, key.upper())))
    if '--extract' in sys.argv:
        d = f'foot/{sid}'; os.makedirs(d, exist_ok=True)
        if len(os.listdir(d)) >= n: continue
        vf = f"fps={FPS},scale=-2:1920:flags=lanczos,crop=1080:1920:(iw-1080)*{cx}:0,unsharp=5:5:0.6,eq=contrast=1.05:saturation=1.12"
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', RAW[key], '-frames:v', str(n), '-vf', vf, '-q:v', '3', f'{d}/%05d.jpg'], check=True)
        print('extracted', sid, len(os.listdir(d)))
json.dump(shots, open('shots.json', 'w'), indent=1)
print(len(shots), 'shots')
