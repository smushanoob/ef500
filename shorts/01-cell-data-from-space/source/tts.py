import sys, json, numpy as np, soundfile as sf, re
from kokoro_onnx import Kokoro
model, voices, voice, speed, out = sys.argv[1:6]
k=Kokoro(model, voices)
lines=json.load(open('script.json'))
sr=24000; audio=[np.zeros(int(0.12*sr),np.float32)]; t=0.12; words=[]
def trim(a, th=0.008):
    e=np.convolve(np.abs(a),np.ones(240)/240,'same'); idx=np.where(e>th)[0]
    return a[max(0,idx[0]-120):idx[-1]+240]
for li,L in enumerate(lines):
    a,_=k.create(L['say'], voice=voice, speed=float(speed), lang='en-us'); a=trim(a)
    # silence gaps inside
    e=np.convolve(np.abs(a),np.ones(480)/480,'same'); quiet=e<0.006
    gaps=[]; i=0
    while i<len(quiet):
        if quiet[i]:
            j=i
            while j<len(quiet) and quiet[j]: j+=1
            if (j-i)/sr>0.07 and i>0 and j<len(quiet): gaps.append(((i+j)/2/sr,(j-i)/sr))
            i=j
        else: i+=1
    # weights per display word by spoken letters
    toks=[]
    for w in L['show']:
        spoken = w[2] if len(w)>2 else w[0]
        toks.append((w[0], len(re.sub(r'[^a-z]','',spoken.lower()))+2, bool(re.search(r'[,.]$',w[0]))))
    dur=len(a)/sr
    # segment by punctuation boundaries, snapping to the largest gaps in order
    segs=[[]]
    for tk in toks:
        segs[-1].append(tk)
        if tk[2] and tk is not toks[-1]: segs.append([])
    nb=len(segs)-1
    tot=sum(x[1] for x in toks)
    # predicted boundaries
    acc=0; pred=[]
    for s in segs[:-1]:
        acc+=sum(x[1] for x in s); pred.append(acc/tot*dur)
    bounds=[]
    for p in pred:
        cand=[g for g in gaps if abs(g[0]-p)<0.6 and (not bounds or g[0]>bounds[-1]+0.2)]
        bounds.append(min(cand,key=lambda g:abs(g[0]-p))[0] if cand else p)
    edges=[0]+bounds+[dur]
    for s,(a0,a1) in zip(segs,zip(edges[:-1],edges[1:])):
        sw=sum(x[1] for x in s); c=a0
        for tk in s:
            d=(a1-a0)*tk[1]/sw; words.append({'w':tk[0],'s':round(t+c,3),'e':round(t+c+d,3),'line':li}); c+=d
    print(li, round(dur,2), 'gaps', [round(g[0],2) for g in gaps], 'bounds', [round(b,2) for b in bounds])
    audio.append(a); t+=dur
    audio.append(np.zeros(int(L['gap']*sr),np.float32)); t+=L['gap']
full=np.concatenate(audio); sf.write(out+'.wav', full, sr)
json.dump({'dur':len(full)/sr,'words':words}, open(out+'.json','w'), indent=0)
print('TOTAL', len(full)/sr)
