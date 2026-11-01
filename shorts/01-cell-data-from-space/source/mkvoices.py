import numpy as np, glob, os, sys
d={}
for f in glob.glob(sys.argv[1]+'/*.bin'):
    a=np.fromfile(f,dtype=np.float32).reshape(-1,1,256); d[os.path.basename(f)[:-4]]=a
np.savez(sys.argv[2],**d); print(len(d), a.shape)
