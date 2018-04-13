###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) 2018 Crossbar.io Technologies GmbH and contributors
# Copyright (c) 2007-2018 by the Sphinx team
#
# This file is based on code originally published here
# https://github.com/sphinx-doc/sphinx/blob/master/sphinx/domains/python.py
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import

import re

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from six import iteritems
from sphinx import addnodes, locale
from sphinx.builders import Builder
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, Index, ObjType
from sphinx.locale import _, __
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docfields import Field, GroupedField, TypedField
from sphinx.util.nodes import make_refnode

if False:
    # For type annotation
    from typing import Any, Dict, Iterable, Iterator, List, Tuple, Union  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


# REs for XBR signatures
xbr_sig_re = re.compile(
    r'''^ ([\w.]*\.)?            # interface name(s)
          (\w+)  \s*             # thing name
          (?: \(\s*(.*)\s*\)     # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
          ''', re.VERBOSE)


pairindextypes = {
    'namespace': _('namespace'),
    'keyword': _('keyword'),
    'operator': _('operator'),
    'object': _('object'),
    'exception': _('exception'),
    'statement': _('statement'),
    'builtin': _('built-in function'),
}  # Dict[unicode, unicode]


def _pseudo_parse_arglist(signode, arglist):
    # type: (addnodes.desc_signature, unicode) -> None
    """"Parse" a list of arguments separated by commas.

    Arguments can have "optional" annotations given by enclosing them in
    brackets.  Currently, this will split at any comma, even if it's inside a
    string literal (e.g. default argument value).
    """
    paramlist = addnodes.desc_parameterlist()
    stack = [paramlist]
    try:
        for argument in arglist.split(','):
            argument = argument.strip()
            ends_open = ends_close = 0
            while argument.startswith('['):
                stack.append(addnodes.desc_optional())
                stack[-2] += stack[-1]
                argument = argument[1:].strip()
            while argument.startswith(']'):
                stack.pop()
                argument = argument[1:].strip()
            while argument.endswith(']') and not argument.endswith('[]'):
                ends_close += 1
                argument = argument[:-1].strip()
            while argument.endswith('['):
                ends_open += 1
                argument = argument[:-1].strip()
            if argument:
                stack[-1] += addnodes.desc_parameter(argument, argument)
            while ends_open:
                stack.append(addnodes.desc_optional())
                stack[-2] += stack[-1]
                ends_open -= 1
            while ends_close:
                stack.pop()
                ends_close -= 1
        if len(stack) != 1:
            raise IndexError
    except IndexError:
        # if there are too few or too many elements on the stack, just give up
        # and treat the whole argument list as one argument, discarding the
        # already partially populated paramlist node
        signode += addnodes.desc_parameterlist()
        signode[-1] += addnodes.desc_parameter(arglist, arglist)
    else:
        signode += paramlist


# This override allows our inline type specifiers to behave like :interface: link
# when it comes to handling "." and "~" prefixes.
class XBRXrefMixin(object):
    def make_xref(self,
                  rolename,                  # type: unicode
                  domain,                    # type: unicode
                  target,                    # type: unicode
                  innernode=nodes.emphasis,  # type: nodes.Node
                  contnode=None,             # type: nodes.Node
                  env=None,                  # type: BuildEnvironment
                  ):
        # type: (...) -> nodes.Node
        result = super(XBRXrefMixin, self).make_xref(rolename, domain, target,  # type: ignore
                                                     innernode, contnode, env)
        result['refspecific'] = True
        if target.startswith(('.', '~')):
            prefix, result['reftarget'] = target[0], target[1:]
            if prefix == '.':
                text = target[1:]
            elif prefix == '~':
                text = target.split('.')[-1]
            for node in result.traverse(nodes.Text):
                node.parent[node.parent.index(node)] = nodes.Text(text)
                break
        return result

    def make_xrefs(self,
                   rolename,                  # type: unicode
                   domain,                    # type: unicode
                   target,                    # type: unicode
                   innernode=nodes.emphasis,  # type: nodes.Node
                   contnode=None,             # type: nodes.Node
                   env=None,                  # type: BuildEnvironment
                   ):
        # type: (...) -> List[nodes.Node]
        delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+)'
        delims_re = re.compile(delims)
        sub_targets = re.split(delims, target)

        split_contnode = bool(contnode and contnode.astext() == target)

        results = []
        for sub_target in filter(None, sub_targets):
            if split_contnode:
                contnode = nodes.Text(sub_target)

            if delims_re.match(sub_target):  # type: ignore
                results.append(contnode or innernode(sub_target, sub_target))
            else:
                results.append(self.make_xref(rolename, domain, sub_target,
                                              innernode, contnode, env))

        return results


class XBRField(XBRXrefMixin, Field):
    pass


class XBRGroupedField(XBRXrefMixin, GroupedField):
    pass


class XBRTypedField(XBRXrefMixin, TypedField):
    pass


class XBRObject(ObjectDescription):
    """
    Description of a general XBR object.

    :cvar allow_nesting: Class is an object that allows for nested namespaces
    :vartype allow_nesting: bool
    """
    option_spec = {
        'noindex': directives.flag,
        'namespace': directives.unchanged,
        'annotation': directives.unchanged,
    }

    doc_field_types = [
        XBRTypedField('parameter', label=_('Parameters'),
                      names=('param', 'parameter', 'arg', 'argument',
                             'keyword', 'kwarg', 'kwparam'),
                      typerolename='interface', typenames=('paramtype', 'type'),
                      can_collapse=True),

        XBRTypedField('variable', label=_('Variables'), rolename='obj',
                      names=('var', 'ivar', 'cvar'),
                      typerolename='interface', typenames=('vartype',),
                      can_collapse=True),

        XBRGroupedField('exceptions', label=_('Raises'), rolename='exc',
                        names=('raises', 'raise', 'exception', 'except'),
                        can_collapse=True),


        XBRGroupedField('publications', label=_('Publications'), rolename='pub',
                        names=('publishes', 'publish', 'publication'),
                        can_collapse=True),

        Field('returnvalue', label=_('Returns'), has_arg=False,
              names=('returns', 'return')),
        XBRField('returntype', label=_('Return type'), has_arg=False,
                 names=('rtype',), bodyrolename='interface'),

        Field('price', label=_('Price'), has_arg=False,
              names=('price',)),
    ]

    allow_nesting = False

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        """May return a prefix to put before the object name in the
        signature.
        """
        return ''

    def needs_arglist(self):
        # type: () -> bool
        """May return true if an empty argument list is to be generated even if
        the document contains none.
        """
        return False

    def handle_signature(self, sig, signode):
        # type: (unicode, addnodes.desc_signature) -> Tuple[unicode, unicode]
        """Transform a XBR signature into RST nodes.

        Return (fully qualified name of the thing, interfacename if any).

        If inside an interface, the current interface name is handled intelligently:
        * it is stripped from the displayed name if present
        * it is added to the full name (return value) if not present
        """
        m = xbr_sig_re.match(sig)  # type: ignore
        if m is None:
            raise ValueError
        name_prefix, name, arglist, retann = m.groups()

        # determine namespace and interface name (if applicable), as well as full name
        nsname = self.options.get(
            'namespace', self.env.ref_context.get('xbr:namespace'))
        interfacename = self.env.ref_context.get('xbr:interface')
        if interfacename:
            add_namespace = False
            if name_prefix and name_prefix.startswith(interfacename):
                fullname = name_prefix + name
                # interface name is given again in the signature
                name_prefix = name_prefix[len(interfacename):].lstrip('.')
            elif name_prefix:
                # interface name is given in the signature, but different
                # (shouldn't happen)
                fullname = interfacename + '.' + name_prefix + name
            else:
                # interface name is not given in the signature
                fullname = interfacename + '.' + name
        else:
            add_namespace = True
            if name_prefix:
                interfacename = name_prefix.rstrip('.')
                fullname = name_prefix + name
            else:
                interfacename = ''
                fullname = name

        signode['namespace'] = nsname
        signode['interface'] = interfacename
        signode['fullname'] = fullname

        sig_prefix = self.get_signature_prefix(sig)
        if sig_prefix:
            signode += addnodes.desc_annotation(sig_prefix, sig_prefix)

        if name_prefix:
            signode += addnodes.desc_addname(name_prefix, name_prefix)
        # exceptions are a special case, since they are documented in the
        # 'exceptions' namespace.
        elif add_namespace and self.env.config.add_module_names:
            nsname = self.options.get(
                'namespace', self.env.ref_context.get('xbr:namespace'))
            if nsname and nsname != 'exceptions':
                nodetext = nsname + '.'
                signode += addnodes.desc_addname(nodetext, nodetext)

        anno = self.options.get('annotation')

        signode += addnodes.desc_name(name, name)
        if not arglist:
            if self.needs_arglist():
                # for callables, add an empty parameter list
                signode += addnodes.desc_parameterlist()
            if retann:
                signode += addnodes.desc_returns(retann, retann)
            if anno:
                signode += addnodes.desc_annotation(' ' + anno, ' ' + anno)
            return fullname, name_prefix

        _pseudo_parse_arglist(signode, arglist)
        if retann:
            signode += addnodes.desc_returns(retann, retann)
        if anno:
            signode += addnodes.desc_annotation(' ' + anno, ' ' + anno)
        return fullname, name_prefix

    def get_index_text(self, nsname, name):
        # type: (unicode, unicode) -> unicode
        """Return the text for the index entry of the object."""
        raise NotImplementedError('must be implemented in subinterfaces')

    def add_target_and_index(self, name_ifc, sig, signode):
        # type: (unicode, unicode, addnodes.desc_signature) -> None
        nsname = self.options.get(
            'namespace', self.env.ref_context.get('xbr:namespace'))
        fullname = (nsname and nsname + '.' or '') + name_ifc[0]
        # note target
        if fullname not in self.state.document.ids:
            signode['names'].append(fullname)
            signode['ids'].append(fullname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            objects = self.env.domaindata['xbr']['objects']
            if fullname in objects:
                self.state_machine.reporter.warning(
                    'duplicate object description of %s, ' % fullname +
                    'other instance in ' +
                    self.env.doc2path(objects[fullname][0]) +
                    ', use :noindex: for one of them',
                    line=self.lineno)
            objects[fullname] = (self.env.docname, self.objtype)

        indextext = self.get_index_text(nsname, name_ifc)
        if indextext:
            self.indexnode['entries'].append(('single', indextext,
                                              fullname, '', None))

    def before_content(self):
        # type: () -> None
        """Handle object nesting before content

        :xbr:interface:`XBRObject` represents XBR language constructs. For
        constructs that are nestable, such as a XBR interfaces, this method will
        build up a stack of the nesting heirarchy so that it can be later
        de-nested correctly, in :xbr:meth:`after_content`.

        For constructs that aren't nestable, the stack is bypassed, and instead
        only the most recent object is tracked. This object prefix name will be
        removed with :xbr:meth:`after_content`.
        """
        prefix = None
        if self.names:
            # fullname and name_prefix come from the `handle_signature` method.
            # fullname represents the full object name that is constructed using
            # object nesting and explicit prefixes. `name_prefix` is the
            # explicit prefix given in a signature
            (fullname, name_prefix) = self.names[-1]
            if self.allow_nesting:
                prefix = fullname
            elif name_prefix:
                prefix = name_prefix.strip('.')
        if prefix:
            self.env.ref_context['xbr:interface'] = prefix
            if self.allow_nesting:
                interfaces = self.env.ref_context.setdefault('xbr:interfaces', [])
                interfaces.append(prefix)
        if 'namespace' in self.options:
            namespaces = self.env.ref_context.setdefault('xbr:namespaces', [])
            namespaces.append(self.env.ref_context.get('xbr:namespace'))
            self.env.ref_context['xbr:namespace'] = self.options['namespace']

    def after_content(self):
        # type: () -> None
        """Handle object de-nesting after content

        If this interface is a nestable object, removing the last nested interface prefix
        ends further nesting in the object.

        If this interface is not a nestable object, the list of interfaces should not
        be altered as we didn't affect the nesting levels in
        :xbr:meth:`before_content`.
        """
        interfaces = self.env.ref_context.setdefault('xbr:interfaces', [])
        if self.allow_nesting:
            try:
                interfaces.pop()
            except IndexError:
                pass
        self.env.ref_context['xbr:interface'] = (interfaces[-1] if len(interfaces) > 0
                                                 else None)
        if 'namespace' in self.options:
            namespaces = self.env.ref_context.setdefault('xbr:namespaces', [])
            if namespaces:
                self.env.ref_context['xbr:namespace'] = namespaces.pop()
            else:
                self.env.ref_context.pop('xbr:namespace')


class XBRNamespacelevel(XBRObject):
    """
    Description of an object on namespace level (functions, data).
    """

    def needs_arglist(self):
        # type: () -> bool
        return self.objtype == 'function'

    def get_index_text(self, nsname, name_ifc):
        # type: (unicode, unicode) -> unicode
        if self.objtype == 'function':
            if not nsname:
                return _('%s() (built-in function)') % name_ifc[0]
            return _('%s() (in namespace %s)') % (name_ifc[0], nsname)
        elif self.objtype == 'data':
            if not nsname:
                return _('%s (built-in variable)') % name_ifc[0]
            return _('%s (in namespace %s)') % (name_ifc[0], nsname)
        else:
            return ''


class XBRInterfacelike(XBRObject):
    """
    Description of a interface-like object (interfaces, interfaces, exceptions).
    """

    allow_nesting = True

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        return 'XBR {} '.format(self.objtype.capitalize())

    def get_index_text(self, nsname, name_ifc):
        # type: (unicode, unicode) -> unicode
        if self.objtype == 'interface':
            if not nsname:
                return _('%s (built-in interface)') % name_ifc[0]
            return _('%s (interface in %s)') % (name_ifc[0], nsname)
        elif self.objtype == 'exception':
            return name_ifc[0]
        else:
            return ''


class XBRInterfacemember(XBRObject):
    """
    Description of a interface member (methods, attributes).
    """

    def needs_arglist(self):
        # type: () -> bool
        return self.objtype.endswith('method')

    def get_signature_prefix(self, sig):
        # type: (unicode) -> unicode
        if self.objtype == 'staticmethod':
            return 'static '
        elif self.objtype in ['interfacemethod', 'event', 'procedure', 'error']:
            return 'XBR {} '.format(self.objtype.capitalize())
        return ''

    def get_index_text(self, nsname, name_ifc):
        # type: (unicode, unicode) -> unicode
        name, ifc = name_ifc
        add_namespaces = self.env.config.add_module_names
        if self.objtype == 'method':
            try:
                ifcname, methname = name.rsplit('.', 1)
            except ValueError:
                if nsname:
                    return _('%s() (in namespace %s)') % (name, nsname)
                else:
                    return '%s()' % name
            if nsname and add_namespaces:
                return _('%s() (%s.%s method)') % (methname, nsname, ifcname)
            else:
                return _('%s() (%s method)') % (methname, ifcname)
        elif self.objtype == 'staticmethod':
            try:
                ifcname, methname = name.rsplit('.', 1)
            except ValueError:
                if nsname:
                    return _('%s() (in namespace %s)') % (name, nsname)
                else:
                    return '%s()' % name
            if nsname and add_namespaces:
                return _('%s() (%s.%s static method)') % (methname, nsname,
                                                          ifcname)
            else:
                return _('%s() (%s static method)') % (methname, ifcname)
        elif self.objtype == 'interfacemethod':
            try:
                ifcname, methname = name.rsplit('.', 1)
            except ValueError:
                if nsname:
                    return _('%s() (in namespace %s)') % (name, nsname)
                else:
                    return '%s()' % name
            if nsname:
                return _('%s() (%s.%s interface method)') % (methname, nsname,
                                                             ifcname)
            else:
                return _('%s() (%s interface method)') % (methname, ifcname)
        elif self.objtype == 'attribute':
            try:
                ifcname, attrname = name.rsplit('.', 1)
            except ValueError:
                if nsname:
                    return _('%s (in namespace %s)') % (name, nsname)
                else:
                    return name
            if nsname and add_namespaces:
                return _('%s (%s.%s attribute)') % (attrname, nsname, ifcname)
            else:
                return _('%s (%s attribute)') % (attrname, ifcname)
        else:
            return ''


class XBRDecoratorMixin(object):
    """
    Mixin for decorator directives.
    """

    def handle_signature(self, sig, signode):
        # type: (unicode, addnodes.desc_signature) -> Tuple[unicode, unicode]
        ret = super(XBRDecoratorMixin, self).handle_signature(sig, signode)  # type: ignore
        signode.insert(0, addnodes.desc_addname('@', '@'))
        return ret

    def needs_arglist(self):
        # type: () -> bool
        return False


class XBRDecoratorFunction(XBRDecoratorMixin, XBRNamespacelevel):
    """
    Directive to mark functions meant to be used as decorators.
    """

    def run(self):
        # type: () -> List[nodes.Node]
        # a decorator function is a function after all
        self.name = 'xbr:function'
        return XBRNamespacelevel.run(self)


class XBRDecoratorMethod(XBRDecoratorMixin, XBRInterfacemember):
    """
    Directive to mark methods meant to be used as decorators.
    """

    def run(self):
        # type: () -> List[nodes.Node]
        self.name = 'xbr:method'
        return XBRInterfacemember.run(self)


class XBRNamespace(Directive):
    """
    Directive to mark description of a new namespace.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'platform': lambda x: x,
        'synopsis': lambda x: x,
        'noindex': directives.flag,
        'deprecated': directives.flag,
    }

    def run(self):
        # type: () -> List[nodes.Node]
        env = self.state.document.settings.env
        nsname = self.arguments[0].strip()
        noindex = 'noindex' in self.options
        env.ref_context['xbr:namespace'] = nsname
        ret = []
        if not noindex:
            env.domaindata['xbr']['namespaces'][nsname] = \
                (env.docname, self.options.get('synopsis', ''),
                 self.options.get('platform', ''), 'deprecated' in self.options)
            # make a duplicate entry in 'objects' to facilitate searching for
            # the namespace in XBRDomain.find_obj()
            env.domaindata['xbr']['objects'][nsname] = (env.docname, 'namespace')
            targetnode = nodes.target('', '', ids=['namespace-' + nsname],
                                      ismod=True)
            self.state.document.note_explicit_target(targetnode)
            # the platform and synopsis aren't printed; in fact, they are only
            # used in the nsindex currently
            ret.append(targetnode)
            indextext = _('%s (namespace)') % nsname
            inode = addnodes.index(entries=[('single', indextext,
                                             'namespace-' + nsname, '', None)])
            ret.append(inode)
        return ret


class XBRCurrentNamespace(Directive):
    """
    This directive is just to tell Sphinx that we're documenting
    stuff in namespace foo, but links to namespace foo won't lead here.
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}  # type: Dict

    def run(self):
        # type: () -> List[nodes.Node]
        env = self.state.document.settings.env
        nsname = self.arguments[0].strip()
        if nsname == 'None':
            env.ref_context.pop('xbr:namespace', None)
        else:
            env.ref_context['xbr:namespace'] = nsname
        return []


class XBRXRefRole(XRefRole):
    def process_link(self, env, refnode, has_explicit_title, title, target):
        # type: (BuildEnvironment, nodes.Node, bool, unicode, unicode) -> Tuple[unicode, unicode]  # NOQA
        refnode['xbr:namespace'] = env.ref_context.get('xbr:namespace')
        refnode['xbr:interface'] = env.ref_context.get('xbr:interface')
        if not has_explicit_title:
            title = title.lstrip('.')    # only has a meaning for the target
            target = target.lstrip('~')  # only has a meaning for the title
            # if the first character is a tilde, don't display the namespace/interface
            # parts of the contents
            if title[0:1] == '~':
                title = title[1:]
                dot = title.rfind('.')
                if dot != -1:
                    title = title[dot + 1:]
        # if the first character is a dot, search more specific namespaces first
        # else search builtins first
        if target[0:1] == '.':
            target = target[1:]
            refnode['refspecific'] = True
        return title, target


class XBRNamespaceIndex(Index):
    """
    Index subinterface to provide the XBR namespace index.
    """

    name = 'nsindex'
    localname = _('XBR Namespace Index')
    shortname = _('namespaces')

    def generate(self, docnames=None):
        # type: (Iterable[unicode]) -> Tuple[List[Tuple[unicode, List[List[Union[unicode, int]]]]], bool]  # NOQA
        content = {}  # type: Dict[unicode, List]
        # list of prefixes to ignore
        ignores = None  # type: List[unicode]
        ignores = self.domain.env.config['modindex_common_prefix']  # type: ignore
        ignores = sorted(ignores, key=len, reverse=True)
        # list of all namespaces, sorted by namespace name
        namespaces = sorted(iteritems(self.domain.data['namespaces']),
                            key=lambda x: x[0].lower())
        # sort out collapsable namespaces
        prev_nsname = ''
        num_toplevels = 0
        for nsname, (docname, synopsis, platforms, deprecated) in namespaces:
            if docnames and docname not in docnames:
                continue

            for ignore in ignores:
                if nsname.startswith(ignore):
                    nsname = nsname[len(ignore):]
                    stripped = ignore
                    break
            else:
                stripped = ''

            # we stripped the whole namespace name?
            if not nsname:
                nsname, stripped = stripped, ''

            entries = content.setdefault(nsname[0].lower(), [])

            package = nsname.split('.')[0]
            if package != nsname:
                # it's a subnamespace
                if prev_nsname == package:
                    # first subnamespace - make parent a group head
                    if entries:
                        entries[-1][1] = 1
                elif not prev_nsname.startswith(package):
                    # subnamespace without parent in list, add dummy entry
                    entries.append([stripped + package, 1, '', '', '', '', ''])
                subtype = 2
            else:
                num_toplevels += 1
                subtype = 0

            qualifier = deprecated and _('Deprecated') or ''
            entries.append([stripped + nsname, subtype, docname,
                            'namespace-' + stripped + nsname, platforms,
                            qualifier, synopsis])
            prev_nsname = nsname

        # apply heuristics when to collapse nsindex at page load:
        # only collapse if number of toplevel namespaces is larger than
        # number of subnamespaces
        collapse = len(namespaces) - num_toplevels < num_toplevels

        # sort by first letter
        sorted_content = sorted(iteritems(content))

        return sorted_content, collapse


class XBRDomain(Domain):
    """XBR language domain."""
    name = 'xbr'
    label = 'XBR'
    object_types = {
        'function': ObjType(_('function'), 'func', 'obj'),
        'data': ObjType(_('data'), 'data', 'obj'),
        'interface': ObjType(_('interface'), 'interface', 'exc', 'obj'),
        'exception': ObjType(_('exception'), 'exc', 'interface', 'obj'),
        'method': ObjType(_('method'), 'meth', 'obj'),
        'interfacemethod': ObjType(_('interface method'), 'meth', 'obj'),
        'staticmethod': ObjType(_('static method'), 'meth', 'obj'),
        'attribute': ObjType(_('attribute'), 'attr', 'obj'),
        'namespace': ObjType(_('namespace'), 'ns', 'obj'),
    }  # type: Dict[unicode, ObjType]

    directives = {
        'function': XBRNamespacelevel,
        'data': XBRNamespacelevel,
        'interface': XBRInterfacelike,
        'exception': XBRInterfacelike,
        'method': XBRInterfacemember,

        'interfacemethod': XBRInterfacemember,

        'event': XBRInterfacemember,
        'procedure': XBRInterfacemember,
        'error': XBRInterfacemember,


        'staticmethod': XBRInterfacemember,
        'attribute': XBRInterfacemember,
        'namespace': XBRNamespace,
        'currentnamespace': XBRCurrentNamespace,
        'decorator': XBRDecoratorFunction,
        'decoratormethod': XBRDecoratorMethod,
    }
    roles = {
        'data': XBRXRefRole(),
        'exc': XBRXRefRole(),
        'pub': XBRXRefRole(),
        'func': XBRXRefRole(fix_parens=True),
        'interface': XBRXRefRole(),
        'const': XBRXRefRole(),
        'attr': XBRXRefRole(),
        'meth': XBRXRefRole(fix_parens=True),
        'ns': XBRXRefRole(),
        'obj': XBRXRefRole(),
    }
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
        'namespaces': {},  # nsname -> docname, synopsis, platform, deprecated
    }  # type: Dict[unicode, Dict[unicode, Tuple[Any]]]
    indices = [
        XBRNamespaceIndex,
    ]

    def clear_doc(self, docname):
        # type: (unicode) -> None
        for fullname, (fn, _l) in list(self.data['objects'].items()):
            if fn == docname:
                del self.data['objects'][fullname]
        for nsname, (fn, _x, _x, _x) in list(self.data['namespaces'].items()):
            if fn == docname:
                del self.data['namespaces'][nsname]

    def merge_domaindata(self, docnames, otherdata):
        # type: (List[unicode], Dict) -> None
        # XXX check duplicates?
        for fullname, (fn, objtype) in otherdata['objects'].items():
            if fn in docnames:
                self.data['objects'][fullname] = (fn, objtype)
        for nsname, data in otherdata['namespaces'].items():
            if data[0] in docnames:
                self.data['namespaces'][nsname] = data

    def find_obj(self, env, nsname, interfacename, name, type, searchmode=0):
        # type: (BuildEnvironment, unicode, unicode, unicode, unicode, int) -> List[Tuple[unicode, Any]]  # NOQA
        """Find a XBR object for "name", perhaps using the given namespace
        and/or interfacename.  Returns a list of (name, object entry) tuples.
        """
        # skip parens
        if name[-2:] == '()':
            name = name[:-2]

        if not name:
            return []

        objects = self.data['objects']
        matches = []  # type: List[Tuple[unicode, Any]]

        newname = None
        if searchmode == 1:
            if type is None:
                objtypes = list(self.object_types)
            else:
                objtypes = self.objtypes_for_role(type)
            if objtypes is not None:
                if nsname and interfacename:
                    fullname = nsname + '.' + interfacename + '.' + name
                    if fullname in objects and objects[fullname][1] in objtypes:
                        newname = fullname
                if not newname:
                    if nsname and nsname + '.' + name in objects and \
                       objects[nsname + '.' + name][1] in objtypes:
                        newname = nsname + '.' + name
                    elif name in objects and objects[name][1] in objtypes:
                        newname = name
                    else:
                        # "fuzzy" searching mode
                        searchname = '.' + name
                        matches = [(oname, objects[oname]) for oname in objects
                                   if oname.endswith(searchname) and
                                   objects[oname][1] in objtypes]
        else:
            # NOTE: searching for exact match, object type is not considered
            if name in objects:
                newname = name
            elif type == 'ns':
                # only exact matches allowed for namespaces
                return []
            elif interfacename and interfacename + '.' + name in objects:
                newname = interfacename + '.' + name
            elif nsname and nsname + '.' + name in objects:
                newname = nsname + '.' + name
            elif nsname and interfacename and \
                    nsname + '.' + interfacename + '.' + name in objects:
                newname = nsname + '.' + interfacename + '.' + name
            # special case: builtin exceptions have namespace "exceptions" set
            elif type == 'exc' and '.' not in name and \
                    'exceptions.' + name in objects:
                newname = 'exceptions.' + name
            # special case: object methods
            elif type in ('func', 'meth') and '.' not in name and \
                    'object.' + name in objects:
                newname = 'object.' + name
        if newname is not None:
            matches.append((newname, objects[newname]))
        return matches

    def resolve_xref(self, env, fromdocname, builder,
                     type, target, node, contnode):
        # type: (BuildEnvironment, unicode, Builder, unicode, unicode, nodes.Node, nodes.Node) -> nodes.Node  # NOQA
        nsname = node.get('xbr:namespace')
        ifcname = node.get('xbr:interface')
        searchmode = node.hasattr('refspecific') and 1 or 0
        matches = self.find_obj(env, nsname, ifcname, target,
                                type, searchmode)
        if not matches:
            return None
        elif len(matches) > 1:
            logger.warning(__('more than one target found for cross-reference %r: %s'),
                           target, ', '.join(match[0] for match in matches),
                           type='ref', subtype='xbr', location=node)
        name, obj = matches[0]

        if obj[1] == 'namespace':
            return self._make_namespace_refnode(builder, fromdocname, name,
                                                contnode)
        else:
            return make_refnode(builder, fromdocname, obj[0], name,
                                contnode, name)

    def resolve_any_xref(self, env, fromdocname, builder, target,
                         node, contnode):
        # type: (BuildEnvironment, unicode, Builder, unicode, nodes.Node, nodes.Node) -> List[Tuple[unicode, nodes.Node]]  # NOQA
        nsname = node.get('xbr:namespace')
        ifcname = node.get('xbr:interface')
        results = []  # type: List[Tuple[unicode, nodes.Node]]

        # always search in "refspecific" mode with the :any: role
        matches = self.find_obj(env, nsname, ifcname, target, None, 1)
        for name, obj in matches:
            if obj[1] == 'namespace':
                results.append(('xbr:ns',
                                self._make_namespace_refnode(builder, fromdocname,
                                                             name, contnode)))
            else:
                results.append(('xbr:' + self.role_for_objtype(obj[1]),
                                make_refnode(builder, fromdocname, obj[0], name,
                                             contnode, name)))
        return results

    def _make_namespace_refnode(self, builder, fromdocname, name, contnode):
        # type: (Builder, unicode, unicode, nodes.Node) -> nodes.Node
        # get additional info for namespaces
        docname, synopsis, platform, deprecated = self.data['namespaces'][name]
        title = name
        if synopsis:
            title += ': ' + synopsis
        if deprecated:
            title += _(' (deprecated)')
        if platform:
            title += ' (' + platform + ')'
        return make_refnode(builder, fromdocname, docname,
                            'namespace-' + name, contnode, title)

    def get_objects(self):
        # type: () -> Iterator[Tuple[unicode, unicode, unicode, unicode, unicode, int]]
        for nsname, info in iteritems(self.data['namespaces']):
            yield (nsname, nsname, 'namespace', info[0], 'namespace-' + nsname, 0)
        for refname, (docname, type) in iteritems(self.data['objects']):
            if type != 'namespace':  # namespaces are already handled
                yield (refname, refname, type, docname, refname, 1)

    def get_full_qualified_name(self, node):
        # type: (nodes.Node) -> unicode
        nsname = node.get('xbr:namespace')
        ifcname = node.get('xbr:interface')
        target = node.get('reftarget')
        if target is None:
            return None
        else:
            return '.'.join(filter(None, [nsname, ifcname, target]))


class XBRBuilder(Builder):
    name = "xbr"

    def init(self):
        # type: () -> None
        """Load necessary templates and perform initialization.  The default
        implementation does nothing.
        """
        pass

    def get_outdated_docs(self):
        # type: () -> Union[unicode, Iterable[unicode]]
        """Return an iterable of output files that are outdated, or a string
        describing what an update build will build.

        If the builder does not output individual files corresponding to
        source files, return a string here.  If it does, return an iterable
        of those files that need to be written.
        """
        print('XBR: get_outdated_docs()')
        return 'xbr.json'

    def prepare_writing(self, docnames):
        # type: (Set[unicode]) -> None
        """A place where you can add logic before :meth:`write_doc` is run"""
        print('XBR: prepare_writing()')

    def get_target_uri(self, docname, typ=None):
        # type: (unicode, unicode) -> unicode
        """Return the target URI for a document name.

        *typ* can be used to qualify the link characteristic for individual
        builders.
        """
        target_uri = 'network.xbr'
        print('XBR: get_target_uri(docname={}, typ={}) -> {}'.format(docname, typ, target_uri))
        return target_uri

    def write_doc(self, docname, doctree):
        # type: (unicode, nodes.Node) -> None
        """Where you actually write something to the filesystem."""
        print('XBR: write_doc(docname={}, doctree={})'.format(docname, type(doctree)))

        from pprint import pprint

        def _print(nodes):
            for node in nodes:
                print('\nNODE:', dir(node), node.attributes, node.list_attributes)
                if 'interface' in str(node):
                    print(node)
                # print(node.attributes)
                # pprint(dir(node))
            if node.children:
                print('\nCHILDREN:')
                _print(node.children)

        _print(doctree)

#        for node in doctree:
#            print(dir(node), node.attributes)
#            for child in node.children:
#                print(dir(child), child.attributes)

    def finish(self):
        # type: () -> None
        """Finish the building process.

        The default implementation does nothing.
        """
        pass


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_domain(XBRDomain)
    app.add_builder(XBRBuilder)

    return {
        'version': 'builtin',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }


# https://github.com/sphinx-contrib/restbuilder/blob/master/sphinxcontrib/builders/rst.py
# https://github.com/Arello-Mobile/sphinx-confluence/blob/master/sphinx_confluence/__init__.py
# https://github.com/cgwrench/rst2md/blob/master/markdown.py
