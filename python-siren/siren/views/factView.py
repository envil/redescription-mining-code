import classViewBasis

import pdb

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]    

class ViewFactory(object):
    
    root_classes = [classViewBasis.ViewRed, classViewBasis.ViewList]       

    map_typeI_tids = {}
    map_tid_details = {}
    for parent_class in root_classes: 
        for cls in all_subclasses(parent_class):
            dets = cls.getViewsDetails()
            map_tid_details.update(dets)
            for tid, det in dets.items():
                for typeI in cls.getTypesI():
                    if typeI not in map_typeI_tids:
                        map_typeI_tids[typeI] = []
                    map_typeI_tids[typeI].append((det.get("ord", 100), tid))

    typesI = map_typeI_tids.keys()
    for typeI in typesI:        
        map_typeI_tids[typeI] = [x[1] for x in sorted(map_typeI_tids[typeI])]

    @classmethod
    def typeIWhat(tcl, what):
        return classViewBasis.typeIWhat(what)
                    
    @classmethod
    def getViewsInfo(tcl, typeI="r", geo=False, ext_keys=None, what=None, excludeT=None):
        infos = []
        for viewT in tcl.map_typeI_tids.get(typeI, []):
            if (excludeT is None or viewT not in excludeT):
                details = tcl.map_tid_details[viewT]
                infos.append({"viewT": viewT, "title": details["title"],
                                  "short_title": details.get("short_title", details["title"]),
                                  "ord": details["ord"], "suitable": details["class"].suitableView(geo, ext_keys, what)})
        # infos.sort(key=lambda x: (x["ord"], x["title"]))
        return infos

    @classmethod
    def getView(tcl, viewT, parent, vid):
        view_dets = tcl.map_tid_details.get(viewT)
        if view_dets is not None:
            return view_dets["class"](parent, vid, view_dets["more"])

    @classmethod
    def getDefaultViewT(tcl, typeI="r", geo=False):
        for tid in tcl.map_typeI_tids.get(typeI):
            if tcl.map_tid_details[tid]["class"].isGeoV() == geo:
                return tid
