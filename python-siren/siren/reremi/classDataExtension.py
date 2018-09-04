import os.path
import numpy

import polys.prepare_polygons as prep_polys
from classCol import DataError, ColM, BoolColM, CatColM, NumColM
from classRedescription import Redescription
from classSParts import SSetts
import csv_reader
import pdb

# from polys.prepare_polygons import PolyMap

class DataExtension(object):

    extension_key = "-"
    extras_map = {}
    filing = []
    params_keys = []

    def __init__(self, data, filenames=None, params=None, details=None):
        self.parent_data = data
        self.own_data = {}
        self.params_changed = set()
        if filenames is not None:
            self.doWithFiles("load", filenames, details)
        pp = {}
        if details is not None and "params" in details:
            pp.update(details["params"])
        if params is not None:
            pp.update(params)
        if len(pp) > 0:
            self.setParams(pp)
            
    @classmethod
    def getKey(tcl):
        return tcl.extension_key

    @classmethod
    def getExtensionDetails(tcl):
        return {}
    @classmethod
    def getExtrasKeys(tcl):
        return tcl.extras_map.keys()
    @classmethod
    def getFilenamesKeys(tcl):
        fks = []
        for f in tcl.filing:
            fks.extend(f.get("filenames", {}).keys())
        return fks
    @classmethod
    def getFilesDict(tcl):
        fks = {}
        for f in tcl.filing:
            fks.update(f.get("filenames", {}))
        return fks
    def getActiveFilesDict(self):
        fks = {}
        for f in self.filing:
            if ("active" not in f) or eval("self.%s()" % f["active"]):
                fks.update(f.get("filenames", {}))
        return fks

    
    def getParentData(self):
        return self.parent_data

    def hasElement(self, key):
        return key in self.own_data
    def getElement(self, key, default=None):
        return self.own_data.get(key, default)
    def setElement(self, key, elem):
        self.own_data[key] = elem
    def delElement(self, key):
        if self.hasElement(key):
            del self.own_data[key]
    def updateElements(self, vs={}):
        self.own_data.update(vs)
    def resetElements(self, replacement={}):
        self.own_data = replacement
    def retainElements(self, keys=[]):
        replacement = {}
        for k in keys:
            if self.hasElement(k):
                replacement[k] = self.getElement(k)
        self.resetElements(replacement)


    def hasChangedParams(self, pks):
        for pk in pks:
            if pk in self.params_changed:
                return True
        return False
    def checkedParams(self, pks):
        for pk in pks:
            self.params_changed.discard(pk)        
        
    def setParams(self, params):
        if "params" in params:
            params = params.get("params")
        for k in self.params_keys:
            if k in params:
                v = params[k]
                if type(v) is dict and "data" in v:
                    v = v["data"]
                if self.getElement(k) != v:
                    self.setElement(k, v)
                    self.params_changed.add(k)

        
    def closeFp(self, fp, details=None):
        if details is None or details.get("package") is None:
            fp.close()

        
    def getFp(self, fk, filenames=None, details=None, mode="r"):
        fn, folder, pck = (None, "", None)
        if filenames is None or fk not in filenames:
            fn = self.getFilesDict().get(fk)
        else:
            fn = filenames[fk]
            
        if fn is not None:
            if details is not None:
                if "tmp_dir" in details:
                    folder = details["tmp_dir"]
                if "dir" in details:
                    folder = details["dir"]
                if "package" in details:
                    pck = details["package"]
            if len(folder) > 0:
                fn = os.path.join(folder, fn)
                
            if pck is not None:
                return pck.open(fn, mode)
            else:
                return open(fn, mode)
            
    def computeExtras(self, item, extra_keys=None, details=None):
        if extra_keys is None:
            extra_keys = self.extras_map.keys()
        out = dict([(e, None) for e in extra_keys])
        map_meths = {}
        for extra_key in extra_keys:
            if extra_key in self.extras_map:
                meth = self.extras_map[extra_key]
                if meth not in map_meths:
                    map_meths[meth] = []
                map_meths[meth].append(extra_key)
        for meth, ekeys in map_meths.items():
            tmp = self.call_meth(meth, item, details)
            for ek in ekeys:
                out[ek] = tmp[ek]
        return out

    def computeExtra(self, item, extra_key=None, details=None):
        out = {}
        if extra_key in self.extras_map:
            out = self.call_meth(self.extras_map[extra_key], item, details)
        return out.get(extra_key)
    def call_meth(self, method_name, item, details=None):
        return getattr(self, method_name)(item, details)
    
    def doWithFiles(self, action="save", filenames={}, details=None):
        set_fks = None
        if filenames is not None:
            set_fks = set(filenames.keys())
        for f in self.filing:
            ffiles = f.get("filenames", {}).keys()
            if set_fks is None or len(set_fks.intersection(ffiles)) == len(ffiles):
                if f.get(action) is not None:
                    self.call_meth(f.get(action), filenames, details)
        
    
class GeoPlusExtension(DataExtension):

    extension_key = "geoplus"
    extras_map = {}
    filing = []
    params_keys = ["gridh_percentile", "gridw_fact", "smooth_fact", "natural_borders"]
    
    def reset(self):
        self.retainElements(self.params_keys)
    
    # ######################################
    # #### COMPUTATIONS
    # ######################################
    def gatherPoints(self):
        PointsMap={}
        PointsIds={}
        coords = self.getParentData().getCoordPoints()
        rnames = self.getParentData().getRNames()

        map_merge = None
        key = None
        if self.hasElement("coords_bckg"):
            map_merge = {}
            if self.hasElement("rnames_bckg"):
                key = "rnames"
            else:
                key = "coords"
                
        for i, coord in enumerate(rnames):
            PointsIds[i] = rnames[i]
            PointsMap[i] = (coords[i, 0], coords[i, 1])
            if map_merge is not None:
                if key == "rnames":
                    map_merge[PointsIds[i]] = i
                else:
                    map_merge[PointsMap[i]] = i
        org_nb = len(PointsMap)
        if self.hasElement("coords_bckg"):
            i = len(PointsIds)
            rnames = self.getElement("rnames_bckg")
            for ci, coord in enumerate(self.getElement("coords_bckg")):
                kv = coord
                rname = "bckg_%d" % i
                if key == "rnames":
                    kv = rnames[ci]
                    rname = rnames[ci]

                if kv in map_merge:
                    next_id = map_merge[kv]
                else:
                    next_id = i
                    map_merge[kv] = next_id
                    i +=1
                    
                PointsIds[next_id] = rname
                PointsMap[next_id] = coord
        ## print "NBS", org_nb, len(PointsMap)
        return PointsMap, PointsIds

    def computePolys(self, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        loc_params = ["gridw_fact", "gridh_percentile"]
        if force or not self.hasElement("polys") or self.hasChangedParams(loc_params):
            self.checkedParams(loc_params)
            PointsMap, PointsIds = self.gatherPoints()
            polys, details, edges, nodes = prep_polys.compute_polys(PointsMap, self.getElement("gridh_percentile", -1), self.getElement("gridw_fact", -1), PointsIds)
            dets = {"polys": polys, "details": details, "edges": edges, "nodes": nodes, "p_ids": PointsIds, "p_map": PointsMap}
            self.updateElements(dets)            
        return dict([(k, self.getElement(k)) for k in ["polys", "details", "edges", "nodes", "p_ids", "p_map"]])

    def prepPolys(self, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        if force or not self.hasElement("border_edges") or not self.hasElement("coordsp") or self.hasChangedParams(["gridw_fact", "gridh_percentile"]):
            self.computePolys(details=details, force=force)
            coordsp, border_edges, cell_map = prep_polys.prepPolys(self.getElement("p_ids"), self.getElement("polys"), self.getElement("details"), self.getElement("edges"), self.getElement("nodes"))
            dets = {"coordsp": coordsp, "border_edges": border_edges, "cell_map": cell_map}
            self.updateElements(dets)
        return dict([(k, self.getElement(k)) for k in ["coordsp", "border_edges", "cell_map"]])

    def prepNodePairs(self, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        if force or not self.hasElement("node_pairs") or self.hasChangedParams(["gridw_fact", "gridh_percentile"]):
            self.computePolys(details=details, force=force)
            node_pairs = prep_polys.compute_node_pairs(self.getElement("edges"), self.getParentData().nbRows())
            self.setElement("node_pairs", node_pairs)
        return dict([(k, self.getElement(k)) for k in ["node_pairs"]])

    def prepExteriorData(self, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        if force or not self.hasElement("edges_graph") or self.hasChangedParams(["gridw_fact", "gridh_percentile"]):
            self.prepPolys(details=details, force=force)
            cells_graph, edges_graph, out_data = prep_polys.prepare_exterior_data(self.getElement("coordsp"), self.getElement("border_edges"))
            dets = {"cells_graph": cells_graph, "edges_graph": edges_graph, "out_data": out_data}
            self.updateElements(dets)
        return dict([(k, self.getElement(k)) for k in ["cells_graph", "edges_graph", "out_data"]])
    
    def computeAreasData(self, cells_colors, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        self.prepExteriorData(details=details, force=force)
        ccs_data, cks, adjacent = prep_polys.prepare_areas_data(cells_colors, self.getElement("coordsp"), 
                  self.getElement("cells_graph"), self.getElement("edges_graph"), self.getElement("out_data"), self.getElement("smooth_fact", 1))
        return {"ccs_data": ccs_data, "cks": cks, "adjacent": adjacent}
        
    def computeCohesion(self, item, details=None, force=False):
        if details is None:
            details = {}
        cohesion = -1
        back_v = details.get("back_v")
        if isinstance(item, Redescription):
            vec = numpy.array(item.supports().getVectorABCD())
            back_v = SSetts.Eoo
            if details.get("spids") is not None:
                back_v = 0
                vec_org = vec
                vec = numpy.zeros(vec_org.shape, dtype=int)
                for spid in details.get("spids"):
                    vec[vec_org==spid] = 1
        elif isinstance(item, ColM):
            vec = item.getVector()
            if item.simpleBool():
                back_v = 0
        elif type(item) is tuple and len(items) >= 2:
            var = self.col(item[0], item[1])
            vec = var.getVector()
            if var.simpleBool():
                back_v = 0
        else:
            vec = item
        cohesion = self.computeVectorCohesion(vec, back_v, details, force)
        return {"cohesion": cohesion}
    extras_map["cohesion"] = "computeCohesion"
    
    def computeVectorCohesion(self, vec_org, back_v=None, details=None, force=False):
        if details is None:
            details = {}
        self.setParams(details)
        self.prepNodePairs(details=details, force=force)
        cohesion = -1
        bv = back_v if back_v is not None else float("Inf")
        node_pairs = self.getElement("node_pairs")
        vec = numpy.concatenate([vec_org, [bv]])
        nb_inner_edges = numpy.sum((vec[node_pairs[:,2]] != bv) & (vec[node_pairs[:,1]] == vec[node_pairs[:,2]]))
        if self.getElement("natural_borders", False):
            nb_outer_edges = numpy.sum((node_pairs[:,2] != -1) & (vec[node_pairs[:,1]] != vec[node_pairs[:,2]]))
        else:
            nb_outer_edges = numpy.sum(vec[node_pairs[:,1]] != vec[node_pairs[:,2]])    
        if nb_outer_edges > 0:
            cohesion = nb_inner_edges/float(nb_inner_edges+nb_outer_edges)
        return cohesion


    # ######################################
    # #### SAVING / LOADING
    # ######################################
    F_COORD_BCKG = "coords_bckg"
    filing.append({"filenames": {"extf_"+F_COORD_BCKG: F_COORD_BCKG+".csv"},
                   "save": "writeBckgCoords", "load": "readBckgCoords", "active": "containsBckgCoords"})
    def containsBckgCoords(self):
        return self.hasElement("coords_bckg")
    def writeBckgCoords(self, filenames, details=None):
        if self.hasElement("coords_bckg"):
            fp = self.getFp("extf_"+self.F_COORD_BCKG, filenames, details, "w")        
            csv_reader.write_coords_csv(fp, self.getElement("coords_bckg"), self.getElement("rnames_bckg"))
            self.closeFp(fp, details)
    def readBckgCoords(self, filenames, details=None):
        fp = self.getFp("extf_"+self.F_COORD_BCKG, filenames, details, "r")
        coords_bckg, rnames_bckg = csv_reader.read_coords_csv(fp)
        self.closeFp(fp, details)
        if coords_bckg is not None:
            self.setElement("coords_bckg", coords_bckg)
            if rnames_bckg is not None:
                self.setElement("rnames_bckg", rnames_bckg)
        return coords_bckg, rnames_bckg
    
    F_POLYS = "polys"
    F_BEDGES = "border_edges"
    filing.append({"filenames": {"extf_"+F_BEDGES: F_BEDGES+".csv", "extf_"+F_POLYS: F_POLYS+".csv"},
                   "save": "writeGeom", "load": "readGeom", "active": "containsGeom"})    
    def containsGeom(self):
        return self.hasElement("border_edges") and self.hasElement("coordsp") and self.hasElement("cell_map")
    def writeGeom(self, filenames, details=None):
        self.writePolys(filenames, details)
        self.writeBorderEdges(filenames, details)
    def readGeom(self, filenames, details=None):
        x,y = self.readPolys(filenames, details)
        z = self.readBorderEdges(filenames, details)
        return x,y,z
    
    def writePolys(self, filenames, details=None):
        if self.hasElement("coordsp") and self.hasElement("cell_map"):
            coordsp = self.getElement("coordsp")
            cell_map = self.getElement("cell_map")
            fp = self.getFp("extf_"+self.F_POLYS, filenames, details, "w")
            cell_list = sorted(cell_map.keys(), key=lambda x: cell_map[x]) 
            for ci, cn in enumerate(cell_list):
                ex, ey = zip(*coordsp[ci])
                fp.write("\"%s\",\"%s\",\"%s\"\n" % (cn, 
                                ":".join(["%s" % x for x in ex]),
                                ":".join(["%s" % y for y in ey])))
            self.closeFp(fp, details)            
    def readPolys(self, filenames, details=None):
        fp = self.getFp("extf_"+self.F_POLYS, filenames, details, "r")
        id_int = details.get("id_int", False)
        coordsp = []
        cell_map = {}
        for line in fp:
            parts = line.strip().split(",")
            iid = parts[0].strip("\"")
            if id_int:
                iid = int(iid)
            cell_map[iid] = len(cell_map)
            xs = map(float, parts[1].strip("\"").split(":"))
            ys = map(float, parts[2].strip("\"").split(":"))
            coords = None
            if len(xs) == len(ys):
                coords = zip(xs, ys)
            cc = coords #dedup_poly(coords)
            coordsp.append(cc)
        self.closeFp(fp, details)
        self.setElement("coordsp", coordsp)
        self.setElement("cell_map", cell_map)
        return coordsp, cell_map
    
    def writeBorderEdges(self, filenames, details=None): #det_fn, border_edges):
        if self.hasElement("border_edges"):
            fp = self.getFp("extf_"+self.F_BEDGES, filenames, details, "w")
            for edge, cell in border_edges.items():
                fp.write("%s:%s,%s:%s,%s,%s\n" % (edge[0][0], edge[1][0], edge[0][1], edge[1][1], cell[0], cell[1]))
            self.closeFp(fp, details)            
    def readBorderEdges(self, filenames, details=None):
        fp = self.getFp("extf_"+self.F_BEDGES, filenames, details, "r")
        id_int = details.get("id_int", False)
        border_edges = {}
        for line in fp:
            parts = line.strip().split(",")
            xs = map(float, parts[0].split(":"))
            ys = map(float, parts[1].split(":"))
            w = int(parts[3])
            iid = parts[2].strip("\"")
            if id_int:
                iid = int(iid)
            border_edges[((xs[0], ys[0]), (xs[1], ys[1]))] = (iid, w)
        self.closeFp(fp, details)
        self.setElement("border_edges", border_edges)
        return border_edges

    F_NPAIRS = "node_pairs"
    filing.append({"filenames": {"extf_"+F_NPAIRS: F_NPAIRS+".csv"}, "save": "writeNodePairs", "load": "readNodePairs", "active": "containsNodePairs"})
    def containsNodePairs(self):        
        return self.hasElement("node_pairs")
    def writeNodePairs(self, filenames, details=None):
        if self.containsNodePairs():            
            N = self.getElement("node_pairs")
            fp = self.getFp("extf_"+self.F_NPAIRS, filenames, details, "w")
            numpy.savetxt(fp, N, fmt="%d")
            self.closeFp(fp, details)
    def readNodePairs(self, filenames, details=None):
        fp = self.getFp("extf_"+self.F_NPAIRS, filenames, details, "r")
        N = numpy.loadtxt(fp, dtype=int)
        self.closeFp(fp, details)
        self.setElement("node_pairs", N)
        return N

    F_EDGES = "edges"
    filing.append({"filenames": {"extf_"+F_EDGES: F_EDGES+".csv"}, "save": "writeEdges", "load": "readEdges", "active": "containsEdges"})
    def containsEdges(self):        
        return self.hasElement("edges")
    def writeEdges(self, filenames, details=None):
        if self.containsEdges():
            edges = self.getElement("edges")
            fp = self.getFp("extf_"+self.F_EDGES, filenames, details, "w")
            fields = [('edge', "(%s,%s)"), ('cut_edge', "(%s,%s)"), ('nodes', "(%d,%d)"),
                       ('n_dist', "%f"), ('n_distTE', "%f"), ('angle', "%f"), ('far', "%d"), ('n_closer', "%d")]
            fp.write("\t".join([k for k,f in fields])+"\n")
            for edge in edges:                
                fp.write("\t".join([f % edge[k] if k in edge else "" for k,f in fields])+"\n")
            self.closeFp(fp, details)
    def readEdges(self, filenames, details=None):
        fp = self.getFp("extf_"+self.F_EDGES, filenames, details, "r")
        edges = []
        head = None
        for li, line in enumerate(fp):
            parts =  line.strip().split("\t")
            if li == 0:                
                head = [(p, i) for i,p in enumerate(parts)]
            else:
                edge = {}
                for p,i in head:
                    if len(parts[i]) > 0:
                        if p in ["edge", "cut_edge"]:
                            v = eval(parts[i])
                        elif p in ["nodes"]:
                            pp = parts[i].strip("()").split(",")
                            v = (int(pp[0]), int(pp[1]))
                        elif p in ["far", "n_closer"]:
                            v = int(parts[i])
                        else:
                            v = float(parts[i])
                        edge[p] = v
                edges.append(edge)                
        self.closeFp(fp, details)
        self.setElement("edges", edges)
        return edges
