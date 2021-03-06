# -*- coding: utf-8 -*-
"""
The Renderer class provides the infrastructure for generating template-based
code. It's used by the .grammars module for parser generation.
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import itertools
import string
from .util import trim, ustr, isiter, strtype, indent


def render(item, join='', **fields):
    """ Render the given item
    """
    if item is None:
        return ''
    elif isinstance(item, strtype):
        return item
    elif isinstance(item, Renderer):
        return item.render(join=join, **fields)
    elif isiter(item):
        return join.join(render(e, join=join, **fields) for e in iter(item) if e is not None)
    else:
        return ustr(item)


class RenderingFormatter(string.Formatter):
    def render(self, item, join='', **fields):
        return render(item, join=join, **fields)

    def format_field(self, value, spec):
        if ':' not in spec:
            return super(RenderingFormatter, self).format_field(render(value), spec)

        ind, sep, fmt = spec.split(':')
        if sep == '\\n':
            sep = '\n'

        if not ind:
            ind = 0
            mult = 0
        elif '*' in ind:
            ind, mult = ind.split('*')
        else:
            mult = 4
        ind = int(ind)
        mult = int(mult)

        if not fmt:
            fmt = '%s'

        if isiter(value):
            return indent(sep.join(fmt % self.render(v) for v in value), ind, mult)
        else:
            return indent(fmt % self.render(value), ind, mult)


class Renderer(object):
    """ Renders the fileds in the current object using a template
        provided statically, on the constructor, or as a parameter
        to render().

        Fields with a leading underscore are not made available to
        the template. Additional fields may be made available by
        overriding render_fields().
    """
    template = '{__class__}'
    _counter = itertools.count()
    formatter = RenderingFormatter()

    def __init__(self, template=None):
        if template is not None:
            self.template = template

    @classmethod
    def counter(cls):
        return next(cls._counter)

    @classmethod
    def reset_counter(cls):
        Renderer._counter = itertools.count()

    def rend(self, item, join='', **fields):
        """ A shortcut for self.formatter.render()
        """
        return self.formatter.render(item, join=join, **fields)

    def indent(self, item, ind=1, multiplier=4):
        return indent(self.rend(item), indent=ind, multiplier=4)

    def trim(self, item, tabwidth=4):
        return trim(self.rend(item), tabwidth=tabwidth)

    def render_fields(self, fields):
        """ Pre-render fields before rendering the template.
        """
        pass

    def render(self, template=None, **fields):
        fields.update(__class__=self.__class__.__name__)
        fields.update({k: v for k, v in vars(self).items() if not k.startswith('_')})

        override = self.render_fields(fields)
        if template is None:
            if override is not None:
                template = override
            else:
                template = self.template

        try:
            return self.formatter.format(trim(template), **fields)
        except KeyError:
            # find the missing key
            keys = (p[1] for p in self.formatter.parse(template))
            for key in keys:
                if key and not key in fields:
                    raise KeyError(key, type(self))
            raise

    def __str__(self):
        return self.render()

    def __repr__(self):
        return str(self)
