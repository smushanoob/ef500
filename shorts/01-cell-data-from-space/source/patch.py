import numpy as np, math, sys
from PIL import Image
T=sys.argv[1]; z=7; n=2**z
lon0,lon1,lat0,lat1=-100.0,-70.0,15.0,40.0
ppd=n*256/360.0
W=int((lon1-lon0)*ppd); H=int((lat1-lat0)*ppd)
lon=np.linspace(lon0,lon1,W); lat=np.linspace(lat1,lat0,H)
X=(lon+180)/360*n*256
Y=(1-np.log(np.tan(np.radians(lat))+1/np.cos(np.radians(lat)))/math.pi)/2*n*256
tx0,tx1=int(X.min()//256),int(X.max()//256); ty0,ty1=int(Y.min()//256),int(Y.max()//256)
mos=np.zeros(((ty1-ty0+1)*256,(tx1-tx0+1)*256,3),np.uint8)
for tx in range(tx0,tx1+1):
  for ty in range(ty0,ty1+1):
    mos[(ty-ty0)*256:(ty-ty0+1)*256,(tx-tx0)*256:(tx-tx0+1)*256]=np.array(Image.open(f'{T}/{z}/{tx}/{ty}.jpeg').convert('RGB'))
m=Image.fromarray(mos)
xs=X-tx0*256; ys=Y-ty0*256
# resample rows via PIL transform per row is slow; use map with numpy bilinear
xx,yy=np.meshgrid(xs,ys)
x0=np.floor(xx).astype(int); y0=np.floor(yy).astype(int); fx=(xx-x0)[...,None]; fy=(yy-y0)[...,None]
x0=np.clip(x0,0,mos.shape[1]-2); y0=np.clip(y0,0,mos.shape[0]-2)
a=mos.astype(np.float32)
out=(a[y0,x0]*(1-fx)*(1-fy)+a[y0,x0+1]*fx*(1-fy)+a[y0+1,x0]*(1-fx)*fy+a[y0+1,x0+1]*fx*fy)
Image.fromarray(out.clip(0,255).astype(np.uint8)).save('assets/patch_se_us.jpg',quality=93)
print(W,H, lon0,lon1,lat0,lat1)
