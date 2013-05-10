#! /usr/local/bin/python

import sys
import voronoi_poly
import pdb
import numpy as np
import matplotlib.pyplot as plt


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


#Run this using the pipe: "cat sample_city_data.cat | python main_example.py"
if __name__=="__main__":


  #Creating the PointsMap from the input data
  PointsMap={}
  fp=open("coords.csv", "r")
  for line in fp:
    data=line.strip().split(",")
    try:
      PointsMap[len(PointsMap)]=(float(data[2]),float(data[1]))
    except:
      sys.stderr.write( "(warning) Invalid Input Line: "+line)
  fp.close()
  
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
  vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox=[max(sy)+1, min(sx)-1, min(sy)-1, max(sx)+1], PlotMap=True)

  dc = dict([(v["info"], k) for k,v in vl.items()])
#  vl=voronoi_poly.VoronoiPolygonsMod(PointsMap, BoundingBox="W", PlotMap=True)

  lens = []
  lensi = []
  for so, details in vl.items():
    d = details["coordinate"]
    for ei, edge in enumerate(details['obj_polygon']):
      for end in [0,1]:
        lens.append((so, ei, end, (edge[end][0]-d[0])**2+(edge[end][1]-d[1])**2))
        #lens.append((edge[end][0]-d[0])**2+(edge[end][1]-d[1])**2)
  lens.sort(key=lambda x:x[3], reverse=True)
  del lens[int(0.1*len(lens)):]
  tmp = lens.pop()
  lens.sort()
  ml = tmp[3]

  # alle = set()
  # for so, details in vl.items():
  #   alle |= set(vl[so]['obj_polygon'])

  # for edge in alle:
  #   ex,ey = zip(*edge)
  #   plt.plot(ex, ey, "k")


  while len(lens) > 0: # and lens[-1][0] == 2667:
    so, ei, end, li = lens.pop()
    if len(lens) > 0 and lens[-1][0:3] == (so, ei, 1-end):
      so, ei, endo, lio = lens.pop()
      ttl = {end: li, endo: lio}
      tmp = vl[so]['obj_polygon'][ei]
      vl[so]['obj_polygon'][ei] = tuple([tuple([vl[so]["coordinate"][c]-(vl[so]["coordinate"][c]-tmp[en][c])*np.sqrt(ml/ttl[en])
                                                for c in [0,1]]) for en in [0,1]])

    else:
      tmp = list(vl[so]['obj_polygon'][ei])

      tll = (tmp[1-end][0]-tmp[end][0])**2+(tmp[1-end][1]-tmp[end][1])**2

      tmpadd = tuple([vl[so]["coordinate"][c]-(vl[so]["coordinate"][c]-tmp[end][c])*np.sqrt(ml/li) for c in [0,1]])
      tmpsti = tuple([tmp[1-end][c]-(tmp[1-end][c]-tmp[end][c])*np.sqrt(ml/(2*tll)) for c in [0,1]])

      if end == 1:
        vl[so]['obj_polygon'][ei] = (tmpsti, tmpadd)
        vl[so]['obj_polygon'].insert(ei,(tmp[0], tmpsti))

      if end == 0:
        vl[so]['obj_polygon'][ei] = (tmpadd, tmpsti)
        vl[so]['obj_polygon'].insert(ei+1,(tmpsti, tmp[1]))


  alle = set()
  for so, details in vl.items():
    alle |= set(details['obj_polygon'])

  
  for edge in alle:
    ex,ey = zip(*edge)
    plt.plot(ex, ey, "b")


  plt.plot(sx, sy, "go")
  pedges = {}
  for so in statson:
    s = dc[so] 
    if vl.has_key(s):
      plt.plot(vl[s]['coordinate'][0], vl[s]['coordinate'][1], "bo")
      
      for edge in vl[s]['obj_polygon']:
        if pedges.has_key(edge):
          pedges[edge] += 1
        else:
          pedges[edge] = 1
    else:
      print "MISSING", s 

  ledges = [k for k,v in pedges.items() if v==1]
  for edge in ledges:
    sx,sy = zip(*edge)
    plt.plot(sx, sy, "r")

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

