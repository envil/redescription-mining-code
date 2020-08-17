import numpy
from matplotlib.collections import LineCollection

from ..clired.classSParts import SSetts
# from .classDrawerMap import DrawerMap
from .classDrawerMapCarto import DrawerMap
from .classDrawerBasis import DrawerEntitiesTD
from .classDrawerClust import DrawerClustTD

import pdb

SMOOTH = True

class DrawerMappoly(DrawerMap):
    def_background_zorder = 20
    
    def plotSimple(self):
        return False
    
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

            pp_data = geoplus.prepAreasData(vcc)
            if pp_data is not None and "cks" in pp_data:
                for cii, ck in enumerate(pp_data["cks"]):
                    pp_polys = pp_data["ccs_data"][ck]["polys"]
                    
                    for pi in pp_data["ccs_data"][ck]["exterior_polys"]:
                        cpoly = geoplus.prepEdgesCoordsFlatten(seids=pp_polys[pi])
                        xs, ys = self.getProjP(cpoly)
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
            edges_coords = numpy.array(geoplus.prepEdgesCoordsFlatten())
            edges_tensor = self.getProjT(edges_coords)
            node_pairs = np_data["node_pairs"]
            
            # outer = node_pairs[node_pairs[:,-1] < 0, :]
            ## outer = node_pairs[node_pairs[:,-1] == -2, :]
            outer = node_pairs[node_pairs[:,-1] < 0, :]
            edges_outer = edges_tensor[outer[:,0], :, :]
            
            inner = node_pairs[node_pairs[:,-1] >= 0, :]
            edges_inner = edges_tensor[inner[:,0], :, :]
            if etor.dtype == "bool":
                ## nb_diff_spc
                vals = numpy.sum(numpy.logical_xor(etor[inner[:,1], :], etor[inner[:,2], :]), axis=1)
                # ## diff_nb_spc
                vcs = numpy.abs(numpy.sum(etor[inner[:,1], :], axis=1) - numpy.sum(etor[inner[:,2], :], axis=1))
                name_over = None
            else:
                rng = numpy.max(etor, axis=0) - numpy.min(etor, axis=0)
                rng[rng==0] = 1.
                vals = numpy.sum(etor[inner[:,1], :] != etor[inner[:,2], :], axis=1)
                vcs = numpy.sum(numpy.abs(etor[inner[:,1], :] - etor[inner[:,2], :]) / rng, axis=1)
                name_over = "Purples"

            ### STORE EDGES FOR LATER USE
            # self.getParent().addTmpStore("edges", edges_inner[vals>0, :, :])
            
            top_vcs = numpy.max(vcs)
            step = numpy.maximum(1, int(top_vcs)/10)
            binVals = numpy.arange(0, top_vcs+step, step)
            binLbls = ["%d" % b for b in binVals]
                 
            mapper = self.prepMapper(vmin=0, vmax=numpy.max(vcs), ltid=1, name_over=name_over)
            colors = mapper.to_rgba(vcs, alpha=draw_settings["default"]["color_e"][-1])

            dots_draw = {"edges_inner": edges_inner, "edges_outer": edges_outer,
                          "vals": vals, "colors": colors}
            vec_dets.update({"binLbls": binLbls, "binVals": binVals})
        return dots_draw, mapper
    
    def plotDotsPoly(self, axe, dots_draw, draw_indices, draw_settings):
        if draw_settings.get("delta_on", True):
            # line_segments = LineCollection(dots_draw["edges_outer"], colors=draw_settings["default"]["color_e"], linewidths=1., alpha=0.6)
            line_segments = LineCollection(dots_draw["edges_outer"], colors=draw_settings[SSetts.Eoo]["color_e"], linewidths=1., alpha=0.6)            
            axe.add_collection(line_segments)

        mv = float(numpy.max(dots_draw["vals"]))
        if mv > 0:
            line_segments = LineCollection(dots_draw["edges_inner"], colors=dots_draw["colors"], linewidths=2*dots_draw["vals"]/mv)
            axe.add_collection(line_segments)


    def plotMapperHist(self, axe, vec, vec_dets, mapper, nb_bins, corners, draw_settings):
        x0, x1, y0, y1, bx, by = corners
        fracts = [.25, .05] ## ratio bars occ/fixed
        nbc = len(vec_dets["binLbls"])        
        bins_ticks = numpy.arange(nbc)
        tmpb = [b-0.5 for b in bins_ticks]
        tmpb.append(tmpb[-1]+1)

        # norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in bins_ticks]
        # norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) * 0.95*float(y1-y0) + y0 + 0.025*float(y1-y0) for bi in tmpb]
        norm_bins_ticks = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in bins_ticks]
        norm_bins = [(bi-tmpb[0])/float(tmpb[-1]-tmpb[0]) *float(y1-y0) + y0 for bi in tmpb]
        left = [norm_bins[i] for i in range(nbc)]
        width = [norm_bins[i+1]-norm_bins[i] for i in range(nbc)]

        h_hist = fracts[1]*(x1-x0)+2*bx
        bottom_hist = x1
        top_hist = bottom_hist+h_hist
        
        bckc = "white"        
        bins_lbl = vec_dets["binLbls"]
        #vvmax = int(numpy.max(vec))
        colors = [mapper.to_rgba(i) for i in vec_dets["binVals"]]        
        # colors[-1] = draw_settings["default"]["color_f"]
        
        axe.barh(y0, h_hist, y1-y0, x1, color=bckc, edgecolor=bckc, align="edge")
        # axe.plot([bottom_occ, bottom_occ], [y0, y1-y0], color="blue")
        # axe.plot([bottom_hist, bottom_hist], [y0, y1-y0], color="red")
        # axe.plot([bottom+nbr*h, bottom+nbr*h], [y0, y1-y0], color="red")
        axe.barh(left, numpy.ones(nbc)*h_hist, width, numpy.ones(nbc)*bottom_hist, color=colors, edgecolor=bckc, linewidth=2, align="edge")
        axe.plot([bottom_hist, bottom_hist], [norm_bins[0], norm_bins[-1]], color="black", linewidth=.2)
        
        x1 += h_hist #(fracts[0]+fracts[1])*(x1-x0)+2*bx

        axe.set_yticks(norm_bins_ticks)
        axe.set_yticklabels(bins_lbl, **self.view.getFontProps())
        # self.axe.yaxis.tick_right()
        axe.tick_params(direction="inout", left="off", right="on",
                            labelleft="off", labelright="on")
        return (x0, x1, y0, y1, bx, by)

    
    def makeAdditionalElements(self, panel=None):
        self.setElement("buttons", [])
        self.setElement("inter_elems", {})        
        return []
