import os
import pdb
def check(cmd, mf):
    m = mf.findNode('mpl_toolkits')
    if m is None or m.filename is None:
        return None
    return dict(
        prescripts=['py2app.recipes.mpltk_prescript'],
        resources=[os.path.join(os.path.dirname(m.filename), 'basemap', 'data')],
        )
