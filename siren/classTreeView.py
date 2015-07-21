### TODO check which imports are needed 
from __future__ import unicode_literals
import wx
import numpy
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

from reremi.classQuery import Query, Literal, QTree
from reremi.classRedescription import Redescription
from reremi.classData import BoolColM, CatColM, NumColM
from classGView import GView, CustToolbar
from classInterObjects import ResizeableRectangle, DraggableRectangle
import toolMath

import pdb
            
class TreeView(GView):

    TID = "TR"
    SDESC = "Tree."
    ordN = 1
    title_str = "Tree"

    all_width = 1.
    height_inter = [2., 5.] ### starting at zero creates troubles with supp drawing, since it's masking non zero values..
    maj_space = 0.05
    min_space = 0.01
    flat_space = 0.03


    def __init__(self, parent, vid, more=None):
        self.reps = set()
        self.current_r = None
        self.zds = None
        self.sc = None
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

    def updateQuery(self, sd=None, query=None, force=False, upAll=True, update_trees=True):
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
            self.updateMap(update_trees)
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

        # self.MapcanvasMap.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleMouse) 
        self.MapfigMap.canvas.mpl_connect('pick_event', self.OnPick)
        # self.MapfigMap.canvas.mpl_connect('key_press_event', self.key_press_callback)
        # self.MapfigMap.canvas.mpl_connect('button_press_event', self.on_press)
        # self.MapfigMap.canvas.mpl_connect('button_release_event', self.on_release)
        # self.MapfigMap.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.MapcanvasMap.draw()

    def plotTrees(self, trees):
        draw_settings = self.getDrawSettings()
        self.plotTreesT(trees, draw_settings)
        # self.plotTreesBasic(trees, draw_settings)
        for side in [0,1]:
            self.plotTree(side, trees[side], None, draw_settings)

    def plotTreesBasic(self, trees, draw_settings):
        keys = []
        for side in [0,1]:
            for k in trees[side].getLeaves():
                keys.append((side, k, trees[side].getNodeXY(k)[1]))
                    
        mat = numpy.zeros((self.parent.dw.data.nbRows(), len(keys)+1))
        for ki, (side, k, pos) in enumerate(keys):
            for si, supp_part in enumerate(trees[side].getNodeSuppSets(k)):
                mat[list(supp_part), ki] = pos
                mat[list(supp_part), -1] = si

        mask = mat > 0
        parts = list(mat[:,-1])
        oids = numpy.argsort((mat[:,:-1].sum(axis=1)+(mat[:,-1]+1)*mat.max()*mat.shape[1])/(mask.sum(axis=1)))
        mat[oids,-1] = numpy.linspace(self.height_inter[0], self.height_inter[1], mat.shape[0])
        for li, k in zip(*numpy.where(mat[:, :-1]> 0)):
            x,y = trees[keys[k][0]].getNodeXY(keys[k][1])
            b = trees[keys[k][0]].getBottomX()
            self.axe.plot((b, 0), (y, mat[li,-1]), color=draw_settings[parts[li]]["color_e"])

    def plotTreesT(self, trees, draw_settings):
        keys = []
        lparts = trees[0].getNodeSupps(None)
        order_parts = [r for r in range(len(lparts)) if r != 2][::-1]+[2]
        pmap = dict([(v,i) for (i,v) in enumerate(order_parts)])
        nbrows = numpy.sum(lparts)
        nbtot = .05*nbrows
        nbparts = len(lparts)
        for side in [0,1]:
            for k in trees[side].getLeaves():
                keys.append((side, k, trees[side].getNodeXY(k)[1]))
                    
        mat = numpy.zeros(nbrows, dtype=int)
        parts = numpy.zeros((nbrows, nbparts), dtype=bool)
        for ki, (side, k, pos) in enumerate(keys):
            for si, supp_part in enumerate(trees[side].getNodeSuppSets(k)):
                mat[list(supp_part)] += 2**(ki+1)
                parts[list(supp_part), si] = True
        connects = []
        for v in numpy.unique(mat):
            idxs = tuple([i for (i,vb) in enumerate(bin(v)[::-1]) if vb == '1'])
            for i in range(parts.shape[1]):
                c = numpy.sum((mat == v)*parts[:,i])
                if c > 0:
                    connects.append((i, idxs, c))

        tot_height = self.height_inter[1]-self.height_inter[0]
        scores = {}
        for x in connects:
            ppi = pmap[x[0]]
            lmp = numpy.mean([keys[xx-1][-1] for xx in x[1] if keys[xx-1][0]==0])
            rmp = numpy.mean([keys[xx-1][-1] for xx in x[1] if keys[xx-1][0]==1])
            scores[x] = (ppi, lmp, rmp)

        connects.sort(key=lambda x: scores[x])
        counts = [[] for i in lparts]
        for (i, idx, c) in connects:
            counts[pmap[i]].append(c)
        bb = (1-(len(lparts)-1)*self.maj_space)*numpy.cumsum([0]+[lparts[p] for p in order_parts])/(1.*numpy.sum(lparts))
        
        pos = []
        for i in range(len(counts)):
            if len(counts[i]) > 0 and numpy.sum(counts[i]) > 0:
                bot, top = bb[i] + i*self.maj_space, bb[i+1] + i*self.maj_space
                span = top-bot - (len(counts[i])-1)*self.min_space
                sbb = span*numpy.cumsum([0]+counts[i])/(1.0*numpy.sum(counts[i]))
                for j in range(len(sbb)-1): 
                    pos.append((self.height_inter[0]+tot_height*(bot+j*self.min_space+sbb[j]),
                                self.height_inter[0]+tot_height*(bot+j*self.min_space+sbb[j+1])))

        # pos = numpy.linspace(1., 2., len(connects))
        for pi, (part, points, nb) in enumerate(connects):
            for point in points:
                #self.axe.plot((0, Xss[keys[point-1][0]][-1], 0, 0),
                b = trees[keys[point-1][0]].getBottomX()
                ff = -2.*(0.5-keys[point-1][0])*self.flat_space
                self.axe.fill((0, ff, b, ff, 0, 0),
                              (pos[pi][0], pos[pi][0], keys[point-1][-1],
                               pos[pi][1], pos[pi][1], pos[pi][0]),
                              color=draw_settings[part]["color_e"]) #, linewidth=nb/nbtot)

        
    def plotTree(self, side, tree, node, ds=None):
        
        align = {0: 'left', 1: "right"}
        color_dot = {0: ds[0]["color_e"], 1: ds[1]["color_e"]}
        line_style = {QTree.branchY: "-", QTree.branchN: "--"}
        # rsym = {0: ">", 1: "<"}
        x, y = tree.getNodeXY(node)

        # if node is not None:
        #     self.axe.annotate("#%d" % node,
        #                       xy =(x, y), xytext =(x, y-0.05))

        if tree.isLeafNode(node):
            b = tree.getBottomX()
            self.axe.plot((x, b), (y, y), 'k:')
            self.axe.plot(x, y, 'k.')
            if tree.isLeafInNode(node):
                self.axe.plot(b, y, 'ko', picker=5, gid="%d:%d:-1.T" % (side, node))
            else:
                self.axe.plot(b, y, 'wo', picker=5, gid="%d:%d:+1.T" % (side, node))
                
        else:
            # if tree.isRootNode(node):
            #     self.axe.plot(x, y, 'k'+rsym[side], picker=5, gid="%d.S" % side)
            if tree.isParentNode(node):
                for ynb in [0,1]:                        
                    for ci, child in enumerate(tree.getNodeChildren(node, ynb)):
                        xc, yc = tree.getNodeXY(child)
                        self.axe.plot((x, xc), (y, yc), 'k'+line_style[ynb], linewidth=1.5)
                        self.plotTree(side, tree, child, ds=ds)

            if tree.isSplitNode(node):
                self.axe.plot(x, y, color=color_dot[side], marker='s')
                self.axe.annotate(tree.getNodeSplit(node).disp(), # NO NAMES names=self.parent.dw.getData().getNames(side)),
                # self.axe.annotate(tree.getNodeSplit(node).disp(names=self.parent.dw.getData().getNames(side)),
                                  xy =(x, y), xytext =(x, y+0.02),
                                  horizontalalignment='center', color=color_dot[side],
                                  bbox=dict(boxstyle="round", fc="w", ec="none", alpha=0.7),
                                  )
                self.axe.annotate(tree.getNodeSplit(node).disp(), # NO NAMES names=self.parent.dw.getData().getNames(side)),
                # self.axe.annotate(tree.getNodeSplit(node).disp(names=self.parent.dw.getData().getNames(side)),
                                  xy =(x, y), xytext =(x, y+0.02),
                                  horizontalalignment='center', color=color_dot[side],
                                  bbox=dict(boxstyle="round", fc=color_dot[side], ec="none", alpha=0.3),
                                  )
                # self.axe.text(Xs[tree[node]["depth"]], Ys[node]-0.05, "%s" % (supps[node]), horizontalalignment='center')


    def updateMap(self, update_trees=True):
        """ Redraws the map
        """

        if self.current_r is not None:

            self.highl = {}
            self.hight = {}
            
            red = self.current_r
            if update_trees:
                self.trees = [red.queries[0].toTree(), red.queries[1].toTree()]
                    
            if self.trees[0] is not None and self.trees[1] is not None:
                rsupp = red.supports().parts()
                for side in [0,1]:
                    self.trees[side].computeSupps(side, self.parent.dw.getData(), rsupp)
                    if update_trees:
                        self.trees[side].positionTree(side, all_width=self.all_width, height_inter=self.height_inter)

                self.axe.cla()
                    
                # print "========= LEFT =======\n%s\n%s\n" % (red.queries[0], self.trees[0])
                # print "========= RIGHT =======\n%s\n%s\n" % ( red.queries[1], self.trees[1])

                self.plotTrees(self.trees)

                self.axe.set_xlim([-self.all_width-.5, self.all_width+.5])
                self.axe.set_ylim([self.height_inter[0]-0.1, self.height_inter[1]+0.1])

                self.axe.set_xticks([])
                self.axe.set_yticks([])

                self.MapcanvasMap.draw()
                self.MapfigMap.canvas.SetFocus()


    def additionalElements(self):
        t = self.parent.dw.getPreferences()
        add_box = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALIGN_CENTER | wx.ALL | wx.EXPAND

        add_box.Add(self.MaptoolbarMap, 0, border=3, flag=flags)
        add_box.AddSpacer((10,-1))
        self.buttons = []
        self.buttons.extend([{"element": wx.Button(self.mapFrame, wx.NewId(), size=(80,-1), label="Expand"),
                             "function": self.OnExpandSimp},
                            {"element": wx.Button(self.mapFrame, wx.NewId(), size=(110,-1), label="Simplify LHS"),
                             "function": self.OnSimplifyLHS},
                            {"element": wx.Button(self.mapFrame, wx.NewId(), size=(110,-1), label="Simplify RHS"),
                             "function": self.OnSimplifyRHS}])

        for bi, butt in enumerate(self.buttons):
            if bi > 0:
                add_box.AddSpacer((20,-1))
            add_box.Add(butt["element"], 0, border=3, flag=flags)
        add_box.AddSpacer((10,-1))

        return [add_box]

    def additionalBinds(self):
        for button in self.buttons:
            button["element"].Bind(wx.EVT_BUTTON, button["function"])


    def sendOtherPick(self, gid_parts):
        if gid_parts[-1] == "T":
            pp = gid_parts[0].split(":")
            if len(pp) == 3:
                side, node, onoff = map(int, pp)
                if self.trees[side] is not None and self.trees[side].hasNode(node):
                    if onoff == -1:
                        self.removeBranchQ(side, node)
                    else:
                        self.addBranchQ(side, node)
        elif gid_parts[-1] == "S":
            self.simplify(int(gid_parts[0]))

    def removeBranchQ(self, side, node):
        if self.trees[side].isLeafInNode(node):
            bidd = self.trees[side].getNodeLeaf(node)
            qu = self.queries[side].copy()
            bd = qu.buk.pop(bidd)                        
            if qu != self.queries[side]:
                for n in self.trees[side].getLeaves():
                    if self.trees[side].getNodeLeaf(n) > bidd:
                        self.trees[side].setNodeLeaf(n, self.trees[side].getNodeLeaf(n)-1)
                self.trees[side].setNodeLeaf(node, -1)
                self.updateQuery(side, query=qu, update_trees=False)

    def addBranchQ(self, side, node):
        if self.trees[side].isLeafOutNode(node):
            buk = self.trees[side].getBranchQuery(node)
            qu = self.queries[side].copy()
            bid = qu.appendBuk(buk)
            if qu != self.queries[side]:
                self.trees[side].setNodeLeaf(node, bid)
                self.updateQuery(side, query=qu, update_trees=False)


    def OnSimplifyLHS(self, event):
        self.simplify(0)
    def OnSimplifyRHS(self, event):
        self.simplify(1)
    def simplify(self, side):
        qu = self.trees[side].getSimpleQuery()
        self.updateQuery(side, query=qu, force=True)

