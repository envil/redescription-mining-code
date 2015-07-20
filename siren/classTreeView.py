### TODO check which imports are needed 
from __future__ import unicode_literals
import wx
import numpy as np
# The recommended way to use wx with mpl is with the WXAgg
# backend. 
import matplotlib
#matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
import scipy.spatial.distance
import scipy.cluster
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.patches import Ellipse
import itertools

from reremi.classQuery import Query, Literal
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView, CustToolbar
from classInterObjects import ResizeableRectangle, DraggableRectangle
import toolMath

import pdb

SIGN = -1
            
class TreeView(GView):

    TID = "TR"
    SDESC = "Tree."
    ordN = 1
    title_str = "Tree"

    def __init__(self, parent, vid, more=None):
        self.reps = set()
        self.current_r = None
        self.zds = None
        self.sc = None
        self.sld = None
        self.ri = None
        self.qcols = None
        self.trees = None
        GView.__init__(self, parent, vid)
    
    def getId(self):
        return (self.TID, self.vid)

    def setCurrent(self, qr=None, source_list=None):
        if qr is not None:
            if type(qr) in [list, tuple]:
                queries = qr
                red = Redescription.fromQueriesPair(qr, self.parent.dw.getData())
            else:
                red = qr
                queries = [red.query(0), red.query(1)]
            self.queries = queries
            red.setRestrictedSupp(self.parent.dw.getData())
            self.suppABCD = red.supports().getVectorABCD()
            self.current_r = red
            self.source_list=source_list
            self.updateText(red)
            self.updateMap()
            self.updateHist(red)
            return red

    def updateQuery(self, sd=None, query=None, force=False, upAll=True):
        if sd is None:
            queries = [self.parseQuery(0),self.parseQuery(1)]
        else:
            queries = [None, None]
            if query is None:
                queries[sd] = self.parseQuery(sd)
            else:
                queries[sd] = query

        changed = False
        old = [None, None]
        for side in [0,1]:
            old[side] = self.queries[side]
            if queries[side] != None and queries[side] != self.queries[side]:
                self.queries[side] = queries[side]
                changed = True

        red = None
        if changed or force:
            try:
                red = Redescription.fromQueriesPair(self.queries, self.parent.dw.getData())
            except Exception:
                ### Query could be parse but not recomputed
                red = None
                self.queries = old
        if red is not None:
            red.setRestrictedSupp(self.parent.dw.getData())
            self.suppABCD = red.supports().getVectorABCD()
            self.current_r = red
            if upAll:
                self.updateText(red)
                self.makeMenu()
                self.updateOriginal(red)
                self.updateHist(red)
            self.updateMap()
            return red
        else: ### wrongly formatted query, revert
            for side in [0,1]:
                self.updateQueryText(self.queries[side], side)
        return None
        
    def drawMap(self):
        """ Draws the map
        """
        self.highl = {}
        self.hight = {}
        self.MapfigMap = plt.figure()
        self.MapcanvasMap = FigCanvas(self.mapFrame, -1, self.MapfigMap)
        self.MaptoolbarMap = CustToolbar(self.MapcanvasMap, self)
        self.MapfigMap.clear()
        self.axe = self.MapfigMap.add_subplot(111)

        self.el = Ellipse((2, -1), 0.5, 0.5)
        self.axe.add_patch(self.el)

        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        # self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        # self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press)
        # self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release)
        # self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.MapcanvasMap.draw()

    def plotTrees(self, trees, supps, lparts, Xss, Yss):
        draw_settings = self.getDrawSettings()
        self.plotTreesT(trees, supps, lparts, Xss, Yss, draw_settings)
        for side in [0,1]:
            self.plotTree(side, trees[side], None, Xss[side], Yss[side], supps[side], draw_settings)


    def plotTreesBasic(self, trees, supps, lparts, Xss, Yss, draw_settings):
        keys = []
        nbparts = 0
        for side in [0,1]:
            for k,ls in supps[side].items():
                if type(k) is tuple:
                    if len(ls) > nbparts:
                        nbparts = len(ls)
                    keys.append((side, k, Yss[side][k]))
                    
        mat = np.zeros((self.parent.dw.data.nbRows(), len(keys)+1))
        for ki, (side, k, pos) in enumerate(keys):
            for si, supp_part in enumerate(supps[side][k]):
                mat[list(supp_part), ki] = pos
                mat[list(supp_part), -1] = si
        mask = mat > 0
        parts = list(mat[:,-1])
        oids = np.argsort((mat[:,:-1].sum(axis=1)+(mat[:,-1]+1)*mat.max()*mat.shape[1])/(mask.sum(axis=1)))
        mat[oids,-1] = np.linspace(1., 2., mat.shape[0])
        for li, k in zip(*np.where(mat[:, :-1]> 0)):
            self.axe.plot((Xss[keys[k][0]][-1], 0), (SIGN*keys[k][-1], SIGN*mat[li,-1]), color=draw_settings[parts[li]]["color_e"])

    def plotTreesT(self, trees, supps, lparts, Xss, Yss, draw_settings):
        keys = []
        order_parts = [r for r in range(len(lparts)) if r != 2][::-1]+[2]
        pmap = dict([(v,i) for (i,v) in enumerate(order_parts)])
        nbtot = .05*self.parent.dw.data.nbRows()
        nbparts = 0
        for side in [0,1]:
            for k,ls in supps[side].items():
                if type(k) is tuple:
                    if len(ls) > nbparts:
                        nbparts = len(ls)
                    keys.append((side, k, Yss[side][k]))
                    
        mat = np.zeros(self.parent.dw.data.nbRows(), dtype=int)
        parts = np.zeros((self.parent.dw.data.nbRows(), nbparts), dtype=bool)
        for ki, (side, k, pos) in enumerate(keys):
            for si, supp_part in enumerate(supps[side][k]):
                mat[list(supp_part)] += 2**(ki+1)
                parts[list(supp_part), si] = True
        connects = []
        for v in np.unique(mat):
            idxs = [i for (i,vb) in enumerate(bin(v)[::-1]) if vb == '1']
            for i in range(parts.shape[1]):
                c = np.sum((mat == v)*parts[:,i])
                if c > 0:
                    connects.append((i, idxs, c))

        maj_space = 0.05
        min_space = 0.01
        connects.sort(key=lambda x: (pmap[x[0]], sum(x[1]), x[2]))
        counts = [[] for i in lparts]
        for (i, idx, c) in connects:
            counts[pmap[i]].append(c)
        bb = (1-(len(lparts)-1)*maj_space)*np.cumsum([0]+[lparts[p] for p in order_parts])/(1.0*np.sum(lparts))
        
        pos = []
        for i in range(len(counts)):
            if len(counts[i]) > 0 and np.sum(counts[i]) > 0:
                bot, top = bb[i] + i*maj_space, bb[i+1] + i*maj_space
                span = top-bot - (len(counts[i])-1)*min_space
                sbb = span*np.cumsum([0]+counts[i])/(1.0*np.sum(counts[i]))
                for j in range(len(sbb)-1): 
                    pos.append((1+bot+j*min_space+sbb[j], 1+bot+j*min_space+sbb[j+1]))

        # pos = np.linspace(1., 2., len(connects))
        for pi, (part, points, nb) in enumerate(connects):
            for point in points:
                #self.axe.plot((0, Xss[keys[point-1][0]][-1], 0, 0),
                if SIGN > 0:
                    self.axe.fill((0, Xss[keys[point-1][0]][-1], 0, 0),
                                  (pos[pi][0], keys[point-1][-1], pos[pi][1], pos[pi][0]),
                                  color=draw_settings[part]["color_e"]) #, linewidth=nb/nbtot)
                else:
                    self.axe.fill((0, Xss[keys[point-1][0]][-1], 0, 0),
                                  (pos[pi][0]-3., SIGN*keys[point-1][-1], pos[pi][1]-3., pos[pi][0]-3.),
                                  color=draw_settings[part]["color_e"]) #, linewidth=nb/nbtot)

        
    def plotTree(self, side, tree, node, Xs, Ys, supps=None, ds=None):
        
        align = {0: 'left', 1: "right"}
        color_dot = {0: ds[0]["color_e"], 1: ds[1]["color_e"]}
        line_style = {0: "-", 1: "--"}
        if "leaves" in tree[node]:
            self.axe.plot((Xs[tree[node]["depth"]], Xs[-1]), (SIGN*Ys[node], SIGN*Ys[(node, "L")]), 'k:')
            self.axe.plot(Xs[tree[node]["depth"]], SIGN*Ys[node], 'k.')
            self.axe.plot(Xs[-1], SIGN*Ys[(node, "L")], 'ko', picker=5, gid="%d:%d:-1.T" % (side, node))
            # self.axe.text(Xs[-1], Ys[(node, "L")], "%s" % tree[node]["leaves"])
            # self.axe.text(Xs[-1], Ys[(node, "L")], "%s" % (supps[node]), horizontalalignment=align[side])

        else:
            if "children" in tree[node]:
                for ynb in [0,1]:
                    cs = tree[node]["children"][ynb]
                    if len(cs) == 0 and node is not None:
                        self.axe.plot((Xs[tree[node]["depth"]], Xs[tree[node]["depth"]+1]), (SIGN*Ys[node], SIGN*Ys[(node, "X%d" % ynb)]), 'k'+line_style[ynb], linewidth=1.5)
                        self.axe.plot((Xs[tree[node]["depth"]+1], Xs[-1]), (SIGN*Ys[(node, "X%d" % ynb)], SIGN*Ys[(node, "X%d" % ynb)]), 'k:')
                        self.axe.plot(Xs[tree[node]["depth"]+1], SIGN*Ys[(node, "X%d" % ynb)], 'k.')
                        self.axe.plot(Xs[-1], SIGN*Ys[(node, "X%d" % ynb)], 'wo', picker=5, gid="%d:%d:%d.T" % (side, node, ynb))
                        # self.axe.text(Xs[-1], Ys[(node, "X%d" % ynb)], "%s" % ([len(s) for s in supps[(node, "X%d" % ynb)]]), horizontalalignment=align[side])

                        
                    for ci, child in enumerate(cs):
                        self.axe.plot((Xs[tree[node]["depth"]], Xs[tree[child]["depth"]]), (SIGN*Ys[node], SIGN*Ys[child]), 'k'+line_style[ynb], linewidth=1.5)
                        self.plotTree(side, tree, child, Xs, Ys, supps, ds=ds)

            if "split" in tree[node]:
                self.axe.plot(Xs[tree[node]["depth"]], SIGN*Ys[node], color=color_dot[side], marker='s')
                self.axe.annotate(tree[node]["split"].disp(), # NO NAMES names=self.parent.dw.getData().getNames(side)),
                                  xy =(Xs[tree[node]["depth"]], SIGN*Ys[node]), xytext =(Xs[tree[node]["depth"]], SIGN*Ys[node]+0.02), horizontalalignment='center', color=color_dot[side],
                                  bbox=dict(boxstyle="round", fc="w", ec="none", alpha=0.7),
                                  )
                self.axe.annotate(tree[node]["split"].disp(), # NO NAMES names=self.parent.dw.getData().getNames(side)),
                                  xy =(Xs[tree[node]["depth"]], SIGN*Ys[node]), xytext =(Xs[tree[node]["depth"]], SIGN*Ys[node]+0.02), horizontalalignment='center', color=color_dot[side],
                                  bbox=dict(boxstyle="round", fc=color_dot[side], ec="none", alpha=0.3),
                                  )
                # self.axe.text(Xs[tree[node]["depth"]], Ys[node]-0.05, "%s" % (supps[node]), horizontalalignment='center')



    def getLeavesYs(self, side, tree, node, interval, leaves):
        if "leaves" in tree[node]:
            leaves.append((node, "L", (interval[1]+interval[0])/2.))
        elif "children" in tree[node]:
            eps = (interval[1]-interval[0])/10.
            mid = (interval[1]+interval[0])/2.
            for ynb, subint in [(0, (interval[0]+eps, mid)), (1, (mid, interval[1]-eps))]:
                cs = tree[node]["children"][ynb]
                if len(cs) == 0 and node is not None:
                    leaves.append((node, "X%d" % ynb, (subint[1]+subint[0])/2.))                    

                if len(cs) > 0:
                    width = (subint[1]-subint[0])/len(cs)
                    for ci, child in enumerate(cs):
                        self.getLeavesYs(side, tree, child, [subint[0]+ci*width, subint[0]+(ci+1)*width], leaves)

    def setYs(self, side, tree, node, Ys):
        if "leaves" in tree[node]:
            Ys[node] = Ys[(node, "L")]
            return Ys[node]

        elif "children" in tree[node]:
            ext_p = [[],[]]
            for ynb in [0,1]:
                cs = tree[node]["children"][ynb]
                if len(cs) == 0 and node is not None:
                    ext_p[ynb].append(Ys[(node, "X%d" % ynb)])

                for ci, child in enumerate(cs):
                    ext_p[ynb].append(self.setYs(side, tree, child, Ys))
            if node is not None:
                Ys[node] = (np.max(ext_p[0]) + np.min(ext_p[1]))/2.01
            else:
                if len(ext_p[0])+len(ext_p[1]) > 0:
                    Ys[node] = np.mean(ext_p[0]+ext_p[1])
                else:
                    Ys[node] = 1.5 
        return Ys[node]

    def computeSuppSide(self, side, tree, supps={}, node=None, subsets=None):
        if subsets is None:
            subsets = [self.parent.dw.data.rows()]
        supps[node] = [len(s) for s in subsets]
        if "leaves" in tree[node]:
            supps[(node, "L")] = subsets
        else:
            if "split" in tree[node]:
                supp, miss = self.parent.dw.data.literalSuppMiss(side, tree[node]["split"])
                supps_node = [[supp & s for s in subsets],
                              [(s - supp) - miss  for s in subsets],
                              [supp & miss for s in subsets]]

            else:
                supps_node = [subsets, [set() for s in subsets], [set() for s in subsets]] 
            if "children" in tree[node]:
                for ynb in [0,1]:
                    cs = tree[node]["children"][ynb]
                    if len(cs) == 0 and node is not None:
                        supps[(node, "X%d" % ynb)] = supps_node[ynb]

                    for ci, child in enumerate(cs):
                        self.computeSuppSide(side, tree, supps, child, supps_node[ynb])


    def computeSupps(self, trees, rsupp):
        supps = [{},{}]
        for side in [0,1]:
            self.computeSuppSide(side, trees[side], supps[side], None, rsupp)
            # print [(k, len(vs)) for k,vs in supps[side].items()]
        return supps
        
    def positionTree(self, side, tree):
        mdepth = max([t.get("depth", 0) for t in tree.values()])
        width = 1./(mdepth+1)
        Xs = [-2*(0.5-side)*(i+2)*width for i in range(mdepth+2)][::-1]
        leaves = []
        self.getLeavesYs(side, tree, None, [0.,1.], leaves)
        leaves.sort(key=lambda x: x[-1])
        if len(leaves) < 2:
            width = 0
        else:
            width = 1./(len(leaves)-1)
        Ys = {}
        for li, leaf in enumerate(leaves):
            Ys[(leaf[0], leaf[1])] = 1 + li*width
        self.setYs(side, tree, None, Ys)
        return Xs, Ys


    def updateMap(self):
        """ Redraws the map
        """

        if self.current_r is not None:

            self.highl = {}
            self.hight = {}

            red = self.current_r
            draw_settings = self.getDrawSettings()
            self.axe.cla()
            self.trees = [red.queries[0].toTree(), red.queries[1].toTree()]
            if self.trees[0] is not None and self.trees[1] is not None:
                rsupp = red.supports().parts()
                supps = self.computeSupps(self.trees, rsupp)
                Xs0, Ys0 = self.positionTree(0, self.trees[0])
                Xs1, Ys1 = self.positionTree(1, self.trees[1])
                
                self.plotTrees(self.trees, supps, [len(r) for r in rsupp], [Xs0, Xs1], [Ys0, Ys1])

                self.axe.set_xlim([-1.5,1.5])
                if SIGN > 0:
                    self.axe.set_ylim([0.9,2.1])
                else:
                    self.axe.set_ylim([-2.1, -0.9,])
                self.axe.set_xticks([])
                self.axe.set_yticks([])

            self.MapcanvasMap.draw()
            self.MapfigMap.canvas.SetFocus()

    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.EXPAND

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        self.buttons = []
        self.buttons.append({"element": wx.Button(self.mapFrame, size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp})
        self.sld = wx.Slider(self.mapFrame, -1, t["details_level"]["data"], 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
        self.sld_sel = wx.Slider(self.mapFrame, -1, 10, 0, 100, wx.DefaultPosition, (150, -1), wx.SL_HORIZONTAL)
        add_box.Add(self.buttons[-1]["element"], 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY,u"- opac. disabled  +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL)
        v_box.Add(self.sld_sel, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)
        add_box.AddSpacer((20,-1))
        
        v_box = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.mapFrame, wx.ID_ANY, "-      details      +")
        v_box.Add(label, 0, border=3, flag=wx.ALIGN_CENTER | wx.ALL )
        v_box.Add(self.sld, 0, border=3, flag=flags)
        add_box.Add(v_box, 0, border=3, flag=flags)
        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])


    def sendOtherPick(self, gid_parts):
        if gid_parts[-1] == "T":
            pp = gid_parts[0].split(":")
            if len(pp) == 3:
                side, node, onoff = map(int, pp)
                if self.trees is not None and node in self.trees[side]:
                    if onoff == -1:
                        self.removeBranchQ(side, node)
                    else:
                        self.addBranchQ(side, node, onoff)

    def removeBranchQ(self, side, node):
        if self.trees[side][node].get("bid") is not None:
            bidd = self.trees[side][node].get("bid")[0]
            qu = self.queries[side].copy()
            bd = qu.buk.pop(bidd)            
            # print "BEFORE", self.queries[side]
            # print "AFTER", qu
            if qu != self.queries[side]:
                self.updateQuery(side, query=qu)

    def addBranchQ(self, side, node, ynb):
        cn = node
        buk = [Literal(ynb, self.trees[side][cn]["split"])]
        while self.trees[side][cn]["parent"] is not None:
            prt = self.trees[side][cn]["parent"]
            neg = cn in self.trees[side][prt]["children"][1]
            buk.insert(0, Literal(neg, self.trees[side][prt]["split"]))
            cn = prt
        # pdb.set_trace()
        qu = self.queries[side].copy()
        qu.appendBuk(buk)
        # print "BEFORE", self.queries[side]
        # print "AFTER", qu
        if qu != self.queries[side]:
            self.updateQuery(side, query=qu)
