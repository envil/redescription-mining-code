import pdb
import numpy as np
import voronoi_poly


def makePolys(pdp, upd):
    PointsMap=dict([(p, (c1,c2)) for (p, c1, c2) in pdp])
    sx, sy = zip(*PointsMap.values())
    vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=[max(sy)+1, min(sx)-1, min(sy)-1, max(sx)+1])

    dc = dict([(v["info"], k) for k,v in vl.items()])
    vss = set([int(p/7) for p in upd[1]])
  
    neighdc = {}
    lens = []
    lst = dict([(k,[]) for k in vss])
    for so, details in vl.items():
        ppi = int(upd[1][details["info"]]/7)
        d = details["coordinate"]
        for ei, edge in enumerate(details['obj_polygon']):
            if neighdc.has_key(edge):
                neighdc[edge].append(so)
            else:
                neighdc[edge] = [so]
            for end in [0,1]:
                lst[ppi].append((edge[end][0]-d[0])**2+(edge[end][1]-d[1])**2)
                lens.append((so, ei, end, (edge[end][0]-d[0])**2+(edge[end][1]-d[1])**2, ppi))
    lens.sort(key=lambda x:x[3], reverse=True)
    mlb = lens[int(0.1*len(lens))][3]
    mlabs = dict([(p,(mlb+4*sorted(vp)[int(0.4*len(vp))])/5) for (p,vp) in lst.items()])

    lensi = [p for p in lens if p[3] > mlabs[p[4]]]
    lend = dict([(tuple(l[:3]), (l[3], l[4])) for l in lensi])
    lens = sorted(lend.keys())

    # #lens.sort(key=lambda x:x[3]*vl[x[0]]["obj_polygon"][x[1]][x[2]][1], reverse=True)
    # tmpc = int(0.1*len(lens))
    # while lens[tmpc-1][-1] == lens[tmpc][-1] or lens[tmpc-1][0] == lens[tmpc][0]:
    #     tmpc+=1
    # del lens[tmpc+1:]
    # tmp = lens.pop()
    # ml = tmp[3]

    # lend = dict([(tuple(l[:3]), l[3]) for l in lens])
    # lens = sorted(lend.keys())

    mods = {}

    while len(lens) > 0:
        so, ei, end = lens.pop()
        li, mli = lend[(so,ei,end)]
        ml = mlabs[mli]
        if len(lens) > 0 and lens[-1] == (so, ei, 1-end):
            lens.pop()
            ttl = {end: li, 1-end: lend[(so,ei,1-end)][0]}
            tmp = vl[so]['obj_polygon'][ei]
            vl[so]['obj_polygon'][ei] = tuple([tuple([vl[so]["coordinate"][c]-(vl[so]["coordinate"][c]-tmp[en][c])*np.sqrt(ml/ttl[en])
                                                      for c in [0,1]]) for en in [0,1]])

        else:
            tmp = vl[so]['obj_polygon'][ei]

            tll = (tmp[1-end][0]-tmp[end][0])**2+(tmp[1-end][1]-tmp[end][1])**2
            tmpadd = tuple([vl[so]["coordinate"][c]-(vl[so]["coordinate"][c]-tmp[end][c])*np.sqrt(ml/li) for c in [0,1]])

            neighs = neighdc[tmp]

            neigh = min(neighs)
            if neigh == so:
                neigh = max(neighs)
                tmpn = mods.get((neigh,tmp))
            else:
                tmpn = vl[neigh]['obj_polygon'].index(tmp)        
                mods[(so,tmp)] = ei

            lin, dummy = lend.get((neigh, tmpn, end), (None, None))
            if lin is not None:
                tmpaddn = tuple([vl[neigh]["coordinate"][c]-(vl[neigh]["coordinate"][c]-tmp[end][c])*np.sqrt(ml/lin) for c in [0,1]])

                AB = (tmpadd, tmpaddn)
                CD = tmp
                if AB[0][0] == AB[1][0]:
                    x = AB[0][0]
                    y = (CD[0][1]-CD[1][1])/(CD[0][0]-CD[1][0]) *x \
                        + (CD[1][1] - CD[1][0]*(CD[0][1]-CD[1][1])/(CD[0][0]-CD[1][0]))
                elif CD[0][0] == CD[1][0]:
                    x = CD[0][0]
                    y = (AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]) *x \
                        + (AB[1][1] - AB[1][0]*(AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]))
                else:
                    x = ((CD[1][1] - CD[1][0]*(CD[0][1]-CD[1][1])/(CD[0][0]-CD[1][0])) \
                         - (AB[1][1] - AB[1][0]*(AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]))) / \
                         ( (AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]) \
                           - (CD[0][1]-CD[1][1])/(CD[0][0]-CD[1][0]))
                    y = (AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]) *x \
                        + (AB[1][1] - AB[1][0]*(AB[0][1]-AB[1][1])/(AB[0][0]-AB[1][0]))

                tmpsti = (x,y)
            else:
                tmpsti = tmp[end]
            if end == 1:
                vl[so]['obj_polygon'][ei] = (tmpsti, tmpadd)
                vl[so]['obj_polygon'].insert(ei,(tmp[0], tmpsti))

            if end == 0:
                vl[so]['obj_polygon'][ei] = (tmpadd, tmpsti)
                vl[so]['obj_polygon'].insert(ei+1,(tmpsti, tmp[1]))

    ready = {} 
    for s, obj in vl.items():
        ready[obj["info"]] = []

        tmpd = {}
        for a in obj['obj_polygon']:
            for end in [0,1]:
                tmpd.setdefault(a[end], []).append(a[1-end])

        tmpspe = [k for (k,p) in tmpd.items() if len(p) != 2]
        tmp = []
        for k in tmpspe:
            tt = []
            dbls = []
            for e in tmpd[k]:
                if e in tt:
                    tt.remove(e)
                    dbls.append(e)
                else:
                    tt.append(e)
            if len(tt) == 2:
                tmpd[k] = tt
                for di in dbls:
                    if len(tmpd[di]) == 2 and tmpd[di][0] == tmpd[di][1]:
                        del tmpd[di]

            else:
                tmp.append(k)

        if len(tmp) > 0:
            ti = 0
            while ti < len(tmpd[tmp[0]]) and len(tmpd[tmpd[tmp[0]][ti]]) != 2:
                ti += 1
            if ti == len(tmpd[tmp[0]]):
                raise Exception("TROP DUR !")
            else:
                m1 = tmpd[tmp[0]].pop(ti)
                m0, m2 = tmpd.pop(m1)
                if m0 == tmp[0]:
                    tmp1 = [m0, m1, m2]
                else:
                    tmp1 = [m2, m1, m0]
        else:
            m1, (m0, m2) = tmpd.popitem()
            tmp1 = [m0, m1, m2]

        while len(tmpd) > 0:
            try:
                ms = tmpd.pop(tmp1[-1])
            except KeyError:
                pdb.set_trace()
                print tmp1, tmpd
            if len(ms) != 2:
                if tmp1[0] in ms:
                    tmp1.append(ms.pop(ms.index(tmp1[0])))
                    if len(tmpd) > 0:
                        ready[obj["info"]].append(tmp1)
                        tmp1 = [ms.pop(0), tmp1[-2], ms.pop(1)]
            else:
                if ms[0] == tmp1[-2]:
                    tmp1.append(ms[1])
                else:
                    tmp1.append(ms[0])
        ready[obj["info"]].append(tmp1)
    return ready
