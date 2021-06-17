from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docfields import DocFieldTransformer
from sphinx import addnodes
from sphinx.domains.std import GenericObject
from sphinx.locale import _, __

# /usr/lib/python3/dist-packages/sphinx/domains


class CustParam(GenericObject):

    indextemplate_one = _('%s')
    indextemplate_two = _('%s; %s')
    indextemplate = _(' preferences%s parameter identifier; %s')
    indextemplate_lbl = _(' preferences parameter label; %s')
    indextemplate_conf = _(' preferences definition file; %s')
    indextemplate_path = _(' preferences section; %s')
    indextemplate_choice = _(' preferences parameter value; %s')
    indextemplate_type = _(' preferences parameter type; %s')
    option_spec = {
        'core': directives.flag,
        'label': directives.unchanged,
        'conf_def': directives.unchanged,
        'path': directives.unchanged,
        'choices': directives.unchanged,
        'type': directives.unchanged,
    }

    def add_target_and_index(self, name, lblnode, signode):
        # type: (unicode, unicode, addnodes.desc_signature) -> None
        targetname = '%s-%s' % (self.objtype, name)
        signode['ids'].append(targetname)
        self.state.document.note_explicit_target(signode)

        # if 'core' in self.options:
        #     self.indexnode['entries'].append(("pair", self.indextemplate % (" core", name,),
        #                                       targetname, '', None))
        #     self.indexnode['entries'].append(("single", self.indextemplate % ("", name,),
        #                                       targetname, '', None))

        # else:
        #     self.indexnode['entries'].append(("pair", self.indextemplate % ("", name,),
        #                                       targetname, '', None))
        # if self.options.get('conf_def') is not None:
        #     self.indexnode['entries'].append(("single", self.indextemplate_conf % (self.options.get('conf_def'),),
        #                                       targetname, '', None))
        # if self.options.get('type') is not None:
        #     self.indexnode['entries'].append(("single", self.indextemplate_type % (self.options.get('type'),),
        #                                       targetname, '', None))

        #################################
        self.indexnode['entries'].append(("single", self.indextemplate_one % (name,),
                                          targetname, '', None))

        if self.options.get('path') is not None:
            pths = [pth.strip() for pth in self.options.get('path').split(",")]
            for i in range(len(pths)):
                self.indexnode['entries'].append(("single", _("; ".join(pths[i:]+[name])),
                                                  targetname, '', None))

        if self.options.get('choices') is not None:
            for choice in self.options.get('choices').split(","):
                c = choice.strip()
                if len(c) > 1:
                    self.indexnode['entries'].append(("single", self.indextemplate_two % (c, name),
                                                      targetname, '', None))

        if self.options.get('label') is not None and lblnode is not None:
            targetname = '%s-%s-lbl' % (self.objtype, name)
            lblnode['ids'].append(targetname)
            self.state.document.note_explicit_target(lblnode)

            self.indexnode['entries'].append(("single", self.indextemplate_one % (self.options.get('label'),),
                                              targetname, '', None))

        if self.options.get('conf_def') is not None:
            self.indexnode['entries'].append(("single", self.indextemplate_two % ("# parameters defined in "+self.options.get('conf_def'), name),
                                              targetname, '', None))
        if self.options.get('type') is not None:
            self.indexnode['entries'].append(("single", self.indextemplate_two % ("# " + self.options.get('type')+" parameters", name),
                                              targetname, '', None))

    def run(self):
        # type: () -> List[nodes.Node]
        """
        Main directive entry function, called by docutils upon encountering the
        directive.

        This directive is meant to be quite easily subclassable, so it delegates
        to several additional methods.  What it does:

        * find out if called as a domain-specific directive, set self.domain
        * create a `desc` node to fit all description inside
        * parse standard options, currently `noindex`
        * create an index node if needed as self.indexnode
        * parse all given signatures (as returned by self.get_signatures())
          using self.handle_signature(), which should either return a name
          or raise ValueError
        * add index entries using self.add_target_and_index()
        * parse the content and handle doc fields in it
        """
        if ':' in self.name:
            self.domain, self.objtype = self.name.split(':', 1)
        else:
            self.domain, self.objtype = '', self.name
        self.indexnode = addnodes.index(entries=[])

        node = addnodes.desc()
        node.document = self.state.document
        node['domain'] = self.domain
        # 'desctype' is a backwards compatible attribute
        node['objtype'] = node['desctype'] = self.objtype
        node['noindex'] = noindex = ('noindex' in self.options)

        self.names = []  # type: List[unicode]
        signatures = self.get_signatures()

        lblnode = None
        if self.options.get('label') is not None:
            label = self.options.get('label')
            lblnode = addnodes.desc_signature(label, label)
            lblnode['first'] = False
            node.append(lblnode)

        for i, sig in enumerate(signatures):
            # add a signature node for each signature in the current unit
            # and add a reference target for it
            signode = addnodes.desc_signature(sig, '')
            signode['first'] = False
            node.append(signode)
            try:
                # name can also be a tuple, e.g. (classname, objname);
                # this is strictly domain-specific (i.e. no assumptions may
                # be made in this base class)
                name = self.handle_signature(sig, signode)
            except ValueError:
                # signature parsing failed
                signode.clear()
                signode += addnodes.desc_name(sig, sig)
                continue  # we don't want an index entry here
            if name not in self.names:
                self.names.append(name)

        self.add_target_and_index(name, lblnode, signode)

        contentnode = addnodes.desc_content()
        node.append(contentnode)
        if self.names:
            # needed for association of version{added,changed} directives
            self.env.temp_data['object'] = self.names[0]
        self.before_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        DocFieldTransformer(self).transform_all(contentnode)
        self.env.temp_data['object'] = None
        self.after_content()
        return [self.indexnode, node]


def setup(app):
    app.add_directive("cparam", CustParam)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
