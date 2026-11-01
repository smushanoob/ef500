import json, sys, os, urllib.request, concurrent.futures as cf
op = urllib.request.build_opener(); op.addheaders = [('User-Agent', 'ShortVideoBuilder/1.0 (CC0 asset fetch)')]; urllib.request.install_opener(op)
def files(aid): return json.load(urllib.request.urlopen(f'https://api.polyhaven.com/files/{aid}', timeout=60))
def get_model(aid, res='1k'):
    f = files(aid)['gltf'][res]['gltf']; base = f'assets/models/{aid}'; os.makedirs(base, exist_ok=True)
    urllib.request.urlretrieve(f['url'], f'{base}/{aid}.gltf')
    for rel, inc in f.get('include', {}).items():
        p = os.path.join(base, rel); os.makedirs(os.path.dirname(p), exist_ok=True); urllib.request.urlretrieve(inc['url'], p)
    return aid
def get_tex(aid, res='1k'):
    f = files(aid); base = f'assets/tex/{aid}'; os.makedirs(base, exist_ok=True); got = []
    for m in ['Diffuse', 'nor_gl', 'Rough', 'arm', 'AO', 'Displacement']:
        if m in f and res in f[m]:
            e = f[m][res].get('jpg') or f[m][res].get('png'); ext = e['url'].rsplit('.', 1)[1]
            urllib.request.urlretrieve(e['url'], f'{base}/{m}.{ext}'); got.append(m)
    return aid + ':' + ','.join(got)
def get_hdri(aid, res='2k'):
    f = files(aid)['hdri'][res]['hdr']; os.makedirs('assets/hdri', exist_ok=True); urllib.request.urlretrieve(f['url'], f'assets/hdri/{aid}.hdr'); return aid
def safe(a):
    try: return fn(a)
    except Exception as e: return f'ERR {a} {e}'
kind = sys.argv[1]; ids = sys.argv[2:]
fn = {'m': get_model, 't': get_tex, 'h': get_hdri}[kind]
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(lambda a: safe(a), ids):
        print(r)
