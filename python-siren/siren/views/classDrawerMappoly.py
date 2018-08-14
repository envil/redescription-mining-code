from classDrawerMap import DrawerEntitiesMap
from ..reremi.csv_reader import read_coords_csv

import pdb

SMOOTH = True

class DrawerEntitiesMappoly(DrawerEntitiesMap):

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
            pp_data = data.prepare_areas_data(vec, pm_params)
            if pp_data is not None:
                for cii, ck in enumerate(pp_data["cks"]):
                    if SMOOTH and "smooth_polys" in pp_data["ccs_data"][ck]:
                        pp_polys = pp_data["ccs_data"][ck]["smooth_polys"]
                    else:
                        pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
                    for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                        if self.bm is None:
                            xs, ys = zip(*pp_polys[pi])
                        else:
                            xs, ys = zip(*[self.bm(x,y) for (x,y) in pp_polys[pi]])
                        
                            
                        if pp_data["ccs_data"][ck]["color"] == -1:
                            axe.fill(xs, ys, color="white", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=0.66)
                        elif pp_data["ccs_data"][ck]["color"] == -2:
                            axe.fill(xs, ys, color="#FAFAFA", zorder=pp_data["ccs_data"][ck]["level"]+2, alpha=0.33)
                        else:
                            axe.fill(xs, ys, color=draw_settings[pp_data["ccs_data"][ck]["color"]]["color_e"], zorder=pp_data["ccs_data"][ck]["level"]+2)

