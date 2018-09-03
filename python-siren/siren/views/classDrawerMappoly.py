import numpy
from matplotlib.collections import LineCollection

from classDrawerMap import DrawerMap
from classDrawerBasis import DrawerEntitiesTD
from classDrawerClust import DrawerClustTD

import pdb

SMOOTH = False #True

class DrawerMappoly(DrawerMap):

    def plotSimple(self):
        return False

    def plotDotsPoly(self, axe, dots_draws, draw_indices, draw_settings):
        data = self.getParentData()
        
        if data is not None:
            inter_params = self.getParamsInter()
            vec, vec_dets = self.getVecAndDets(inter_params)
            t = self.view.getParentPreferences()
            pm_params = {}
            for key in ["gridh_percentile", "gridw_fact", "smooth_fact"]:
                if key in t:
                    pm_params[key] = t[key]["data"]
            vcc = vec            
            if numpy.min(vec) < 0:
                vcc -=  numpy.min(vec)
            ## vcc = numpy.arange(vcc.shape[0])
            pp_data = data.prepare_areas_data(vcc, pm_params)
            if pp_data is not None:
                for cii, ck in enumerate(pp_data["cks"]):
                    if SMOOTH and "smooth_polys" in pp_data["ccs_data"][ck]:
                        pp_polys = pp_data["ccs_data"][ck]["smooth_polys"]
                    else:
                        pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
                    for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                        if pp_polys[pi][0] != pp_polys[pi][-1]:
                            print cii, ck, pi, pp_data["ccs_data"][ck]["color"], pp_polys[pi][0] == pp_polys[pi][-1]
                        # if pp_polys[pi][0] == pp_polys[pi][-1]:
                        #     continue
                        if self.bm is None:
                            xs, ys = zip(*pp_polys[pi])
                        else:
                            xs, ys = zip(*[self.bm(x,y) for (x,y) in pp_polys[pi]])
                        # pdb.set_trace()
                        if pp_data["ccs_data"][ck]["color"] == -1:
                            axe.fill(xs, ys, color="white", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=0.66)
                        elif pp_data["ccs_data"][ck]["color"] == -2:
                            axe.fill(xs, ys, color="#FAFAFA", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=0.33)
                        else:
                            # axe.fill(xs, ys, color=draw_settings[pp_data["ccs_data"][ck]["color"]]["color_e"], zorder=pp_data["ccs_data"][ck]["level"]+2)
                            axe.fill(xs, ys, fc=self.getPlotColor(pp_data["ccs_data"][ck]["cells"][0], "fc"), ec=self.getPlotColor(pp_data["ccs_data"][ck]["cells"][0], "ec"), zorder=pp_data["ccs_data"][ck]["level"]+2)


class DrawerEntitiesMappoly(DrawerMappoly, DrawerEntitiesTD): pass
    
class DrawerClustMappoly(DrawerMappoly, DrawerClustTD): pass

class DrawerBorders(DrawerMap, DrawerClustTD):
    
    cmap_name = "Oranges"
    redistrib_colors = False

    def plotSimple(self):
        return False

    def prepareEntitiesDots(self,  vec, vec_dets, draw_settings):
        mapper = self.prepMapper()
        return [], mapper
    
    def prepareSingleVarDots(self, vec, vec_dets, draw_settings):
        dots_draws = {}
        mapper = None
        data = self.getParentData()       
        if data is not None:
            # etor  = vec_dets["etor"]
            mat, dets, mc = data.getMatrix(types=self.getTidForName(["Boolean"]), only_able=True)
            etor = numpy.array(mat.T, dtype=bool)

            max_id, max_val = etor.shape

            t = self.view.getParentPreferences()
            pm_params = {}
            for key in ["gridh_percentile", "gridw_fact", "smooth_fact"]:
                if key in t:
                    pm_params[key] = t[key]["data"]

            pp_data = data.initPolymapData(pm_params)
            if self.bm is None:
                edges = numpy.array([edge.get("cut_edge", edge["edge"]) for edge in pp_data["edges"]])
            else:
                edges = numpy.array([zip(*self.bm(*zip(*edge.get("cut_edge", edge["edge"])))) for edge in pp_data["edges"]])
                # edges = numpy.array([zip(*self.bm(*zip(*edge["edge"]))) for edge in pp_data["edges"]])
            
            node_pairs = numpy.array([edge["nodes"] for edge in pp_data["edges"]], dtype=int)
            far_vs = numpy.array([edge["far"] for edge in pp_data["edges"]], dtype=int)
            nodes_in = (node_pairs < max_id) & (node_pairs != -1)
            
            borders_inner = (numpy.sum(nodes_in, axis=1) == 2) & (far_vs == 0)
            borders_inter = (numpy.sum(nodes_in, axis=1) == 1) & (far_vs == 0)            
            # borders_outer = numpy.sum(nodes_in, axis=1) == 1

            edges_inner = edges[borders_inner, :, :]
            edges_inter = edges[borders_inter, :, :]
            # edges_outer = edges[borders_outer, :, :]

            nb_diff_spc = numpy.sum(numpy.logical_xor(etor[node_pairs[borders_inner,0], :], etor[node_pairs[borders_inner,1], :]), axis=1)
            diff_nb_spc = numpy.abs(numpy.sum(etor[node_pairs[borders_inner,0], :], axis=1) - numpy.sum(etor[node_pairs[borders_inner,1], :], axis=1))
            vals = diff_nb_spc # nb_diff_spc - diff_nb_spc

            mapper = self.prepMapper(vmin=0, vmax=numpy.max(nb_diff_spc), ltid=1)
            # mapper = self.prepMapper(vmin=0, vmax=numpy.max(vals), ltid=1)
            colors = mapper.to_rgba(vals, alpha=draw_settings["default"]["color_e"][-1])
            dots_draws = {"edges_inter": edges_inter, "edges_inner": edges_inner, "vals": vals, "colors": colors}
            #, "far_vs": far_vs, "sums_in": sums_in, "edges_outer": edges_outer, "edges": edges, "edges_cut": edges_cut}
        return dots_draws, mapper
    
    def plotDotsPoly(self, axe, dots_draws, draw_indices, draw_settings):
        line_segments = LineCollection(dots_draws["edges_inter"], colors="#AAAAAA", linewidths=1.)
        axe.add_collection(line_segments)

        mv = float(numpy.max(dots_draws["vals"]))
        if mv > 0:
            line_segments = LineCollection(dots_draws["edges_inner"], colors=dots_draws["colors"], linewidths=2*dots_draws["vals"]/mv)
            axe.add_collection(line_segments)

    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):
        x0, x1, y0, y1, bx, by = corners
        self.hist_click_info = {"left_edge_map": x0, "right_edge_map": x1, "right_edge_occ": x1, "right_edge_hist": x1,
                                "hedges_hist": [y0], "vedges_occ": [y0]}                
        return corners
