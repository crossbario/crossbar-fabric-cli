#####################################################################################
#
#  Copyright (c) Crossbar.io Technologies GmbH
#
#  Unless a separate license agreement exists between you and Crossbar.io GmbH (e.g.
#  you have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#####################################################################################

import re
import os
from typing import List

# .. xbr:namespace:: network.xbr.mobility.navigation
# .. xbr:interface:: INavigationMonitor

# traverse directory for *.rst files,
# extract ".. xbr:" directives,
# check and parse directives
# fill in-memory data structure (trie)

# traverse in-memory data structure (trie)
# export data to

TEST = """.. xbr:interface:: INavigationMonitor

    1.0 baz

    1.1 bla

        1.1.0 foo
        1.1.1 bar

        1.1.2 bar

        1.1.3 bar

            1.1.1.1 sadsa
            1.1.1.2 sdfdsf

            1.1.1.3 yxxcs
            1.1.1.4 999s

    1.2 blub

        1.2.0 hhh
            1.2.0.0 dsfsdf
            1.2.0.1 sdfdsf
        1.2.1 jjj

"""

PAT_NSP = re.compile(r'^\s*.. xbr:namespace:: (?P<name>\S.*)$')
PAT_IFC = re.compile(r'^\s*.. xbr:interface:: (?P<name>\S.*)$')

# re.. xbr:event:: on_navigation_started(navigation_id, destination_name, coordinates, estimated_arrival, estimated_distance)

# ####------------------- 1
# ########--------------- 2
# ########--------------- 3
# ############----------- 4
# ########--------------- 5
# ####------------------- 6
# ####------------------- 7
# ########--------------- 8

# (None, [(1, []), (6, []), (8, [])])


class XBRIDLNode(object):
    def __init__(self,
                 level=0,
                 parent=None,
                 start_line=0,
                 line_no=0,
                 line=None):
        if parent and parent.level != level - 1:
            raise Exception(
                'invalid parent level {} for node with level {}'.format(
                    parent.level, level))
        self.level = level
        self.parent = parent or self
        self.start_line = start_line
        self.line_no = line_no
        self.line = line
        self.children = []

    def __str__(self):
        return 'XBRIDLNode[{id}](level={level}, parent={parent}, file_line_no={file_line_no}, line="{line}")'.format(
            id=id(self),
            level=self.level,
            parent=id(self.parent),
            line_no=self.line_no,
            file_line_no=self.start_line + self.line_no,
            line=self.line)


def _parse_tree(lines, root):

    nodes = [root]

    start_line = root.start_line
    line_no = 0

    stack = [root]

    for line in lines:

        line_no += 1

        ls = len(line) - len(line.lstrip(' '))

        is_non_empty = line.strip() != ""

        if is_non_empty:
            if ls % 4:
                raise ValueError(
                    'Indentation not a multiple of 4 spaces: "{0}" [line {}]'.
                    format(line, line_no))
            level = int(ls / 4) + 1

            if 'procedure' in line:
                print(is_non_empty, level, stack[-1].level, ls, line_no,
                      '||{}||'.format(line))

            if level > stack[-1].level + 1:
                raise ValueError(
                    'Indentation too deep: "{}" [level={}, whitespace={}, line_no={}]'.
                    format(line, level, ls, line_no))

            if level > stack[-1].level:

                # print(line)

                node = XBRIDLNode(level, stack[-1], stack[-1].start_line,
                                  line_no, line)
                stack[-1].children.append(node)

                nodes.append(node)
                # yield node

                stack.append(node)

            elif level == stack[-1].level:

                print('ZZZ ', line)

                node = XBRIDLNode(level, stack[-1].parent,
                                  stack[-1].start_line, line_no, line)
                stack[-1].children.append(node)

                nodes.append(node)
                # yield node

            else:
                print('>')

                while level + 1 < stack[-1].level:
                    stack.pop()
                print('.')
                node = XBRIDLNode(stack[-1].level, stack[-1].parent,
                                  start_line, line_no, line)
                # stack[-1].children.append(node)

                nodes.append(node)
                # yield node

        else:
            if False:
                node = XBRIDLNode(
                    None,
                    None,
                    start_line=start_line,
                    line_no=line_no,
                    line=line)
                nodes.append(node)
                # yield node
            else:
                # skip empty line
                pass
    return nodes


def _test_parse_tree():
    lines = TEST.splitlines()
    nodes = _parse_tree(lines)

    for node in nodes:
        print(node)


def _extract_from_block(block, start_line):
    lines = block.splitlines()
    l0 = lines[0]
    if l0.startswith('.. xbr:namespace::'):
        ns_match = PAT_NSP.match(lines[0])
        if not ns_match:
            raise ValueError('invalid namespace declaration: {}'.format(l0))
        #     ns_name = ns_match.group('name')
    root = XBRIDLNode(start_line=start_line)
    nodes = _parse_tree(lines, root)
    return nodes


def _extract(root, filterpaths=None):
    fileblocks = {}
    for (dirpath, dirnames, filenames) in os.walk(root):
        for f in filenames:
            if f.endswith('.rst'):
                fn = os.path.join(dirpath, f)
                blocks = []  # type: List[List[str]]
                if filterpaths is None or fn in filterpaths:
                    with open(fn) as fd:
                        contents = fd.read()
                        lines = contents.splitlines()
                        for i in range(len(lines)):
                            if lines[i].startswith('.. xbr:'):
                                j = i + 1
                                found_end = False
                                while j < len(lines):
                                    if lines[j] and not lines[j][0].isspace():
                                        found_end = True
                                        break
                                    j += 1
                                if found_end:
                                    block = '\n'.join(lines[i:j])
                                else:
                                    block = '\n'.join(lines[i:])

                                block_nodes = _extract_from_block(block, i)
                                if block_nodes:
                                    blocks.extend(block_nodes)

                if blocks:
                    fileblocks[fn] = blocks
    return fileblocks


if True:
    filterpaths = ['./api/namespace/network/xbr/mobility/navigation.rst']
    filterpaths = None
    filterpaths = ['./api/namespace/org/genivi/vss/body.rst']
    filterpaths = ['./api/namespace/com/example/basic.rst']
    fileblocks = _extract('./api/namespace', filterpaths=filterpaths)

    for fn, block_nodes in fileblocks.items():
        print('\n{}:'.format(fn))
        for node in block_nodes:
            # print(node)
            for child in node.children:
                print(node)
            # if True or '.. xbr:' in node.line or node.level == 0:
            #    print(node)

    # pprint(fileblocks)

    # _test_parse_tree()
