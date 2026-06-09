#!/usr/bin/env python3
"""Blueprint verify: what ARE crawler's dungeon walls, and what SHOULD they be?

Replicates crawler's EXACT pointy-top hex geometry (src/hexgeo.loft) and the
current wall pipeline (src/wallgeo.loft) on a representative gen.loft layout
(axial-rectangle rooms + greedy-hex corridor), to pin the concrete end-result
for "straight dungeon walls" BEFORE porting anything to loft.

Three panels per layout:
  A. RAW hex-edge boundary           — straight unit segments, no smoothing (sawtooth)
  B. LAPLACIAN-smoothed (current)    — wallgeo step C: rounds corners, wavy corridors
  C. SNAP-to-room-lines (target)     — snap boundary corners onto each room's exact
                                       rhombus side-lines -> straight + sharp rooms,
                                       corridors & door-gaps untouched (automatic)

The rooms are lattice RHOMBI whose 4 corners gen already knows; the snap needs no
sawtooth simplification — it projects onto the known lines.

    python3 hexdungeon.py
"""
import math, os
from PIL import Image, ImageDraw

SQRT3 = 1.7320508075688772
HW = SQRT3 / 2.0

def hex_to_px(q, r): return (SQRT3 * q + HW * r, 1.5 * r)
CORNER = {0:(0.0,1.0), 1:(-HW,0.5), 2:(-HW,-0.5), 3:(0.0,-1.0), 4:(HW,-0.5), 5:(HW,0.5)}
def hex_corner_px(q, r, i):
    cx, cy = hex_to_px(q, r); ox, oy = CORNER[i]; return (cx + ox, cy + oy)
NEI = {0:(1,0), 1:(1,-1), 2:(0,-1), 3:(-1,0), 4:(-1,1), 5:(0,1)}
def hex_neighbor(q, r, d): dq,dr = NEI[d]; return (q+dq, r+dr)
EDGE_CORNERS = {0:(4,5), 1:(3,4), 2:(2,3), 3:(1,2), 4:(0,1), 5:(5,0)}
def hex_distance(q1,r1,q2,r2):
    dq,dr=q1-q2,r1-r2; return (abs(dq)+abs(dq+dr)+abs(dr))//2

def gen(w, h, rooms):
    tiles=[1]*(w*h); rects=[]; centres=[]
    for (q0,r0,rw,rh) in rooms:
        for r in range(r0,r0+rh):
            for q in range(q0,q0+rw): tiles[r*w+q]=0
        rects.append((q0,r0,rw,rh)); centres.append((q0+rw//2,r0+rh//2))
    for i in range(len(centres)-1):
        (aq,ar),(bq,br)=centres[i],centres[i+1]; cq,cr=aq,ar; guard=0
        while (cq,cr)!=(bq,br) and guard<2000:
            guard+=1; tiles[cr*w+cq]=0
            best=hex_distance(cq,cr,bq,br); nq,nr=cq,cr
            for d in range(6):
                tq,tr=hex_neighbor(cq,cr,d)
                if 1<=tq<w-1 and 1<=tr<h-1:
                    dd=hex_distance(tq,tr,bq,br)
                    if dd<best: best=dd; nq,nr=tq,tr
            if (nq,nr)==(cq,cr): break
            cq,cr=nq,nr
        tiles[br*w+bq]=0
    return tiles, rects

def is_wall(tiles,w,h,q,r):
    if q<0 or r<0 or q>=w or r>=h: return True
    return tiles[r*w+q]==1

def boundary_edges(tiles,w,h):
    edges=[]
    for r in range(h):
        for q in range(w):
            if tiles[r*w+q]!=0: continue
            for d in range(6):
                nq,nr=hex_neighbor(q,r,d)
                if is_wall(tiles,w,h,nq,nr):
                    ca,cb=EDGE_CORNERS[d]
                    edges.append((hex_corner_px(q,r,ca),hex_corner_px(q,r,cb)))
    return edges

# ── corner graph shared by smooth + snap ────────────────────────────
def key(p): return (round(p[0]*1000), round(p[1]*1000))
def graph(edges):
    idx={}; pts=[]; nb=[]
    def goa(p):
        k=key(p)
        if k in idx: return idx[k]
        i=len(pts); idx[k]=i; pts.append(list(p)); nb.append([]); return i
    E=[(goa(a),goa(b)) for a,b in edges]
    for a,b in E: nb[a].append(b); nb[b].append(a)
    return pts, nb, E

def smooth(edges, iters=3, lam=0.5):
    pts,nb,E=graph(edges)
    for _ in range(iters):
        for i in range(len(pts)):
            if len(nb[i])==2:
                p1,p2=pts[nb[i][0]],pts[nb[i][1]]
                mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
                pts[i][0]+=lam*(mx-pts[i][0]); pts[i][1]+=lam*(my-pts[i][1])
    return [(tuple(pts[a]),tuple(pts[b])) for a,b in E]

# ── TARGET: snap boundary corners onto each room's exact rhombus side-lines ──
def room_sides(rect):
    """The 4 exact rhombus corner points + the 4 side-segments, from gen's rect.
    loft-faithful: integer centre cell, squared distance (no sqrt), corner-cell
    cyclic order (no atan2 sort)."""
    q0,r0,rw,rh=rect
    cx,cy=hex_to_px(q0+rw//2, r0+rh//2)              # room centre cell (world)
    cells=[(q0,r0),(q0+rw-1,r0),(q0+rw-1,r0+rh-1),(q0,r0+rh-1)]  # cyclic
    tips=[]
    for (q,r) in cells:                              # outermost corner of each corner-cell
        best=None;bd=-1
        for i in range(6):
            p=hex_corner_px(q,r,i); d=(p[0]-cx)**2+(p[1]-cy)**2
            if d>bd: bd=d;best=p
        tips.append(best)
    return [(tips[i],tips[(i+1)%4]) for i in range(4)]   # consecutive tips = sides

def proj(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; L2=dx*dx+dy*dy
    if L2==0: return (a,1e9,0)
    t=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2
    fx,fy=a[0]+t*dx,a[1]+t*dy
    return ((fx,fy), math.hypot(p[0]-fx,p[1]-fy), t)

def snap(edges, rects, tol=0.62):
    pts,nb,E=graph(edges)
    sides=[s for rect in rects for s in room_sides(rect)]
    for i in range(len(pts)):
        best=None; bd=tol
        for (a,b) in sides:
            f,d,t=proj(pts[i],a,b)
            if d<bd and -0.12<=t<=1.12: bd=d; best=f
        if best: pts[i][0],pts[i][1]=best[0],best[1]
    return [(tuple(pts[a]),tuple(pts[b])) for a,b in E], sides

def hybrid(edges, rects, tol=0.62, iters=3, lam=0.5):
    """Snap corners on a room side-line (-> straight+sharp rooms); Laplacian-smooth
    the rest (-> smooth corridors). Snapped corners are anchored against smoothing."""
    pts,nb,E=graph(edges)
    sides=[s for rect in rects for s in room_sides(rect)]
    anchored=[False]*len(pts)
    for i in range(len(pts)):
        best=None; bd=tol
        for (a,b) in sides:
            f,d,t=proj(pts[i],a,b)
            if d<bd and -0.12<=t<=1.12: bd=d; best=f
        if best: pts[i][0],pts[i][1]=best[0],best[1]; anchored[i]=True
    for _ in range(iters):
        for i in range(len(pts)):
            if len(nb[i])==2 and not anchored[i]:
                p1,p2=pts[nb[i][0]],pts[nb[i][1]]
                mx,my=(p1[0]+p2[0])/2,(p1[1]+p2[1])/2
                pts[i][0]+=lam*(mx-pts[i][0]); pts[i][1]+=lam*(my-pts[i][1])
    return [(tuple(pts[a]),tuple(pts[b])) for a,b in E], sides

# ── render ──────────────────────────────────────────────────────────
def render(tiles,w,h,panels,fname,title=""):
    sc=24; pad=20
    xs=[];ys=[]
    for r in range(h):
        for q in range(w):
            x,y=hex_to_px(q,r); xs.append(x); ys.append(y)
    minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys)
    PW=int((maxx-minx)*sc)+2*pad; PH=int((maxy-miny)*sc)+2*pad
    n=len(panels); W=PW*n+30*(n-1)
    img=Image.new("RGB",(W,PH+30),(248,248,248)); dr=ImageDraw.Draw(img)
    def px(p,k): return (k*(PW+30)+pad+(p[0]-minx)*sc, PH-(pad+(p[1]-miny)*sc)+20)
    FLOOR=(204,190,150)
    for k,(lab,edges,sides) in enumerate(panels):
        for r in range(h):
            for q in range(w):
                if tiles[r*w+q]==0:
                    dr.polygon([px(hex_corner_px(q,r,i),k) for i in range(6)],fill=FLOOR)
        if sides:
            for (a,b) in sides:   # faint guide: the exact room side-lines
                dr.line([px(a,k),px(b,k)],fill=(210,170,170),width=1)
        for a,b in edges:
            dr.line([px(a,k),px(b,k)],fill=(36,32,30),width=3)
        dr.text((k*(PW+30)+pad,4),lab,fill=(20,20,20))
    if title: dr.text((14,PH+12),title,fill=(90,40,40))
    img.save(fname)

if __name__=="__main__":
    out=os.path.join(os.path.dirname(__file__),"out"); os.makedirs(out,exist_ok=True)
    W,H=30,22
    layouts={"2room_corr":[(4,4,6,5),(18,12,7,6)], "3room":[(3,3,5,5),(16,4,7,5),(10,13,8,6)]}
    for name,rooms in layouts.items():
        tiles,rects=gen(W,H,rooms)
        raw=boundary_edges(tiles,W,H)
        sm=smooth(raw)
        sn,sides=snap(raw,rects)
        hy,_=hybrid(raw,rects)
        render(tiles,W,H,[("B. Laplacian (current)",sm,None),
                          ("C. snap-only (rooms sharp, corridor sawtooth)",sn,sides),
                          ("D. HYBRID = snap rooms + smooth corridors",hy,sides)],
               f"{out}/dungeon_{name}.png",
               title=f"{name}: D snaps room corners to known rhombus lines, smooths the rest")
    print("rendered ->",out)
