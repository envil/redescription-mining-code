#! /usr/local/bin/python

import sys
import voronoi_poly1
import pdb
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D


def OnPick(event):
  print type(event.artist)
  if isinstance(event.artist, Polygon):
    
    for ind in event.ind:
      print ind


def binSegments(V, max_k):

  max_k = int(max_k)
  [T,I,J] = np.unique(V, True, True)
  occurences, bds = np.histogram(J, max(J)+1)

  n = len(T)
  cumocc = np.concatenate((np.array([0]), np.cumsum(occurences)), 1)
  cs = np.concatenate((np.array([0]), np.cumsum(T*occurences)), 1)
  css = np.concatenate((np.array([0]), np.cumsum(T**2*occurences)), 1)
  sigma = np.zeros((n,n));

  for i in range(len(T)):
    for j in range(i+1,len(T)):
        sigma[i,j] = (css[j+1] - css[i]) - (1.0/(cumocc[j+1]-cumocc[i]))*(cs[j+1]-cs[i])**2

  E = np.zeros((max_k,n))
  E[0,:] = sigma[0,:]
  B = np.zeros((max_k,n))

  for k in range(1,max_k):
    for cutp in range(k,n):
      tmp = E[k-1,:cutp]+sigma[1:cutp+1,cutp]
      B[k,cutp] = np.argmin(tmp)
      E[k,cutp] = tmp[B[k,cutp]]
  
  opt_k = np.argmin(E[:,n-1])
  cost = E[opt_k,n-1]

  cuts = [B[opt_k,n-1], n-1]
  for j in range(opt_k-1,0,-1):
    cuts = [B[j,cuts[0]]]+cuts
  cuts = np.unique([-1] + cuts)

  buckets = np.zeros((n,1))
  bounds = []
  for i in range(len(cuts)-1):
    buckets[cuts[i]+1:cuts[i+1]+1] = i
    bounds.append(T[cuts[i]+1])

  bounds.pop(0)
  assign = [int(buckets[j][0]) for j in J]
  return assign, bounds, cost, opt_k

WATER_COLOR = "#FFFFFF"
GROUND_COLOR = "#FFFFFF"
LINES_COLOR = "gray"

def setM(datapoints):
  pl = plt.figure()
  ax = pl.add_axes([0, 0, 1, 1])
  t, x, y = zip(*datapoints)
  llon, ulon, llat, ulat = min(x)-2, max(x)+2, min(y)-2, max(y)+2
  m = Basemap(llcrnrlon=llon, llcrnrlat=llat, urcrnrlon=ulon, urcrnrlat=ulat, \
              resolution = 'c', projection = 'mill', \
              lon_0 = llon + (ulon-llon)/2.0, \
              lat_0 = llat + (ulat-llat)/2.04)

  m.drawcoastlines(color=LINES_COLOR)
  m.drawcountries(color=LINES_COLOR)
  m.drawmapboundary(fill_color=WATER_COLOR) 
  m.fillcontinents(color=GROUND_COLOR, lake_color=WATER_COLOR) #'#EEFFFF')
  px, py = m(x,y)
  coords_proj = zip(t, px, py)
  return m, coords_proj, ax, pl

#Run this using the pipe: "cat sample_city_data.cat | python main_example.py"
if __name__=="__main__":


  #Creating the PointsMap from the input data
  fp=open("coords.csv", "r")
  datapoints = []
  for line in fp:
    data=line.strip().split(",")
    try:
#      datapoints.append((data[0], float(data[1]),float(data[2])))
      datapoints.append((len(datapoints), float(data[2]),float(data[1])))
    except:
      sys.stderr.write( "(warning) Invalid Input Line: "+line)
  fp.close()

  m, pdp, ax, pl = setM(datapoints)

  PointsMap=dict([(p, (c1,c2)) for (p, c1, c2) in pdp])
  
  statson = []
  fp=open("supp.csv", "r")
  for line in fp:
    for st in line.strip().split(" "):
      try:
        statson.append(int(st))
      except:
        sys.stderr.write( "(warning) Invalid Input Line: "+line)
  fp.close()

  sx, sy = zip(*PointsMap.values())
  #1. Stations, Lines and edges
  vl=voronoi_poly1.VoronoiPolygonsMod(PointsMap, BoundingBox=[max(sy)+1, min(sx)-1, min(sy)-1, max(sx)+1])

  dc = dict([(v["info"], k) for k,v in vl.items()])
#  vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox="W", PlotMap=True)

  vss = set([int(p[2]/7) for p in datapoints])
  print vss

  neighdc = {}
  lens = []
  lst = dict([(k,[]) for k in vss])
  for so, details in vl.items():
    ppi = int(datapoints[details["info"]][2]/7)
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
#  mlabs = dict([(p,(mlb+np.median(vp))/2) for (p,vp) in lst.items()])
  mlbbs = dict([(p,sorted(vp)[int(0.4*len(vp))]) for (p,vp) in lst.items()])
  mlabs = dict([(p,(mlb+4*sorted(vp)[int(0.4*len(vp))])/5) for (p,vp) in lst.items()])
  #mlabs = {8: 10**20, 7: 10**10, 6: 10**10, 5: 10**10, 4: 10**10, 3: 10**9, 2: 10**7}
  print mlbbs
  # tmpc = int(0.075*len(lens))
  # while lens[tmpc-1][-1] == lens[tmpc][-1] or lens[tmpc-1][0] == lens[tmpc][0]:
  #   tmpc+=1
  # del lens[tmpc+1:]
  # tmp = lens.pop()
  # ml = tmp[3]

  lensi = [p for p in lens if p[3] > mlabs[p[4]]]
  lend = dict([(tuple(l[:3]), (l[3], l[4])) for l in lensi])
  lens = sorted(lend.keys())
              
  # alle = set()
  # for so, details in vl.items():
  #   alle |= set(vl[so]['obj_polygon'])

  # for edge in alle:
  #   ex,ey = zip(*edge)
  #   m.plot(ex, ey, "k")


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


  # for edge in vl[1466]['obj_polygon']:
  #   ex,ey = zip(*edge)
  #   m.plot(ex, ey, "k")

  # for edge in vl[1843]['obj_polygon']:
  #   ex,ey = zip(*edge)
  #   m.plot(ex, ey, "k")

  # plt.show()

  i = 0
  ready = {} 
  #for s, obj in [(1293, vl[1293])]:
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
        print tmp1
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

  #pdb.set_trace()
  for s, ps in ready.items():
    if s in statson:
      clr = "#EE0000"
      clre = "#FF0000"
    else:
      clr = "#00EE00"
      clre = "#00FF00"
    for p in ps:
      ax.add_patch(Polygon(p, closed=True, fill=True, fc=clr, ec=clre, picker=True))
      
  pl.canvas.mpl_connect('pick_event', OnPick)
  plt.show()


  exit()
##################################
  

  # #ps = sorted(PointsMap.values(), key=lambda x:(x[1], x[0]))
  # sx, sy = zip(*PointsMap.values())

  # assigny, boundsy, cost, opt_k = binSegments(sy, 2*int(max(sy)+0.99-min(sy)))
  # # plt.scatter(sx, sy, c=assigny, s=500)
  # # plt.show()
  
  # stepx = (max(sx)-min(sx))/6

  # lbx = min(sx)
  # while lbx < max(sx):
  #   tmp = [(i,v[0],v[1]) for i,v in enumerate(PointsMap.values()) if v[0] >= lbx and v[0] < lbx+stepx and v]

  #   if len(tmp) > 25:
  #     ti, tx, ty = zip(*tmp)
      
  #     assignx, boundsx, cost, opt_k = binSegments(tx, 2*int(max(tx)+0.99-min(tx)))

  #     asspairs = zip(assignx, [assigny[t] for t in ti])

  #     pdb.set_trace()
  #     addap = []
  #     for ap in asspairs:
  #       for (la, lo) in [(1,-1), (-1,1), (1,1), (-1,-1)]:
  #         if (ap[0]+la, ap[1]+lo) not in asspairs \
  #                and (ap[0]+la, ap[1]+lo) not in asspairs \
  #                and (ap[0]+la, ap[1]+2*lo) not in asspairs \
  #                and (ap[0]+2*la, ap[1]+lo) not in asspairs \
  #                and (ap[0]+2*la, ap[1]+2*lo) not in asspairs \
  #                and (ap[0]+la, ap[1]+lo) not in addap \
  #                and (ap[0]+la, ap[1]+2*lo) not in addap \
  #                and (ap[0]+2*la, ap[1]+lo) not in addap \
  #                and (ap[0]+2*la, ap[1]+2*lo) not in addap:

  #           addap.append((ap[0]+la, ap[1]+lo))
  #     print len(addap)

  #     tbx = boundsx+[boundsx[-1]+1, boundsx[0]-1]
  #     tby = boundsy+[boundsy[-1]+1, boundsy[0]-1]
  #     adds = [(tbx[a[0]], tby[a[1]]) for a in addap]
  #     plt.scatter(tx, ty, c=assignx, s=200)
  #     adx, ady = zip(*adds)
  #     plt.scatter(adx, ady, s=90)
  #     plt.show()
  #     pdb.set_trace()
      
  #     #pdb.set_trace()
  #   lbx += stepx

  # # dx = np.diff(sx)
  # # std2 = np.std([d for d in dx if d > 0])
  # # dpx = [d for d in dx if d > 0 and d<std2]
  # # hist, bin_edges = np.histogram(dpx, 100)
  # # ddx = np.diff(hist)
  # # i = 1
  # # while i<len(ddx) and ddx[i] < 0:
  # #   i+=1
  # # bd = bin_edges[i]

  # # mv = np.mean([d for d in dpx if d < bd])
  # # #bd = std2
  # # bd = 10
  # # print "X", bd, mv

  # mv = 1
  # ps = sorted(PointsMap.values(), key=lambda x:(int(x[1]), x[0]))
  # print ps[0]
  # added = []
  # for i in range(1, 10):
  #   print ps[i]
  #   if ps[i+1][0] - ps[i][0] >  2*(ps[i][0] - ps[i-1][0]) or ps[i+1][0] - ps[i][0] < 0:
  #     #print ps[i-1], ps[i], ps[i+1], ps[i+1][0] - ps[i][0]
  #     added.append((ps[i][0]+mv, ps[i][1]))
  #     added.append((ps[i+1][0]-mv, ps[i+1][1]))
  # pdb.set_trace()

