#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# CAVEAT UTILITOR
# This file was automatically generated by Grako.
#    https://bitbucket.org/apalala/grako/
# Any changes you make to it will be overwritten the
# next time the file is generated.
#

from __future__ import print_function, division, unicode_literals
from grako.parsing import * # @UnusedWildImport
from grako.exceptions import * # @UnusedWildImport

__version__ = '18.298.14.45.43'

class RedQueryParser(Parser):
    def __init__(self, whitespace=None, nameguard=True, **kwargs):
        super(RedQueryParser, self).__init__(whitespace=whitespace,
            nameguard=nameguard, **kwargs)

    @rule_def
    def _QUERIES_(self):
        self._query_()
        self.ast.add_list('@', self.last_node)
        def block1():
            self._LB_()
            self._query_()
            self.ast.add_list('@', self.last_node)
        self._closure(block1)
        def block3():
            self._LB_()
        self._closure(block3)

    @rule_def
    def _LB_(self):
        self._pattern(r'\n')

    @rule_def
    def _query_(self):
        with self._choice():
            with self._option():
                self._disjunction_()
                self.ast['disjunction'] = self.last_node
            with self._option():
                self._conjunction_()
                self.ast['conjunction'] = self.last_node
            with self._option():
                self._literal_()
                self.ast['literal'] = self.last_node
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['mass_neg'] = self.last_node
                self._op_parenthesis_()
                self._conjunction_()
                self.ast['conjunction'] = self.last_node
                self._cl_parenthesis_()
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['mass_neg'] = self.last_node
                self._op_parenthesis_()
                self._disjunction_()
                self.ast['disjunction'] = self.last_node
                self._cl_parenthesis_()
            self._error('no available options')

    @rule_def
    def _disjunction_(self):
        self._disj_item_()
        self.ast.add_list('@', self.last_node)
        def block1():
            self._disj_op_()
            self._cut()
            self._disj_item_()
            self.ast.add_list('@', self.last_node)
        self._positive_closure(block1)

    @rule_def
    def _conjunction_(self):
        self._conj_item_()
        self.ast.add_list('@', self.last_node)
        def block1():
            self._conj_op_()
            self._conj_item_()
            self.ast.add_list('@', self.last_node)
        self._positive_closure(block1)

    @rule_def
    def _disj_item_(self):
        with self._choice():
            with self._option():
                self._literal_()
            with self._option():
                with self._group():
                    with self._optional():
                        self._neg_()
                        self.ast['mass_neg'] = self.last_node
                    self._op_parenthesis_()
                    self._conjunction_()
                    self.ast['conjunction'] = self.last_node
                    self._cl_parenthesis_()
            self._error('no available options')

    @rule_def
    def _conj_item_(self):
        with self._choice():
            with self._option():
                self._literal_()
            with self._option():
                with self._group():
                    with self._optional():
                        self._neg_()
                        self.ast['mass_neg'] = self.last_node
                    self._op_parenthesis_()
                    self._disjunction_()
                    self.ast['disjunction'] = self.last_node
                    self._cl_parenthesis_()
            self._error('no available options')

    @rule_def
    def _literal_(self):
        with self._choice():
            with self._option():
                self._categorical_literal_()
                self.ast['categorical_literal'] = self.last_node
            with self._option():
                self._realvalued_literal_()
                self.ast['realvalued_literal'] = self.last_node
            with self._option():
                self._anonymous_literal_()
                self.ast['anonymous_literal'] = self.last_node
            with self._option():
                self._boolean_literal_()
                self.ast['boolean_literal'] = self.last_node
            self._error('no available options')

    @rule_def
    def _categorical_literal_(self):
        with self._choice():
            with self._option():
                with self._group():
                    self._op_braket_()
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
                    self._cat_test_()
                    self.ast['cat_test'] = self.last_node
                    self._cut()
                    self._categories_()
                    self.ast['categories'] = self.last_node
                    self._cl_braket_()
            with self._option():
                with self._group():
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
                    self._cat_test_()
                    self.ast['cat_test'] = self.last_node
                    self._cut()
                    self._categories_()
                    self.ast['categories'] = self.last_node
            with self._option():
                self._neg_()
                self.ast['neg'] = self.last_node
                with self._group():
                    self._op_braket_()
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
                    self._cat_true_()
                    self._cut()
                    self._categories_()
                    self.ast['categories'] = self.last_node
                    self._cl_braket_()
            with self._option():
                self._neg_()
                self.ast['neg'] = self.last_node
                with self._group():
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
                    self._cat_true_()
                    self._cut()
                    self._categories_()
                    self.ast['categories'] = self.last_node
            self._error('no available options')

    @rule_def
    def _anonymous_literal_(self):
        with self._optional():
            self._neg_()
            self.ast['neg'] = self.last_node
        with self._group():
            self._token('?')
            self._variable_name_()
            self.ast['variable_name'] = self.last_node

    @rule_def
    def _realvalued_literal_(self):
        with self._choice():
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['neg'] = self.last_node
                with self._group():
                    self._op_braket_()
                    with self._group():
                        with self._choice():
                            with self._option():
                                with self._group():
                                    with self._optional():
                                        self._variable_value_()
                                        self.ast['lower_bound'] = self.last_node
                                        self._lth_()
                                        self._cut()
                                    self._variable_name_()
                                    self.ast['variable_name'] = self.last_node
                                    self._lth_()
                                    self._cut()
                                    self._variable_value_()
                                    self.ast['upper_bound'] = self.last_node
                            with self._option():
                                with self._group():
                                    with self._optional():
                                        self._variable_value_()
                                        self.ast['upper_bound'] = self.last_node
                                        self._gth_()
                                        self._cut()
                                    self._variable_name_()
                                    self.ast['variable_name'] = self.last_node
                                    self._gth_()
                                    self._cut()
                                    self._variable_value_()
                                    self.ast['lower_bound'] = self.last_node
                            with self._option():
                                with self._group():
                                    self._variable_value_()
                                    self.ast['lower_bound'] = self.last_node
                                    self._lth_()
                                    self._cut()
                                    self._variable_name_()
                                    self.ast['variable_name'] = self.last_node
                            with self._option():
                                with self._group():
                                    self._variable_value_()
                                    self.ast['upper_bound'] = self.last_node
                                    self._gth_()
                                    self._cut()
                                    self._variable_name_()
                                    self.ast['variable_name'] = self.last_node
                            self._error('no available options')
                    self._cl_braket_()
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['neg'] = self.last_node
                with self._group():
                    with self._choice():
                        with self._option():
                            with self._group():
                                with self._optional():
                                    self._variable_value_()
                                    self.ast['lower_bound'] = self.last_node
                                    self._lth_()
                                    self._cut()
                                self._variable_name_()
                                self.ast['variable_name'] = self.last_node
                                self._lth_()
                                self._cut()
                                self._variable_value_()
                                self.ast['upper_bound'] = self.last_node
                        with self._option():
                            with self._group():
                                with self._optional():
                                    self._variable_value_()
                                    self.ast['upper_bound'] = self.last_node
                                    self._gth_()
                                    self._cut()
                                self._variable_name_()
                                self.ast['variable_name'] = self.last_node
                                self._gth_()
                                self._cut()
                                self._variable_value_()
                                self.ast['lower_bound'] = self.last_node
                        with self._option():
                            with self._group():
                                self._variable_value_()
                                self.ast['lower_bound'] = self.last_node
                                self._lth_()
                                self._cut()
                                self._variable_name_()
                                self.ast['variable_name'] = self.last_node
                        with self._option():
                            with self._group():
                                self._variable_value_()
                                self.ast['upper_bound'] = self.last_node
                                self._gth_()
                                self._cut()
                                self._variable_name_()
                                self.ast['variable_name'] = self.last_node
                        self._error('no available options')
            self._error('no available options')

    @rule_def
    def _boolean_literal_(self):
        with self._choice():
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['neg'] = self.last_node
                with self._group():
                    self._op_braket_()
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
                    self._cl_braket_()
            with self._option():
                with self._optional():
                    self._neg_()
                    self.ast['neg'] = self.last_node
                with self._group():
                    self._variable_name_()
                    self.ast['variable_name'] = self.last_node
            self._error('no available options')

    @rule_def
    def _variable_name_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._STRING_()
                with self._option():
                    self._pattern(r'v\d+')
                self._error('expecting one of: v\\d+')

    @rule_def
    def _categories_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._category_()
                    self.ast['category'] = self.last_node
                with self._option():
                    self._op_curl_()
                    self._catlist_()
                    self.ast['catlist'] = self.last_node
                    self._cl_curl_()
                self._error('no available options')

    @rule_def
    def _catlist_(self):
        self._category_()
        self.ast.add_list('@', self.last_node)
        def block1():
            self._list_sep_()
            self._cut()
            self._category_()
            self.ast.add_list('@', self.last_node)
        self._closure(block1)

    @rule_def
    def _category_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._STRING_()
                with self._option():
                    self._pattern(r'\d+([.])?\d*')
                self._error('expecting one of: \\d+([.])?\\d*')

    @rule_def
    def _variable_value_(self):
        self._NUMBER_()

    @rule_def
    def _NUMBER_(self):
        self._pattern(r'[+-]?\d+([.])?\d*([Ee][-+]\d+)?')

    @rule_def
    def _STRING_(self):
        self._pattern(r'[^<>=!\[\]\(\)\{\}\?&|,\n\t\u2227\u2228\u2264\u2265\u2208\u2209\u2260\u00ac \d]+([^<>=!\[\]\(\)\{\}&|,\n\t\u2227\u2228\u2264\u2265\u2208\u2209\u2260\u00ac]*[^<>=!\[\]\(\)\{\}&|,\n\t\u2227\u2228\u2264\u2265\u2208\u2209\u2260\u00ac ])?')

    @rule_def
    def _op_parenthesis_(self):
        self._token('(')

    @rule_def
    def _cl_parenthesis_(self):
        self._token(')')

    @rule_def
    def _op_braket_(self):
        self._token('[')

    @rule_def
    def _cl_braket_(self):
        self._token(']')

    @rule_def
    def _op_curl_(self):
        self._token('{')

    @rule_def
    def _cl_curl_(self):
        self._token('}')

    @rule_def
    def _list_sep_(self):
        self._token(',')

    @rule_def
    def _conj_op_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('&')
                with self._option():
                    self._token('\u2227')
                self._error('expecting one of: & \u2227')

    @rule_def
    def _disj_op_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('|')
                with self._option():
                    self._token('\u2228')
                self._error('expecting one of: | \u2228')

    @rule_def
    def _lth_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('<')
                with self._option():
                    self._token('\u2264')
                self._error('expecting one of: < \u2264')

    @rule_def
    def _gth_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('>')
                with self._option():
                    self._token('\u2265')
                self._error('expecting one of: > \u2265')

    @rule_def
    def _cat_test_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._cat_true_()
                    self.ast['cat_true'] = self.last_node
                with self._option():
                    self._cat_false_()
                    self.ast['cat_false'] = self.last_node
                self._error('no available options')

    @rule_def
    def _cat_true_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._eq_()
                with self._option():
                    self._in_()
                self._error('no available options')

    @rule_def
    def _cat_false_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._neq_()
                with self._option():
                    self._nin_()
                self._error('no available options')

    @rule_def
    def _eq_(self):
        self._token('=')

    @rule_def
    def _in_(self):
        self._token('\u2208')

    @rule_def
    def _neq_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('!=')
                with self._option():
                    self._token('\u2260')
                self._error('expecting one of: \u2260 !=')

    @rule_def
    def _nin_(self):
        self._token('\u2209')

    @rule_def
    def _neg_(self):
        with self._group():
            with self._choice():
                with self._option():
                    self._token('!')
                with self._option():
                    self._token('\xac')
                self._error('expecting one of: ! \xac')



class RedQuerySemanticParser(CheckSemanticsMixin, RedQueryParser):
    pass


class RedQuerySemantics(object):
    def QUERIES(self, ast):
        return ast

    def LB(self, ast):
        return ast

    def query(self, ast):
        return ast

    def disjunction(self, ast):
        return ast

    def conjunction(self, ast):
        return ast

    def disj_item(self, ast):
        return ast

    def conj_item(self, ast):
        return ast

    def literal(self, ast):
        return ast

    def categorical_literal(self, ast):
        return ast

    def anonymous_literal(self, ast):
        return ast

    def realvalued_literal(self, ast):
        return ast

    def boolean_literal(self, ast):
        return ast

    def variable_name(self, ast):
        return ast

    def categories(self, ast):
        return ast

    def catlist(self, ast):
        return ast

    def category(self, ast):
        return ast

    def variable_value(self, ast):
        return ast

    def NUMBER(self, ast):
        return ast

    def STRING(self, ast):
        return ast

    def op_parenthesis(self, ast):
        return ast

    def cl_parenthesis(self, ast):
        return ast

    def op_braket(self, ast):
        return ast

    def cl_braket(self, ast):
        return ast

    def op_curl(self, ast):
        return ast

    def cl_curl(self, ast):
        return ast

    def list_sep(self, ast):
        return ast

    def conj_op(self, ast):
        return ast

    def disj_op(self, ast):
        return ast

    def lth(self, ast):
        return ast

    def gth(self, ast):
        return ast

    def cat_test(self, ast):
        return ast

    def cat_true(self, ast):
        return ast

    def cat_false(self, ast):
        return ast

    def eq(self, ast):
        return ast

    def in_(self, ast):
        return ast

    def neq(self, ast):
        return ast

    def nin(self, ast):
        return ast

    def neg(self, ast):
        return ast

def main(filename, startrule, trace=False):
    import json
    with open(filename) as f:
        text = f.read()
    parser = RedQueryParser(parseinfo=False)
    ast = parser.parse(text, startrule, filename=filename, trace=trace)
    print('AST:')
    print(ast)
    print()
    print('JSON:')
    print(json.dumps(ast, indent=2))
    print()

if __name__ == '__main__':
    import argparse
    import sys
    class ListRules(argparse.Action):
        def __call__(self, parser, namespace, values, option_string):
            print('Rules:')
            for r in RedQueryParser.rule_list():
                print(r)
            print()
            sys.exit(0)
    parser = argparse.ArgumentParser(description="Simple parser for RedQuery.")
    parser.add_argument('-l', '--list', action=ListRules, nargs=0,
                        help="list all rules and exit")
    parser.add_argument('-t', '--trace', action='store_true',
                        help="output trace information")
    parser.add_argument('file', metavar="FILE", help="the input file to parse")
    parser.add_argument('startrule', metavar="STARTRULE",
                        help="the start rule for parsing")
    args = parser.parse_args()

    main(args.file, args.startrule, trace=args.trace)
