#! /usr/local/bin/python

import sys
import pdb
import numpy
import matplotlib.pyplot as plt

import matplotlib.cm
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

import prepare_polygons

PLOT = True
VERBOSE = False

GRT_CIR = 6370.997

COLORS = {-1: "#FFFFFF", 0: "#F0F0F0", 1:"#662A8D", 2: "#FC5864", 3: "#74A8F6", 4:"#AAAAAA"}


def computeExt(neigh_fn, sep=",", id_int=False, coordsp={}):    
    neighbors = {}
    split_graph = {}
    border_points = set()
    edges = {}
    exts = set()
    with open(neigh_fn) as fp:
        for line in fp:
            parts = line.strip().split(sep)
            idE = int(parts[0])
            
            iidA = parts[1].strip("\"")
            if iidA == "None":
                iidA = None
            elif id_int:
                iidA = int(iidA)

            iidB = parts[2].strip("\"")
            if iidB == "None":
                iidB = None
            elif id_int:
                iidB = int(iidB)

            typN = int(parts[3].strip())
            xs = [float(x) for x in parts[4].strip("\"").split(":")]
            ys = [float(y) for y in parts[5].strip("\"").split(":")]
            edges[idE] = (xs, ys)
            if typN != 0:
                for ii, jj in [(0,1), (1,0)]:
                    if (xs[ii], ys[ii]) not in split_graph:
                        split_graph[(xs[ii], ys[ii])] = {}
                    split_graph[(xs[ii], ys[ii])][(xs[jj], ys[jj])] = idE
                if typN == -1:
                    border_points.update([(xs[0], ys[0]), (xs[1], ys[1])])
                    
    all_split_points = split_graph.keys()
    seen={}
    ccs = []
    idEs = [] 
    for v in border_points:
        if v not in seen:
            c, idEsX = ss_spides(v, split_graph)
            ccs.append(list(c))
            idEs.append(idEsX)
            seen.update(c)
                    
    border_edges = {}
    parts = neigh_fn.split(".")
    parts[-2] += "_details"
    det_fn = ".".join(parts)
    with open(det_fn) as fp:
        for line in fp:
            parts = line.strip().split(sep)
            pps = parts[-1].split(":")
            found = []
            i = 0
            while i < len(pps) and not found: 
                if len(pps[i]) > 0 and abs(int(pps[i])) in idEs[0]:
                    found.append(abs(int(pps[i]))) #= True
                i += 1
            if len(found) > 0:
                cid = parts[0].strip("\"")
                if id_int:
                    cid = int(cid)
                start = int(parts[-3])
                stop = int(parts[-2])
                if stop == -1 or stop+1 >= len(coordsp[cid]):
                    stop = len(coordsp[cid])-1
                    
                for i in range(start, stop):
                    border_edges[(coordsp[cid][i], coordsp[cid][i+1])] = (cid, i)
                    border_edges[(coordsp[cid][i+1], coordsp[cid][i])] = (cid, -(i+1))
    return border_edges


def loadNeighbors(neigh_fn, sep=",", id_int=False):    
    neighbors = {}
    exts = set()
    with open(neigh_fn) as fp:
        for line in fp:
            parts = line.strip().split(sep)
            iidA = parts[0].strip("\"")
            if iidA == "None":
                iidA = None
            elif id_int:
                iidA = int(iidA)

            iidB = parts[1].strip("\"")
            if iidB == "None":
                iidB = None
            elif id_int:
                iidB = int(iidB)

            typN = int(parts[2].strip())
            if typN != 0:
                exts.add(iidA)
                exts.add(iidB)
                
            if iidA not in neighbors:
                neighbors[iidA] = {}
            neighbors[iidA][iidB] = typN
            if iidB not in neighbors:
                neighbors[iidB] = {}
            neighbors[iidB][iidA] = typN
    exts.discard(None)
    return neighbors, exts

    
def loadCoordsPolys(coordsp_fn, sep=",", id_int=False):    
    coordsp = {}
    with open(coordsp_fn) as fp:
        for line in fp:
            parts = line.strip().split(sep)
            iid = parts[0].strip("\"")
            if id_int:
                iid = int(iid)
            xs = map(float, parts[1].strip("\"").split(":"))
            ys = map(float, parts[2].strip("\"").split(":"))
            coords = None
            if len(xs) == len(ys):
                coords = zip(xs, ys)
            coordsp[iid] = prepare_polygons.dedup_poly(coords)
    return coordsp

def prepare_cc_polys(ccells, cell_list, coordsp):
    edge_counts = {}
    for cell in ccells:
        ss = cell_list[cell]
        for i in range(1, len(coordsp[ss])):
            org_edge = (coordsp[ss][i-1], coordsp[ss][i])
            if org_edge[1] < org_edge[0]:
                edge = (org_edge[1], org_edge[0])
            else:
                edge = (org_edge[0], org_edge[1])
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    borders = [e for e,c in edge_counts.items() if c == 1]
    fps, fpis = prepare_polygons.flatten_poly(borders)
    polys = []
    for pp in fps:
        polys.extend(prepare_polygons.clean_poly(pp))
    return polys

def make_edges_graph(coordsp, cell_map):
    edges_graph = {}
    edges_list = []
    edges_map = {}
    for ss in coordsp:                                
        for i in range(1, len(coordsp[ss])):
            org_edge = (coordsp[ss][i-1], coordsp[ss][i])
            if org_edge not in edges_map:                
                if org_edge[1] < org_edge[0]:
                    edge = (org_edge[1], org_edge[0])
                else:
                    edge = (org_edge[0], org_edge[1])
                edges_map[edge] = len(edges_list)
                edges_map[(edge[1], edge[0])] = -len(edges_list)
                edges_list.append(edge)
                edges_graph[edges_map[edge]] = []
            edges_graph[abs(edges_map[org_edge])].append(cell_map[ss])
    return edges_graph, edges_list, edges_map

def make_cells_graph(edges_graph):
    cells_graph = {}
    for (edge, cells) in edges_graph.items():
        for cell in cells:
            if cell not in cells_graph:
                cells_graph[cell] = {}
            for cellx in cells:
                if cell != cellx:
                    cells_graph[cell][cellx] = edge
    return cells_graph


def ss_spides(source, splits_graph):
    seen={}                  # level (number of hops) when seen in BFS
    idEs = set()
    level=0                  # the current level
    nextlevel=set([source])  # dict of nodes to check at next level
    while nextlevel:
        thislevel=nextlevel  # advance to next level
        nextlevel=set()         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v]=level # set the level of vertex v
                for c, idE in splits_graph[v].items():
                    idEs.add(idE)
                    nextlevel.add(c) # add neighbors of v
        level=level+1
    return seen, idEs  # return all path lengths as dictionary


def ss_splength(source, cells_graph, cells_colors=None):
    seen={}                  # level (number of hops) when seen in BFS
    level=0                  # the current level
    nextlevel=set([source])  # dict of nodes to check at next level
    while nextlevel:
        thislevel=nextlevel  # advance to next level
        nextlevel=set()         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v]=level # set the level of vertex v
                nextlevel.update([c for c in cells_graph[v].keys() if cells_colors is None or (c >= 0 and cells_colors[v] == cells_colors[c])]) # add neighbors of v
        level=level+1
    return seen  # return all path lengths as dictionary


def connected_components(cells_graph, cells_colors, color):
    seen={}
    pool = numpy.where(cells_colors == color)[0]
    for v in pool:
        if v not in seen:
            c = ss_splength(v, cells_graph, cells_colors)
            yield list(c)
            seen.update(c)


#Run this for instance as "python prepare_polygons.py ~/coords.csv ~/poly_coords.csv - map"
if __name__=="__main__":

    NAMES_CID = 0
    LAT_CID = 2
    LNG_CID = 1
    SEP = ","
    
    REP = "./"
    SUPP_FN = "supp_EU.csv"
    POLY_FN = "poly_coords_EU.csv"
    EDGES_FN = "poly_edges_EU.csv"
    MK_MAP = True
    ID_INT = False
    
    # POLY_FN = None
    # EDGES_FN = None
    # MK_MAP = False


    if len(sys.argv) == 2:
        REP = sys.argv[1]
    elif len(sys.argv) > 1:
        SUPP_FN = sys.argv[1]
        
    if len(sys.argv) > 2:
        if sys.argv[2] != "-":
            POLY_FN = sys.argv[2]
    if len(sys.argv) > 3:
        if sys.argv[3] != "-":
            EDGES_FN = sys.argv[3]
    if len(sys.argv) > 4:
        if sys.argv[4] == "map":
            MK_MAP = True
    

    print REP, SUPP_FN, POLY_FN, EDGES_FN, MK_MAP

    coordsp = loadCoordsPolys(REP+POLY_FN, sep=SEP, id_int=ID_INT)
    border_edges = computeExt(REP+EDGES_FN, sep=SEP, id_int=ID_INT, coordsp=coordsp)
    
    cell_list = sorted(coordsp.keys())
    cell_map = dict([(v,k) for (k,v) in enumerate(cell_list)])
    
    edges_graph, edges_list, edges_map = make_edges_graph(coordsp, cell_map)

    ### EXTERIOR/INTERIOR BORDERS
    out = [edges_list[k] for k,vs in edges_graph.items() if len(vs) == 1]
    fps, fpis = prepare_polygons.flatten_poly(out)
    out_data = {}
    for pp in fps:        
        for poly in prepare_polygons.clean_poly(pp):
            ci = -(len(out_data)+1)
            interior = True
            for i in range(1, len(poly)):
                org_edge = (poly[i-1], poly[i])
                if org_edge in border_edges:
                    interior = False
                edges_graph[abs(edges_map[org_edge])].append(ci)
            out_data[ci] = {"ci": ci, "cells": [], "polys": [poly], "color": -1, "level": -int(interior)}
                    
    cells_graph = make_cells_graph(edges_graph)

    if SUPP_FN is not None:
        head = None
        with open(REP+SUPP_FN) as fp:
            for line in fp:
                parts = line.strip().split("\t")
                if head is None:
                    head = dict([(v,k) for (k,v) in enumerate(parts)])
                else:
                    cells_colors = numpy.zeros(len(cell_map), dtype=int)
                    cells_to_ccs = numpy.zeros(len(cell_map), dtype=int)
                    ccs_data = {}
                    for si, supp in enumerate(["Exx", "Exo", "Eox", "Eoo"]):
                        for p in parts[head["supp_%s" % supp]].split(","):
                            cid = p.strip()
                            if ID_INT:
                                cid = int(cid)
                            if cid in cell_map:
                                cells_colors[cell_map[cid]] = si+1

                    adjacent = dict([(ci, {}) for ci in out_data.keys()])
                    for si in set(cells_colors):
                        for cc in connected_components(cells_graph, cells_colors, si):
                            ci = len(ccs_data)
                            cc_polys = prepare_cc_polys(cc, cell_list, coordsp)
                            ccs_data[ci] = {"ci": ci, "cells": cc, "polys": cc_polys, "color": si, "level": -1}
                            adjacent[ci] = {}
                            for c in cc:
                                cells_to_ccs[c] = ci
                    ccs_data.update(out_data)
                                
                    for edge, cs in edges_graph.items():
                        cc0 = cells_to_ccs[cs[0]] if cs[0] >= 0 else cs[0]
                        cc1 = cells_to_ccs[cs[1]] if cs[1] >= 0 else cs[1]
                        if cc0 != cc1:
                            adjacent[cc1][cc0] = adjacent[cc1].get(cc0, 0) + 1
                            adjacent[cc0][cc1] = adjacent[cc0].get(cc1, 0) + 1
                            
                    queue = [k for (k, vs) in ccs_data.items() if vs["level"] == 0]
                    nextlevel = set()
                    level = 1
                    while len(queue) > 0:                        
                        for ci in queue:
                            for cj in adjacent[ci].keys():
                                if ccs_data[cj]["level"] < 0:
                                    ccs_data[cj]["level"] = level
                                    nextlevel.add(cj)
                        queue = nextlevel
                        nextlevel = set()
                        level += 1

                    cks = sorted(ccs_data.keys(), key=lambda x: ccs_data[x]["level"])
                    for ck, data in ccs_data.items():
                        data["exterior_polys"] = [i for i in range(len(data["polys"]))]
                        if data["level"] == 0:
                            data["exterior_polys"] = []
                            continue
                        if len(data["polys"]) < 2:
                            continue
                        interior_dots = set()
                        for k in adjacent[ck].keys():
                            if data["level"] <  ccs_data[k]["level"]:
                                interior_dots.update(*ccs_data[k]["polys"])
                            
                        if len(interior_dots) > 0:                            
                            data["exterior_polys"] = [pi for pi, poly in enumerate(data["polys"]) if len(set(poly).difference(interior_dots)) > 0]
                                               
                    color_list = []
                    poly_list = []
                    for cii, ck in enumerate(cks):
                        for pi in ccs_data[ck]["exterior_polys"]:
                            color_list.append(ccs_data[ck]["color"])
                            poly_list.append(ccs_data[ck]["polys"][pi])
                        
                    for pi, poly in enumerate(poly_list):
                        xs, ys = zip(*poly)
                        plt.fill(xs, ys, color=COLORS[color_list[pi]])
                    plt.show()
                    
