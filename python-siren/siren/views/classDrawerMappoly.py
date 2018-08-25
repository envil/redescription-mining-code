import numpy

from classDrawerMap import DrawerMap
from classDrawerBasis import DrawerEntitiesTD
from classDrawerClust import DrawerClustTD

from ..reremi.csv_reader import read_coords_csv

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
    
    cmap_name = "Reds"
    def plotSimple(self):
        return False

    def prepareEntitiesDots(self,  vec, vec_dets, draw_settings):
        mapper = self.prepMapper()
        return [], mapper
    
    def prepareSingleVarDots(self, vec, vec_dets, draw_settings):
        mapper = self.prepMapper(vmin=0, vmax=vec_dets["etor"].shape[1], ltid=1)
        dots_draws = []
        data = self.getParentData()
        if data is not None:
            pp_data = data.initPolymapData({"gridh_percentile": 0})
            # etor = numpy.vstack([vec_dets["etor"], numpy.zeros((1, vec_dets["etor"].shape[1]), dtype=bool)])
            etor  = vec_dets["etor"]
            max_id, max_val = etor.shape
            for edge in pp_data["edges"]:
                if edge["nodes"][0] < max_id and edge["nodes"][1] < max_id and edge["nodes"][0] != -1 and edge["nodes"][1] != -1:
                    # val = numpy.sum(etor[edge["nodes"][0], :] != etor[edge["nodes"][1], :])
                    val = numpy.sum(numpy.logical_xor(etor[edge["nodes"][0], :], etor[edge["nodes"][1], :]))
                else:
                    val = max_val
                color = mapper.to_rgba(val, alpha=draw_settings["default"]["color_e"][-1])
                if val > 0:
                    dots_draws.append((edge["edge"], color, val))
        return dots_draws, mapper
    
    def plotDotsPoly(self, axe, dots_draws, draw_indices, draw_settings):
        for (ccs, color, val) in dots_draws:
            if self.bm is None:
                xs, ys = zip(*ccs)
            else:
                xs, ys = zip(*[self.bm(x,y) for (x,y) in ccs])
            axe.plot(xs, ys, color=color)
            
    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):
        return corners
