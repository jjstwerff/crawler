#!/usr/bin/env python3
"""Triangle-subdivision wall model — 2D reference prototype (see ../../WALLS.md).

A constructed wall is the band of small triangles a wall line passes through
(vertex-based straddle: a triangle is room iff all 3 vertices are inside the
inner face, exterior iff all 3 are outside the outer face, else wall). Walls in
the 3 lattice directions come out straight; others get a collision-correct band
whose faces are straightened by the center-of-lines pass (offset polygon, miter
corners). Validates: rhombus / rect / thick / door, plus corner tests.

    python3 walltri.py            # render forms to ./out + run corner tests
"""
import math, os
from PIL import Image, ImageDraw

S3 = math.sqrt(3.0)
def vert(i, j): return (i + 0.5*j, j*S3/2.0)
def tri_pts(i, j, up):
    return [vert(i,j),vert(i+1,j),vert(i,j+1)] if up else \
           [vert(i+1,j),vert(i,j+1),vert(i+1,j+1)]

# ── geometry helpers ────────────────────────────────────────────────
def pip(pt, poly):
    x,y=pt; n=len(poly); ins=False; j=n-1
    for i in range(n):
        xi,yi=poly[i]; xj,yj=poly[j]
        if ((yi>y)!=(yj>y)) and (x<(xj-xi)*(y-yi)/(yj-yi)+xi): ins=not ins
        j=i
    return ins
def dseg(p,a,b):
    px,py=p; ax,ay=a; bx,by=b; dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    if L2==0: return math.hypot(px-ax,py-ay)
    t=max(0.0,min(1.0,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx),py-(ay+t*dy))
def dpoly(pt,poly): return min(dseg(pt,poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly)))

# ── classification: vertex-based straddle ───────────────────────────
WALL,ROOM,EXT = 0,1,2
def vstate(v, poly, ht):
    ins=pip(v,poly); d=dpoly(v,poly)
    if ins and d>ht: return 1          # inside inner face -> room
    if (not ins) and d>ht: return 2    # outside outer face -> exterior
    return 0                           # in the band
def classify(i,j,up, poly, ht):
    s=[vstate(v,poly,ht) for v in tri_pts(i,j,up)]
    if all(x==1 for x in s): return ROOM
    if all(x==2 for x in s): return EXT
    return WALL

# ── center-of-lines pass: straighten faces, miter corners ───────────
def enorm(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; L=math.hypot(dx,dy); return (dy/L,-dx/L)
def isect(p1,d1,p2,d2):
    x1,y1=p1; ax,ay=d1; x2,y2=p2; bx,by=d2; den=ax*by-ay*bx
    if abs(den)<1e-9: return None
    t=((x2-x1)*by-(y2-y1)*bx)/den; return (x1+t*ax,y1+t*ay)
def offset_poly(poly, dist):
    n=len(poly); out=[]
    for i in range(n):
        a,b,c=poly[(i-1)%n],poly[i],poly[(i+1)%n]
        nab,nbc=enorm(a,b),enorm(b,c)
        pab=(b[0]+dist*nab[0],b[1]+dist*nab[1]); dab=(b[0]-a[0],b[1]-a[1])
        pbc=(b[0]+dist*nbc[0],b[1]+dist*nbc[1]); dbc=(c[0]-b[0],c[1]-b[1])
        x=isect(pab,dab,pbc,dbc); out.append(x if x else pab)
    return out
def lerp(a,b,t): return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))

# ── rendering ───────────────────────────────────────────────────────
BAND=(36,32,30); ROOMC=(216,198,150)
def render(poly, ht, fname, straighten, door=None, title=""):
    scale=40; ox=70; oy=30; W=980; H=620
    img=Image.new("RGB",(W,H),(248,248,248)); dr=ImageDraw.Draw(img)
    def px(p): return (ox+p[0]*scale, H-(oy+p[1]*scale))
    de,s0,s1 = (door if door else (-1,0,0)); n=len(poly)
    if straighten:
        outer=offset_poly(poly,max(ht,0.18)); inner=offset_poly(poly,-max(ht,0.18))
        for k in range(n):
            if k==de:
                ji0,ji1=lerp(inner[k],inner[(k+1)%n],s0),lerp(inner[k],inner[(k+1)%n],s1)
                jo0,jo1=lerp(outer[k],outer[(k+1)%n],s0),lerp(outer[k],outer[(k+1)%n],s1)
                dr.polygon([px(inner[k]),px(ji0),px(jo0),px(outer[k])],fill=BAND)
                dr.polygon([px(ji1),px(inner[(k+1)%n]),px(outer[(k+1)%n]),px(jo1)],fill=BAND)
            else:
                dr.polygon([px(inner[k]),px(inner[(k+1)%n]),px(outer[(k+1)%n]),px(outer[k])],fill=BAND)
        dr.polygon([px(p) for p in inner],fill=ROOMC)
        for c in poly: dr.ellipse([px(c)[0]-4,px(c)[1]-4,px(c)[0]+4,px(c)[1]+4],fill=(210,40,40))
    else:
        for i in range(-10,26):
            for j in range(0,17):
                for up in (True,False):
                    if classify(i,j,up,poly,ht)!=WALL: continue
                    if de>=0:
                        c=[(p[0],p[1]) for p in tri_pts(i,j,up)]
                        cc=((c[0][0]+c[1][0]+c[2][0])/3,(c[0][1]+c[1][1]+c[2][1])/3)
                        best=(1e9,0,0.0)
                        for ei in range(n):
                            a=poly[ei]; b=poly[(ei+1)%n]; dx,dy=b[0]-a[0],b[1]-a[1]; L2=dx*dx+dy*dy
                            t=max(0.0,min(1.0,((cc[0]-a[0])*dx+(cc[1]-a[1])*dy)/L2))
                            d=math.hypot(cc[0]-(a[0]+t*dx),cc[1]-(a[1]+t*dy))
                            if d<best[0]: best=(d,ei,t)
                        if best[1]==de and s0<=best[2]<=s1: continue
                    dr.polygon([px(p) for p in tri_pts(i,j,up)],fill=BAND)
    if title: dr.text((14,10),title,fill=(20,20,20))
    img.save(fname)

# ── corner tests ────────────────────────────────────────────────────
def ang(a,b,c):
    v1=(a[0]-b[0],a[1]-b[1]); v2=(c[0]-b[0],c[1]-b[1])
    d=(v1[0]*v2[0]+v1[1]*v2[1])/(math.hypot(*v1)*math.hypot(*v2))
    return math.degrees(math.acos(max(-1,min(1,d))))
def corner_tests(poly, ht, name, expect):
    outer=offset_poly(poly,ht); inner=offset_poly(poly,-ht); n=len(poly); ok=True
    print(f"== {name} (ht={ht}) ==")
    for i in range(n):
        a,b,c=poly[(i-1)%n],poly[i],poly[(i+1)%n]
        A=ang(a,b,c); cov=(not pip(b,inner)) and pip(b,outer)
        aok=abs(A-expect[i])<0.5
        print(f"  corner {i} {tuple(round(x,2) for x in b)}: angle {A:6.2f} (exp {expect[i]:.2f}) "
              f"{'OK' if aok else 'BAD'}  miter o={tuple(round(x,2) for x in outer[i])} "
              f"i={tuple(round(x,2) for x in inner[i])}  covers={'OK' if cov else 'BAD'}")
        ok = ok and aok and cov
    print("  ->", "PASS" if ok else "FAIL"); return ok

def rh(i0,j0,a,b): return [vert(i0,j0),vert(i0+a,j0),vert(i0+a,j0+b),vert(i0,j0+b)]

if __name__=="__main__":
    out=os.path.join(os.path.dirname(__file__),"out"); os.makedirs(out,exist_ok=True)
    rect=[(3,3),(15,3),(15,11),(3,11)]; rhom=rh(4,2,11,9)
    render(rhom,0.0,f"{out}/01_rhombus_aligned.png",False,title="rhombus (lattice-aligned): auto-straight band")
    render(rect,0.0,f"{out}/02_rect_raw.png",False,title="rect: raw band (90deg sides sawtooth, collision-correct)")
    render(rect,0.0,f"{out}/03_rect_straight.png",True,title="rect: center-of-lines straightened")
    render(rect,0.75,f"{out}/04_rect_thick.png",True,title="rect ~1hex thick: straightened")
    render(rect,0.0,f"{out}/05_door_raw.png",False,door=(3,0.38,0.62),title="room+door: raw band, real collision gap")
    render(rect,0.0,f"{out}/06_door_straight.png",True,door=(3,0.38,0.62),title="room+door: straightened, clean jambs")
    print("rendered 6 forms ->", out)
    re=[ang(rhom[-1],rhom[0],rhom[1]),ang(rhom[0],rhom[1],rhom[2]),
        ang(rhom[1],rhom[2],rhom[3]),ang(rhom[2],rhom[3],rhom[0])]
    a=corner_tests(rect,0.30,"rect",[90,90,90,90]); b=corner_tests(rhom,0.30,"rhombus",re)
    print("\nALL CORNER TESTS:", "PASS" if a and b else "FAIL")
