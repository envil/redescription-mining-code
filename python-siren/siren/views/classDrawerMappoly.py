import numpy
from matplotlib.collections import LineCollection

from classDrawerMap import DrawerMap
from classDrawerBasis import DrawerEntitiesTD
from classDrawerClust import DrawerClustTD

import pdb

SMOOTH = True

class DrawerMappoly(DrawerMap):
    def_background_zorder = 10
    
    def plotSimple(self):
        return False

    def prepareDotsDraw(self, vec, vec_dets, draw_settings):
       return self.prepareDotsDrawOther(vec, vec_dets, draw_settings)
    
    def plotDotsPoly(self, axe, dots_draw, draw_indices, draw_settings):
        data = self.getParentData()
        geoplus = None
        # pdb.set_trace()
        if data is not None:
            geoplus = data.getExtension("geoplus")
            
        if geoplus is not None:
            inter_params = self.getParamsInter()
            vec, vec_dets = self.getVecAndDets(inter_params)
            vcc = vec            
            if numpy.min(vec) < 0:
                vcc -=  numpy.min(vec)

            pp_data = geoplus.computeAreasData(vcc)
            if pp_data is not None and "cks" in pp_data:
                for cii, ck in enumerate(pp_data["cks"]):
                    pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
                    for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                        cpoly = geoplus.getEdgesCoordsFlatten(seids=pp_polys[pi])
                        if self.bm is None:
                            xs, ys, nxs, nys = zip(*cpoly)
                        else:
                            xs, ys = zip(*[self.bm(x,y) for (x,y,nx,ny) in cpoly])
                        # pdb.set_trace()
                        if pp_data["ccs_data"][ck]["color"] == -1:
                            axe.fill(xs, ys, color="white", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=1)
                        elif pp_data["ccs_data"][ck]["color"] == -2:
                            axe.fill(xs, ys, color="#FAFAFA", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=1)
                        else:
                            # axe.fill(xs, ys, color=draw_settings[pp_data["ccs_data"][ck]["color"]]["color_e"], zorder=pp_data["ccs_data"][ck]["level"]+2)
                            colorX = self.getPlotColor(pp_data["ccs_data"][ck]["nodes"][0], "fc")
                            axe.fill(xs, ys, fc=colorX[:3], ec=self.getPlotColor(pp_data["ccs_data"][ck]["nodes"][0], "ec"), zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=1)


class DrawerEntitiesMappoly(DrawerMappoly, DrawerEntitiesTD): pass
    
class DrawerClustMappoly(DrawerMappoly, DrawerClustTD): pass

class DrawerBorders(DrawerMap, DrawerClustTD):
    
    cmap_name = "Oranges"
    redistrib_colors = False

    # def initBM(self):
    #     return None, {}
    
    def plotSimple(self):
        return False

    def prepareDotsDrawOther(self, vec, vec_dets, draw_settings):
        dots_draw = {}
        mapper = None

        data = self.getParentData()
        geoplus = None
        if data is not None:
            geoplus = data.getExtension("geoplus")
            
        if geoplus is not None:
            etor  = vec_dets["etor"]

            np_data = geoplus.prepNodePairs()
            edges_coords = numpy.array(geoplus.getEdgesCoordsFlatten())
            if self.bm is None:
                edges_tensor = numpy.array([[edges_coords[:,0], edges_coords[:,2]], [edges_coords[:,1], edges_coords[:,3]]]).T
            else:
                xA, yA = self.bm(edges_coords[:,0], edges_coords[:,1])
                xZ, yZ = self.bm(edges_coords[:,2], edges_coords[:,3])
                edges_tensor = numpy.array([[xA, xZ], [yA, yZ]]).T
                # edges = numpy.array([zip(*self.bm(*zip(*edge.get("cut_edge", edge["edge"])))) for edge in pp_data["edges"]])
                # edges = numpy.array([zip(*self.bm(*zip(*edge["edge"]))) for edge in pp_data["edges"]])

            node_pairs = np_data["node_pairs"]
            
            outer = node_pairs[node_pairs[:,-1] == -1, :]
            edges_outer = edges_tensor[outer[:,0], :, :]
            
            inner = node_pairs[node_pairs[:,-1] != -1, :]
            edges_inner = edges_tensor[inner[:,0], :, :]
            ## nb_diff_spc
            vals = numpy.sum(numpy.logical_xor(etor[inner[:,1], :], etor[inner[:,2], :]), axis=1)
            # ## diff_nb_spc
            vcs = numpy.abs(numpy.sum(etor[inner[:,1], :], axis=1) - numpy.sum(etor[inner[:,2], :], axis=1))

            mapper = self.prepMapper(vmin=0, vmax=numpy.max(vcs), ltid=1)
            colors = mapper.to_rgba(vcs, alpha=draw_settings["default"]["color_e"][-1])
            dots_draw = {"edges_inner": edges_inner, "edges_outer": edges_outer,
                          "vals": vals, "colors": colors}
        return dots_draw, mapper
    
    def plotDotsPoly(self, axe, dots_draw, draw_indices, draw_settings):
        line_segments = LineCollection(dots_draw["edges_outer"], colors="#AAAAAA", linewidths=1.)
        axe.add_collection(line_segments)

        mv = float(numpy.max(dots_draw["vals"]))
        if mv > 0:
            line_segments = LineCollection(dots_draw["edges_inner"], colors=dots_draw["colors"], linewidths=2*dots_draw["vals"]/mv)
            axe.add_collection(line_segments)

    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):
        x0, x1, y0, y1, bx, by = corners
        self.hist_click_info = {"left_edge_map": x0, "right_edge_map": x1, "right_edge_occ": x1, "right_edge_hist": x1,
                                "hedges_hist": [y0], "vedges_occ": [y0]}                
        return corners
    
