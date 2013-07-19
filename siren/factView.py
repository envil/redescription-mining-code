from classGView import GView
from classMapView import MapView
from classParaView import ParaView
from classEProjView import EProjView
#from classVProjView import VProjView

import pdb

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]

class ViewFactory:

    avs_views = {}
    for cls in all_subclasses(GView):
        avs_views.update(cls.getViewsDetails())

    @classmethod
    def getViewsInfo(tcl, geo=False, typesI=None):
        infos = [{"viewT": viewT, "title": details["title"], "ord": details["ord"]} \
                 for viewT, details in tcl.avs_views.items() \
                 if (geo or not details["class"].geo) and (typesI is None or typesI in details["class"].typesI)]
        infos.sort(key=lambda x: (x["ord"], x["title"]))
        return infos

    @classmethod
    def getView(tcl, viewT, parent, vid):
        if tcl.avs_views.has_key(viewT):
            return tcl.avs_views[viewT]["class"](parent, vid, tcl.avs_views[viewT]["more"])

    @classmethod
    def getDefaultViewT(tcl, geo=False, type_tab="Reds"):
        if type_tab == "Row":
            return EProjView.defaultViewT
        elif geo:
            return MapView.TID
        else:
            return ParaView.TID
